"""
Punto de entrada principal para el Sistema Experto de Consejos de Apuestas Deportivas.
"""
import os
import sys

# Asegurarnos de que src esté en el path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Importar el fix de experta antes de cualquier otra importación
from src import experta_fix

# Importar el procesador de datos
from data_processor import UCLDataProcessor


def mostrar_menu():
    """Muestra el menú principal de opciones."""
    print("\n" + "="*60)
    print("    SISTEMA EXPERTO DE APUESTAS DEPORTIVAS - MENÚ")
    print("="*60)
    print("1. Generar estadísticas de TODOS los equipos (exportar a archivo)")
    print("2. Consultar resumen de un equipo específico")
    print("0. Salir")
    print("="*60)


def mostrar_lista_equipos(processor):
    """Muestra la lista de todos los equipos disponibles."""
    try:
        teams = processor.get_teams_list()
        print(f"\n📋 EQUIPOS DISPONIBLES ({len(teams)} equipos):")
        print("-" * 50)
        
        for i, team in enumerate(teams, 1):
            print(f"{i:2d}. {team}")
        
        return teams
    except Exception as e:
        print(f"❌ Error al obtener lista de equipos: {str(e)}")
        return []


def consultar_equipo(processor):
    """Permite al usuario consultar el resumen de un equipo."""
    teams = mostrar_lista_equipos(processor)
    
    if not teams:
        return
    
    print(f"\n🔍 CONSULTA DE EQUIPO")
    print("Puedes escribir:")
    print("- El nombre completo del equipo")
    print("- El número del equipo de la lista")
    print("- 'menu' para volver al menú principal")
    
    while True:
        user_input = input("\n👉 Ingresa el equipo a consultar: ").strip()
        
        if user_input.lower() == 'menu':
            return
        
        # Verificar si es un número
        if user_input.isdigit():
            team_index = int(user_input) - 1
            if 0 <= team_index < len(teams):
                selected_team = teams[team_index]
            else:
                print(f"❌ Número inválido. Debe ser entre 1 y {len(teams)}")
                continue
        else:
            # Buscar por nombre (busqueda flexible)
            matching_teams = [team for team in teams if user_input.lower() in team.lower()]
            
            if len(matching_teams) == 1:
                selected_team = matching_teams[0]
            elif len(matching_teams) > 1:
                print(f"\n⚠️ Encontrados {len(matching_teams)} equipos similares:")
                for i, team in enumerate(matching_teams, 1):
                    print(f"  {i}. {team}")
                print("Por favor, sé más específico.")
                continue
            else:
                print(f"❌ No se encontró ningún equipo con '{user_input}'")
                print("Verifica la ortografía o usa el número del equipo.")
                continue
        
        # Mostrar resumen del equipo seleccionado
        mostrar_resumen_equipo(processor, selected_team)
        
        # Preguntar si quiere consultar otro equipo
        otra_consulta = input("\n¿Quieres consultar otro equipo? (s/n): ").strip().lower()
        if otra_consulta not in ['s', 'si', 'sí', 'y', 'yes']:
            break


