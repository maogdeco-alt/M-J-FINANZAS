@echo off
REM Instalacion por una sola vez. Requiere Python 3.10 o superior.
setlocal
cd /d "%~dp0"

echo.
echo  Buscando Python...

REM Primero "python"; si no sirve, el lanzador "py" que trae el instalador.
set PY=python
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 set PY=py
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo.
  echo  ERROR: no encontre Python.
  echo.
  echo  Descarguelo de https://www.python.org/downloads/ y al instalarlo
  echo  MARQUE la casilla "Add python.exe to PATH".
  echo  Si ya lo instalo, cierre esta ventana, abra una nueva y vuelva a
  echo  intentar: el PATH solo se actualiza en ventanas nuevas.
  echo.
  pause
  exit /b 1
)
%PY% --version

echo.
echo  Instalando los componentes de la app...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo  ERROR al instalar. Revise la conexion a internet.
  echo.
  pause
  exit /b 1
)

echo.
echo  Creando la plantilla de ejemplo...
%PY% crear_plantilla_ejemplo.py

echo.
echo  Comprobando que todo quedo bien...
%PY% verificar.py
if errorlevel 1 (
  echo.
  echo  Quedaron problemas por resolver. Lealos arriba.
  echo.
  pause
  exit /b 1
)

echo.
echo  Instalacion completa. Ahora puede usar iniciar.bat
echo.
pause
