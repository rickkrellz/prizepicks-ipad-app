@echo off
echo ========================================
echo Starting PrizePicks Data Fetcher
echo ========================================

cd /d C:\Users\venen\Desktop\prizepicks-ipad-app

echo Activating virtual environment...
call venv\Scripts\activate

echo Running fetcher...
python local_fetcher.py

echo.
echo Press any key to close...
pause > nul