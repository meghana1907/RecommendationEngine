# Setup Python 3.11 Environment for RecommendationEngine
# This script downloads Python 3.11, creates a virtual environment, and installs all dependencies

Write-Host "=== Python 3.11 Setup for RecommendationEngine ===" -ForegroundColor Green

# Step 1: Check if Python 3.11 is already installed
Write-Host "Checking for Python 3.11..." -ForegroundColor Yellow
$python311Path = ""

# Common Python 3.11 installation paths
$possiblePaths = @(
    "C:\Python311\python.exe",
    "C:\Program Files\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:APPDATA\Local\Programs\Python\Python311\python.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $version = & $path --version 2>$null
        if ($version -match "Python 3\.11") {
            $python311Path = $path
            Write-Host "Found Python 3.11 at: $path" -ForegroundColor Green
            break
        }
    }
}

# Step 2: Download and install Python 3.11 if not found
if (-not $python311Path) {
    Write-Host "Python 3.11 not found. Downloading and installing..." -ForegroundColor Yellow
    
    $downloadUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installerPath = "$env:TEMP\python-3.11.9-amd64.exe"
    
    try {
        Write-Host "Downloading Python 3.11.9..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "Installing Python 3.11.9..." -ForegroundColor Yellow
        Write-Host "Please wait for the installation to complete..." -ForegroundColor Cyan
        
        # Install Python silently with PATH addition
        Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
        
        # Clean up installer
        Remove-Item $installerPath -Force
        
        # Refresh environment variables
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        
        # Try to find Python 3.11 again
        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $version = & $path --version 2>$null
                if ($version -match "Python 3\.11") {
                    $python311Path = $path
                    Write-Host "Python 3.11 installed successfully at: $path" -ForegroundColor Green
                    break
                }
            }
        }
        
        if (-not $python311Path) {
            Write-Host "ERROR: Python 3.11 installation failed or not found in expected locations" -ForegroundColor Red
            Write-Host "Please manually install Python 3.11 from https://www.python.org/downloads/" -ForegroundColor Red
            exit 1
        }
        
    } catch {
        Write-Host "ERROR: Failed to download or install Python 3.11: $_" -ForegroundColor Red
        Write-Host "Please manually install Python 3.11 from https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Navigate to project directory
Write-Host "Navigating to project directory..." -ForegroundColor Yellow
Set-Location "C:\Users\Meghana Nemani\Documents\RecommendationEngine\backend_python"

# Step 4: Remove existing virtual environment if it exists
if (Test-Path "venv") {
    Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

# Step 5: Create new virtual environment with Python 3.11
Write-Host "Creating virtual environment with Python 3.11..." -ForegroundColor Yellow
try {
    & $python311Path -m venv venv
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to create virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Step 6: Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Step 7: Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip

# Step 8: Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan

try {
    & ".\venv\Scripts\pip.exe" install -r requirements.txt
    Write-Host "All requirements installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to install some requirements: $_" -ForegroundColor Red
    Write-Host "Trying to install packages individually..." -ForegroundColor Yellow
    
    # Try installing packages one by one
    $packages = Get-Content requirements.txt
    foreach ($package in $packages) {
        if ($package -and -not $package.StartsWith("#")) {
            Write-Host "Installing: $package" -ForegroundColor Cyan
            try {
                & ".\venv\Scripts\pip.exe" install $package
            } catch {
                Write-Host "Failed to install: $package" -ForegroundColor Red
            }
        }
    }
}

# Step 9: Verify installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" --version
& ".\venv\Scripts\pip.exe" list

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "To activate the environment in the future, run:" -ForegroundColor Cyan
Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To start your FastAPI server, run:" -ForegroundColor Cyan
Write-Host ".\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000" -ForegroundColor White