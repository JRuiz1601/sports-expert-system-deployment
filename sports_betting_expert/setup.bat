@echo off
REM ========================================================================
REM Setup completo del proyecto Sistema Experto UCL
REM ========================================================================

echo 🚀 Configurando Sistema Experto para Apuestas Deportivas UCL
echo ========================================================================
echo.

REM Verificar que Python está disponible
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: Python no encontrado
    echo    Instala Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 🐍 Python encontrado:
python --version
echo.

REM Paso 1: Crear entorno virtual
echo 📦 Creando entorno virtual...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo ❌ Error creando entorno virtual
    pause
    exit /b 1
)
echo ✓ Entorno virtual creado
echo.

REM Paso 2: Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ❌ Error activando entorno virtual
    pause
    exit /b 1
)
echo ✓ Entorno virtual activado
echo.

REM Paso 3: Instalar dependencias
echo 📚 Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)
echo ✓ Dependencias instaladas
echo.

REM Paso 4: Crear estructura de carpetas
echo 📁 Creando estructura de carpetas...
if not exist "data" mkdir data
if not exist "data\raw" mkdir data\raw
echo ✓ Carpeta data\raw creada
echo.

REM Paso 5: Descargar datos UCL
echo 📥 Descargando datos UCL 2021/22...
python setup\download_dataset.py
if %ERRORLEVEL% neq 0 (
    echo ❌ Error descargando datos
    pause
    exit /b 1
)
echo.

REM Paso 6: Ejecutar test de verificación
echo 🧪 Ejecutando test de verificación...
python setup\test_download.py
if %ERRORLEVEL% neq 0 (
    echo ❌ Error en test de verificación
    pause
    exit /b 1
)
echo.

REM Resumen final
echo ========================================================================
echo 🎉 ¡SETUP COMPLETADO EXITOSAMENTE!
echo.
echo ✅ Configuración finalizada:
echo   ✓ Entorno virtual: venv\
echo   ✓ Dependencias instaladas
echo   ✓ Carpeta data\raw creada
echo   ✓ Datos UCL descargados
echo   ✓ Verificación completada
echo.
echo ========================================================================

pause
