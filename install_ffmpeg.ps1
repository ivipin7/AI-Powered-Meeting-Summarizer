# Simple FFmpeg Download Script for Windows
Write-Host "=== Fast FFmpeg Download ===" -ForegroundColor Green
Write-Host ""

$ffmpegDir = "C:\ffmpeg"
$ffmpegBin = "$ffmpegDir\bin"

# Check if already installed
if (Test-Path "$ffmpegBin\ffmpeg.exe") {
    Write-Host "FFmpeg already installed at $ffmpegBin" -ForegroundColor Green
    & "$ffmpegBin\ffmpeg.exe" -version | Select-Object -First 1
    exit 0
}

Write-Host "Downloading FFmpeg (essential build - smaller and faster)..." -ForegroundColor Yellow

# Use essential build (much smaller - ~30MB vs 169MB)
$url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$zipFile = "$env:TEMP\ffmpeg.zip"

try {
    # Download
    Invoke-WebRequest -Uri $url -OutFile $zipFile -UseBasicParsing
    
    Write-Host "Download completed!" -ForegroundColor Green
    Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
    
    # Extract to temp location first
    $tempExtract = "$env:TEMP\ffmpeg_extract"
    if (Test-Path $tempExtract) {
        Remove-Item $tempExtract -Recurse -Force
    }
    
    # Extract zip
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipFile, $tempExtract)
    
    # Find the extracted folder
    $extractedFolder = Get-ChildItem $tempExtract | Where-Object { $_.PSIsContainer } | Select-Object -First 1
    
    # Create target directory
    if (!(Test-Path $ffmpegDir)) {
        New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
    }
    
    # Copy bin folder
    Copy-Item "$($extractedFolder.FullName)\bin" -Destination $ffmpegDir -Recurse -Force
    
    Write-Host "FFmpeg extracted to $ffmpegDir" -ForegroundColor Green
    
    # Add to PATH for current session
    $env:PATH = "$ffmpegBin;$env:PATH"
    
    # Test installation
    Write-Host "Testing FFmpeg installation..." -ForegroundColor Yellow
    & "$ffmpegBin\ffmpeg.exe" -version | Select-Object -First 1
    
    Write-Host "FFmpeg installation completed successfully!" -ForegroundColor Green
    Write-Host "You may need to restart your terminal for PATH changes to take effect" -ForegroundColor Yellow
    
    # Cleanup
    Remove-Item $zipFile -Force -ErrorAction SilentlyContinue
    Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please try the manual installation method." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "You can now use FFmpeg! Try running: ffmpeg -version" -ForegroundColor Green
