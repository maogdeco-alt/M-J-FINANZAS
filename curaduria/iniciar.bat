@echo off
REM Arranca la app solo en este equipo. Doble clic y listo.
REM La primera vez, ejecute primero instalar.bat
setlocal
cd /d "%~dp0"

set PY=python
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 set PY=py
%PY% -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo  ERROR: no encontre Python. Ejecute primero instalar.bat
  pause
  exit /b 1
)

echo.
echo  Iniciando el Automatizador de Resoluciones...
echo  Se abrira en el navegador: http://localhost:8501
echo.
echo  NO CIERRE ESTA VENTANA mientras use la app.
echo  Para apagar la app, cierre esta ventana o presione Ctrl+C.
echo.
start "" http://localhost:8501
%PY% -m streamlit run app.py --server.address 127.0.0.1
pause
