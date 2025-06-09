"""
Script de prueba para verificar la descarga automática de datos.
"""
import os
import sys

def test_download():
    """Probar la funcionalidad de descarga."""
    print("🧪 Probando la descarga automática de datos UCL...")
    
    # Ejecutar el script de descarga (import directo desde mismo directorio)
    from download_dataset import check_data_availability, download_ucl_dataset
    
    print("\n1. Verificando estado actual de los datos...")
    data_available, missing_files = check_data_availability()
    
    if not data_available:
        print(f"\n2. Iniciando descarga de {len(missing_files)} archivos faltantes...")
        success = download_ucl_dataset()
        
        if success:
            print("\n3. ✅ Verificando que la descarga fue exitosa...")
            data_available, missing_files = check_data_availability()
            
            if data_available:
                print("🎉 ¡Todos los archivos están disponibles!")                # Mostrar información de los archivos descargados
                current_dir = os.getcwd()
                project_root = os.path.dirname(current_dir) if os.path.basename(current_dir) == 'setup' else current_dir
                data_dir = os.path.join(project_root, 'data', 'raw')
                print(f"\n📁 Archivos en {os.path.abspath(data_dir)}:")
                
                expected_files = [
                    'attacking.csv', 'attempts.csv', 'defending.csv', 
                    'disciplinary.csv', 'distributon.csv', 'goalkeeping.csv', 
                    'goals.csv', 'key_stats.csv'
                ]
                
                for file in expected_files:
                    file_path = os.path.join(data_dir, file)
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        print(f"  ✓ {file} ({size:,} bytes)")
                    else:
                        print(f"  ❌ {file} (no encontrado)")
            else:
                print("❌ Error: algunos archivos siguen faltando después de la descarga")
        else:
            print("❌ Error en la descarga")
    else:
        print("\n✅ Los datos ya están disponibles. No es necesario descargar.")

if __name__ == "__main__":
    test_download()
