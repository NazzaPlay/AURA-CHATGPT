@echo off
setlocal
title AURA Launcher
cd /d A:\AURA\project

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en A:\AURA\project\.venv
    pause
    exit /b 1
)

if not defined AURA_MODEL_DIR set "AURA_MODEL_DIR=A:\AURA\models"
if not defined AURA_LLAMA_PATH if not defined AURA_PRIMARY_LLAMA_PATH set "AURA_LLAMA_PATH=llama-cli"

echo Iniciando AURA...
echo [INFO] project: A:\AURA\project
echo [INFO] models: %AURA_MODEL_DIR%
if defined AURA_PRIMARY_LLAMA_PATH (
    echo [INFO] primary llama override: %AURA_PRIMARY_LLAMA_PATH%
) else (
    echo [INFO] llama-cli: %AURA_LLAMA_PATH%
)

call ".venv\Scripts\activate.bat"
python aura.py

echo.
echo AURA se cerro.
pause
