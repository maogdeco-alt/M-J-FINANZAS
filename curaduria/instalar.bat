@echo off
REM Instalacion por una sola vez. Requiere Python 3.10 o superior.
REM Descargue Python de python.org marcando "Add Python to PATH".

cd /d "%~dp0"
echo.
echo  Verificando Python...
python --version
if errorlevel 1 (
  echo.
  echo  ERROR: Python no esta instalado o no quedo en el PATH.
  echo  Descarguelo de https://www.python.org/downloads/
  echo  y marque la casilla "Add Python to PATH" al instalarlo.
  echo.
  pause
  exit /b 1
)

echo.
echo  Instalando los componentes de la app...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo  ERROR al instalar. Revise la conexion a internet.
  echo.
  pause
  exit /b 1
)

echo.
echo  Creando la plantilla de ejemplo...
python crear_plantilla_ejemplo.py

echo.
echo  Comprobando que todo quedo bien...
python verificar.py
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
