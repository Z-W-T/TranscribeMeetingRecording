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
    speech_engine_type=config.AGENT_CONFIG.get("speech_engine_type"),
    api_settings=config.DEEPSEEK_SETTINGS
)

ROOT_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(ROOT_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve the static frontend from / (mounts frontend folder if present)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.post("/api/process")
async def process_meeting(
    file: UploadFile = File(...),
    attendees: str = Form(None),
    meeting_topic: str = Form(None),
    generate_minutes: bool = Form(True),
    generate_summary: bool = Form(True),
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
        results = agent.process_meeting(
            audio_input=dest_path,
            generate_minutes=bool(generate_minutes),
            generate_summary=bool(generate_summary),
            attendees=attendees_list,
            meeting_topic=meeting_topic,
        )
        # Optionally include link/path to saved uploaded file
        results["uploaded_file"] = dest_path
        return results
    except FileNotFoundError:
        return JSONResponse({"error": "Uploaded audio file not found after save."}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e), "repr": repr(e)}, status_code=500)
