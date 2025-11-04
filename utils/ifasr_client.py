import os
import shutil
import subprocess
import tempfile
import glob
from typing import Optional, List

from utils.ifasr_lib import Ifasr, orderResult  # vendor client and parser


class IfasrAPI:
    """Wrapper that splits a (possibly large) WAV into smaller WAV files and
    uploads each part using the bundled XfyunAsrClient.upload_audio().

    This implements chunked upload by creating multiple audio files locally
    and calling the vendor client's existing upload method for each part.

    Behavior:
    - Converts non-WAV inputs to 16k mono WAV using ffmpeg.
    - Splits WAV into segments of N seconds controlled by
      IFASR_CHUNK_DURATION (default 300s = 5 minutes).
    - For each segment, calls XfyunAsrClient.upload_audio() and collects
      the responses. Does NOT poll for final transcription results.
    - Returns a list of upload responses (raw JSON dicts) in part order.
    """

    def __init__(self, appid: Optional[str] = None, access_key_id: Optional[str] = None, access_key_secret: Optional[str] = None):
        self.appid = appid or os.getenv('IFASR_APPID')
        self.access_key_id = access_key_id or os.getenv('IFASR_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('IFASR_ACCESS_KEY_SECRET')
        if not (self.appid and self.access_key_id and self.access_key_secret):
            raise ValueError('IFASR_APPID, IFASR_ACCESS_KEY_ID and IFASR_ACCESS_KEY_SECRET must be provided')

        self._client_cls = Ifasr.XfyunAsrClient

    def _ensure_wav(self, path: str) -> tuple[str, bool]:
        if not path:
            raise ValueError("audio_file_path must be provided")
        ext = os.path.splitext(path)[1].lower()
        if ext == '.wav':
            return path, False

        tmp_fd, tmp_wav = tempfile.mkstemp(suffix='.wav')
        os.close(tmp_fd)

        ffmpeg = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
        if not ffmpeg:
            raise RuntimeError('ffmpeg not found on PATH. Please install ffmpeg and ensure it is available to Python process.')

        cmd = [ffmpeg, '-y', '-i', path, '-ar', '16000', '-ac', '1', tmp_wav]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return tmp_wav, True
        except subprocess.CalledProcessError as e:
            try:
                if os.path.exists(tmp_wav):
                    os.remove(tmp_wav)
            except Exception:
                pass
            raise RuntimeError(f'ffmpeg conversion failed: {e}') from e

    def _split_wav_to_segments(self, wav_path: str, segment_seconds: int) -> List[str]:
        """Split wav into segments with ffmpeg and return list of segment file paths.

        Uses ffmpeg -f segment -segment_time to create files named part_000.wav etc.
        """
        tmpdir = tempfile.mkdtemp(prefix='ifasr_parts_')
        ffmpeg = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
        if not ffmpeg:
            raise RuntimeError('ffmpeg not found on PATH. Please install ffmpeg and ensure it is available to Python process.')

        out_pattern = os.path.join(tmpdir, 'part_%03d.wav')
        cmd = [ffmpeg, '-y', '-i', wav_path, '-f', 'segment', '-segment_time', str(segment_seconds), '-c', 'copy', out_pattern]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            # clean up dir
            try:
                for f in glob.glob(os.path.join(tmpdir, '*')):
                    os.remove(f)
                os.rmdir(tmpdir)
            except Exception:
                pass
            raise RuntimeError(f'ffmpeg splitting failed: {e}') from e

        parts = sorted(glob.glob(os.path.join(tmpdir, 'part_*.wav')))
        return parts

    def transcribe_audio(self, audio_file_path: str, chunk_seconds: Optional[int] = None) -> str:
        """Split original audio into multiple WAV parts, upload each part, wait
        for each part's transcription and return the concatenated full text.

        - audio_file_path: original audio (wav or other). Non-WAV will be converted.
        - chunk_seconds: seconds per chunk. If None, read from env IFASR_CHUNK_DURATION or default 300s.

        Returns the combined transcript string for all parts in order.
        """
        if chunk_seconds is None:
            try:
                chunk_seconds = int(os.getenv('IFASR_CHUNK_DURATION', '300'))
            except Exception:
                chunk_seconds = 300

        wav_path, tmp_created = self._ensure_wav(audio_file_path)
        parts = []
        try:
            parts = self._split_wav_to_segments(wav_path, chunk_seconds)

            part_texts = []
            for idx, part in enumerate(parts, start=1):
                client = self._client_cls(
                    appid=self.appid,
                    access_key_id=self.access_key_id,
                    access_key_secret=self.access_key_secret,
                    audio_file_path=part,
                )

                # after upload, blockingly fetch transcription for this part
                try:
                    result = client.get_transcribe_result()
                except Exception as e:
                    raise RuntimeError(f'Failed to get transcribe result for part {idx}: {e}') from e

                # parse the vendor result into text
                try:
                    text = orderResult.parse_order_result(result)
                except Exception:
                    # fallback to stringify content if parser fails
                    try:
                        text = str(result)
                    except Exception:
                        text = ''

                part_texts.append(text)

            # join parts with double newline to preserve separations
            combined = '\n\n'.join([t for t in part_texts if t])
            return combined
        finally:
            # clean up temporary files: split parts and converted wav if created
            for p in parts:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            try:
                tmpdir = os.path.dirname(parts[0]) if parts else None
                if tmpdir and os.path.isdir(tmpdir):
                    try:
                        os.rmdir(tmpdir)
                    except Exception:
                        pass
            except Exception:
                pass

            if tmp_created and wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
