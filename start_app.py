#!/usr/bin/env python3
"""
开发环境启动脚本
"""

import os
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """开发环境启动"""
    print("🚀 启动开发服务器...")
    
    # 设置环境变量
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # 导入并启动 uvicorn
    import uvicorn
    
    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # 开发环境启用热重载
        log_level="info"
    )

if __name__ == "__main__":
    main()