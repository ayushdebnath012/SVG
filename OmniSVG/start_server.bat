@echo off
echo ============================================
echo  OmniSVG Web Server
echo ============================================
echo.

REM Activate conda env if it exists
IF EXIST "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat" omnisvg
) ELSE IF EXIST "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat" omnisvg
)

cd /d "%~dp0"

echo Starting server on http://localhost:8000
echo Open your browser to http://localhost:8000
echo Press Ctrl+C to stop.
echo.

python server.py --port 8000 --model-size 4B

pause
