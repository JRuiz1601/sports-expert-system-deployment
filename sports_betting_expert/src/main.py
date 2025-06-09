"""
Sistema Experto de Apuestas Deportivas - UEFA Champions League 2021/22
Integración completa: data_processor + knowledge_model + rules_engine + bayesian_model
VERSIÓN CONVERSACIONAL OPTIMIZADA
"""

import os
import sys
import re
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

# Añadir el directorio src al path para importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # sports_betting_expert/
src_dir = current_dir  # src/
sys.path.insert(0, src_dir)
sys.path.insert(0, parent_dir)

# Importaciones del sistema
try:
    from src.data_processor import UCLDataProcessor
    from src.knowledge_model import TeamFact, MatchupFact, BetType, FactBuilder
    from src.rules_engine import BettingExpertSystem
    from src.bayesian_model import BettingBayesianNetwork
    from src import experta_fix
except ImportError:
    try:
        # Intento alternativo de importación
        from data_processor import UCLDataProcessor
        from knowledge_model import TeamFact, MatchupFact, BetType, FactBuilder
        from rules_engine import BettingExpertSystem
        from bayesian_model import BettingBayesianNetwork
        import collections
        import collections.abc
        # Fix para experta
        if not hasattr(collections, 'Mapping'):
            collections.Mapping = collections.abc.Mapping
        if not hasattr(collections, 'MutableMapping'):
            collections.MutableMapping = collections.abc.MutableMapping
        print("✓ No se necesitaron patches")
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Verifica que todos los archivos estén en el directorio src/")
        sys.exit(1)


