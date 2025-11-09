# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['main.py'],  # 主入口文件
    pathex=[],
    binaries=[],
    datas=[
        # 包含必要的文件
        ('api_server.py', '.'),           # FastAPI 应用文件
        ('config/', 'config'),            # 配置文件目录
        ('agent/', 'agent'),              # 代理模块目录
        ('frontend/', 'frontend'),        # 前端文件
        ('data/', 'data'),                # 数据目录
        ('.env', '.'),                    # 环境配置文件
    ],
    hiddenimports=[
        # FastAPI 相关
        'fastapi',
        'fastapi.middleware'
        'uvicorn',
        'pydantic',
        'starlette',
        
        # 标准库隐藏导入
        'asyncio',
        'json',
        'email.mime.text',
        'email.mime.multipart',
        
        # 其他可能需要的模块
        'dotenv',
        'aiofiles',
        'httpx',
        
        # 平台特定
        'win32timezone' if sys.platform == 'win32' else '',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TranscribeMeetingRecording',  # 可执行文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 显示控制台窗口以便查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TranscribeMeetingRecording'  # 输出目录名
)