@echo off
title Setup Weekly Task Scheduler
echo ============================================
echo   Setting up Weekly Auto-Refresh
echo   Every Monday at 8:00 AM
echo ============================================
echo.

:: Get the full path to run_scraper.bat
set "SCRIPT_PATH=%~dp0run_scraper.bat"
set "TASK_NAME=SCEIN_Weekly_Scraper"

echo Creating scheduled task: %TASK_NAME%
echo Script: %SCRIPT_PATH%
echo Schedule: Every Monday at 8:00 AM
echo.

:: Delete existing task if it exists
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Create new weekly task
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%SCRIPT_PATH%\"" ^
  /sc WEEKLY ^
  /d MON ^
  /st 08:00 ^
  /rl HIGHEST ^
  /f

if errorlevel 1 (
    echo.
    echo ERROR: Could not create task. Try running as Administrator.
    echo Right-click this .bat file and select "Run as administrator"
) else (
    echo.
    echo SUCCESS! Task scheduled successfully.
    echo.
    echo The scraper will now run automatically every Monday at 8:00 AM.
    echo Your laptop must be ON at that time.
    echo.
    echo To verify: Open Task Scheduler and look for "%TASK_NAME%"
    echo To run now: Double-click run_scraper.bat
)

echo.
pause
