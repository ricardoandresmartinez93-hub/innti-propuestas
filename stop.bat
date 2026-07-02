@echo off
setlocal enableextensions
title Innti Propuestas - Detener
cd /d "%~dp0"

echo [INFO] Deteniendo la aplicacion...
docker compose down
echo [OK] Contenedores detenidos. Los datos se conservan en el volumen.
pause
endlocal
