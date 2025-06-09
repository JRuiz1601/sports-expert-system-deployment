#!/usr/bin/env python3
"""
DIAGNÓSTICO ESPECÍFICO: Real Madrid vs Barcelona
Investigar por qué no se generan recomendaciones para este enfrentamiento
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_processor import UCLDataProcessor
from knowledge_model import TeamFact, MatchupFact, BetType, FactBuilder
from rules_engine import BettingExpertSystem

def debug_real_madrid_vs_barcelona():
    """Debug específico Real Madrid vs Barcelona"""
    
    print("🔍 DIAGNÓSTICO: Real Madrid vs Barcelona")
    print("=" * 60)
      # 1. Cargar datos reales
    processor = UCLDataProcessor()
    processor.load_data()
    
    home_team = "Real Madrid"
    away_team = "Barcelona"
      # 2. Obtener stats reales
    home_stats = processor.create_team_summary(home_team)
    away_stats = processor.create_team_summary(away_team)
    
    print(f"\n📊 STATS REALES:")
    print(f"🏠 {home_team}:")
    for key, value in home_stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n✈️ {away_team}:")
    for key, value in away_stats.items():
        print(f"   {key}: {value}")
      # 3. Crear facts reales
    home_fact = FactBuilder.create_team_fact(home_stats)
    away_fact = FactBuilder.create_team_fact(away_stats)
    matchup_fact = FactBuilder.create_matchup_fact(home_team, away_team, home_fact, away_fact)
    
    print(f"\n⚖️ MATCHUP FACT GENERADO:")
    for key, value in matchup_fact.items():
        print(f"   {key}: {value}")
    
    # 4. Analizar condiciones de reglas específicas
    print(f"\n🔍 ANÁLISIS DE CONDICIONES DE REGLAS:")
    
    # Regla: clear_favorite_home_win
    clear_favorite = matchup_fact['clear_favorite']
    home_team_name = matchup_fact['home_team']
    margin = matchup_fact['overall_margin']
    
    print(f"\n🎯 REGLA: clear_favorite_home_win")
    print(f"   clear_favorite: '{clear_favorite}'")
    print(f"   home_team: '{home_team_name}'")
    print(f"   margin: {margin:.3f}")
    print(f"   TEST condition: {clear_favorite and clear_favorite == home_team_name}")
    
    # Regla: strong_home_attack_vs_weak_away_defense
    h_attack = home_fact['attacking_strength']
    a_defense = away_fact['defensive_strength']
    h_goals = home_fact['goals_per_match']
    a_conceded = away_fact['goals_conceded_per_match']
    att_adv = matchup_fact['attacking_advantage']
    
    print(f"\n🎯 REGLA: strong_home_attack_vs_weak_away_defense")
    print(f"   h_attack > 0.59: {h_attack:.3f} > 0.59 = {h_attack > 0.59}")
    print(f"   a_defense < 0.32: {a_defense:.3f} < 0.32 = {a_defense < 0.32}")
    print(f"   h_goals > 1.67: {h_goals:.3f} > 1.67 = {h_goals > 1.67}")
    print(f"   a_conceded > 1.3: {a_conceded:.3f} > 1.3 = {a_conceded > 1.3}")
    print(f"   att_adv == home_team: '{att_adv}' == '{home_team_name}' = {att_adv == home_team_name}")
    
    all_conditions = (h_attack > 0.59 and a_defense < 0.32 and h_goals > 1.67 and 
                     a_conceded > 1.3 and att_adv == home_team_name)
    print(f"   TODAS las condiciones: {all_conditions}")
    
    # Regla: offensive_home_vs_defensive_away
    h_style = home_fact['team_style']
    a_style = away_fact['team_style']
    h_strength = home_fact['overall_strength']
    a_strength = away_fact['overall_strength']
    
    print(f"\n🎯 REGLA: offensive_home_vs_defensive_away")
    print(f"   h_style == 'offensive': '{h_style}' == 'offensive' = {h_style == 'offensive'}")
    print(f"   a_style == 'defensive': '{a_style}' == 'defensive' = {a_style == 'defensive'}")
    print(f"   h_strength > a_strength + 0.1: {h_strength:.3f} > {a_strength:.3f} + 0.1 = {h_strength > a_strength + 0.1}")
    
    # 5. Ejecutar sistema experto
    print(f"\n🧠 EJECUTANDO SISTEMA EXPERTO:")
    expert_system = BettingExpertSystem()
    
    # Declarar facts
    expert_system.declare(home_fact)
    expert_system.declare(away_fact)
    expert_system.declare(matchup_fact)
    
    # Crear BetTypes
    bet_types = ['home_win', 'away_win', 'draw', 'over', 'under']
    for bet_type in bet_types:
        if bet_type in ['over', 'under']:
            bet = BetType.create(bet_type, home_team, away_team, threshold=2.5)
        else:
            bet = BetType.create(bet_type, home_team, away_team)
        expert_system.declare(bet)
    
    # Ejecutar
    expert_system.run()
    
    # Obtener resultados
    recommendations = expert_system.get_recommendations()
    rules_fired = expert_system.get_rules_fired_summary()
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Recomendaciones generadas: {len(recommendations)}")
    print(f"   Reglas activadas: {len(rules_fired)}")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n   ✅ RECOMENDACIÓN #{i}:")
            print(f"      Tipo: {rec.get('bet_type', 'N/A')}")
            print(f"      Recomendación: {rec.get('recommendation', 'N/A')}")
            print(f"      Confianza: {rec.get('confidence', 'N/A')}")
            if 'explanation' in rec:
                print(f"      Explicación: {rec['explanation'][:80]}...")
    else:
        print("   ❌ No se generaron recomendaciones")
        
    if rules_fired:
        for rule, count in rules_fired.items():
            print(f"   🔥 {rule}: {count} veces")
    else:
        print("   ❌ No se activaron reglas")
        
    # 6. Comparar con umbrales de las reglas
    print(f"\n📏 COMPARACIÓN CON UMBRALES DE REGLAS:")
    print(f"   Barcelona defensa: {a_defense:.3f} (necesita < 0.32 para regla fuerte)")
    print(f"   Barcelona concede: {a_conceded:.3f} goles/partido (necesita > 1.3)")
    print(f"   Barcelona estilo: '{a_style}' (necesita 'defensive' para regla de estilos)")
    
    return recommendations, rules_fired

if __name__ == "__main__":
    try:
        debug_real_madrid_vs_barcelona()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
