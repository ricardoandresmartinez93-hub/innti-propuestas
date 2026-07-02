@echo off
setlocal enableextensions
title Innti Propuestas - Iniciar
cd /d "%~dp0"

docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop no esta corriendo. Abrelo y reintenta.
  pause
  exit /b 1
)

echo [INFO] Iniciando la aplicacion...
docker compose up -d
if errorlevel 1 (
  echo [ERROR] No se pudo iniciar. Si es la primera vez, ejecuta install.bat
  pause
  exit /b 1
)

echo [OK] Aplicacion disponible en http://localhost
start "" http://localhost
endlocal
