@echo off
REM Arranca la app para toda la oficina, desde el equipo que hace de servidor.
REM Los demas entran desde su navegador a http://IP-DE-ESTE-EQUIPO:8501
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
echo  Iniciando el Automatizador de Resoluciones en modo servidor...
echo.
echo  Direcciones de este equipo:
ipconfig | findstr /i "IPv4"
echo.
echo  Los sustanciadores entran a:  http://LA-IP-DE-ARRIBA:8501
echo.
echo  NO CIERRE ESTA VENTANA: si la cierra, la app deja de responder
echo  para todos.
echo.
%PY% -m streamlit run app.py --server.address 0.0.0.0
pause
