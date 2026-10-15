@echo off
REM Arranca la app para toda la oficina, desde el equipo que hace de servidor.
REM Los demas entran desde su navegador a http://IP-DE-ESTE-EQUIPO:8501

cd /d "%~dp0"
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
python -m streamlit run app.py --server.address 0.0.0.0
pause
