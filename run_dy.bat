@echo off
rem Douyin default entry (= dy_download.bat, best MP4 + MP3)
rem Trio: dy_download.bat / dy_download720.bat / dy_audio_only.bat
rem Prereq: run finddyUP.bat first
cd /d "%~dp0"
".venv\Scripts\python.exe" dy_run.py video
echo.
pause
