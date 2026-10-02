@echo off
rem Douyin single video download (ORIGINAL quality MP4 + MP3)
rem Usage: dy_one.bat "<douyin URL>" [original^|video^|720^|audio]
rem        or double-click and paste the URL.
setlocal
set "PYEXE=%~dp0.venv\Scripts\python.exe"
echo ============================================================
echo   Douyin: download ONE video
echo   1. Paste the video URL, then press Enter
echo      (douyin.com/video/xxx  /  ...?modal_id=xxx  /  v.douyin.com/xxx)
echo   2. Leave blank = use the 1st douyin link in dy_urls.txt
echo   Mode ORIGINAL by default; 2nd arg = video / 720 / audio
echo ============================================================
if "%~1"=="" (set /p "URL=Paste douyin URL + Enter: ") else (set "URL=%~1")
"%PYEXE%" "%~dp0dy_one.py" "%URL%" "%~2"
echo.
pause
