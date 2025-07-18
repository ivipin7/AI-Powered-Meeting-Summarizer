@echo off
echo ====================================================
echo AI-Powered Meeting Summarizer Setup for Windows
echo ====================================================
echo.

echo Step 1: Creating Python virtual environment...
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

echo.
echo Step 2: Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Step 3: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 4: Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Step 5: Checking for whisper.cpp...
if not exist whisper.cpp (
    echo Cloning whisper.cpp repository...
    git clone https://github.com/ggerganov/whisper.cpp.git
) else (
    echo whisper.cpp already exists.
)

echo.
echo ====================================================
echo MANUAL STEPS REQUIRED:
echo ====================================================
echo.
echo 1. Install FFmpeg:
echo    - Download from: https://ffmpeg.org/download.html
echo    - Or use: winget install --id=Gyan.FFmpeg -e
echo    - Make sure ffmpeg is in your PATH
echo.
echo 2. Install Ollama:
echo    - Download from: https://ollama.com/
echo    - Install and run: ollama run llama3.2
echo.
echo 3. Build whisper.cpp:
echo    - You need Visual Studio Build Tools or MinGW
echo    - Navigate to whisper.cpp folder and run: make
echo.
echo 4. Download Whisper model:
echo    - In whisper.cpp folder, run: models\download-ggml-model.sh small
echo.
echo ====================================================
echo After completing manual steps, run: python main.py
echo ====================================================

pause
