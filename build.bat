@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo          ZYROTECH FREE - BUILD
echo ========================================
python --version
if errorlevel 1 goto error

python -m pip install -r requirements-build.txt
if errorlevel 1 goto error

python tools\build.py
if errorlevel 1 goto error

if not exist dist\ZyroTech-Free.exe goto error

echo.
echo BUILD OK: dist\ZyroTech-Free.exe
pause
exit /b 0

:error
echo.
echo ERROR: no se pudo compilar ZyroTech Free.
pause
exit /b 1
