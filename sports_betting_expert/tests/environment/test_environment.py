import pytest
import sys
import os
import inspect

# Agregar el directorio src al path para poder importar experta_fix
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)    # tests/
root_dir = os.path.dirname(parent_dir)       # sports_betting_expert/
sys.path.insert(0, os.path.join(root_dir, 'src'))

# Importar el fix antes de cualquier otra importación
import experta_fix

def test_python_version():
    """Verifica que estemos usando una versión de Python compatible"""
    assert sys.version_info.major == 3 and sys.version_info.minor >= 8, \
        f"Python 3.8+ requerido, versión actual: {sys.version_info.major}.{sys.version_info.minor}"

def test_experta_import():
    """Verifica que experta se importe correctamente sin el error de collections.Mapping"""
    try:
        from experta import KnowledgeEngine, Fact, Rule, DefFacts
        # Crear un motor de conocimiento simple para probar
        class TestEngine(KnowledgeEngine):
            @DefFacts()
            def initial_facts(self):
                yield Fact(test=True)
            
            @Rule(Fact(test=True))
            def test_rule(self):
                pass
        
        # Intentar crear una instancia
        engine = TestEngine()
        assert True
    except ImportError as e:
        assert False, f"Error al importar experta: {str(e)}"
    except AttributeError as e:
        assert False, f"Error de atributo (posible problema collections.Mapping): {str(e)}"
    except Exception as e:
        assert False, f"Error inesperado con experta: {str(e)}"

def test_pgmpy_import():
    """Verifica que pgmpy se importe correctamente"""
    try:
        # Usar DiscreteBayesianNetwork en lugar de BayesianNetwork
        from pgmpy.models import DiscreteBayesianNetwork
        from pgmpy.factors.discrete import TabularCPD
        
        # Crear un modelo básico para probar
        model = DiscreteBayesianNetwork([('A', 'B')])
        assert True
    except ImportError as e:
        assert False, f"Error al importar pgmpy: {str(e)}"
    except Exception as e:
        assert False, f"Error inesperado con pgmpy: {str(e)}"

def test_pandas_numpy_import():
    """Verifica que pandas y numpy se importen correctamente"""
    try:
        import pandas as pd
        import numpy as np
        
        # Operación básica para verificar funcionalidad
        df = pd.DataFrame({'A': np.random.rand(5)})
        assert len(df) == 5
    except ImportError as e:
        assert False, f"Error al importar pandas/numpy: {str(e)}"
    except Exception as e:
        assert False, f"Error inesperado con pandas/numpy: {str(e)}"

if __name__ == "__main__":
    # Ejecutar las pruebas directamente si se ejecuta el script
    print("Verificando entorno de desarrollo...")
    
    try:
        test_python_version()
        print("✓ Versión de Python correcta")
    except AssertionError as e:
        print(f"✗ {str(e)}")
    
    try:
        test_experta_import()
        print("✓ Experta importado correctamente")
    except AssertionError as e:
        print(f"✗ {str(e)}")
    
    try:
        test_pgmpy_import()
        print("✓ pgmpy importado correctamente")
    except AssertionError as e:
        print(f"✗ {str(e)}")
    
    try:
        test_pandas_numpy_import()
        print("✓ pandas y numpy importados correctamente")
    except AssertionError as e:
        print(f"✗ {str(e)}")
    
    print("Verificación de entorno completada.")