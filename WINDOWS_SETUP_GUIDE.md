# Windows Setup Guide for AI-Powered Meeting Summarizer

## Current Status ✅
- ✅ Python 3.10.11 installed
- ✅ Git installed
- ✅ Virtual environment created (.venv)
- ✅ Python dependencies installed
- ✅ whisper.cpp repository cloned

## Next Steps Required 🚧

### 1. Install FFmpeg
FFmpeg is required for audio processing. Choose one of these options:

**Option A: Using winget (Recommended)**
```powershell
winget install --id=Gyan.FFmpeg -e
```

**Option B: Manual Installation**
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to your system PATH

**Option C: Using Chocolatey (if installed)**
```powershell
choco install ffmpeg -y
```

### 2. Install Ollama
Ollama is required for text summarization.

1. Download Ollama from: https://ollama.com/
2. Install the Windows version
3. Open Command Prompt/PowerShell and run:
```powershell
ollama run llama3.2
```
This will download and run the Llama 3.2 model (about 2GB download).

### 3. Build whisper.cpp
This is the most complex step as it requires compilation.

**Option A: Using Visual Studio (Recommended)**
1. Install Visual Studio Community (free) from: https://visualstudio.microsoft.com/
2. During installation, select "C++ build tools"
3. Open "Developer Command Prompt for VS"
4. Navigate to your project folder
5. Run:
```cmd
cd whisper.cpp
nmake
```

**Option B: Using MinGW/MSYS2**
1. Install MSYS2 from: https://www.msys2.org/
2. Open MSYS2 terminal
3. Install build tools:
```bash
pacman -S mingw-w64-x86_64-toolchain mingw-w64-x86_64-cmake make
```
4. Navigate to whisper.cpp folder and run:
```bash
make
```

### 4. Download Whisper Model
After building whisper.cpp:
```cmd
cd whisper.cpp
bash models/download-ggml-model.sh small
```

### 5. Test the Setup
1. Activate virtual environment:
```powershell
.venv\Scripts\Activate.ps1
```

2. Test Ollama connection:
```powershell
curl http://localhost:11434/api/tags
```

3. Test FFmpeg:
```powershell
ffmpeg -version
```

4. Run the application:
```powershell
python main.py
```

## Troubleshooting

### FFmpeg Issues
- Make sure FFmpeg is in your PATH
- Restart your terminal after installation
- Test with: `ffmpeg -version`

### Ollama Issues
- Make sure Ollama service is running
- Check if you can access: http://localhost:11434
- Try running: `ollama run llama3.2`

### whisper.cpp Build Issues
- Make sure you have C++ build tools installed
- Try using "Developer Command Prompt for VS" instead of regular PowerShell
- Check that you have enough disk space (build requires ~1GB)

### Python Issues
- Make sure virtual environment is activated
- Try: `pip install requests gradio` separately if needed

## Alternative: Pre-built whisper.cpp
If building whisper.cpp fails, you can try using pre-built binaries:
1. Check the whisper.cpp releases page: https://github.com/ggerganov/whisper.cpp/releases
2. Download the Windows binary
3. Extract and place in your project folder

## Quick Start Commands
After completing all installations:
```powershell
# 1. Activate virtual environment
.venv\Scripts\Activate.ps1

# 2. Start Ollama (in another terminal)
ollama serve

# 3. Run the application
python main.py
```

The application will be available at: http://127.0.0.1:7860
