@echo off
rem Douyin: batch-download ALL followed UPs (no URL copying needed)
rem Prereq: valid douyin login session (sessionid) in config.yml cookies
setlocal
cd /d "%~dp0"
set /p "ARGS=Mode (video/720/audio, optional name filter, e.g.: video): "
".venv\Scripts\python.exe" dy_follow.py %ARGS%
echo.
pause
