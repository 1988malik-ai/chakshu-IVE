# Windows Build — AI-IVE

## Requirements

- Windows 10/11 (64-bit recommended)
- Python 3.10+
- FFmpeg on PATH
- Visual Studio Build Tools (for PyInstaller native deps)

## 64-bit Build

```powershell
cd $env:USERPROFILE\Desktop\AI-IVE
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
.\build\windows\build_x64.ps1
```

Output: `dist/AI-IVE/AI-IVE.exe`

## 32-bit Legacy Build

Use a 32-bit Python installation:

```powershell
# Install 32-bit Python 3.10 from python.org
C:\Python310-32\python.exe -m venv .venv32
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
.\build\windows\build_x86.ps1
```

## Codec Notes

- **FFmpeg**: primary decode/encode path
- **DirectShow / VfW**: Windows adapters in `src/aive/codecs/decoders.py` (FFmpeg fallback when native bridge unavailable)
- **QuickTime**: optional; legacy `.mov` codecs via FFmpeg on modern Windows

## GPU Encoding

Verify encoders:

```powershell
ffmpeg -encoders | findstr nvenc
ffmpeg -encoders | findstr qsv
```
