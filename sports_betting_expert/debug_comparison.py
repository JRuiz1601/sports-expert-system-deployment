#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPARATIVO: Motor de Reglas vs Red Bayesiana
Comparar las recomendaciones generadas por ambos enfoques para el mismo enfrentamiento
"""
import sys
import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_processor import UCLDataProcessor
from knowledge_model import TeamFact, MatchupFact, BetType, FactBuilder
from rules_engine import BettingExpertSystem
from bayesian_model import BettingBayesianNetwork

# ========================================================================
# FORMATO UNIFICADO PARA COMPARACIÓN
# ========================================================================

class RecommendationDecision(Enum):
    """Decisiones unificadas para recomendaciones"""
    RECOMMENDED = "RECOMMENDED"
    NOT_RECOMMENDED = "NOT RECOMMENDED"
    NOT_EVALUATED = "NO EVALUADO"

class ConfidenceLevel(Enum):
    """Niveles de confianza unificados"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNAVAILABLE = "N/A"

@dataclass
class UnifiedPrediction:
    """Formato unificado para predicciones de apuestas"""
    bet_type: str
    decision: RecommendationDecision
    confidence: ConfidenceLevel
    probability: float
    explanation: str
    source: str
    raw_data: Dict[str, Any]
    
    def __str__(self) -> str:
        """Representación legible del objeto"""
        decision_symbol = "✅" if self.decision == RecommendationDecision.RECOMMENDED else "❌"
        if self.decision == RecommendationDecision.NOT_EVALUATED:
            decision_symbol = "⚪"
            
        return (f"{decision_symbol} {self.bet_type.upper()}: "
                f"{self.decision.value} ({self.confidence.value}, {self.probability:.1%})")

class UnifiedFormatter:
    """Conversor a formato unificado"""
    
    @staticmethod
    def from_rules_engine(bet_type: str, data: Dict[str, Any]) -> UnifiedPrediction:
        """Convertir resultado del motor de reglas a formato unificado"""
        if not data:
            return UnifiedPrediction(
                bet_type=bet_type,
                decision=RecommendationDecision.NOT_EVALUATED,
                confidence=ConfidenceLevel.UNAVAILABLE,
                probability=0.0,
                explanation="No evaluado por el motor de reglas (ninguna regla activada)",
                source="rules_engine",
                raw_data={}
            )
        
        # Convertir decisión
        rec_text = data.get('recommendation', '').lower()
        if rec_text == 'recommended':
            decision = RecommendationDecision.RECOMMENDED
        else:
            decision = RecommendationDecision.NOT_RECOMMENDED
        
        # Convertir confianza
        conf_text = data.get('confidence', '').lower()
        if conf_text == 'high':
            confidence = ConfidenceLevel.HIGH
        elif conf_text == 'medium':
            confidence = ConfidenceLevel.MEDIUM
        elif conf_text == 'low':
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.UNAVAILABLE
        
        # Generar explicación
        explanation = data.get('explanation', 'Sin explicación disponible')
        rules_fired = ", ".join(data.get('rules_fired', []))
        if rules_fired:
            explanation += f" [Reglas activadas: {rules_fired}]"
            
        return UnifiedPrediction(
            bet_type=bet_type,
            decision=decision,
            confidence=confidence,
            probability=data.get('probability', 0.5),
            explanation=explanation,
            source="rules_engine",
            raw_data=data
        )
    
    @staticmethod
    def from_bayesian_network(bet_type: str, data: Dict[str, Any]) -> UnifiedPrediction:
        """Convertir resultado de la red bayesiana a formato unificado"""
        if not data:
            return UnifiedPrediction(
                bet_type=bet_type,
                decision=RecommendationDecision.NOT_EVALUATED,
                confidence=ConfidenceLevel.UNAVAILABLE,
                probability=0.0,
                explanation="No evaluado por la red bayesiana",
                source="bayesian_network",
                raw_data={}
            )
        
        # Extraer probabilidad y confianza
        prob_recommended = data.get('recommended', 0.0)
        prob_not_recommended = data.get('not_recommended', 0.0)
        
        # Convertir decisión
        decision = RecommendationDecision.RECOMMENDED if prob_recommended > 0.5 else RecommendationDecision.NOT_RECOMMENDED
        
        # Convertir confianza
        conf_text = data.get('confidence', '').lower()
        if conf_text == 'high':
            confidence = ConfidenceLevel.HIGH
        elif conf_text == 'medium':
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Generar explicación
        explanation = (f"Probabilidad bayesiana: {prob_recommended:.1%} recomendado, "
                      f"{prob_not_recommended:.1%} no recomendado")
            
        return UnifiedPrediction(
            bet_type=bet_type,
            decision=decision,
            confidence=confidence,
            probability=prob_recommended,
            explanation=explanation,
            source="bayesian_network",
            raw_data=data
        )

