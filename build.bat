@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Comprobando Python...
python --version
if errorlevel 1 goto error

echo [2/4] Instalando dependencias...
python -m pip install pyinstaller customtkinter cryptography
if errorlevel 1 goto error

if not exist tools\zyrotech_private.pem (
    echo [3/4] Generando claves...
    python tools\keygen.py init
    if errorlevel 1 goto error
) else (
    echo [3/4] Clave privada existente; se conserva.
)

echo [4/4] Compilando aplicaciones...
python tools\build.py
if errorlevel 1 goto error

if not exist dist\ZyroTech-Free.exe goto error
if not exist dist\ZyroTech-Pro.exe goto error
echo.
echo COMPILACION EXITOSA. Los ejecutables estan en dist\
pause
exit /b 0

:error
echo.
echo ERROR: la compilacion fallo. Revisa el mensaje anterior.
pause
exit /b 1
