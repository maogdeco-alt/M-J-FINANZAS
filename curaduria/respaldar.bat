@echo off
REM Copia la biblioteca de bloques y las plantillas a una carpeta con fecha.
REM Es lo unico que la app guarda en disco: con esto no se pierde nada.
setlocal
cd /d "%~dp0"

REM La fecha se pide a PowerShell para no depender del formato regional.
set HOY=
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set HOY=%%i
if "%HOY%"=="" set HOY=respaldo

set DESTINO=respaldos\%HOY%

echo.
echo  Respaldando en %DESTINO% ...
if not exist "respaldos" mkdir "respaldos"
if not exist "%DESTINO%" mkdir "%DESTINO%"
xcopy "biblioteca" "%DESTINO%\biblioteca" /E /I /Y /Q >nul
xcopy "plantillas" "%DESTINO%\plantillas" /E /I /Y /Q >nul
if exist "configuracion.json" copy /Y "configuracion.json" "%DESTINO%\" >nul

echo.
echo  Listo. Copie la carpeta "%DESTINO%" a la carpeta compartida
echo  o a una USB.
echo.
pause
