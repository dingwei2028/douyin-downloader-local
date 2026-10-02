@echo off
rem Douyin download - AUDIO ONLY, MP3 128k (counterpart of yt-dlp audio_only.bat)
rem Flow: download MP4 -> convert to MP3 -> delete MP4 (incremental via database)
rem Note: to get MP4 back later, run dy_download.bat (it re-downloads missing files)
rem Prereq: run finddyUP.bat first to write the UP's homepage into config.yml
cd /d "%~dp0"
".venv\Scripts\python.exe" dy_run.py audio
echo.
pause
