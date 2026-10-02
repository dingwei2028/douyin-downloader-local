@echo off
rem Douyin download - 720p MP4 + MP3 (counterpart of yt-dlp download720.bat)
rem Prereq: run finddyUP.bat first to write the UP's homepage into config.yml
cd /d "%~dp0"
".venv\Scripts\python.exe" dy_run.py 720
echo.
pause
