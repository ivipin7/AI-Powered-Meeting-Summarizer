# Configure Ollama to use D drive for data storage
# This script sets up Ollama to store models and data on D drive

Write-Host "=== Configuring Ollama for D Drive Storage ===" -ForegroundColor Green
Write-Host ""

# Create Ollama directory on D drive
$ollamaDir = "D:\Ollama"
$ollamaModels = "$ollamaDir\models"
$ollamaData = "$ollamaDir\data"

Write-Host "Creating Ollama directories on D drive..." -ForegroundColor Yellow

# Create directories
if (!(Test-Path $ollamaDir)) {
    New-Item -ItemType Directory -Path $ollamaDir -Force | Out-Null
    Write-Host "Created: $ollamaDir" -ForegroundColor Green
}

if (!(Test-Path $ollamaModels)) {
    New-Item -ItemType Directory -Path $ollamaModels -Force | Out-Null
    Write-Host "Created: $ollamaModels" -ForegroundColor Green
}

if (!(Test-Path $ollamaData)) {
    New-Item -ItemType Directory -Path $ollamaData -Force | Out-Null
    Write-Host "Created: $ollamaData" -ForegroundColor Green
}

Write-Host ""
Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Set environment variables for current session
$env:OLLAMA_MODELS = $ollamaModels
$env:OLLAMA_HOME = $ollamaDir

# Set permanent environment variables
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $ollamaModels, "User")
[Environment]::SetEnvironmentVariable("OLLAMA_HOME", $ollamaDir, "User")

Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "  OLLAMA_MODELS = $ollamaModels" -ForegroundColor White
Write-Host "  OLLAMA_HOME = $ollamaDir" -ForegroundColor White

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Yellow
Write-Host "1. Download Ollama installer from: https://ollama.com/" -ForegroundColor White
Write-Host "2. Install Ollama (it can install to C drive - models will still go to D drive)" -ForegroundColor White
Write-Host "3. Restart your terminal/PowerShell" -ForegroundColor White
Write-Host "4. Run: ollama run llama3.2" -ForegroundColor White
Write-Host "5. Models will be downloaded to: $ollamaModels" -ForegroundColor White

Write-Host ""
Write-Host "Configuration completed!" -ForegroundColor Green
