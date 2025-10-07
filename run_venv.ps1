Write-Host "🚀 SRMIST Syllabus Extractor Portal - Virtual Environment Setup" -ForegroundColor Cyan
Write-Host ""

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created!" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install fastapi==0.104.1
pip install "uvicorn[standard]==0.24.0"
pip install requests==2.31.0
pip install PyPDF2==3.0.1
pip install fuzzywuzzy==0.18.0
pip install python-levenshtein==0.23.0
pip install python-multipart==0.0.6

Write-Host ""
Write-Host "✅ All dependencies installed!" -ForegroundColor Green
Write-Host ""

# Start the application
Write-Host "🚀 Starting SRMIST Syllabus Extractor Portal..." -ForegroundColor Cyan
Write-Host "📚 Ready to search the 587-page Computing Programmes Syllabus 2021" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Open your browser and go to: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""

python app.py