def mostrar_resumen_equipo(processor, team_name):
    """Muestra el resumen COMPLETO de un equipo con TODOS los datos para apuestas."""
    try:
        print(f"\n{'='*80}")
        print(f"    📊 ANÁLISIS COMPLETO PARA APUESTAS - {team_name.upper()}")
        print(f"{'='*80}")
        
        # Obtener resumen básico
        basic_summary = processor.get_team_statistics_summary(team_name)
        
        if 'error' in basic_summary:
            print(f"❌ {basic_summary['error']}")
            return
        
        # Obtener resumen detallado completo
        detailed_summary = processor.create_team_summary(team_name)
        
        # ==================== SECCIÓN 1: FORTALEZAS PRINCIPALES ====================
        print(f"\n🏆 FORTALEZAS PRINCIPALES (para apuestas de victoria):")
        print(f"   ┌─ Nivel del Equipo: {basic_summary['tier']} ({'Elite' if basic_summary['tier'] == 'Elite' else 'No Elite'})")
        print(f"   ├─ Fuerza General: {basic_summary['overall_strength']:.3f}/1.000 ({basic_summary['overall_strength']*100:.1f}%)")
        print(f"   ├─ Fuerza Ofensiva: {detailed_summary['attacking_strength']:.3f}/1.000 ({detailed_summary['attacking_strength']*100:.1f}%)")
        print(f"   ├─ Fuerza Defensiva: {detailed_summary['defensive_strength']:.3f}/1.000 ({detailed_summary['defensive_strength']*100:.1f}%)")
        print(f"   └─ Estilo de Juego: {detailed_summary.get('team_style', 'unknown').title()}")
        
        # ==================== SECCIÓN 2: MÉTRICAS DE GOLES (Over/Under) ====================
        print(f"\n⚽ MÉTRICAS DE GOLES (para apuestas Over/Under):")
        goals_per_match = detailed_summary['goals_per_match']
        goals_conceded = detailed_summary['goals_conceded_per_match']
        total_goals_per_match = goals_per_match + goals_conceded
        goal_diff = detailed_summary.get('goal_difference_per_match', 0)
        
        print(f"   ┌─ Goles a favor por partido: {goals_per_match:.2f}")
        print(f"   ├─ Goles en contra por partido: {goals_conceded:.2f}")
        print(f"   ├─ TOTAL goles por partido: {total_goals_per_match:.2f} (clave para Over/Under)")
        print(f"   ├─ Diferencia de goles: {goal_diff:+.2f} por partido")
        print(f"   └─ Tendencia Over/Under 2.5: {'OVER' if total_goals_per_match > 2.5 else 'UNDER'} (histórico)")
        
        # ==================== SECCIÓN 3: ANÁLISIS OFENSIVO DETALLADO ====================
        print(f"\n🎯 ANÁLISIS OFENSIVO DETALLADO:")
        print(f"   ┌─ Goles totales en torneo: {detailed_summary.get('total_goals', 0)}")
        print(f"   ├─ Penales convertidos: {detailed_summary.get('penalties_scored', 0)}")
        print(f"   ├─ Goles dentro del área: {detailed_summary.get('goals_inside_area', 0)}")
        print(f"   ├─ Goles fuera del área: {detailed_summary.get('goals_outside_area', 0)}")
        print(f"   ├─ Goles de cabeza: {detailed_summary.get('header_goals', 0)}")
        print(f"   ├─ Goles pie derecho: {detailed_summary.get('right_foot_goals', 0)}")
        print(f"   ├─ Goles pie izquierdo: {detailed_summary.get('left_foot_goals', 0)}")
        
        # Eficiencia de finalización
        finishing_eff = detailed_summary.get('finishing_efficiency', 0)
        print(f"   └─ Eficiencia de finalización: {finishing_eff:.3f} ({finishing_eff*100:.1f}% de intentos convertidos)")
        
        # ==================== SECCIÓN 4: ANÁLISIS DEFENSIVO DETALLADO ====================
        print(f"\n🛡️ ANÁLISIS DEFENSIVO DETALLADO:")
        cleansheets = detailed_summary.get('cleansheets', 0)
        cleansheet_rate = detailed_summary.get('cleansheet_rate', 0)
        saves_made = detailed_summary.get('saves_made', 0)
        penalties_saved = detailed_summary.get('penalties_saved', 0)
        
        print(f"   ┌─ Porterías en cero: {cleansheets}")
        print(f"   ├─ Tasa de portería en cero: {cleansheet_rate:.2%} (importante para Under/Draw)")
        print(f"   ├─ Paradas del portero: {saves_made}")
        print(f"   ├─ Penales detenidos: {penalties_saved}")
        print(f"   └─ Fortaleza defensiva: {'Alta' if detailed_summary['defensive_strength'] > 0.7 else 'Media' if detailed_summary['defensive_strength'] > 0.5 else 'Baja'}")
        
        # ==================== SECCIÓN 5: DISCIPLINA Y FAIR PLAY ====================
        print(f"\n🟨 DISCIPLINA Y FAIR PLAY:")
        yellow_cards = detailed_summary.get('yellow_cards', 0)
        red_cards = detailed_summary.get('red_cards', 0)
        yellow_per_match = detailed_summary.get('yellow_cards_per_match', 0)
        red_per_match = detailed_summary.get('red_cards_per_match', 0)
        discipline_rating = detailed_summary.get('discipline_rating', 0.5)
        
        print(f"   ┌─ Tarjetas amarillas totales: {yellow_cards}")
        print(f"   ├─ Tarjetas rojas totales: {red_cards}")
        print(f"   ├─ Amarillas por partido: {yellow_per_match:.2f}")
        print(f"   ├─ Rojas por partido: {red_per_match:.2f}")
        print(f"   ├─ Rating disciplina: {discipline_rating:.3f}/1.000 ({discipline_rating*100:.1f}%)")
        print(f"   └─ Comportamiento: {'Limpio' if discipline_rating > 0.8 else 'Normal' if discipline_rating > 0.6 else 'Agresivo'}")
        
        # ==================== SECCIÓN 6: DISTRIBUCIÓN Y PASES ====================
        if 'pass_accuracy' in detailed_summary:
            print(f"\n⚽ CONTROL Y DISTRIBUCIÓN:")
            pass_accuracy = detailed_summary['pass_accuracy']
            passes_attempted = detailed_summary.get('passes_attempted', 0)
            passes_completed = detailed_summary.get('passes_completed', 0)
            
            print(f"   ┌─ Precisión de pases: {pass_accuracy:.2%}")
            print(f"   ├─ Pases intentados: {passes_attempted:,}")
            print(f"   ├─ Pases completados: {passes_completed:,}")
            print(f"   └─ Control del juego: {'Alto' if pass_accuracy > 0.85 else 'Medio' if pass_accuracy > 0.75 else 'Bajo'}")
        
        # ==================== SECCIÓN 7: PREDICCIONES PARA APUESTAS ====================
        print(f"\n🎰 PREDICCIONES PARA TIPOS DE APUESTA:")
        
        # Home Win prediction factors
        home_win_factors = []
        if detailed_summary['overall_strength'] > 0.65:
            home_win_factors.append("✓ Fuerza general alta")
        if detailed_summary['attacking_strength'] > 0.6:
            home_win_factors.append("✓ Ataque potente")
        if goals_per_match > 2.0:
            home_win_factors.append("✓ Buenos números goleadores")
        
        print(f"   🏠 Victoria Local (con ventaja de casa):")
        print(f"      Factores a favor: {len(home_win_factors)}/3")
        for factor in home_win_factors[:3]:
            print(f"      {factor}")
        
        # Away Win prediction factors  
        away_win_factors = []
        if detailed_summary['overall_strength'] > 0.7:
            away_win_factors.append("✓ Equipo de elite")
        if detailed_summary['defensive_strength'] > 0.6:
            away_win_factors.append("✓ Defensa sólida")
        if discipline_rating > 0.7:
            away_win_factors.append("✓ Equipo disciplinado")
            
        print(f"   ✈️ Victoria Visitante (sin ventaja):")
        print(f"      Factores a favor: {len(away_win_factors)}/3")
        for factor in away_win_factors[:3]:
            print(f"      {factor}")
        
        # Draw prediction factors
        draw_factors = []
        if abs(goal_diff) < 0.3:
            draw_factors.append("✓ Balance goleador equilibrado")
        if detailed_summary['defensive_strength'] > 0.6:
            draw_factors.append("✓ Defensa sólida (pocos goles)")
        if cleansheet_rate > 0.3:
            draw_factors.append("✓ Buen porcentaje porterías en cero")
        
        print(f"   ⚖️ Empate:")
        print(f"      Factores a favor: {len(draw_factors)}/3")
        for factor in draw_factors[:3]:
            print(f"      {factor}")
        
        # Over/Under predictions
        over_factors = []
        under_factors = []
        
        if total_goals_per_match > 2.5:
            over_factors.append(f"✓ Promedio histórico: {total_goals_per_match:.2f} goles")
        if detailed_summary['attacking_strength'] > 0.6:
            over_factors.append("✓ Ataque efectivo")
        if goals_conceded > 1.2:
            over_factors.append("✓ Defensa permeable")
            
        if total_goals_per_match < 2.5:
            under_factors.append(f"✓ Promedio histórico: {total_goals_per_match:.2f} goles")
        if detailed_summary['defensive_strength'] > 0.7:
            under_factors.append("✓ Defensa muy sólida")
        if cleansheet_rate > 0.4:
            under_factors.append("✓ Muchas porterías en cero")
        
        print(f"   📈 Over 2.5 goles:")
        print(f"      Factores a favor: {len(over_factors)}/3")
        for factor in over_factors[:3]:
            print(f"      {factor}")
            
        print(f"   📉 Under 2.5 goles:")
        print(f"      Factores a favor: {len(under_factors)}/3")
        for factor in under_factors[:3]:
            print(f"      {factor}")
        
        # ==================== SECCIÓN 8: RESUMEN EJECUTIVO ====================
        print(f"\n💡 RESUMEN EJECUTIVO PARA APUESTAS:")
        
        # Determinar fortaleza principal
        if detailed_summary['attacking_strength'] > detailed_summary['defensive_strength'] + 0.1:
            main_strength = "⚔️ Equipo OFENSIVO - Busca victoria por goles"
        elif detailed_summary['defensive_strength'] > detailed_summary['attacking_strength'] + 0.1:
            main_strength = "🛡️ Equipo DEFENSIVO - Juega al resultado mínimo"
        else:
            main_strength = "⚖️ Equipo EQUILIBRADO - Adaptable según rival"
        
        print(f"   {main_strength}")
        
        # Recomendación principal
        if detailed_summary['overall_strength'] > 0.7:
            recommendation = "🌟 EQUIPO ELITE - Favorito en la mayoría de partidos"
        elif detailed_summary['overall_strength'] > 0.55:
            recommendation = "💪 EQUIPO FUERTE - Competitivo contra la mayoría"
        elif detailed_summary['overall_strength'] > 0.45:
            recommendation = "📊 EQUIPO PROMEDIO - Depende mucho del rival"
        else:
            recommendation = "⚠️ EQUIPO DÉBIL - Pocas probabilidades contra rivales fuertes"
        
        print(f"   {recommendation}")
        
        # Over/Under tendency
        if total_goals_per_match > 3.0:
            over_under_rec = "🔥 ALTA tendencia a Over - Partidos con muchos goles"
        elif total_goals_per_match > 2.5:
            over_under_rec = "📈 LEVE tendencia a Over - Considera Over 2.5"
        elif total_goals_per_match < 2.0:
            over_under_rec = "🔒 FUERTE tendencia a Under - Partidos cerrados"
        else:
            over_under_rec = "📊 NEUTRAL en Over/Under - Analizar rival específico"
        
        print(f"   {over_under_rec}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"❌ Error al obtener resumen del equipo: {str(e)}")
        import traceback
        traceback.print_exc()



def seleccionar_equipo_simple(teams):
    """Selección simple de equipo por número o nombre."""
    for i, team in enumerate(teams, 1):
        print(f"  {i:2d}. {team}")
    
    while True:
        user_input = input("👉 Selecciona equipo (número o nombre): ").strip()
        
        if user_input.isdigit():
            team_index = int(user_input) - 1
            if 0 <= team_index < len(teams):
                return teams[team_index]
            else:
                print(f"❌ Número inválido. Debe ser entre 1 y {len(teams)}")
        else:
            matching_teams = [team for team in teams if user_input.lower() in team.lower()]
            if len(matching_teams) == 1:
                return matching_teams[0]
            elif len(matching_teams) > 1:
                print(f"⚠️ Múltiples coincidencias: {', '.join(matching_teams)}")
                print("Sé más específico.")
            else:
                print(f"❌ Equipo '{user_input}' no encontrado.")


def generar_estadisticas_todos_equipos(processor):
    """Genera estadísticas completas de todos los equipos y las guarda en un archivo."""
    try:
        print("\n🔄 Generando estadísticas completas de todos los equipos...")
        
        # Obtener lista de todos los equipos
        teams = processor.get_teams_list()
        
        if not teams:
            print("❌ No se encontraron equipos para procesar.")
            return
        
        print(f"📊 Procesando {len(teams)} equipos...")
        
        # Crear nombre del archivo con timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"estadisticas_completas_equipos_{timestamp}.txt"
        
        # Crear la ruta completa del archivo (en el directorio del proyecto)
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Escribir encabezado del archivo
            f.write("=" * 100 + "\n")
            f.write("    SISTEMA EXPERTO DE APUESTAS DEPORTIVAS - UEFA CHAMPIONS LEAGUE 2021/22\n")
            f.write("    ESTADÍSTICAS COMPLETAS DE TODOS LOS EQUIPOS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generado el: {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n")
            f.write(f"Total de equipos analizados: {len(teams)}\n")
            f.write("=" * 100 + "\n\n")
            
            # Procesar cada equipo
            for i, team_name in enumerate(teams, 1):
                try:
                    print(f"⏳ Procesando {i}/{len(teams)}: {team_name}")
                    
                    # Escribir estadísticas del equipo en el archivo
                    escribir_estadisticas_equipo_archivo(f, processor, team_name, i)
                    
                except Exception as e:
                    error_msg = f"❌ Error procesando {team_name}: {str(e)}"
                    print(error_msg)
                    f.write(f"\n{error_msg}\n")
                    f.write("-" * 80 + "\n\n")
            
            # Escribir resumen final
            f.write("\n" + "=" * 100 + "\n")
            f.write("                            RESUMEN FINAL\n")
            f.write("=" * 100 + "\n")
            f.write(f"✅ Análisis completado exitosamente\n")
            f.write(f"📊 {len(teams)} equipos procesados\n")
            f.write(f"📁 Archivo generado: {filename}\n")
            f.write("🏆 Sistema Experto de Apuestas Deportivas v0.2\n")
            f.write("=" * 100 + "\n")
        
        print(f"\n✅ ¡Estadísticas generadas exitosamente!")
        print(f"📁 Archivo guardado como: {filename}")
        print(f"📍 Ubicación completa: {output_path}")
        print(f"📊 Total equipos procesados: {len(teams)}")
        
        # Ofrecer abrir el archivo
        respuesta = input("\n¿Quieres abrir el archivo ahora? (s/n): ").strip().lower()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            try:
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(output_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', output_path])
                else:  # Linux
                    subprocess.call(['xdg-open', output_path])
                    
                print("📖 Archivo abierto en el editor predeterminado.")
            except Exception as e:
                print(f"⚠️ No se pudo abrir automáticamente: {str(e)}")
                print(f"Puedes abrir manualmente el archivo: {output_path}")
        
    except Exception as e:
        print(f"❌ Error general generando estadísticas: {str(e)}")
        import traceback
        traceback.print_exc()


def escribir_estadisticas_equipo_archivo(file_handle, processor, team_name, team_number):
    """Escribe las estadísticas completas de un equipo en el archivo."""
    try:
        # Obtener datos del equipo
        basic_summary = processor.get_team_statistics_summary(team_name)
        
        if 'error' in basic_summary:
            file_handle.write(f"❌ Error obteniendo datos de {team_name}: {basic_summary['error']}\n")
            file_handle.write("-" * 80 + "\n\n")
            return
        
        detailed_summary = processor.create_team_summary(team_name)
        
        # Escribir encabezado del equipo
        file_handle.write(f"{'=' * 100}\n")
        file_handle.write(f"    EQUIPO #{team_number:02d}: {team_name.upper()}\n")
        file_handle.write(f"{'=' * 100}\n\n")
        
        # ==================== RESUMEN EJECUTIVO ====================
        file_handle.write("🏆 RESUMEN EJECUTIVO:\n")
        file_handle.write(f"   ┌─ Nivel del Equipo: {basic_summary['tier']} ({'Elite' if basic_summary['tier'] == 'Elite' else 'No Elite'})\n")
        file_handle.write(f"   ├─ Fuerza General: {basic_summary['overall_strength']:.3f}/1.000 ({basic_summary['overall_strength']*100:.1f}%)\n")
        file_handle.write(f"   ├─ Fuerza Ofensiva: {detailed_summary['attacking_strength']:.3f}/1.000 ({detailed_summary['attacking_strength']*100:.1f}%)\n")
        file_handle.write(f"   ├─ Fuerza Defensiva: {detailed_summary['defensive_strength']:.3f}/1.000 ({detailed_summary['defensive_strength']*100:.1f}%)\n")
        file_handle.write(f"   └─ Estilo de Juego: {detailed_summary.get('team_style', 'unknown').title()}\n\n")
        
        # ==================== MÉTRICAS DE GOLES ====================
        goals_per_match = detailed_summary['goals_per_match']
        goals_conceded = detailed_summary['goals_conceded_per_match']
        total_goals_per_match = goals_per_match + goals_conceded
        goal_diff = detailed_summary.get('goal_difference_per_match', 0)
        
        file_handle.write("⚽ MÉTRICAS DE GOLES (Over/Under):\n")
        file_handle.write(f"   ┌─ Goles a favor por partido: {goals_per_match:.2f}\n")
        file_handle.write(f"   ├─ Goles en contra por partido: {goals_conceded:.2f}\n")
        file_handle.write(f"   ├─ TOTAL goles por partido: {total_goals_per_match:.2f}\n")
        file_handle.write(f"   ├─ Diferencia de goles: {goal_diff:+.2f} por partido\n")
        file_handle.write(f"   └─ Tendencia Over/Under 2.5: {'OVER' if total_goals_per_match > 2.5 else 'UNDER'}\n\n")
        
        # ==================== ANÁLISIS OFENSIVO ====================
        file_handle.write("🎯 ANÁLISIS OFENSIVO:\n")
        file_handle.write(f"   ┌─ Goles totales: {detailed_summary.get('total_goals', 0)}\n")
        file_handle.write(f"   ├─ Penales convertidos: {detailed_summary.get('penalties_scored', 0)}\n")
        file_handle.write(f"   ├─ Goles dentro del área: {detailed_summary.get('goals_inside_area', 0)}\n")
        file_handle.write(f"   ├─ Goles fuera del área: {detailed_summary.get('goals_outside_area', 0)}\n")
        file_handle.write(f"   ├─ Goles de cabeza: {detailed_summary.get('header_goals', 0)}\n")
        
        finishing_eff = detailed_summary.get('finishing_efficiency', 0)
        file_handle.write(f"   └─ Eficiencia de finalización: {finishing_eff:.3f} ({finishing_eff*100:.1f}%)\n\n")
        
        # ==================== ANÁLISIS DEFENSIVO ====================
        cleansheets = detailed_summary.get('cleansheets', 0)
        cleansheet_rate = detailed_summary.get('cleansheet_rate', 0)
        saves_made = detailed_summary.get('saves_made', 0)
        
        file_handle.write("🛡️ ANÁLISIS DEFENSIVO:\n")
        file_handle.write(f"   ┌─ Porterías en cero: {cleansheets}\n")
        file_handle.write(f"   ├─ Tasa de portería en cero: {cleansheet_rate:.2%}\n")
        file_handle.write(f"   ├─ Paradas del portero: {saves_made}\n")
        file_handle.write(f"   └─ Fortaleza defensiva: {'Alta' if detailed_summary['defensive_strength'] > 0.7 else 'Media' if detailed_summary['defensive_strength'] > 0.5 else 'Baja'}\n\n")
        
        # ==================== DISCIPLINA ====================
        yellow_cards = detailed_summary.get('yellow_cards', 0)
        red_cards = detailed_summary.get('red_cards', 0)
        discipline_rating = detailed_summary.get('discipline_rating', 0.5)
        
        file_handle.write("🟨 DISCIPLINA:\n")
        file_handle.write(f"   ┌─ Tarjetas amarillas: {yellow_cards}\n")
        file_handle.write(f"   ├─ Tarjetas rojas: {red_cards}\n")
        file_handle.write(f"   ├─ Rating disciplina: {discipline_rating:.3f}/1.000 ({discipline_rating*100:.1f}%)\n")
        file_handle.write(f"   └─ Comportamiento: {'Limpio' if discipline_rating > 0.8 else 'Normal' if discipline_rating > 0.6 else 'Agresivo'}\n\n")
        
        # ==================== PREDICCIONES PARA APUESTAS ====================
        file_handle.write("🎰 RECOMENDACIONES DE APUESTA:\n")
        
        # Recomendación principal basada en fuerza general
        if detailed_summary['overall_strength'] > 0.7:
            recommendation = "🌟 EQUIPO ELITE - Favorito en la mayoría de partidos"
        elif detailed_summary['overall_strength'] > 0.55:
            recommendation = "💪 EQUIPO FUERTE - Competitivo contra la mayoría"
        elif detailed_summary['overall_strength'] > 0.45:
            recommendation = "📊 EQUIPO PROMEDIO - Depende mucho del rival"
        else:
            recommendation = "⚠️ EQUIPO DÉBIL - Pocas probabilidades contra rivales fuertes"
        
        file_handle.write(f"   ┌─ Evaluación General: {recommendation}\n")
        
        # Over/Under recomendation
        if total_goals_per_match > 3.0:
            over_under_rec = "🔥 ALTA tendencia a Over - Partidos con muchos goles"
        elif total_goals_per_match > 2.5:
            over_under_rec = "📈 LEVE tendencia a Over - Considera Over 2.5"
        elif total_goals_per_match < 2.0:
            over_under_rec = "🔒 FUERTE tendencia a Under - Partidos cerrados"
        else:
            over_under_rec = "📊 NEUTRAL en Over/Under - Analizar rival específico"
        
        file_handle.write(f"   ├─ Over/Under 2.5: {over_under_rec}\n")
        
        # Estilo de juego para predicciones
        if detailed_summary['attacking_strength'] > detailed_summary['defensive_strength'] + 0.1:
            style_rec = "⚔️ Equipo OFENSIVO - Busca victoria por goles"
        elif detailed_summary['defensive_strength'] > detailed_summary['attacking_strength'] + 0.1:
            style_rec = "🛡️ Equipo DEFENSIVO - Juega al resultado mínimo"
        else:
            style_rec = "⚖️ Equipo EQUILIBRADO - Adaptable según rival"
        
        file_handle.write(f"   └─ Estilo de Juego: {style_rec}\n")
        
        # Separador entre equipos
        file_handle.write("\n" + "-" * 80 + "\n\n")
        
    except Exception as e:
        file_handle.write(f"❌ Error procesando estadísticas de {team_name}: {str(e)}\n")
        file_handle.write("-" * 80 + "\n\n")


def main():
    """
    Función principal que inicia la aplicación.
    """
    print("=" * 70)
    print("   Sistema Experto de Consejos de Apuestas Deportivas - Versión 0.2")
    print("=" * 70)
    print("\nInicializando sistema...")
    
    # Inicializar el procesador de datos
    try:
        processor = UCLDataProcessor()
        print("✅ Procesador de datos inicializado")
        
        # Cargar y procesar datos
        print("📥 Cargando datos de la UEFA Champions League 2021/22...")
        processor.load_data()
        processor.aggregate_team_data()
        print("✅ Datos cargados y procesados correctamente")
        
        # Menú interactivo
        while True:
            mostrar_menu()
            
            try:
                opcion = input("\n👉 Selecciona una opción (0-2): ").strip()
                
                if opcion == '0':
                    print("\n👋 ¡Gracias por usar el Sistema Experto de Apuestas!")
                    print("🏆 ¡Que tengas buena suerte con tus apuestas responsables!")
                    break
                elif opcion == '1':
                    generar_estadisticas_todos_equipos(processor)
                elif opcion == '2':
                    consultar_equipo(processor)
                else:
                    print("❌ Opción inválida. Por favor selecciona un número del 0 al 2.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Saliendo del sistema...")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {str(e)}")
                print("Intenta nuevamente.")
                
    except Exception as e:
        print(f"❌ Error al inicializar el sistema: {str(e)}")
        print("Verifica que los archivos de datos estén en la carpeta 'data/raw'")


if __name__ == "__main__":
    main()