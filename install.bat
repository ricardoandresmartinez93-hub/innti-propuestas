@echo off
setlocal enableextensions
title Innti Propuestas - Instalador
cd /d "%~dp0"

echo ==================================================
echo    Innti Propuestas - Instalador (Docker)
echo ==================================================
echo.

REM --- 1. Docker instalado? ---
where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker no esta instalado en esta PC.
  echo.
  echo Descarga e instala Docker Desktop desde:
  echo    https://www.docker.com/products/docker-desktop/
  echo Reinicia la PC si el instalador lo pide y vuelve a ejecutar install.bat
  echo.
  pause
  exit /b 1
)

REM --- 2. Docker corriendo? ---
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop esta instalado pero NO esta corriendo.
  echo.
  echo Abre "Docker Desktop", espera a que el icono diga "Running"
  echo y luego vuelve a ejecutar install.bat
  echo.
  pause
  exit /b 1
)

echo [OK] Docker detectado y en ejecucion.
echo.

REM --- 3. Asegurar backend\.env ---
if not exist "backend\.env" (
  echo [INFO] No se encontro backend\.env. Creando desde la plantilla...
  copy "backend\.env.example" "backend\.env" >nul
  echo.
  echo ==================================================
  echo   ACCION REQUERIDA: edita tus credenciales
  echo ==================================================
  echo   Se abrira backend\.env en el Bloc de notas.
  echo   Completa al menos:
  echo     - INNTI_API_KEY   (clave de la IA)
  echo     - SMTP_*          (correo, solo si usas notificaciones)
  echo   Guarda el archivo y cierra el Bloc de notas.
  echo.
  pause
  notepad "backend\.env"
  echo Presiona una tecla cuando hayas guardado los cambios...
  pause >nul
) else (
  echo [OK] backend\.env ya existe, se usara tal cual.
)

REM --- 4. Construir y levantar ---
echo.
echo [INFO] Construyendo y levantando la aplicacion.
echo        La PRIMERA vez puede tardar varios minutos (descarga imagenes).
echo.
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo [ERROR] Fallo al construir/levantar los contenedores.
  echo Revisa el mensaje de error de arriba.
  pause
  exit /b 1
)

REM --- 5. Esperar al backend ---
echo.
echo [INFO] Esperando a que el backend responda...
set /a tries=0
:waitloop
timeout /t 3 /nobreak >nul
curl -s -o nul http://localhost:8000/docs
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% lss 20 goto waitloop
echo [WARN] El backend tardo mas de lo esperado. Continuo igual.
:ready

REM --- 6. Listo ---
echo.
echo ==================================================
echo    INSTALACION COMPLETA
echo ==================================================
echo    Aplicacion:  http://localhost
echo    API / Docs:  http://localhost:8000/docs
echo.
echo    Usuario administrador inicial:
echo       email:    admin@quipux.com
echo       password: Admin2024!
echo.
echo    Para crear los usuarios de demo (creator/revisor/VP),
echo    ejecuta:  seed-usuarios.bat
echo ==================================================
echo.
start "" http://localhost
pause
endlocal
