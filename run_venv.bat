@echo off
echo 🚀 SRMIST Syllabus Extractor Portal - Virtual Environment Setup
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install requests==2.31.0
pip install PyPDF2==2.12.1
pip install fuzzywuzzy==0.18.0
pip install python-levenshtein==0.23.0
pip install python-multipart==0.0.6

echo.
echo ✅ All dependencies installed!
echo.

REM Start the application
echo 🚀 Starting SRMIST Syllabus Extractor Portal...
echo 📚 Ready to search the 587-page Computing Programmes Syllabus 2021
echo.
echo 🌐 Open your browser and go to: http://localhost:8000
echo.
python app.py

pause
