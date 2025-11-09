from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
import asyncio
import json
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import shutil
import uuid
import time
import functools
import sys
import base64
import queue as thread_queue
from pathlib import Path

# 添加资源路径处理函数
def resource_path(relative_path):
    """获取资源的绝对路径，用于打包后访问资源文件"""
    try:
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

# 动态导入配置，避免打包时的问题 
try:
    from config.settings import Config
    from agent.transcription_agent import TranscriptionAgent
except ImportError as e:
    print(f"导入警告: {e}")
    # 创建模拟类用于测试
    class Config:
        def __init__(self):
            self.AGENT_CONFIG = {}
            self.DEEPSEEK_SETTINGS = {}
    
    class TranscriptionAgent:
        def __init__(self, agent_setting, minutes_generator_setting):
            self.agent_setting = agent_setting
            self.minutes_generator_setting = minutes_generator_setting
        
        async def transcribe_audio(self, file_path, progress_callback=None):
            # 模拟转录过程
            if progress_callback:
                for i in range(0, 101, 10):
                    progress_callback(i)
                    await asyncio.sleep(0.1)
            return f"模拟转录结果: {file_path}"
        
        async def generate_summary(self):
            await asyncio.sleep(1)
            return "模拟摘要内容"
        
        async def extract_key_points(self):
            await asyncio.sleep(1)
            return ["关键点1", "关键点2", "关键点3"]
        
        async def explain_technical_terms(self):
            await asyncio.sleep(1)
            return {"术语1": "解释1", "术语2": "解释2"}

# Simple FastAPI wrapper to expose the agent as an HTTP API.
app = FastAPI(title="TranscribeMeetingRecording API")

# Allow the static frontend (or any origin during development) to call the API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]) 

load_dotenv()

# 动态获取根目录
try:
    ROOT_DIR = sys._MEIPASS  # 打包环境
except AttributeError:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # 开发环境

# 配置路径
UPLOAD_DIR = os.path.join(ROOT_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# 只有在开发环境或文件存在时才挂载静态文件
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# 延迟初始化，避免打包时立即执行
config = None
agent = None
TASK_QUEUES: dict[str, asyncio.Queue] = {}

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global config, agent
    try:
        config = Config()
        agent = TranscriptionAgent(
            agent_setting=config.AGENT_CONFIG,
            minutes_generator_setting=config.DEEPSEEK_SETTINGS
        )
        print("✅ 代理初始化成功")
    except Exception as e:
        print(f"❌ 代理初始化失败: {e}")
        # 使用模拟代理
        config = Config()
        agent = TranscriptionAgent({}, {})
        print("⚠️ 使用模拟代理")

# Helper to safely JSON-serialize objects
def _json_dumps(obj):
    return json.dumps(obj, default=lambda o: list(o) if isinstance(o, set) else str(o))

# 前端路由
@app.get("/")
async def root_index():
    """服务前端页面"""
    index_path = os.path.join(FRONTEND_DIR, "NewStyle_index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # 如果前端文件不存在，返回简单的信息页面
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TranscribeMeetingRecording API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .success { background: #d4edda; color: #155724; }
            .warning { background: #fff3cd; color: #856404; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TranscribeMeetingRecording API</h1>
            <div class="status success">✅ 后端服务运行正常</div>
            <div class="status warning">⚠️ 前端界面未找到，请检查前端文件配置</div>
            <p>API 文档: <a href="/docs">/docs</a></p>
            <p>健康检查: <a href="/api/health">/api/health</a></p>
        </div>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

def create_default_favicon():
    """创建默认的ICO图标 - 使用正确的base64数据"""
    try:
        # 正确的16x16像素ICO文件base64编码
        ico_base64 = (
            "AAABAAEAEBAQAAEABAAoAQAAFgAAACgAAAAQAAAAIAAAAAEABAAAAAAAgAAAAAAAAAAAAAAAEAAA"
            "AAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//"
            "AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA"
        )
        
        # 确保base64数据长度是4的倍数
        padding = len(ico_base64) % 4
        if padding:
            ico_base64 += '=' * (4 - padding)
        
        ico_data = base64.b64decode(ico_base64)
        
        fav = os.path.join(FRONTEND_DIR, "favicon.ico")
        with open(fav, 'wb') as f:
            f.write(ico_data)
        print("✅ 创建默认favicon.ico成功")
        return True
    except Exception as e:
        print(f"❌ 创建favicon失败: {e}")
        return False

@app.get("/favicon.ico")
async def favicon():
    """网站图标"""
    fav = os.path.join(FRONTEND_DIR, "favicon.ico")
    if os.path.exists(fav):
        return FileResponse(fav)
    
    # 尝试创建默认图标
    if create_default_favicon():
        print('created default favicon.ico')
        return FileResponse(os.path.join(FRONTEND_DIR, "favicon.ico"))

# 原有的 API 路由保持不变
async def process_stage(queue, stage_name, processing_func, *args, result_key=None, progress_callback=None):
    """通用阶段处理函数，支持进度回调"""
    result_key = result_key or stage_name
        
    # 发送阶段开始消息
    await queue.put(_json_dumps({"stage": stage_name, "status": "started"}))

    try:
        # 如果是转录阶段，实时进度更新
        if stage_name == "transcribe" and progress_callback:
            # 创建线程安全的进度回调包装器
            def create_progress_handler():
                loop = asyncio.get_event_loop()
                
                def handle_progress(progress):
                    # 使用call_soon_threadsafe确保线程安全
                    if loop.is_running():
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(queue.put(_json_dumps({
                                "stage": stage_name,
                                "progress": progress,
                                "type": "progress",
                                "timestamp": time.time()
                            })))
                        )
                return handle_progress
            progress_handler = create_progress_handler()
            
            # 在线程中执行处理函数，传入进度回调
            result = await asyncio.to_thread(
                processing_func, 
                *args, 
                progress_callback=progress_handler  # 传递正确的回调函数
            )  
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
    if agent is None:
        return JSONResponse({"error": "Agent not initialized"}, status_code=500)

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
    status = "ok" if agent is not None else "agent_not_initialized"
    return {"status": status, "timestamp": time.time()}


# Get task status endpoint
@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task"""
    if task_id not in TASK_QUEUES:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    
    # For simplicity, just return that the task exists
    # In a real implementation, you might want to track more detailed status
    return {"task_id": task_id, "status": "processing"}

# 系统信息端点
@app.get("/api/system/info")
async def system_info():
    """获取系统信息"""
    import platform
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.architecture(),
        "python_version": platform.python_version(),
        "is_frozen": getattr(sys, 'frozen', False),
        "root_dir": ROOT_DIR,
    }