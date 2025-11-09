# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.'), ('.gitignore', '.'), ('api_server.py', '.'), ('build.spec', '.'), ('environment.yml', '.'), ('example_agent_usage.py', '.'), ('main.py', '.'), ('MeetingTranscriber.spec', '.'), ('README_AGENT.md', '.'), ('start_app.py', '.'), ('validate_openai.py', '.'), ('智能体开发：智能培训记录助手.md', '.'), ('智能体开发：智能培训记录助手.pdf', '.'), ('agent\\meeting_minutes.py', 'agent'), ('agent\\speech_recognition.py', 'agent'), ('agent\\transcription_agent.py', 'agent'), ('agent\\__init__.py', 'agent'), ('config\\prompts.yaml', 'config'), ('config\\prompts_manager.py', 'config'), ('config\\settings.py', 'config'), ('config\\__init__.py', 'config'), ('data\\dialogue_recording.mp3', 'data'), ('data\\dialogue_recording.wav', 'data'), ('data\\ifasr_output.md', 'data'), ('data\\Ifasr_涉政.wav', 'data'), ('data\\录音 (1)_202511061015_393990 .wav', 'data'), ('data\\录音 (1)_202511061015_393990 _segment_000000000_to_003313250.mp3', 'data'), ('data\\output\\meeting_minutes.md', 'data\\output'), ('data\\output\\summary.md', 'data\\output'), ('data\\output\\summary.txt', 'data\\output'), ('data\\output\\technical_terms.md', 'data\\output'), ('data\\output\\transcript.md', 'data\\output'), ('data\\output\\transcript.txt', 'data\\output'), ('data\\uploads\\2059bd15476b438ebce51d53b9c6e833_Ifasr_涉政.wav', 'data\\uploads'), ('frontend\\favicon.ico', 'frontend'), ('frontend\\index.html', 'frontend'), ('frontend\\NewStyle_index.html', 'frontend'), ('utils\\api_client.py', 'utils'), ('utils\\ifasr_client.py', 'utils'), ('utils\\__init__.py', 'utils'), ('utils\\ifasr_lib\\Ifasr.py', 'utils\\ifasr_lib'), ('utils\\ifasr_lib\\orderResult.py', 'utils\\ifasr_lib'), ('utils\\ifasr_lib\\__init__.py', 'utils\\ifasr_lib')],
    hiddenimports=['fastapi', 'fastapi.middleware', 'fastapi.middleware.cors', 'fastapi.staticfiles', 'uvicorn', 'requests', 'numpy', 'pydub', 'openai', 'whisper', 'wave'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MeetingTranscriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
