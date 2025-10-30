from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent
import os
import shutil
import uuid

# Simple FastAPI wrapper to expose the agent as an HTTP API.
app = FastAPI(title="TranscribeMeetingRecording API")

# Allow the static frontend (or any origin during development) to call the API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]) 

load_dotenv()
config = Config()

# Instantiate the agent once at startup
agent = TranscriptionAgent(
    agent_setting=config.AGENT_CONFIG,
    minutes_generator_setting=config.DEEPSEEK_SETTINGS
)

ROOT_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(ROOT_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve the static frontend from / (mounts frontend folder if present)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
# Mount static files under /static to avoid intercepting API routes (mounting at "/" can capture POST and return 405)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    # Serve index.html at root explicitly so POST to /api/* routes are not intercepted by StaticFiles
    from fastapi.responses import FileResponse, Response

    @app.get("/")
    async def root_index():
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return Response(content="Frontend not found", status_code=404)

    @app.get("/favicon.ico")
    async def favicon():
        fav = os.path.join(FRONTEND_DIR, "favicon.ico")
        if os.path.exists(fav):
            return FileResponse(fav)
        # No favicon provided — return empty 204 so browsers stop requesting repeatedly
        return Response(status_code=204)


@app.post("/api/process")
async def process_meeting(
    file: UploadFile = File(...),
    attendees: str = Form(None),
    meeting_topic: str = Form(None),
    generate_minutes: bool = Form(True),
    generate_summary: bool = Form(True),
    generate_keypoints: bool = Form(False),
    generate_terms: bool = Form(False),
):
    """Upload an audio file and trigger transcription + summary/minutes generation.

    - file: multipart file upload
    - attendees: optional comma-separated list
    - meeting_topic: optional string
    """
    # Save uploaded file
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(dest_path, "wb") as dest:
            shutil.copyfileobj(file.file, dest)
    except Exception as e:
        return JSONResponse({"error": f"Failed to save uploaded file: {e}"}, status_code=500)

    attendees_list = [a.strip() for a in attendees.split(",")] if attendees else []

    try:
        # Transcribe audio first
        transcript = agent.transcribe_audio(dest_path)

        results = {
            "transcript": transcript,
        }

        # Generate summary if requested
        if generate_summary:
            try:
                summary = agent.generate_summary(dest_path)
            except Exception as e:
                # If agent.generate_summary expects transcript-based input, fallback to minutes_generator
                try:
                    summary = agent.minutes_generator.generate_summary(transcript)
                except Exception as e2:
                    summary = f"Failed to generate summary: {e!s}; fallback error: {e2!s}"
            results["summary"] = summary

        # If the UI requests 'full transcript' (was previously 'minutes' toggle), include it in results
        if generate_minutes:
            # provide the full transcript explicitly under a descriptive key
            results["full_transcript"] = transcript

        # Optionally extract key points
        if generate_keypoints:
            try:
                key_points = agent.extract_key_points(dest_path)
                results["key_points"] = key_points
            except Exception as e:
                results["key_points_error"] = str(e)

        # Optionally explain technical terms
        if generate_terms:
            try:
                terms = agent.explain_technical_terms(dest_path)
                # normalize to list of strings for JSON
                if isinstance(terms, (set, list)):
                    results["technical_terms"] = list(terms)
                else:
                    results["technical_terms"] = [str(terms)]
            except Exception as e:
                results["technical_terms_error"] = str(e)

        # Optionally include link/path to saved uploaded file
        results["uploaded_file"] = dest_path
        return JSONResponse(results)
    except FileNotFoundError:
        return JSONResponse({"error": "Uploaded audio file not found after save."}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e), "repr": repr(e)}, status_code=500)
