@echo off
setlocal enableextensions
title Innti Propuestas - Empaquetar instalador
cd /d "%~dp0"

set "STAGE=%TEMP%\innti-pkg"
set "OUTZIP=%USERPROFILE%\Desktop\innti-propuestas-instalador.zip"

echo ==================================================
echo    Empaquetando instalador limpio...
echo ==================================================
echo.

REM --- Limpiar staging previo ---
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%"

echo [INFO] Copiando archivos (excluyendo basura y datos privados)...
robocopy "." "%STAGE%" /E ^
  /XD ".git" "node_modules" "dist" ".idea" ".pytest_cache" "__pycache__" ".opencode" ".atl" ".claude" "htmlcov" "openspec" ^
  /XF "*.db" "*.db.backup-*" "*.log" "*.tmp" "~$*.xlsx" "identifier.sqlite" ^
  /NFL /NDL /NJH /NJS /NP >nul

if %ERRORLEVEL% GEQ 8 (
  echo [ERROR] Fallo al copiar archivos.
  pause
  exit /b 1
)

REM --- Borrar ZIP anterior si existe ---
if exist "%OUTZIP%" del /q "%OUTZIP%"

echo [INFO] Comprimiendo a ZIP...
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE%\*' -DestinationPath '%OUTZIP%' -Force"
if errorlevel 1 (
  echo [ERROR] Fallo al comprimir el ZIP.
  pause
  exit /b 1
)

REM --- Limpiar staging ---
rmdir /s /q "%STAGE%"

echo.
echo ==================================================
echo    LISTO
echo ==================================================
echo    ZIP generado en tu Escritorio:
echo      %OUTZIP%
echo.
echo    OJO: ese ZIP incluye backend\.env con tus claves
echo    reales. Pasalo solo a personas de confianza.
echo ==================================================
echo.
pause
endlocal
