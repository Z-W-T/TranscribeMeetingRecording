import os
import shutil
import subprocess
import tempfile
import glob
import requests
import time
import random
import concurrent.futures
from typing import Optional, List, Callable, Tuple

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

    def transcribe_audio_parallel(self, audio_file_path: str, chunk_seconds: Optional[int] = None, 
                            progress_callback: Optional[Callable[[int], None]] = None,
                            max_workers: Optional[int] = None) -> str:
        """并行版本的音频转录函数"""
        print(f'Starting parallel IFASR transcription for file: {audio_file_path}')
        
        if chunk_seconds is None:
            try:
                chunk_seconds = int(os.getenv('IFASR_CHUNK_DURATION', '300'))
            except Exception:
                chunk_seconds = 300


        wav_path, tmp_created = self._ensure_wav(audio_file_path)
        
        if progress_callback:
            progress_callback(0)

        parts = []
        try:
            parts = self._split_wav_to_segments(wav_path, chunk_seconds)
            
            if progress_callback:
                progress_callback(5)

            # 准备转录任务
            transcription_tasks = [(idx, part_path) for idx, part_path in enumerate(parts)]
            
            # 使用线程池并行执行
            part_texts = self._transcribe_parts_parallel(
                transcription_tasks, 
                progress_callback,
                max_workers
            )

            # 按原始顺序拼接结果
            part_texts.sort(key=lambda x: x[0])  # 按索引排序
            combined = '\n\n'.join([text for _, text in part_texts if text])
            
            if progress_callback:
                progress_callback(85)
                
            return combined
            
        except Exception as e:
            if progress_callback:
                progress_callback(-1)
            raise e
        finally:
            self._cleanup_temp_files(parts, wav_path, tmp_created)

    def _transcribe_single_part_with_retry(self, task, retry_count=0):
        """带重试的单个音频转录"""
        idx, part_path = task
        
        try:
            # 添加随机延迟，避免请求过于集中
            if retry_count > 0:
                delay = (2 ** retry_count) + random.uniform(0, 1)
                time.sleep(delay)
                print(f"🔄 重试 {retry_count}，延迟 {delay:.2f}秒: 部分 {idx}")
            
            # 使用稳健的session进行请求
            client = Ifasr.XfyunAsrClient(
                appid=self.appid,
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                audio_file_path=part_path,
            )
            
            result = client.get_transcribe_result()
            text = self._parse_transcription_result(result)
            
            return (idx, text)
            
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                return self._transcribe_single_part_with_retry(task, retry_count + 1)
            else:
                print(f"❌ 部分 {idx} 超时，已达到最大重试次数")
                return (idx, "")
                
        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                print(f"🔌 连接错误，重试 {retry_count + 1}: {e}")
                return self._transcribe_single_part_with_retry(task, retry_count + 1)
            else:
                print(f"❌ 部分 {idx} 连接错误，已达到最大重试次数: {e}")
                return (idx, "")
                
        except Exception as e:
            print(f"❌ 部分 {idx} 转录失败: {e}")
            return (idx, "")

    def _transcribe_parts_parallel(self, tasks: List[Tuple[int, str]], 
                                progress_callback: Optional[Callable[[int], None]] = None,
                                max_workers: Optional[int] = None) -> List[Tuple[int, str]]:
        """并行转录多个音频片段"""
        if max_workers is None:
            # 根据CPU核心数动态设置，但限制最大并发数
            max_workers = min(len(tasks), 6)
        print('最大并发数量：',max_workers)
        
        completed_count = 0
        total_tasks = len(tasks)
        results = []
        
        # 使用线程锁保护共享变量
        from threading import Lock
        lock = Lock()
        
        def _transcribe_single_part(task: Tuple[int, str]) -> Tuple[int, str]:
            """转录单个音频片段的内部函数"""
            result = self._transcribe_single_part_with_retry(task)
            
            # 更新进度
            nonlocal completed_count
            with lock:
                completed_count += 1
                if progress_callback:
                    # 10% (基础进度) + (已完成任务数/总任务数) * 85%
                    current_progress = 5 + int((completed_count / total_tasks) * 75)
                    progress_callback(min(current_progress, 80))
            
            return result

        # 使用线程池执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(_transcribe_single_part, task): task 
                for task in tasks
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Transcription task failed: {e}")
                    # 可以在这里添加重试逻辑
        
        return results

    def _parse_transcription_result(self, result) -> str:
        """解析转录结果（提取自原函数）"""
        try:
            text = orderResult.parse_order_result(result)
        except Exception:
            try:
                text = str(result)
            except Exception:
                text = ''
        return text

    def _cleanup_temp_files(self, parts: List[str], wav_path: str, tmp_created: bool):
        """清理临时文件（提取自原函数）"""
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