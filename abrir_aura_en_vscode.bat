@echo off
setlocal
cd /d A:\AURA\project

where code >nul 2>nul
if errorlevel 1 (
    echo [ERROR] VS Code no esta disponible en PATH.
    pause
    exit /b 1
)

code .
