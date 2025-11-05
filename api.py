from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent
import os
import shutil
import uuid
import time
import functools

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

# Helper to safely JSON-serialize objects
def _json_dumps(obj):
    return json.dumps(obj, default=lambda o: list(o) if isinstance(o, set) else str(o))

ROOT_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(ROOT_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory task queues for SSE streaming: task_id -> asyncio.Queue
TASK_QUEUES: dict[str, asyncio.Queue] = {}

# Serve the static frontend from / (mounts frontend folder if present)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    from fastapi.responses import FileResponse, Response

    @app.get("/")
    async def root_index():
        index_path = os.path.join(FRONTEND_DIR, "NewStyle_index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return Response(content="Frontend not found", status_code=404)

    @app.get("/favicon.ico")
    async def favicon():
        fav = os.path.join(FRONTEND_DIR, "favicon.ico")
        if os.path.exists(fav):
            return FileResponse(fav)
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
            '<rect width="16" height="16" fill="#5b8def"/>'
            '<text x="8" y="10" font-size="9" text-anchor="middle" fill="#fff" font-family="Arial, Helvetica, sans-serif">M</text>'
            '</svg>'
        )
        return Response(content=svg, media_type="image/svg+xml")


async def process_stage(queue, stage_name, processing_func, *args, result_key=None, progress_callback=None):
    """通用阶段处理函数，支持进度回调"""
    result_key = result_key or stage_name
    
    # 发送阶段开始消息
    await queue.put(_json_dumps({"stage": stage_name, "status": "started"}))
    
    # 获取主线程的事件循环（在异步上下文中）
    main_loop = asyncio.get_event_loop()
    try:
        # 如果是转录阶段，实时进度更新
        if stage_name == "transcribe" and progress_callback:

            # 包装处理函数以支持进度回调
            def progress_callback_wrapper(progress):
                # 在线程中调用时，使用线程安全的方式将进度放入队列
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        queue.put(_json_dumps({
                            "stage": stage_name,
                            "status": "progress",
                            "progress": progress
                        })), main_loop
                    )
                    # 等待结果但不阻塞（设置超时避免永久阻塞）
                    future.result(timeout=60.0)
                except asyncio.TimeoutError:
                    print(f"进度更新超时: {progress}%")
                except Exception as e:
                    print(f"Failed to send progress update: {e}")
            
            # 在线程中执行处理函数，传入进度回调
            try:
                result = await asyncio.to_thread(
                    processing_func, 
                    *args, 
                    progress_callback=progress_callback_wrapper
                )
            except Exception as e:
                print(f"Error during transcription: {e}")
                raise e
        else:
            # 执行实际处理
            result = await asyncio.to_thread(processing_func, *args)
        
        # 构建结果消息
        result_msg = {"stage": stage_name, "status": "done", result_key: result}
        
        # 特殊处理：将"terms"改为"technical_terms"以匹配前端期望
        if stage_name == "terms":
            result_msg["technical_terms"] = result
            if "terms" in result_msg:
                del result_msg["terms"]
        
        await queue.put(_json_dumps(result_msg))
        return result
        
    except Exception as e:
        error_msg = {"stage": stage_name, "status": "error", "error": str(e)}
        await queue.put(_json_dumps(error_msg))
        return None


@app.post("/api/process")
async def process_meeting(
    file: UploadFile = File(...),
    attendees: str = Form(None),
    meeting_topic: str = Form(None),
    generate_summary: bool = Form(True),
    generate_keypoints: bool = Form(False),
    generate_terms: bool = Form(False),
):
    """Accept upload, start background processing and return a task id."""
    # Save uploaded file
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(dest_path, "wb") as dest:
            shutil.copyfileobj(file.file, dest)
    except Exception as e:
        return JSONResponse({"error": f"Failed to save uploaded file: {e}"}, status_code=500)

    task_id = uuid.uuid4().hex
    queue = asyncio.Queue()
    TASK_QUEUES[task_id] = queue

    async def _run():
        try:
            # Upload stage
            await queue.put(_json_dumps({"stage": "upload", "status": "done", "detail": os.path.basename(dest_path)}))
            
            # Transcription stage - 添加进度回调支持
            transcript = await process_stage(
                queue, 
                "transcribe", 
                agent.transcribe_audio, 
                dest_path, 
                result_key="transcript",  # 明确指定结果键名
                progress_callback=True   # 启用进度回调
            )
            if not transcript:
                return  # Stop if transcription failed
                
            print('Transcription completed.')
            results = {"transcript": transcript, "uploaded_file": dest_path}
            
            # Summary stage
            if generate_summary:
                summary = await process_stage(queue, "summary", agent.generate_summary)
                if summary:
                    results["summary"] = summary
            
            # Key points stage
            if generate_keypoints:
                key_points = await process_stage(queue, "key_points", agent.extract_key_points)
                if key_points:
                    results["key_points"] = key_points
            
            # Technical terms stage - 使用正确的阶段名称和结果键
            if generate_terms:
                terms = await process_stage(
                    queue, 
                    "terms", 
                    agent.explain_technical_terms, 
                )
                if terms:
                    results["technical_terms"] = terms
            
            # Final result - 确保结果键名与前端匹配
            final_results = {
                "transcript": results.get("transcript"),
                "summary": results.get("summary"),
                "key_points": results.get("key_points"),
                "technical_terms": results.get("technical_terms")  # 使用前端期望的键名
            }
            
            await queue.put(_json_dumps({"event": "done", "results": final_results}))
            
        except Exception as e:
            await queue.put(_json_dumps({"stage": "processing", "status": "error", "error": str(e)}))
        finally:
            # Cleanup after delay to allow client to receive last message
            await asyncio.sleep(1.0)
            TASK_QUEUES.pop(task_id, None)

    asyncio.create_task(_run())
    return JSONResponse({"task_id": task_id, "status": "started"})


@app.get("/api/events/{task_id}")
async def events(task_id: str):
    """SSE endpoint streaming JSON messages for the given task_id."""
    queue = TASK_QUEUES.get(task_id)
    if not queue:
        return JSONResponse({"error": "unknown task_id"}, status_code=404)

    async def event_stream():
        try:
            while True:
                msg = await queue.get()
                yield f"data: {msg}\n\n"
                # Stop streaming when done event seen
                try:
                    obj = json.loads(msg)
                    if obj.get('event') == 'done':
                        break
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass
        finally:
            # Ensure cleanup
            TASK_QUEUES.pop(task_id, None)

    return StreamingResponse(
        event_stream(), 
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": time.time()}


# Get task status endpoint
@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task"""
    if task_id not in TASK_QUEUES:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    
    # For simplicity, just return that the task exists
    # In a real implementation, you might want to track more detailed status
    return {"task_id": task_id, "status": "processing"}