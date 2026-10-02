@echo off
rem Douyin download - BEST quality MP4 + MP3 (counterpart of yt-dlp download.bat)
rem Prereq: run finddyUP.bat first to write the UP's homepage into config.yml
cd /d "%~dp0"
".venv\Scripts\python.exe" dy_run.py video
echo.
pause
