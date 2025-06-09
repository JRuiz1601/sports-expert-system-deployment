"""
Fix para compatibilidad de experta con Python 3.10+
Soluciona el problema de collections.Mapping movido a collections.abc
"""
import collections
import collections.abc

def apply_experta_compatibility_fix():
    """Aplica los patches necesarios para experta."""
    patches_applied = []
    
    # Fix para Mapping
    if not hasattr(collections, 'Mapping'):
        collections.Mapping = collections.abc.Mapping
        patches_applied.append('Mapping')
    
    # Fix para MutableMapping
    if not hasattr(collections, 'MutableMapping'):
        collections.MutableMapping = collections.abc.MutableMapping
        patches_applied.append('MutableMapping')
    
    # Fix para Iterable
    if not hasattr(collections, 'Iterable'):
        collections.Iterable = collections.abc.Iterable
        patches_applied.append('Iterable')
    
    # Fix para Sequence
    if not hasattr(collections, 'Sequence'):
        collections.Sequence = collections.abc.Sequence
        patches_applied.append('Sequence')
    
    if patches_applied:
        print(f"✓ Patches aplicados: {', '.join(patches_applied)}")
    else:
        print("✓ No se necesitaron patches")
    
    return patches_applied

# Aplicar el fix automáticamente al importar
apply_experta_compatibility_fix()