@echo off
echo ========================================
echo    EJECUTANDO TODOS LOS TESTS UNITARIOS
echo ========================================
echo.

REM Cambiar al directorio del proyecto (donde está este archivo)
cd /d "%~dp0"

echo.
echo ========================================
echo    TEST 1: DATA PROCESSOR
echo ========================================
echo Ejecutando tests unitarios del procesador de datos...
echo.
python -m pytest .\tests\unit\test_data_processor.py -v
echo.
if %ERRORLEVEL% NEQ 0 (
    echo ❌ FALLO en test_data_processor.py
) else (
    echo ✅ test_data_processor.py COMPLETADO
)

echo.
echo ========================================
echo    TEST 2: KNOWLEDGE MODEL
echo ========================================
echo Ejecutando tests unitarios del modelo de conocimiento...
echo.
python -m pytest .\tests\unit\test_knowledge_model.py -v
echo.
if %ERRORLEVEL% NEQ 0 (
    echo ❌ FALLO en test_knowledge_model.py
) else (
    echo ✅ test_knowledge_model.py COMPLETADO
)

echo.
echo ========================================
echo    TEST 3: RULES ENGINE
echo ========================================
echo Ejecutando tests unitarios del motor de reglas...
echo.
python -m pytest .\tests\unit\test_rules_engine.py -v
echo.
if %ERRORLEVEL% NEQ 0 (
    echo ❌ FALLO en test_rules_engine.py
) else (
    echo ✅ test_rules_engine.py COMPLETADO
)

echo.
echo ========================================
echo           EJECUCIÓN COMPLETADA
echo ========================================
echo.

pause