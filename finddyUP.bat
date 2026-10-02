@echo off
rem Douyin: video URL -> find the UP's homepage -> write into config.yml link:
rem Usage: paste URL below, or put it as 1st douyin line in
rem        C:\Github\douyin-downloader\dy_urls.txt
setlocal
set "PYEXE=%~dp0.venv\Scripts\python.exe"
echo ============================================================
echo   Douyin: resolve UP from one video URL
echo   1. Paste any video URL of the UP (blank = read 1st douyin
echo      line of C:\Github\douyin-downloader\dy_urls.txt)
echo   2. Then double-click dy_download.bat / dy_audio_only.bat
echo ============================================================
set /p "KW=Paste douyin video URL + Enter: "
rem Keep the quotes: douyin URLs usually carry & (modal_id=xxx&type=general).
rem A bare %KW% would let cmd split at & and pass only the truncated half.
"%PYEXE%" "%~dp0dy_find_up.py" "%KW%"
pause
