@echo off
rem Douyin download - ORIGINAL quality MP4 + MP3
rem Unlike dy_download720.bat / dy_download.bat, this probes the UPLOADED MASTER
rem (via /aweme/v1/play/?ratio=default) instead of picking from the transcoded
rem bit_rate ladder. The ladder often tops out at 720p, so this is the only way
rem to get e.g. 1440x1080 HEVC 60fps for a video whose ladder max is 960x720.
rem NOTE: the master can be 10x+ the size of the 720p transcode.
rem Prereq: run finddyUP.bat first to write the UP's homepage into config.yml
cd /d "%~dp0"
".venv\Scripts\python.exe" dy_run.py original
echo.
pause
