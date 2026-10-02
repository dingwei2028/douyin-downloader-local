@echo off
rem Douyin: set/clear the download time window (start_time / end_time in config.yml)
rem Use case: UP has 300+ videos, only want the ones from a certain date on
rem Flow: run this -> enter dates -> then dy_download.bat as usual -> clear when done
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" dy_setdate.py
echo.
pause
