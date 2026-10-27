@echo off
rem ============================================================================
rem instalar_windows.bat - Diagnostico e instalacion de dependencias de BAJOTERRA en Windows.
rem Doble clic para ejecutarlo. Escribe todo en logs\instalacion.log (para revisarlo despues).
rem Hace: revisa Python/Node/Git/Arduino, crea .venv, instala requirements-local.txt,
rem instala las dependencias de la web con pnpm (via corepack) y corre las pruebas automaticas.
rem ============================================================================

rem Consola en UTF-8 para ver bien las tildes.
chcp 65001 >nul
rem Se ubica en la raiz del proyecto (la carpeta de arriba de scripts\).
cd /d "%~dp0.."
rem Carpeta de registros (esta en .gitignore).
if not exist logs mkdir logs
rem Archivo de registro.
set "LOG=%cd%\logs\instalacion.log"
rem Encabezado con fecha y hora.
echo ==== Instalacion BAJOTERRA %date% %time% ==== > "%LOG%"

rem --- 1. Diagnostico de herramientas -------------------------------------------
echo [diagnostico] >> "%LOG%"
rem Elige el comando de Python: "python" o, si no existe, el lanzador "py -3".
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
echo PY=%PY% >> "%LOG%"
%PY% --version >> "%LOG%" 2>&1
rem Node.js y corepack (traen pnpm).
node --version >> "%LOG%" 2>&1
where corepack >> "%LOG%" 2>&1
rem Git.
git --version >> "%LOG%" 2>&1
rem Arduino CLI que viene dentro de Arduino IDE 2 (instalacion por usuario o para todos).
set "ACLI=%LOCALAPPDATA%\Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
if not exist "%ACLI%" set "ACLI=%ProgramFiles%\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
if exist "%ACLI%" (echo ARDUINO_CLI=%ACLI% >> "%LOG%") else (echo ARDUINO_CLI=no encontrado >> "%LOG%")

rem --- 2. Entorno de Python ----------------------------------------------------
echo [python] >> "%LOG%"
rem Crea el entorno virtual solo si no existe.
if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv >> "%LOG%" 2>&1
rem Instala backend + simulador + broker local + pytest.
".venv\Scripts\python.exe" -m pip install -q -r requirements-local.txt >> "%LOG%" 2>&1
echo pip_codigo=%errorlevel% >> "%LOG%"

rem --- 3. Web (pnpm via corepack) ----------------------------------------------
echo [web] >> "%LOG%"
pushd web_pwa
rem Evita que corepack pregunte antes de descargar pnpm.
set COREPACK_ENABLE_DOWNLOAD_PROMPT=0
call corepack pnpm install --frozen-lockfile >> "%LOG%" 2>&1
echo pnpm_codigo=%errorlevel% >> "%LOG%"
rem Compila la web para comprobar que no hay errores.
call corepack pnpm build >> "%LOG%" 2>&1
echo build_codigo=%errorlevel% >> "%LOG%"
popd

rem --- 4. Pruebas automaticas ---------------------------------------------------
echo [pruebas backend] >> "%LOG%"
pushd backend
"..\.venv\Scripts\python.exe" -m pytest -q >> "%LOG%" 2>&1
echo pytest_backend_codigo=%errorlevel% >> "%LOG%"
popd
echo [pruebas simulador] >> "%LOG%"
pushd simulador
"..\.venv\Scripts\python.exe" -m pytest -q >> "%LOG%" 2>&1
echo pytest_simulador_codigo=%errorlevel% >> "%LOG%"
popd

rem Fin.
echo ==== FIN %date% %time% ==== >> "%LOG%"
echo Listo. Revisa logs\instalacion.log
timeout /t 5 >nul