def compare_approaches(home_team: str, away_team: str):
    """Comparar motor de reglas vs red bayesiana para un enfrentamiento."""
    
    print(f"🔍 DIAGNÓSTICO COMPARATIVO: {home_team} vs {away_team}")
    print("=" * 80)
    
    # 1. Cargar datos reales
    print("📊 Cargando datos...")
    processor = UCLDataProcessor()
    processor.load_data()
    
    # 2. Obtener estadísticas
    home_stats = processor.create_team_summary(home_team)
    away_stats = processor.create_team_summary(away_team)
    
    print(f"\n📈 ESTADÍSTICAS DE ENTRADA:")
    print(f"🏠 {home_team}:")
    for key, value in home_stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    print(f"\n✈️ {away_team}:")
    for key, value in away_stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    # 3. Crear facts
    home_fact = FactBuilder.create_team_fact(home_stats)
    away_fact = FactBuilder.create_team_fact(away_stats)
    matchup_fact = FactBuilder.create_matchup_fact(home_team, away_team, home_fact, away_fact)
    
    # ========================================================================
    # ENFOQUE 1: MOTOR DE REGLAS
    # ========================================================================
    print(f"\n🧠 ENFOQUE 1: MOTOR DE REGLAS")
    print("-" * 50)
    
    expert_system = BettingExpertSystem()
    
    # Declarar facts
    expert_system.declare(home_fact)
    expert_system.declare(away_fact)
    expert_system.declare(matchup_fact)
    
    # Crear y declarar tipos de apuesta
    bet_types = ['home_win', 'away_win', 'draw', 'over', 'under']
    for bet_type in bet_types:
        if bet_type in ['over', 'under']:
            bet = BetType.create(bet_type, home_team, away_team, threshold=2.5)
        else:
            bet = BetType.create(bet_type, home_team, away_team)
        expert_system.declare(bet)
    
    # Ejecutar motor de reglas
    expert_system.run()
    
    # Obtener resultados del motor de reglas
    rules_recommendations = expert_system.get_recommendations()
    rules_fired = expert_system.get_rules_fired_summary()
    
    print(f"📊 Resultados del Motor de Reglas:")
    print(f"   Recomendaciones generadas: {len(rules_recommendations)}")
    print(f"   Reglas activadas: {len(rules_fired)}")
    
    # Guardar resultados en formato original
    rules_results = {}
    if rules_recommendations:
        for rec in rules_recommendations:
            bet_type = rec.get('bet_type', 'unknown')
            rules_results[bet_type] = {
                'recommendation': rec.get('recommendation', 'unknown'),
                'confidence': rec.get('confidence', 'unknown'),
                'probability': rec.get('probability', 0.5),
                'explanation': rec.get('explanation', 'Sin explicación'),
                'rules_fired': rec.get('rules_fired', [])
            }
            
            print(f"\n   🎯 {bet_type.upper()}:")
            print(f"      ├─ Recomendación: {rec.get('recommendation', 'N/A')}")
            print(f"      ├─ Confianza: {rec.get('confidence', 'N/A')}")
            print(f"      ├─ Probabilidad: {rec.get('probability', 0.5):.2%}")
            print(f"      └─ Reglas: {', '.join(rec.get('rules_fired', []))}")
    else:
        print("   ❌ No se generaron recomendaciones")
    
    # ========================================================================
    # ENFOQUE 2: RED BAYESIANA
    # ========================================================================
    print(f"\n🕸️ ENFOQUE 2: RED BAYESIANA")
    print("-" * 50)
    
    try:
        bayesian_network = BettingBayesianNetwork()
        
        # Preparar evidencia para la red bayesiana
        evidence = {
            'home_strength': home_fact['overall_strength'],
            'away_strength': away_fact['overall_strength'],
            'home_style': home_fact['team_style'],
            'away_style': away_fact['team_style'],
            'home_goals_tendency': home_fact['goals_per_match'],
            'away_goals_tendency': away_fact['goals_per_match']
        }
        
        print(f"🔍 Evidencia para la red bayesiana:")
        for key, value in evidence.items():
            print(f"   {key}: {value}")
        
        # Realizar predicción bayesiana
        bayesian_recommendations = bayesian_network.predict(evidence)
        
        print(f"\n📊 Resultados de la Red Bayesiana:")
        
        # Guardar resultados en formato original
        bayesian_results = {}
        for bet_type, probs in bayesian_recommendations.items():
            bayesian_results[bet_type] = probs
            prob_recommended = probs['recommended']
            confidence = probs['confidence']
            
            print(f"\n   🎯 {bet_type.upper()}:")
            print(f"      ├─ P(Recomendado): {prob_recommended:.2%}")
            print(f"      ├─ P(No Recomendado): {probs['not_recommended']:.2%}")
            print(f"      ├─ Confianza: {confidence}")
            print(f"      └─ Recomendación: {'RECOMMENDED' if prob_recommended > 0.5 else 'NOT RECOMMENDED'}")
            
    except Exception as e:
        print(f"❌ Error en red bayesiana: {e}")
        import traceback
        traceback.print_exc()
        bayesian_results = {}
    
    # ========================================================================
    # CONVERSIÓN A FORMATO UNIFICADO
    # ========================================================================
    rules_unified = {}
    bayesian_unified = {}
    
    # Convertir resultados del motor de reglas a formato unificado
    for bet_type in bet_types:
        rules_data = rules_results.get(bet_type, {})
        rules_unified[bet_type] = UnifiedFormatter.from_rules_engine(bet_type, rules_data)
    
    # Convertir resultados de red bayesiana a formato unificado
    for bet_type in bet_types:
        bayesian_data = bayesian_results.get(bet_type, {})
        bayesian_unified[bet_type] = UnifiedFormatter.from_bayesian_network(bet_type, bayesian_data)
    
    # ========================================================================
    # COMPARACIÓN Y ANÁLISIS (FORMATO UNIFICADO)
    # ========================================================================
    print(f"\n📊 COMPARACIÓN DE ENFOQUES (FORMATO UNIFICADO)")
    print("=" * 80)
    
    comparison_table = []
    
    # Estilos para visualización
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    
    for bet_type in bet_types:
        rules_pred = rules_unified[bet_type]
        bayesian_pred = bayesian_unified[bet_type]
        
        print(f"\n🎯 {BOLD}{bet_type.upper()}{ENDC}:")
        print(f"   📋 Motor de Reglas:")
        
        # Resaltar decisión
        decision_color = ""
        if rules_pred.decision == RecommendationDecision.RECOMMENDED:
            decision_color = GREEN
        elif rules_pred.decision == RecommendationDecision.NOT_RECOMMENDED:
            decision_color = RED
            
        print(f"      ├─ Decisión: {decision_color}{rules_pred.decision.value}{ENDC}")
        print(f"      ├─ Confianza: {rules_pred.confidence.value}")
        print(f"      └─ Probabilidad: {rules_pred.probability:.2%}")
        
        print(f"   🕸️ Red Bayesiana:")
        
        # Resaltar decisión
        decision_color = ""
        if bayesian_pred.decision == RecommendationDecision.RECOMMENDED:
            decision_color = GREEN
        elif bayesian_pred.decision == RecommendationDecision.NOT_RECOMMENDED:
            decision_color = RED
            
        print(f"      ├─ Decisión: {decision_color}{bayesian_pred.decision.value}{ENDC}")
        print(f"      ├─ Confianza: {bayesian_pred.confidence.value}")
        print(f"      └─ Probabilidad: {bayesian_pred.probability:.2%}")
        
        # Análisis de concordancia
        concordance = ""
        concordance_color = ""
        
        if (rules_pred.decision == RecommendationDecision.NOT_EVALUATED or 
            bayesian_pred.decision == RecommendationDecision.NOT_EVALUATED):
            concordance = "PARCIAL (uno no evaluó)"
            concordance_color = YELLOW
        elif rules_pred.decision == bayesian_pred.decision:
            concordance = "CONCORDANTE ✅"
            concordance_color = GREEN
        else:
            concordance = "DISCORDANTE ❌"
            concordance_color = RED
        
        prob_diff = abs(rules_pred.probability - bayesian_pred.probability)
        
        print(f"   🔍 Análisis:")
        print(f"      ├─ Concordancia: {concordance_color}{concordance}{ENDC}")
        print(f"      └─ Diferencia probabilística: {prob_diff:.2%}")
        
        # Guardar para análisis posterior
        comparison_table.append({
            'bet_type': bet_type,
            'rules_unified': rules_pred,
            'bayesian_unified': bayesian_pred,
            'concordance': concordance,
            'prob_difference': prob_diff
        })
    
    # ========================================================================
    # RESUMEN EJECUTIVO (MEJORADO)
    # ========================================================================
    print(f"\n📋 {BOLD}RESUMEN EJECUTIVO{ENDC}")
    print("=" * 80)
    
    # Estadísticas de concordancia
    evaluated_by_both = [item for item in comparison_table 
                        if item['rules_unified'].decision != RecommendationDecision.NOT_EVALUATED and 
                           item['bayesian_unified'].decision != RecommendationDecision.NOT_EVALUATED]
    
    if evaluated_by_both:
        concordant = [item for item in evaluated_by_both 
                     if item['rules_unified'].decision == item['bayesian_unified'].decision]
        
        concordance_rate = len(concordant) / len(evaluated_by_both) if evaluated_by_both else 0
        
        avg_prob_diff = sum(item['prob_difference'] for item in evaluated_by_both) / len(evaluated_by_both)
        
        print(f"{BOLD}📊 Estadísticas de Concordancia:{ENDC}")
        print(f"   ├─ Apuestas evaluadas por ambos: {len(evaluated_by_both)}/{len(bet_types)}")
        print(f"   ├─ Decisiones concordantes: {len(concordant)}/{len(evaluated_by_both)}")
        
        # Colorear tasa de concordancia
        concordance_color = GREEN if concordance_rate >= 0.8 else (YELLOW if concordance_rate >= 0.6 else RED)
        print(f"   ├─ Tasa de concordancia: {concordance_color}{concordance_rate:.1%}{ENDC}")
        
        # Colorear diferencia de probabilidades
        prob_diff_color = GREEN if avg_prob_diff <= 0.1 else (YELLOW if avg_prob_diff <= 0.2 else RED)
        print(f"   └─ Diferencia promedio de probabilidades: {prob_diff_color}{avg_prob_diff:.2%}{ENDC}")
        
        # Interpretación
        print(f"\n{BOLD}🎯 Interpretación:{ENDC}")
        if concordance_rate >= 0.8:
            print(f"   {GREEN}✅ ALTA CONCORDANCIA: Ambos enfoques están muy alineados{ENDC}")
        elif concordance_rate >= 0.6:
            print(f"   {YELLOW}🟡 CONCORDANCIA MODERADA: Mayoría de decisiones alineadas{ENDC}")
        else:
            print(f"   {RED}❌ BAJA CONCORDANCIA: Enfoques discrepan significativamente{ENDC}")
        
        if avg_prob_diff <= 0.1:
            print(f"   {GREEN}✅ PROBABILIDADES SIMILARES: Diferencias menores al 10%{ENDC}")
        elif avg_prob_diff <= 0.2:
            print(f"   {YELLOW}🟡 PROBABILIDADES MODERADAMENTE DIFERENTES: Diferencias del 10-20%{ENDC}")
        else:
            print(f"   {RED}❌ PROBABILIDADES MUY DIFERENTES: Diferencias mayores al 20%{ENDC}")
    
    # Fortalezas y debilidades observadas
    print(f"\n{BOLD}🔍 Análisis Cualitativo:{ENDC}")
    
    rules_evaluations = sum(1 for pred in rules_unified.values() 
                         if pred.decision != RecommendationDecision.NOT_EVALUATED)
    bayesian_evaluations = sum(1 for pred in bayesian_unified.values() 
                           if pred.decision != RecommendationDecision.NOT_EVALUATED)
    
    print(f"   {BOLD}📊 Cobertura de Evaluación:{ENDC}")
    rules_color = GREEN if rules_evaluations >= 4 else (YELLOW if rules_evaluations >= 2 else RED)
    bayesian_color = GREEN if bayesian_evaluations >= 4 else (YELLOW if bayesian_evaluations >= 2 else RED)
    
    print(f"      ├─ Motor de Reglas: {rules_color}{rules_evaluations}/{len(bet_types)} tipos de apuesta{ENDC}")
    print(f"      └─ Red Bayesiana: {bayesian_color}{bayesian_evaluations}/{len(bet_types)} tipos de apuesta{ENDC}")
    
    print(f"\n   {BOLD}🧠 Motor de Reglas:{ENDC}")
    if rules_fired:
        print(f"      {GREEN}✅ Activó {len(rules_fired)} reglas específicas{ENDC}")
        print(f"      {GREEN}✅ Proporciona explicaciones detalladas{ENDC}")
    else:
        print(f"      {RED}❌ No activó ninguna regla para este enfrentamiento{ENDC}")
    
    print(f"   {BOLD}🕸️ Red Bayesiana:{ENDC}")
    print(f"      {GREEN}✅ Evalúa todos los tipos de apuesta consistentemente{ENDC}")
    print(f"      {GREEN}✅ Proporciona probabilidades continuas{ENDC}")
    print(f"      {YELLOW}⚠️ Menor explicabilidad específica{ENDC}")
    
    # Resumir recomendaciones
    recommended_by_rules = [bet for bet, pred in rules_unified.items() 
                         if pred.decision == RecommendationDecision.RECOMMENDED]
    recommended_by_bayesian = [bet for bet, pred in bayesian_unified.items() 
                           if pred.decision == RecommendationDecision.RECOMMENDED]
    
    print(f"\n{BOLD}🎯 RESUMEN DE RECOMENDACIONES:{ENDC}")
    if recommended_by_rules:
        print(f"   {BOLD}🧠 Motor de Reglas recomienda:{ENDC} {', '.join(recommended_by_rules).upper()}")
    else:
        print(f"   {BOLD}🧠 Motor de Reglas no hace recomendaciones{ENDC}")
        
    if recommended_by_bayesian:
        print(f"   {BOLD}🕸️ Red Bayesiana recomienda:{ENDC} {', '.join(recommended_by_bayesian).upper()}")
    else:
        print(f"   {BOLD}🕸️ Red Bayesiana no hace recomendaciones{ENDC}")
    
    return {
        'rules_results': rules_results,
        'bayesian_results': bayesian_results,
        'rules_unified': rules_unified,
        'bayesian_unified': bayesian_unified,
        'comparison_table': comparison_table,
        'concordance_rate': concordance_rate if evaluated_by_both else 0,
        'avg_prob_difference': avg_prob_diff if evaluated_by_both else 0
    }

