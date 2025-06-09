"""
Script para descargar automáticamente los datos de la UCL desde Kaggle.
"""
import os
import shutil
import sys
from pathlib import Path

try:
    import kagglehub
except ImportError:
    print("❌ Error: kagglehub no está instalado")
    print("   Instala con: pip install kagglehub")
    sys.exit(1)

def check_data_availability():
    """Verifica si los datos de la UCL están disponibles."""
    # Cambiar al directorio padre (raíz del proyecto) para acceder correctamente a data/raw
    current_dir = os.getcwd()
    project_root = os.path.dirname(current_dir) if os.path.basename(current_dir) == 'setup' else current_dir
    data_dir = os.path.join(project_root, 'data', 'raw')
    expected_files = [
        'attacking.csv', 
        'attempts.csv', 
        'defending.csv', 
        'disciplinary.csv', 
        'distributon.csv',  
        'goalkeeping.csv', 
        'goals.csv', 
        'key_stats.csv'
    ]
    
    missing_files = []
    for file in expected_files:
        file_path = os.path.join(data_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"Faltan {len(missing_files)} archivos de datos:")
        for file in missing_files:
            print(f"- {file}")
        return False, missing_files
    else:
        print("✓ Todos los archivos de datos necesarios están disponibles.")
        return True, []

def download_ucl_dataset():
    """
    Descarga automáticamente el dataset de la UCL desde Kaggle.
    
    Returns:
        bool: True si la descarga fue exitosa, False en caso contrario.
    """
    try:
        print("📥 Iniciando descarga del dataset UCL 2021/22...")
        
        # Descargar dataset desde Kaggle
        kaggle_path = kagglehub.dataset_download("azminetoushikwasi/ucl-202122-uefa-champions-league")
        print(f"✓ Dataset descargado en: {kaggle_path}")        # Crear directorio de destino si no existe
        current_dir = os.getcwd()
        project_root = os.path.dirname(current_dir) if os.path.basename(current_dir) == 'setup' else current_dir
        target_dir = os.path.join(project_root, 'data', 'raw')
        os.makedirs(target_dir, exist_ok=True)
        print(f"✓ Directorio de destino creado: {os.path.abspath(target_dir)}")
        
        # Lista de archivos esperados
        expected_files = [
            'attacking.csv', 
            'attempts.csv', 
            'defending.csv', 
            'disciplinary.csv', 
            'distributon.csv',  
            'goalkeeping.csv', 
            'goals.csv', 
            'key_stats.csv'
        ]
        
        # Copiar archivos CSV al directorio de destino
        copied_files = []
        for filename in expected_files:
            source_path = os.path.join(kaggle_path, filename)
            target_path = os.path.join(target_dir, filename)
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                copied_files.append(filename)
                print(f"  ✓ Copiado: {filename}")
            else:
                print(f"  ⚠️  No encontrado: {filename}")
        
        print(f"\n✅ Descarga completada. Archivos copiados: {len(copied_files)}/{len(expected_files)}")
        
        if len(copied_files) == len(expected_files):
            print("🎉 Todos los archivos necesarios están disponibles.")
            return True
        else:
            print("⚠️  Algunos archivos no se pudieron descargar.")
            return False
            
    except ImportError:
        print("❌ Error: No se pudo importar 'kagglehub'.")
        print("   Instala con: pip install kagglehub")
        return False
    except Exception as e:
        print(f"❌ Error durante la descarga: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando disponibilidad de datos UCL 2021/22...")
    data_available, missing_files = check_data_availability()
    
    if not data_available:
        print(f"\n📥 Faltan {len(missing_files)} archivos. Iniciando descarga automática...")
        success = download_ucl_dataset()
        
        if success:
            print("\n🎉 ¡Descarga completada exitosamente!")
            print("✓ Todos los archivos están listos para usar.")
        else:
            print("\n❌ Error en la descarga. Verifica:")
            print("1. Conexión a internet")
            print("2. Que tengas instalado kagglehub: pip install kagglehub")
            print("3. Autenticación de Kaggle (si es necesaria)")
    else:
        print("\n✅ Datos ya disponibles. No es necesario descargar.")