class BettingExpertApp:
    """
    Aplicación principal del sistema experto de apuestas.
    Versión conversacional que integra motor de reglas y red bayesiana.
    """
    
    def __init__(self):
        """Inicializar la aplicación."""
        self.processor = None
        self.expert_system = None
        self.bayesian_network = None
        self.available_teams = []
        self.team_facts_cache = {}
        
        # Estado de la conversación
        self.context = {
            "last_teams": [],  # Últimos equipos mencionados
            "last_analysis": None,  # Resultado del último análisis
            "current_intent": None,  # Intención actual detectada
            "follow_up_question": None,  # Pregunta de seguimiento
        }
         
    
    def find_data_directory(self) -> str:
        """
        Buscar el directorio de datos utilizando múltiples estrategias.
        
        Returns:
            Ruta al directorio de datos
        """
        # Lista de posibles ubicaciones relativas
        possible_paths = [
            os.path.join('.', 'data', 'raw'),  # Desde el directorio actual
            os.path.join('..', 'data', 'raw'),  # Un nivel arriba
            os.path.join(os.path.dirname(__file__), 'data', 'raw'),  # Desde la ubicación del script
            os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'),  # Un nivel arriba del script
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'raw'),  # Ruta absoluta
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw'),  # Arriba de ruta absoluta
            os.path.join(parent_dir, 'data', 'raw'),  # Desde el directorio parent
        ]
        
        # Verificar cada posible ubicación
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        
        # Si no se encuentra, buscar en dos niveles más
        current_dir = os.path.dirname(os.path.abspath(__file__))
        for _ in range(3):  # Buscar hasta 3 niveles arriba
            current_dir = os.path.dirname(current_dir)
            potential_path = os.path.join(current_dir, 'data', 'raw')
            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                return potential_path
        
        # Si aún no se encuentra, permitir al usuario especificar la ruta
        print("⚠️ No se pudo encontrar automáticamente el directorio de datos.")
        print("Por favor, especifica la ruta completa al directorio 'data/raw':")
        user_path = input("> ").strip()
        
        if os.path.exists(user_path) and os.path.isdir(user_path):
            return user_path
        else:
            raise FileNotFoundError(f"El directorio especificado no existe: {user_path}")
    
    def initialize_system(self):
        """Inicializar y cargar todos los componentes del sistema."""
        print("🔄 Inicializando Sistema Experto de Apuestas Deportivas...")
        print("=" * 70)
        
        try:
            # 1. Inicializar procesador de datos (con búsqueda inteligente del directorio)
            print("📊 Buscando y cargando datos...")
            try:
                self.processor = UCLDataProcessor()
                self.processor.load_data()
            except FileNotFoundError:
                # Si falla, intentar encontrar directorio de datos
                data_dir = self.find_data_directory()
                print(f"📁 Directorio de datos encontrado en: {data_dir}")
                # Usar data_dir directamente sin dirname
                self.processor = UCLDataProcessor(data_path=data_dir)
                self.processor.load_data()
                
            # Procesar datos
            self.processor.aggregate_team_data()
            print("✅ Datos de la UEFA Champions League cargados correctamente")
            
            # 2. Obtener equipos disponibles
            self.available_teams = sorted(list(self.processor.team_data.keys()))
            print(f"✅ {len(self.available_teams)} equipos disponibles para análisis")
            
            # 3. Inicializar motor de reglas
            print("🧠 Inicializando motor de reglas...")
            self.expert_system = BettingExpertSystem()
            print("✅ Motor de reglas listo")
            
            # 4. Inicializar red bayesiana
            print("🕸️ Construyendo red bayesiana...")
            self.bayesian_network = BettingBayesianNetwork()
            print("✅ Red bayesiana inicializada")
            
            print("🎉 Sistema completamente inicializado")
            print("=" * 70)
            return True
            
        except Exception as e:
            print(f"❌ Error durante la inicialización: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_team_fact(self, team_name: str) -> TeamFact:
        """
        Obtener o crear TeamFact para un equipo.
        Usa cache para eficiencia.
        """
        if team_name not in self.team_facts_cache:
            team_summary = self.processor.create_team_summary(team_name)
            self.team_facts_cache[team_name] = TeamFact.from_team_summary(team_summary)
        
        return self.team_facts_cache[team_name]
    
    def analyze_matchup_hybrid(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Realizar análisis completo de un enfrentamiento usando tanto reglas como red bayesiana.
        
        Args:
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            
        Returns:
            Diccionario con análisis completo
        """
        print(f"\n🔍 ANALIZANDO: {home_team} vs {away_team}")
        print("=" * 60)
        
        # 1. Crear Facts de los equipos
        print("📊 Creando facts de equipos...")
        home_fact = self.get_team_fact(home_team)
        away_fact = self.get_team_fact(away_team)
        
        # 2. Crear MatchupFact
        print("⚖️ Analizando enfrentamiento...")
        matchup_fact = FactBuilder.create_matchup_fact(
            home_team, away_team, home_fact, away_fact
        )
        
        # ---- MOTOR DE REGLAS ----
        
        # 3. Reiniciar motor de reglas
        self.expert_system.reset()
        
        # 4. Declarar facts al motor
        print("🧠 Alimentando motor de reglas...")
        self.expert_system.declare(home_fact)
        self.expert_system.declare(away_fact)
        self.expert_system.declare(matchup_fact)
        
        # 5. Crear y declarar todos los tipos de apuesta
        bet_types = ['home_win', 'away_win', 'draw', 'over', 'under']
        for bet_type in bet_types:
            if bet_type in ['over', 'under']:
                bet = BetType.create(bet_type, home_team, away_team, threshold=2.5)
            else:
                bet = BetType.create(bet_type, home_team, away_team)
            self.expert_system.declare(bet)
        
        # 6. Ejecutar motor de reglas
        print("⚡ Ejecutando motor de inferencia...")
        self.expert_system.run()
        
        # 7. Obtener resultados del motor de reglas
        rules_recommendations = self.expert_system.get_recommendations()
        rules_analysis = self.expert_system.get_betting_analysis(home_team, away_team)
        explanations = self.expert_system.get_explanations()
        rules_summary = self.expert_system.get_rules_fired_summary()
        
        # ---- RED BAYESIANA ----
        
        # 8. Preparar evidencia para la red bayesiana
        print("🕸️ Ejecutando inferencia bayesiana...")
        evidence = {
            'home_strength': home_fact['overall_strength'],
            'away_strength': away_fact['overall_strength'],
            'home_style': home_fact['team_style'],
            'away_style': away_fact['team_style'],
            'home_goals_tendency': home_fact['goals_per_match'],
            'away_goals_tendency': away_fact['goals_per_match']
        }
        
        # 9. Realizar inferencia bayesiana
        bayesian_results = self.bayesian_network.predict(evidence)
        
        # ---- INTEGRACIÓN DE RESULTADOS ----
        
        # 10. Combinar resultados de ambos modelos
        print("🔄 Integrando resultados...")
        hybrid_recommendations = self._combine_recommendations(
            rules_recommendations, 
            bayesian_results,
            home_team,
            away_team
        )
        
        print("✅ Análisis híbrido completado")
        
        return {
            'matchup': f"{home_team} vs {away_team}",
            'home_fact': home_fact,
            'away_fact': away_fact,
            'matchup_fact': matchup_fact,
            'hybrid_recommendations': hybrid_recommendations,
            'rules_recommendations': rules_recommendations,
            'bayesian_results': bayesian_results,
            'rules_analysis': rules_analysis,
            'explanations': explanations,
            'rules_summary': rules_summary
        }
    
    def _combine_recommendations(self, rules_recommendations, bayesian_results, 
                                home_team, away_team):
        """Combinar recomendaciones de ambos modelos."""
        hybrid_results = {}
        bet_types = ['home_win', 'away_win', 'draw', 'over', 'under']
        
        # Procesar cada tipo de apuesta
        for bet_type in bet_types:
            # Obtener recomendación del motor de reglas
            rules_rec = next((r for r in rules_recommendations 
                           if r['bet_type'] == bet_type), None)
            
            # Obtener recomendación de la red bayesiana
            bayesian_rec = bayesian_results.get(bet_type, {})
            
            # Preparar resultado híbrido
            hybrid_rec = {
                'bet_type': bet_type,
                'home_team': home_team,
                'away_team': away_team
            }
            
            # CASO 1: Ambos modelos tienen recomendaciones
            if rules_rec and bayesian_rec:
                rules_recommend = rules_rec['recommendation'] == 'recommended'
                bayesian_recommend = bayesian_rec.get('recommended', 0) > 0.5
                
                # Si están de acuerdo
                if rules_recommend == bayesian_recommend:
                    # Promedio ponderado (60% reglas, 40% bayesiano)
                    rules_prob = rules_rec.get('probability', 0.5)
                    bayes_prob = bayesian_rec.get('recommended', 0.5)
                    
                    hybrid_rec['recommendation'] = 'recommended' if rules_recommend else 'not_recommended'
                    hybrid_rec['probability'] = 0.6 * rules_prob + 0.4 * bayes_prob
                    hybrid_rec['confidence'] = rules_rec.get('confidence', 'medium')
                    hybrid_rec['explanation'] = rules_rec.get('explanation', '')
                    hybrid_rec['concordance'] = 'high'
                    hybrid_rec['rules_fired'] = rules_rec.get('rules_fired', [])
                else:
                    # Si discrepan, preferir motor de reglas (más explicable)
                    hybrid_rec['recommendation'] = rules_rec['recommendation']
                    hybrid_rec['probability'] = rules_rec.get('probability', 0.5)
                    hybrid_rec['confidence'] = 'medium'  # Bajamos confianza por discrepancia
                    hybrid_rec['explanation'] = rules_rec.get('explanation', '') + \
                        f"\n[Nota: La red bayesiana sugiere lo contrario con {bayesian_rec.get('recommended', 0):.1%}]"
                    hybrid_rec['concordance'] = 'low'
                    hybrid_rec['rules_fired'] = rules_rec.get('rules_fired', [])
            
            # CASO 2: Solo el motor de reglas tiene recomendación
            elif rules_rec:
                hybrid_rec['recommendation'] = rules_rec['recommendation']
                hybrid_rec['probability'] = rules_rec.get('probability', 0.5)
                hybrid_rec['confidence'] = rules_rec.get('confidence', 'medium')
                hybrid_rec['explanation'] = rules_rec.get('explanation', '')
                hybrid_rec['source'] = 'rules_only'
                hybrid_rec['rules_fired'] = rules_rec.get('rules_fired', [])
                
            # CASO 3: Solo la red bayesiana tiene recomendación
            elif bayesian_rec:
                prob_rec = bayesian_rec.get('recommended', 0)
                hybrid_rec['recommendation'] = 'recommended' if prob_rec > 0.5 else 'not_recommended'
                hybrid_rec['probability'] = prob_rec if prob_rec > 0.5 else (1 - prob_rec)
                
                # Mapear confianza según probabilidad
                if hybrid_rec['probability'] > 0.7:
                    confidence = 'high'
                elif hybrid_rec['probability'] > 0.6:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                    
                hybrid_rec['confidence'] = confidence
                hybrid_rec['explanation'] = f"Según análisis probabilístico ({hybrid_rec['probability']:.1%})"
                hybrid_rec['source'] = 'bayesian_only'
                
            # CASO 4: Ninguno tiene recomendación
            else:
                hybrid_rec['recommendation'] = 'not_evaluated'
                hybrid_rec['probability'] = 0.5
                hybrid_rec['confidence'] = 'unavailable'
                hybrid_rec['explanation'] = "No hay suficiente información"
                hybrid_rec['source'] = 'none'
            
            hybrid_results[bet_type] = hybrid_rec
            
        return hybrid_results
    
    
    def _format_bet_name(self, bet_type: str, home_team: str, away_team: str) -> str:
        """Formatear nombre de apuesta en formato legible."""
        if bet_type == 'home_win':
            return f"Victoria de {home_team}"
        elif bet_type == 'away_win':
            return f"Victoria de {away_team}" 
        elif bet_type == 'draw':
            return "Empate"
        elif bet_type == 'over':
            return "Más de 2.5 goles"
        elif bet_type == 'under':
            return "Menos de 2.5 goles"
        return bet_type.upper()  
    
    def format_match_analysis_conversational(self, analysis_result: Dict[str, Any]) -> str:
        """
        Formatear resultados del análisis en estilo conversacional con explicaciones detalladas.
        
        Args:
            analysis_result: Resultados del análisis
            
        Returns:
            Respuesta formateada con explicaciones detalladas
        """
        home_team = analysis_result['home_fact']['team']
        away_team = analysis_result['away_fact']['team']
        home_fact = analysis_result['home_fact']
        away_fact = analysis_result['away_fact']
        
        response_parts = [
            f"📊 He analizado el partido {home_team} vs {away_team}."
        ]
        
        # Comparación de equipos con estadísticas más detalladas
        home_strength = home_fact['overall_strength']
        away_strength = away_fact['overall_strength']
        strength_diff = abs(home_strength - away_strength) * 100
        stronger_team = home_team if home_strength > away_strength else away_team
        
        # Resumen general del partido con más estadísticas
        response_parts.append(
            f"\n📈 ANÁLISIS GENERAL:"
            f"\n• {stronger_team} es superior por un {strength_diff:.1f}% en términos generales."
            f"\n• {home_team} (LOCAL): Ataque {home_fact['attacking_strength']:.2f} | "
            f"Defensa {home_fact['defensive_strength']:.2f} | "
            f"Estilo: {self._get_style_description(home_fact['team_style'])}"
            f"\n• {away_team} (VISITANTE): Ataque {away_fact['attacking_strength']:.2f} | "
            f"Defensa {away_fact['defensive_strength']:.2f} | "
            f"Estilo: {self._get_style_description(away_fact['team_style'])}"
        )
        
        # Estadísticas de goles para contextualizar
        response_parts.append(
            f"\n⚽ TENDENCIA DE GOLES:"
            f"\n• {home_team}: Marca {home_fact['goals_per_match']:.2f} y recibe {home_fact['goals_conceded_per_match']:.2f} goles por partido"
            f"\n• {away_team}: Marca {away_fact['goals_per_match']:.2f} y recibe {away_fact['goals_conceded_per_match']:.2f} goles por partido"
            f"\n• Promedio combinado: {home_fact['goals_per_match'] + away_fact['goals_per_match']:.2f} goles por partido"
        )
        
        # Recomendaciones principales con explicaciones detalladas
        recommended = []
        recommendations = analysis_result['hybrid_recommendations']
        
        # Obtener todas las recomendaciones recomendadas
        for bet_type, rec in recommendations.items():
            if rec['recommendation'] == 'recommended':
                confidence_symbol = {"high": "🔥", "medium": "⭐", "low": "✓"}.get(rec['confidence'], "✓")
                recommended.append((bet_type, rec, confidence_symbol))
        
        # Ordenamos por confianza y probabilidad
        recommended.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}.get(x[1]['confidence'], 0),
            x[1]['probability']
        ), reverse=True)
        
        if recommended:
            response_parts.append("\n🎯 RECOMENDACIONES DE APUESTAS:")
            
            # Mostrar todas las recomendaciones con justificaciones detalladas
            for bet_type, rec, confidence_symbol in recommended:
                bet_name = self._format_bet_name(bet_type, home_team, away_team)
                
                # Generar explicación detallada según el tipo de apuesta
                detailed_explanation = self._generate_detailed_explanation(
                    bet_type, rec, home_team, away_team, home_fact, away_fact, analysis_result
                )
                
                response_parts.append(
                    f"\n{confidence_symbol} {bet_name.upper()}"
                    f"\n• Confianza: {rec['confidence'].upper()}"
                    f"\n• Probabilidad: {rec['probability']:.1%}"
                    f"\n• Justificación: {detailed_explanation}"
                )
                
                # Agregar reglas que se activaron para esta recomendación
                if 'rules_fired' in rec and rec['rules_fired']:
                    rules_text = ", ".join(rec['rules_fired'])
                    response_parts.append(f"• Reglas activadas: {rules_text}")
        else:
            response_parts.append("\n⚠️ No puedo recomendarte ninguna apuesta con suficiente confianza para este partido.")
        
        return "\n".join(response_parts)

    def _generate_detailed_explanation(self, bet_type, recommendation, home_team, away_team, 
                                     home_fact, away_fact, analysis_result) -> str:
        """
        Genera explicaciones detalladas para cada tipo de apuesta basadas en estadísticas.
        
        Args:
            bet_type: Tipo de apuesta (home_win, away_win, draw, over, under)
            recommendation: Datos de la recomendación
            home_team, away_team: Nombres de los equipos
            home_fact, away_fact: Datos de los equipos
            analysis_result: Resultado completo del análisis
            
        Returns:
            Explicación detallada
        """
        if bet_type == 'home_win':
            # Explicación para victoria local
            if home_fact['overall_strength'] > away_fact['overall_strength']:
                strength_diff = (home_fact['overall_strength'] - away_fact['overall_strength']) * 100
                return (f"{home_team} tiene un {strength_diff:.1f}% de ventaja sobre {away_team}. "
                       f"Su ataque ({home_fact['attacking_strength']:.2f}) supera a la defensa visitante "
                       f"({away_fact['defensive_strength']:.2f}). Además, {home_team} marca un promedio de "
                       f"{home_fact['goals_per_match']:.2f} goles por partido, lo que le da ventaja como local.")
            else:
                return (f"A pesar de que {away_team} tiene mejores estadísticas generales, "
                       f"{home_team} tiene ventaja de jugar como local y un promedio de "
                       f"{home_fact['goals_per_match']:.2f} goles anotados por partido.")
        
        elif bet_type == 'away_win':
            # Explicación para victoria visitante
            if away_fact['overall_strength'] > home_fact['overall_strength']:
                strength_diff = (away_fact['overall_strength'] - home_fact['overall_strength']) * 100
                return (f"{away_team} es superior por {strength_diff:.1f}% y su ataque ({away_fact['attacking_strength']:.2f}) "
                       f"puede superar la defensa local ({home_fact['defensive_strength']:.2f}). {away_team} anota "
                       f"{away_fact['goals_per_match']:.2f} goles por partido, lo que compensa la desventaja de jugar como visitante.")
            else:
                return (f"Aunque {home_team} tiene mejores estadísticas generales, {away_team} "
                       f"tiene un buen rendimiento como visitante y aprovechará las debilidades defensivas "
                       f"del local que recibe {home_fact['goals_conceded_per_match']:.2f} goles por partido.")
        
        elif bet_type == 'draw':
            # Explicación para empate
            strength_diff = abs(home_fact['overall_strength'] - away_fact['overall_strength']) * 100
            if strength_diff < 10:
                return (f"Los equipos están muy igualados (diferencia de solo {strength_diff:.1f}%). "
                       f"Ambos tienen fortalezas y debilidades similares, con ataques de "
                       f"{home_fact['attacking_strength']:.2f} vs {away_fact['attacking_strength']:.2f} y defensas de "
                       f"{home_fact['defensive_strength']:.2f} vs {away_fact['defensive_strength']:.2f}.")
            else:
                return (f"A pesar de la diferencia de {strength_diff:.1f}% entre los equipos, "
                       f"factores como el estilo de juego de {away_team} ({away_fact['team_style']}) "
                       f"pueden neutralizar las ventajas de {home_team}, llevando a un equilibrio de fuerzas.")
        
        elif bet_type == 'over':
            # Explicación para más de 2.5 goles
            combined_goals = home_fact['goals_per_match'] + away_fact['goals_per_match']
            combined_conceded = home_fact['goals_conceded_per_match'] + away_fact['goals_conceded_per_match']
            
            return (f"El promedio combinado de goles es {combined_goals:.2f} por partido. "
                   f"{home_team} marca {home_fact['goals_per_match']:.2f} y {away_team} {away_fact['goals_per_match']:.2f} goles/partido. "
                   f"Además, ambos equipos conceden un total de {combined_conceded:.2f} goles por partido. "
                   f"El estilo de juego {self._get_style_description(home_fact['team_style'])} de {home_team} y "
                   f"{self._get_style_description(away_fact['team_style'])} de {away_team} favorece un partido con varios goles.")
        
        elif bet_type == 'under':
            # Explicación para menos de 2.5 goles
            defensive_strength = (home_fact['defensive_strength'] + away_fact['defensive_strength']) / 2
            
            return (f"La fuerza defensiva promedio es alta ({defensive_strength:.2f}). "
                   f"{home_team} recibe solo {home_fact['goals_conceded_per_match']:.2f} goles por partido, y "
                   f"{away_team} {away_fact['goals_conceded_per_match']:.2f}. "
                   f"El estilo de juego de los equipos y su solidez defensiva favorecen un partido de pocos goles, "
                   f"probablemente por debajo de 2.5 goles en total.")
        
        # Si no es ninguno de los tipos anteriores
        return recommendation.get('explanation', "Basado en análisis estadístico de los datos históricos de ambos equipos.")

    def _get_style_description(self, style: str) -> str:
        """Obtiene una descripción más detallada del estilo de juego."""
        style_desc = {
            'balanced': "equilibrado",
            'attacking': "ofensivo",
            'offensive': "muy ofensivo",
            'defensive': "defensivo",
            'possessive': "de posesión",
            'counter': "de contraataque",
            'mixed': "mixto/adaptable"
        }
        return style_desc.get(style, style)
    
    def format_team_stats_conversational(self, team: str) -> str:
        """
        Formatear estadísticas de un equipo en estilo conversacional.
        
        Args:
            team: Nombre del equipo
            
        Returns:
            Respuesta formateada
        """
        try:
            team_summary = self.processor.create_team_summary(team)
            
            response_parts = [
                f"📊 Estas son las estadísticas de {team}:"
            ]
            
            # Fortaleza general
            strength_level = ""
            overall = team_summary['overall_strength']
            if overall > 0.7:
                strength_level = "muy fuerte"
            elif overall > 0.6:
                strength_level = "fuerte"
            elif overall > 0.5:
                strength_level = "por encima del promedio"
            elif overall > 0.4:
                strength_level = "promedio"
            else:
                strength_level = "debajo del promedio"
                
            response_parts.append(
                f"\n{team} es un equipo {strength_level} con una valoración general de {overall:.2f}. "
                f"Su fuerza ofensiva es {team_summary['attacking_strength']:.2f} y "
                f"su fuerza defensiva es {team_summary['defensive_strength']:.2f}."
            )
            
            # Estilo de juego
            style = team_summary['team_style']
            style_desc = {
                'balanced': "equilibrado entre ataque y defensa",
                'attacking': "ofensivo, prioriza el ataque",
                'offensive': "ofensivo, prioriza el ataque",
                'defensive': "defensivo, prioriza mantener su portería a cero",
                'possessive': "de posesión, controla el balón",
                'counter': "de contraataque",
                'mixed': "mixto, adaptable según el rival"
            }.get(style, style)
            
            response_parts.append(f"\nSu estilo de juego es {style_desc}.")
            
            # Goles
            goals_per_match = team_summary['goals_per_match']
            goals_conceded = team_summary['goals_conceded_per_match']
            
            response_parts.append(
                f"\nEn cuanto a goles, marca un promedio de {goals_per_match:.2f} por partido "
                f"y recibe {goals_conceded:.2f}, con una diferencia de "
                f"{team_summary['goal_difference_per_match']:.2f} por encuentro."
            )
            
            # Disciplina
            if 'yellow_cards_per_match' in team_summary:
                response_parts.append(
                    f"\nEn términos de disciplina, recibe {team_summary['yellow_cards_per_match']:.2f} "
                    f"tarjetas amarillas y {team_summary['red_cards_per_match']:.2f} rojas por partido."
                )
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Lo siento, no pude obtener estadísticas para {team}: {str(e)}"
    
    def detect_intent(self, message: str) -> str:
        """
        Detectar la intención del usuario basado en palabras clave.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Intención detectada
        """
        message = message.lower()
        
        # Patrones para detectar intenciones
        patterns = {
            "greeting": r"\b(hola|buenos días|buenas tardes|buenas noches|saludos|hey|hi)\b",
            "farewell": r"\b(adiós|chao|hasta luego|nos vemos|salir|terminar|fin|bye|me voy)\b",
            "help": r"\b(ayuda|ayúdame|help|qué puedo hacer|qué puedes hacer|opciones|comandos|instrucciones)\b",
            "list_teams": r"\b(listar|lista|mostrar|ver|cuáles son|tienes|disponibles).+\b(equipos|clubes|conjunto)\b",
            "team_info": r"\b(estadística|estadísticas|datos|información|datos).+\b(equipo|club)\b",
            "match_analysis": r"\b(análisis|analizar|analiza|comparar|compara|partido|enfrentamiento|juegan|versus|vs|contra|recomendación|recomendaciones)\b"
        }
        
        # Verificar cada patrón
        for intent, pattern in patterns.items():
            if re.search(pattern, message):
                return intent
        
        # Si menciona dos equipos, probablemente quiere analizar un partido
        teams_mentioned = self.extract_teams(message)
        if len(teams_mentioned) >= 2:
            return "match_analysis"
        elif len(teams_mentioned) == 1:
            return "team_info"
            
        # Intención por defecto
        return "unknown"
    
    def extract_teams(self, message: str) -> List[str]:
        """
        Extraer menciones de equipos en el mensaje.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Lista de equipos mencionados
        """
        if not self.available_teams:
            return []
            
        mentioned_teams = []
        message_lower = message.lower()
        
        # Buscar equipos por nombre completo primero
        for team in self.available_teams:
            if team.lower() in message_lower:
                mentioned_teams.append(team)
                
        # Si no se encontraron equipos, intentar coincidencias parciales
        if not mentioned_teams:
            # Dividir el mensaje en palabras
            words = re.findall(r'\b\w+\b', message_lower)
            
            # Buscar palabras que estén en nombres de equipos
            for team in self.available_teams:
                team_words = set(re.findall(r'\b\w+\b', team.lower()))
                for word in words:
                    if len(word) >= 4 and word in team_words:  # Al menos 4 letras
                        mentioned_teams.append(team)
                        break
        
        return mentioned_teams
    
    def process_message(self, message: str) -> str:
        """
        Procesar mensaje del usuario y generar respuesta.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Respuesta del sistema
        """
        # Detectar intención
        intent = self.detect_intent(message)
        self.context['current_intent'] = intent
        
        # Procesar según intención
        if intent == "greeting":
            return self._handle_greeting()
        
        elif intent == "farewell":
            return self._handle_farewell()
        
        elif intent == "help":
            return self._handle_help()
        
        elif intent == "list_teams":
            return self._handle_list_teams()
        
        elif intent == "match_analysis":
            return self._handle_match_analysis(message)
        
        elif intent == "team_info":
            return self._handle_team_info(message)
        
        # Si hay una pregunta de seguimiento pendiente
        elif self.context['follow_up_question']:
            return self._handle_follow_up(message)
        
        # Intención desconocida
        else:
            return self._handle_unknown()
    
    def _handle_greeting(self) -> str:
        """Manejar saludo."""
        greetings = [
            "¡Hola! Soy tu asistente experto en apuestas deportivas. ¿En qué puedo ayudarte hoy?",
            "¡Hola! Estoy aquí para ayudarte con análisis de apuestas deportivas. ¿Quieres analizar algún partido de fútbol?",
            "¡Bienvenido! Soy tu asesor de apuestas deportivas. Puedo analizar equipos y recomendarte las mejores opciones."
        ]
        import random
        greeting = random.choice(greetings)
        return f"{greeting}\n\nPuedes pedirme cosas como:\n• \"Analiza Real Madrid vs Barcelona\"\n• \"Muéstrame estadísticas del Liverpool\"\n• \"¿Qué equipos tienes?\"\n• Escribe \"ayuda\" para ver todas las opciones."
    
    def _handle_farewell(self) -> str:
        """Manejar despedida."""
        farewells = [
            "¡Hasta pronto! Ha sido un placer ayudarte con tus análisis de apuestas.",
            "¡Adiós! Espero haberte ayudado con tus decisiones. Recuerda apostar responsablemente.",
            "¡Que tengas suerte con tus apuestas! Mis recomendaciones son sugerencias basadas en datos, no garantías."
        ]
        import random
        return random.choice(farewells)
    
    def _handle_help(self) -> str:
        """Manejar solicitud de ayuda."""
        return ("🔍 **¿En qué puedo ayudarte?**\n\n"
                "Puedo asistirte con:\n\n"
                "**1. Análisis de partidos:**\n"
                "   • \"Analiza Real Madrid contra Barcelona\"\n"
                "   • \"¿Qué me recomiendas para el partido de Manchester City vs Liverpool?\"\n"
                "   • \"¿Quién es favorito entre Bayern Munich y Ajax?\"\n\n"
                "**2. Información de equipos:**\n"
                "   • \"Muéstrame las estadísticas del Chelsea\"\n"
                "   • \"Háblame sobre el Juventus\"\n\n"
                "**3. Equipos disponibles:**\n"
                "   • \"¿Qué equipos tienes en tu base de datos?\"\n"
                "   • \"Muestra los equipos disponibles\"\n\n"
                "**4. Otras opciones:**\n"
                "   • \"Salir\" - Terminar la conversación\n\n"
                "Utilizo un sistema híbrido que combina un motor de reglas y una red bayesiana para ofrecerte las mejores recomendaciones.")
    
    def _handle_list_teams(self) -> str:
        """Manejar solicitud de lista de equipos."""
        team_count = len(self.available_teams)
        
        # Mostrar todos los equipos sin importar la cantidad
        teams_str = "\n• ".join(self.available_teams)
        return f"Estos son todos los equipos disponibles ({team_count} equipos):\n\n• {teams_str}\n\n¿Sobre cuál equipo te gustaría saber más?"
        
    def _handle_match_analysis(self, message: str) -> str:
        """Manejar solicitud de análisis de partido."""
        # Extraer equipos mencionados
        teams = self.extract_teams(message)
        
        # Si no hay equipos claros, preguntar
        if len(teams) < 2:
            if teams:
                self.context['last_teams'] = teams
                self.context['follow_up_question'] = 'second_team'
                return f"Veo que mencionaste a {teams[0]}. ¿Contra qué equipo quieres que analice su enfrentamiento?"
            else:
                self.context['follow_up_question'] = 'both_teams'
                return "¿Qué equipos quieres que analice? Necesito los nombres de ambos equipos para hacer el análisis."
        
        # Si tenemos dos equipos, preguntar cuál es local y cuál visitante
        self.context['last_teams'] = teams
        self.context['follow_up_question'] = 'home_away_selection'
        
        return f"He identificado a {teams[0]} y {teams[1]}. ¿Cuál de los dos es el equipo local?\n\n1. {teams[0]}\n2. {teams[1]}"
        
        # Si tenemos dos equipos, hacer análisis
        # IMPORTANTE: Mantener el orden original - primer equipo es local, segundo es visitante
        home_team, away_team = teams[0], teams[1]
        
        try:
            # Guardar los equipos en contexto
            self.context['last_teams'] = [home_team, away_team]
            
            # Realizar análisis híbrido
            print(f"Analizando: {home_team} vs {away_team}...")
            analysis_result = self.analyze_matchup_hybrid(home_team, away_team)
            self.context['last_analysis'] = analysis_result
            
            # Formatear y devolver resultados
            return self.format_match_analysis_conversational(analysis_result)
            
        except Exception as e:
            print(f"Error al analizar partido: {e}")
            traceback.print_exc()
            return f"Lo siento, ocurrió un error al analizar el partido entre {home_team} y {away_team}: {str(e)}"
    
    def _handle_team_info(self, message: str) -> str:
        """Manejar solicitud de información de equipo."""
        # Extraer equipos mencionados
        teams = self.extract_teams(message)
        
        if not teams:
            self.context['follow_up_question'] = 'team_name'
            return "¿De qué equipo quieres que te muestre las estadísticas?"
        
        # Tomar el primer equipo mencionado
        team = teams[0]
        self.context['last_teams'] = [team]
        
        return self.format_team_stats_conversational(team)
    
    def _handle_follow_up(self, message: str) -> str:
        """Manejar pregunta de seguimiento."""
        question_type = self.context['follow_up_question']
        
        # Resetear la pregunta de seguimiento
        self.context['follow_up_question'] = None
        
        # Selección de equipo local/visitante
        if question_type == 'home_away_selection':
            teams = self.context['last_teams']
            message_lower = message.lower()
            
            # Determinar qué equipo es local basado en la respuesta
            if '1' in message_lower or teams[0].lower() in message_lower:
                home_team = teams[0]
                away_team = teams[1]
            elif '2' in message_lower or teams[1].lower() in message_lower:
                home_team = teams[1]
                away_team = teams[0]
            else:
                # Si la respuesta no es clara, preguntar de nuevo
                self.context['follow_up_question'] = 'home_away_selection'
                return f"No entendí tu elección. Por favor indica quién es el equipo local:\n\n1. {teams[0]}\n2. {teams[1]}"
            
            try:
                print(f"Analizando: {home_team} (LOCAL) vs {away_team} (VISITANTE)...")
                # Guardar los equipos en contexto con el orden correcto
                self.context['last_teams'] = [home_team, away_team]
                
                # Realizar análisis híbrido
                analysis_result = self.analyze_matchup_hybrid(home_team, away_team)
                self.context['last_analysis'] = analysis_result
                
                # Formatear y devolver resultados
                return self.format_match_analysis_conversational(analysis_result)
            except Exception as e:
                print(f"Error al analizar partido: {e}")
                traceback.print_exc()
                return f"Lo siento, ocurrió un error al analizar este partido: {str(e)}"
        
        # Segundo equipo para análisis
        elif question_type == 'second_team':
            teams = self.extract_teams(message)

            if teams:
                home_team = self.context['last_teams'][0]  # Mantener el primero como local
                away_team = teams[0]
                
                try:
                    self.context['last_teams'] = [home_team, away_team]
                    # Mantener el orden correcto en el análisis
                    analysis_result = self.analyze_matchup_hybrid(home_team, away_team) 
                    self.context['last_analysis'] = analysis_result
                    
                    return self.format_match_analysis_conversational(analysis_result)
                except Exception as e:
                    return f"Lo siento, ocurrió un error al analizar este partido: {str(e)}"
            else:
                return "No logré identificar ningún equipo en tu mensaje. Por favor, menciona claramente el nombre del equipo."
        
        # Ambos equipos para análisis
        elif question_type == 'both_teams':
            teams = self.extract_teams(message)
            
            if len(teams) >= 2:
                home_team, away_team = teams[0], teams[1]  # Primer equipo local, segundo visitante
                
                try:
                    self.context['last_teams'] = [home_team, away_team]
                    analysis_result = self.analyze_matchup_hybrid(home_team, away_team)
                    self.context['last_analysis'] = analysis_result
                    
                    return self.format_match_analysis_conversational(analysis_result)
                except Exception as e:
                    return f"Lo siento, ocurrió un error al analizar este partido: {str(e)}"
            else:
                return "Necesito los nombres de dos equipos para hacer el análisis. Por ejemplo: 'Real Madrid y Barcelona'."
        
        # Nombre de equipo para estadísticas
        elif question_type == 'team_name':
            teams = self.extract_teams(message)
            
            if teams:
                team = teams[0]
                self.context['last_teams'] = [team]
                return self.format_team_stats_conversational(team)
            else:
                return "No pude identificar un equipo válido. Por favor, menciona el nombre exacto de un equipo."
        
        # Si llegamos aquí es un error
        return "No entendí completamente tu respuesta. ¿Puedes reformular tu pregunta?"
        
    def _handle_unknown(self) -> str:
        """Manejar intención desconocida."""
        return ("No estoy seguro de lo que estás preguntando. Puedes:\n\n"
                "• Pedirme que analice un partido: \"Analiza Real Madrid vs Barcelona\"\n"
                "• Consultar estadísticas de un equipo: \"Datos del Bayern Munich\"\n"
                "• Ver la lista de equipos disponibles: \"Muestra los equipos\"\n"
                "• Pedir \"ayuda\" para más instrucciones")
    
    def show_available_teams(self):
        """Mostrar todos los equipos disponibles."""
        return self._handle_list_teams()
    
    def run_conversational(self):
        """Ejecutar el chatbot en modo conversacional."""
        print("\n" + "=" * 80)
        print("🤖 ASISTENTE EXPERTO DE APUESTAS DEPORTIVAS")
        print("=" * 80)
        
        # Inicializar sistema
        if not self.initialize_system():
            print("❌ No se pudo inicializar el sistema. Por favor, verifica la instalación y los datos.")
            return
            
        print("\n¡Hola! Soy tu asistente experto en apuestas deportivas basadas en análisis estadísticos.")
        print("Combino un sistema experto basado en reglas con una red bayesiana para darte las mejores recomendaciones.")
        print("💬 Puedes preguntarme sobre equipos, partidos o pedir recomendaciones de apuestas.")
        print("❓ Por ejemplo: \"Analiza Real Madrid vs Barcelona\" o \"Estadísticas de Liverpool\"")
        print("💡 Escribe \"ayuda\" para ver todas las opciones o \"salir\" para terminar.")
        
        # Bucle principal de conversación
        while True:
            try:
                print("\n" + "-" * 80)
                user_input = input("👤 Tú: ").strip()
                
                if not user_input:
                    continue
                
                # Verificar salida
                if user_input.lower() in ['salir', 'exit', 'quit', 'bye', 'adiós', 'chao']:
                    print("\n🤖 Asistente: ¡Hasta pronto! Gracias por usar el asistente de apuestas. Recuerda apostar responsablemente.")
                    break
                    
                # Procesar mensaje y mostrar respuesta
                response = self.process_message(user_input)
                
                # Imprimir respuesta con formato
                print(f"\n🤖 Asistente: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta pronto! Gracias por usar el asistente.")
                break
            except Exception as e:
                print(f"\n❌ Error inesperado: {str(e)}")
                print("Por favor, intenta de nuevo o escribe 'salir' para terminar.")
    
    def run(self):
        """Ejecutar la aplicación principal."""
        print("🏆 SISTEMA EXPERTO DE APUESTAS DEPORTIVAS")
        print("   UEFA Champions League 2021/22")
        print("🔬 Versión Conversacional - Integración Completa")
        print("=" * 70)
        
        try:
            # Iniciar directamente la interfaz conversacional sin preguntar
            self.run_conversational()
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
        except Exception as e:
            print(f"\n❌ Error crítico: {str(e)}")
            traceback.print_exc()


def main():
    """Función principal."""
    try:
        app = BettingExpertApp()
        app.run()
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        traceback.print_exc()
        print("Verifica que todos los archivos estén en su lugar y los datos cargados.")


if __name__ == "__main__":
    main()