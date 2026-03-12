@echo off
title SCEIN Fellowship Scraper
echo ============================================
echo   SCEIN Fellowship - Data Scraper
echo   Running weekly refresh...
echo ============================================
echo.

:: Change to the folder where this .bat file lives
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Install required libraries (safe to run multiple times)
echo Installing/checking required libraries...
pip install pandas openpyxl requests beautifulsoup4 geopy lxml --quiet

echo.
echo Starting scraper...
echo.

:: Run the scraper
python scraper.py

echo.
echo ============================================
echo   Done! Check scraped_data.csv for results.
echo   QGIS will auto-refresh when you reload.
echo ============================================
echo.
pause
