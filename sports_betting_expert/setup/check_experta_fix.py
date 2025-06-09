# Archivo pequeño para verificar que experta_fix funciona
import sys
import os
from src import experta_fix
sys.path.insert(0, os.path.abspath('.'))

try:
    # Importar el fix
    experta_fix = experta_fix.apply_experta_compatibility_fix()
    from src import experta_fix
    print("✓ Importación de experta_fix exitosa")
    
    # Verificar que el parche se aplicó correctamente
    import collections
    if hasattr(collections, 'Mapping'):
        print("✓ collections.Mapping está disponible")
    else:
        print("⨯ collections.Mapping no está disponible")
    
    # Intentar importar experta
    from experta import KnowledgeEngine
    print("✓ Importación de experta exitosa")
    
except Exception as e:
    print(f"⨯ Error: {str(e)}")