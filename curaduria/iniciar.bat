@echo off
REM Arranca la app solo en este equipo. Doble clic y listo.
REM La primera vez, ejecute primero instalar.bat

cd /d "%~dp0"
echo.
echo  Iniciando el Automatizador de Resoluciones...
echo  Se abrira en el navegador: http://localhost:8501
echo.
echo  NO CIERRE ESTA VENTANA mientras use la app.
echo  Para cerrar la app, presione Ctrl+C o cierre esta ventana.
echo.
start "" http://localhost:8501
python -m streamlit run app.py --server.address 127.0.0.1
pause