def run_multiple_comparisons():
    """Ejecutar comparaciones para múltiples enfrentamientos."""
    
    test_matchups = [
        ("Real Madrid", "Barcelona"),
        ("Manchester City", "Liverpool"),
        ("Bayern Munich", "Ajax"),
        ("Atletico Madrid", "Inter Milan"),
        ("Chelsea", "Juventus")
    ]
    
    all_results = []
    
    for i, (home, away) in enumerate(test_matchups, 1):
        print(f"\n{'='*100}")
        print(f"COMPARACIÓN {i}/{len(test_matchups)}")
        print(f"{'='*100}")
        
        try:
            result = compare_approaches(home, away)
            result['matchup'] = f"{home} vs {away}"
            all_results.append(result)
            
        except Exception as e:
            print(f"❌ Error en {home} vs {away}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        if i < len(test_matchups):
            input(f"\n⏸️ Presiona Enter para continuar con la siguiente comparación...")
    
    # Resumen general
    if all_results:
        print(f"\n{'='*100}")
        print(f"RESUMEN GENERAL DE TODAS LAS COMPARACIONES")
        print(f"{'='*100}")
        
        overall_concordance = sum(r['concordance_rate'] for r in all_results) / len(all_results)
        overall_prob_diff = sum(r['avg_prob_difference'] for r in all_results) / len(all_results)
        
        print(f"📊 Estadísticas Generales:")
        print(f"   ├─ Enfrentamientos analizados: {len(all_results)}")
        print(f"   ├─ Concordancia promedio: {overall_concordance:.1%}")
        print(f"   └─ Diferencia probabilística promedio: {overall_prob_diff:.2%}")
        
        print(f"\n🏆 Conclusiones:")
        if overall_concordance >= 0.7:
            print("   ✅ Los enfoques muestran alta consistencia general")
        else:
            print("   ⚠️ Los enfoques muestran discrepancias significativas")
            
        print("   📝 Se recomienda usar ambos enfoques de forma complementaria")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Comparar motor de reglas vs red bayesiana')
    parser.add_argument('--home', type=str, help='Equipo local')
    parser.add_argument('--away', type=str, help='Equipo visitante')
    parser.add_argument('--multiple', action='store_true', help='Ejecutar múltiples comparaciones')
    
    args = parser.parse_args()
    
    try:
        if args.multiple:
            run_multiple_comparisons()
        elif args.home and args.away:
            compare_approaches(args.home, args.away)
        else:
            # Modo interactivo por defecto
            compare_approaches("Real Madrid", "Barcelona")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
