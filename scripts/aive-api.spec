# PyInstaller spec — Chakshu API backend (Windows/macOS build host)
# Run: pyinstaller --noconfirm scripts/aive-api.spec

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
root = Path(SPECPATH).resolve().parent

binaries: list = []
datas = [(str(root / "config"), "config")]
# Bundle built React UI inside the exe (fixes "detail not found" when external path missing)
_frontend_dist = root / "frontend" / "dist"
if _frontend_dist.is_dir() and (_frontend_dist / "index.html").is_file():
    datas.append((str(_frontend_dist), "frontend-dist"))
hiddenimports = collect_submodules("aive")

for pkg in ("cv2", "imageio_ffmpeg", "uvicorn", "multipart", "starlette", "fastapi", "pydantic"):
    try:
        tmp = collect_all(pkg)
        datas += tmp[0]
        binaries += tmp[1]
        hiddenimports += tmp[2]
    except Exception:
        pass

a = Analysis(
    [str(root / "src" / "aive" / "api" / "_launcher.py")],
    pathex=[str(root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt6", "tkinter", "matplotlib", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="aive-api",
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
