@echo off
REM Copia la biblioteca de bloques y las plantillas a una carpeta con fecha.
REM Es lo unico que la app guarda en disco: con esto no se pierde nada.

cd /d "%~dp0"
for /f "tokens=1-3 delims=/-. " %%a in ("%DATE%") do set HOY=%%c-%%b-%%a
set DESTINO=respaldos\%HOY%

echo.
echo  Respaldando en %DESTINO% ...
if not exist "respaldos" mkdir "respaldos"
if not exist "%DESTINO%" mkdir "%DESTINO%"
xcopy "biblioteca" "%DESTINO%\biblioteca" /E /I /Y /Q >nul
xcopy "plantillas" "%DESTINO%\plantillas" /E /I /Y /Q >nul

echo.
echo  Listo. Copie la carpeta "%DESTINO%" a la carpeta compartida
echo  o a una USB.
echo.
pause
