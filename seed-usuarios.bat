@echo off
setlocal enableextensions
title Innti Propuestas - Usuarios de demo
cd /d "%~dp0"

echo [INFO] Creando usuarios de demostracion (creator / revisor / VP)...
echo        Password de todos: Innti2024!
echo.
docker compose exec -T backend python seed_users.py
echo.
pause
endlocal
