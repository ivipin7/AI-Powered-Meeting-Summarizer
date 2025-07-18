# AI-Powered Meeting Summarizer Windows Setup Script
# Run this script in PowerShell as Administrator

param(
    [switch]$InstallFFmpeg,
    [switch]$TestSetup,
    [switch]$DownloadOllama,
    [switch]$BuildWhisper,
    [switch]$All
)

Write-Host "=== AI-Powered Meeting Summarizer Windows Setup ===" -ForegroundColor Green
Write-Host ""

# Function to test if a command exists
function Test-Command($command) {
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Function to install FFmpeg using winget
function Install-FFmpeg {
    Write-Host "Installing FFmpeg..." -ForegroundColor Yellow
    if (Test-Command "winget") {
        try {
            winget install --id=Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
            Write-Host "✅ FFmpeg installed successfully" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to install FFmpeg via winget" -ForegroundColor Red
            Write-Host "Please install FFmpeg manually from https://ffmpeg.org/download.html" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ winget not found. Please install FFmpeg manually" -ForegroundColor Red
    }
}

# Function to test current setup
function Test-Setup {
    Write-Host "Testing current setup..." -ForegroundColor Yellow
    Write-Host ""
    
    # Test Python
    if (Test-Command "python") {
        $pythonVersion = python --version
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python not found" -ForegroundColor Red
    }
    
    # Test Git
    if (Test-Command "git") {
        $gitVersion = git --version
        Write-Host "✅ Git: $gitVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Git not found" -ForegroundColor Red
    }
    
    # Test FFmpeg
    if (Test-Command "ffmpeg") {
        $ffmpegVersion = ffmpeg -version | Select-Object -First 1
        Write-Host "✅ FFmpeg: $ffmpegVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ FFmpeg not found" -ForegroundColor Red
    }
    
    # Test Ollama
    if (Test-Command "ollama") {
        $ollamaVersion = ollama --version
        Write-Host "✅ Ollama: $ollamaVersion" -ForegroundColor Green
        
        # Test Ollama connection
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
            Write-Host "✅ Ollama server is running" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Ollama installed but server not running. Run 'ollama serve' in another terminal" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Ollama not found" -ForegroundColor Red
    }
    
    # Test Virtual Environment
    if (Test-Path ".venv") {
        Write-Host "✅ Virtual environment exists" -ForegroundColor Green
    } else {
        Write-Host "❌ Virtual environment not found" -ForegroundColor Red
    }
    
    # Test whisper.cpp
    if (Test-Path "whisper.cpp") {
        Write-Host "✅ whisper.cpp repository exists" -ForegroundColor Green
        
        # Check if main executable exists
        if (Test-Path "whisper.cpp/main.exe") {
            Write-Host "✅ whisper.cpp is built" -ForegroundColor Green
        } else {
            Write-Host "⚠️ whisper.cpp needs to be built" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ whisper.cpp not found" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Function to provide Ollama download instructions
function Get-OllamaInstructions {
    Write-Host "Ollama Installation Instructions:" -ForegroundColor Yellow
    Write-Host "1. Download Ollama from: https://ollama.com/" -ForegroundColor White
    Write-Host "2. Install the Windows version" -ForegroundColor White
    Write-Host "3. Open a new PowerShell window and run:" -ForegroundColor White
    Write-Host "   ollama run llama3.2" -ForegroundColor Cyan
    Write-Host "4. This will download and start the Llama 3.2 model (~2GB)" -ForegroundColor White
    Write-Host ""
}

# Function to provide whisper.cpp build instructions
function Get-WhisperBuildInstructions {
    Write-Host "whisper.cpp Build Instructions:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Using Visual Studio (Recommended)" -ForegroundColor White
    Write-Host "1. Install Visual Studio Community from: https://visualstudio.microsoft.com/" -ForegroundColor White
    Write-Host "2. Select 'C++ build tools' during installation" -ForegroundColor White
    Write-Host "3. Open 'Developer Command Prompt for VS'" -ForegroundColor White
    Write-Host "4. Navigate to this folder and run:" -ForegroundColor White
    Write-Host "   cd whisper.cpp" -ForegroundColor Cyan
    Write-Host "   nmake" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 2: Using cmake (if available)" -ForegroundColor White
    Write-Host "   cd whisper.cpp" -ForegroundColor Cyan
    Write-Host "   mkdir build && cd build" -ForegroundColor Cyan
    Write-Host "   cmake .. && cmake --build ." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 3: Download pre-built binary" -ForegroundColor White
    Write-Host "1. Visit: https://github.com/ggerganov/whisper.cpp/releases" -ForegroundColor White
    Write-Host "2. Download the Windows binary" -ForegroundColor White
    Write-Host "3. Extract to whisper.cpp folder" -ForegroundColor White
    Write-Host ""
}

# Function to try cmake build
function Try-CmakeBuild {
    Write-Host "Attempting to build whisper.cpp with cmake..." -ForegroundColor Yellow
    
    if (Test-Command "cmake") {
        Set-Location whisper.cpp
        try {
            if (!(Test-Path "build")) {
                New-Item -ItemType Directory -Name "build"
            }
            Set-Location build
            cmake ..
            cmake --build .
            Write-Host "✅ whisper.cpp built successfully" -ForegroundColor Green
        } catch {
            Write-Host "❌ cmake build failed" -ForegroundColor Red
            Get-WhisperBuildInstructions
        } finally {
            Set-Location ../..
        }
    } else {
        Write-Host "❌ cmake not found" -ForegroundColor Red
        Get-WhisperBuildInstructions
    }
}

# Main script logic
if ($All) {
    $InstallFFmpeg = $true
    $TestSetup = $true
    $DownloadOllama = $true
    $BuildWhisper = $true
}

if ($InstallFFmpeg) {
    Install-FFmpeg
}

if ($DownloadOllama) {
    Get-OllamaInstructions
}

if ($BuildWhisper) {
    Try-CmakeBuild
}

if ($TestSetup) {
    Test-Setup
}

# If no parameters provided, show help
if (!$InstallFFmpeg -and !$TestSetup -and !$DownloadOllama -and !$BuildWhisper -and !$All) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  ./setup_windows.ps1 -TestSetup       # Test current setup status" -ForegroundColor White
    Write-Host "  ./setup_windows.ps1 -InstallFFmpeg   # Install FFmpeg" -ForegroundColor White
    Write-Host "  ./setup_windows.ps1 -DownloadOllama  # Show Ollama instructions" -ForegroundColor White
    Write-Host "  ./setup_windows.ps1 -BuildWhisper    # Try to build whisper.cpp" -ForegroundColor White
    Write-Host "  ./setup_windows.ps1 -All             # Run all steps" -ForegroundColor White
    Write-Host ""
    Write-Host "After completing setup, run:" -ForegroundColor Yellow
    Write-Host "  .venv\\Scripts\\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  python main.py" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Setup script completed!" -ForegroundColor Green
