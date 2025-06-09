"""
Script para mover los datos descargados al lugar correcto dentro del proyecto.
"""
import os
import shutil

def move_data_to_correct_location():
    """Mueve los datos de la ubicación incorrecta a la correcta."""
    
    # Ubicación incorrecta (fuera del proyecto)
    wrong_location = os.path.join('..', '..', 'data', 'raw')
    
    # Ubicación correcta (dentro del proyecto)
    current_dir = os.getcwd()
    project_root = os.path.dirname(current_dir) if os.path.basename(current_dir) == 'setup' else current_dir
    correct_location = os.path.join(project_root, 'data', 'raw')
    
    print(f"Ubicación incorrecta: {os.path.abspath(wrong_location)}")
    print(f"Ubicación correcta: {os.path.abspath(correct_location)}")
    
    if os.path.exists(wrong_location):
        print("📁 Datos encontrados en ubicación incorrecta. Moviendo...")
        
        # Crear directorio correcto si no existe
        os.makedirs(correct_location, exist_ok=True)
        
        # Listar archivos en ubicación incorrecta
        files_to_move = []
        for file in os.listdir(wrong_location):
            if file.endswith('.csv'):
                files_to_move.append(file)
        
        print(f"📦 Archivos encontrados: {len(files_to_move)}")
        
        # Mover archivos
        moved_count = 0
        for file in files_to_move:
            source = os.path.join(wrong_location, file)
            destination = os.path.join(correct_location, file)
            
            try:
                shutil.move(source, destination)
                print(f"  ✓ Movido: {file}")
                moved_count += 1
            except Exception as e:
                print(f"  ❌ Error moviendo {file}: {e}")
        
        print(f"\n✅ Archivos movidos: {moved_count}/{len(files_to_move)}")
        
        # Intentar eliminar la carpeta vacía
        try:
            if not os.listdir(wrong_location):
                os.rmdir(wrong_location)
                print("🗑️  Carpeta vacía eliminada")
        except:
            pass
            
    else:
        print("📁 No se encontraron datos en la ubicación incorrecta.")
    
    # Verificar que los datos están en el lugar correcto
    if os.path.exists(correct_location):
        files_in_correct = [f for f in os.listdir(correct_location) if f.endswith('.csv')]
        print(f"\n📊 Archivos en ubicación correcta: {len(files_in_correct)}")
        for file in files_in_correct:
            print(f"  ✓ {file}")
    else:
        print("\n❌ No se encontraron datos en la ubicación correcta.")

if __name__ == "__main__":
    move_data_to_correct_location()
