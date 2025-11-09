#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
from pathlib import Path

def collect_project_files():
    """自动收集项目中的所有文件"""
    
    project_root = Path(__file__).parent
    exclude_dirs = {'.git', '__pycache__', 'build', 'dist', 'venv', '.vscode'}
    exclude_extensions = {'.pyc', '.tmp', '.log'}
    
    add_data_args = []
    
    # 包含根目录文件
    for file_path in project_root.glob('*'):
        if file_path.is_file() and file_path.suffix not in exclude_extensions:
            if file_path.name not in ['build.py', 'build_project.py']:
                add_data_args.append(f'--add-data={file_path.name};.')
    
    # 包含子目录
    for item in project_root.iterdir():
        if item.is_dir() and item.name not in exclude_dirs:
            # 递归包含目录中的所有文件
            for file_path in item.rglob('*'):
                if file_path.is_file() and file_path.suffix not in exclude_extensions:
                    relative_path = file_path.relative_to(project_root)
                    parent_dir = str(relative_path.parent)
                    add_data_args.append(f'--add-data={relative_path};{parent_dir}')
    
    return add_data_args

def build_project():
    """构建整个项目"""
    
    print("🔍 扫描项目文件...")
    
    # 清理之前的构建
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🧹 清理目录: {dir_name}")
    
    # 收集文件
    add_data_args = collect_project_files()
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name=MeetingTranscriber',
        # Flask 相关
        # '--hidden-import=flask',
        # '--hidden-import=flask_cors',
        # '--hidden-import=werkzeug.middleware.proxy_fix',
        # FastAPI 相关
        '--hidden-import=fastapi',
        '--hidden-import=fastapi.middleware',
        '--hidden-import=fastapi.middleware.cors',
        '--hidden-import=fastapi.staticfiles',
        '--hidden-import=uvicorn',
        # 其他依赖
        '--hidden-import=requests',
        '--hidden-import=numpy',
        '--hidden-import=pydub',
        # '--hidden-import=speech_recognition',
        '--hidden-import=openai',
        # '--hidden-import=transformers',
        # '--hidden-import=torch',
        '--hidden-import=whisper',
        '--hidden-import=wave',
        # '--hidden-import=soundfile',
        # '--hidden-import=librosa',
        # '--hidden-import=scipy',
        # '--hidden-import=pytube',
        # '--hidden-import=youtube_dl',
        '--clean',
    ] + add_data_args + ['main.py']
    
    print("🚀 开始构建...")
    print("命令:", ' '.join(cmd))
    
    # 执行构建
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功！")
        
        # 显示构建信息
        exe_path = Path('dist') / 'MeetingTranscriber.exe'
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📦 生成文件: {exe_path} ({size:.2f} MB)")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False
    
    return True

if __name__ == '__main__':
    build_project()