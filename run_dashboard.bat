@echo off
REM Company X Analytics Dashboard Launcher (Windows)
REM Quick start script for the Streamlit dashboard

echo ======================================
echo Company X Analytics Dashboard
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python 3 is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo Python found
echo.

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo Starting dashboard...
echo The dashboard will open in your browser automatically.
echo Press Ctrl+C to stop the server.
echo.

REM Run Streamlit
streamlit run app.py
