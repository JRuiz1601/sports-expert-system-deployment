"""
Motor de reglas para el sistema experto de apuestas deportivas.
REFACTORIZADO: Sistema completo con reglas inteligentes para los 5 tipos de apuesta.
"""
import datetime
from experta import KnowledgeEngine, Rule, Fact, AND, OR, NOT, MATCH, TEST
from typing import Dict, List, Any, Optional, Tuple

# Importación que funciona tanto desde src/ como desde raíz
try:
    from knowledge_model import TeamFact, MatchupFact, BetType, BetRecommendationFact
except ImportError:
    from src.knowledge_model import TeamFact, MatchupFact, BetType, BetRecommendationFact

class BettingExpertSystem(KnowledgeEngine):
    """
    Motor de inferencia para generar recomendaciones de apuestas deportivas.
    
    ARQUITECTURA DEL SISTEMA:
    1. Recibe Facts del knowledge_model (TeamFact, MatchupFact, BetType)
    2. Aplica reglas expertas para evaluar cada tipo de apuesta
    3. Genera BetRecommendationFact con explicaciones detalladas
    
    TIPOS DE APUESTA SOPORTADOS:
    - home_win: Victoria del equipo local
    - away_win: Victoria del equipo visitante  
    - draw: Empate entre equipos
    - over: Más goles que el threshold (ej: Over 2.5)
    - under: Menos goles que el threshold (ej: Under 2.5)
    """
    
    def __init__(self):
        super().__init__()
        self.recommendations = []
        self.explanations = {}
        self.rules_fired_count = {}  # Para tracking de reglas activadas
    
    def reset(self):
        """Reiniciar el motor de inferencia."""
        super().reset()
        self.recommendations = []
        self.explanations = {}
        self.rules_fired_count = {}

    # ================================================================
    # REGLAS PARA HOME_WIN (Victoria Local)
    # ================================================================
    
    @Rule(
        MatchupFact(clear_favorite=MATCH.clear_favorite, home_team=MATCH.home_team, 
                   away_team=MATCH.away_team, overall_margin=MATCH.margin),
        BetType(bet_type=BetType.TYPE_HOME_WIN, home_team=MATCH.home_team),        TEST(lambda clear_favorite, home_team: 
             clear_favorite and clear_favorite == home_team)
    )
    def clear_favorite_home_win(self, clear_favorite, home_team, away_team, margin):
        """
        REGLA HOME_WIN #1: Favorito claro local
        Si el equipo local es claramente superior (>15% diferencia), recomendar victoria local.
        """
        confidence = 'high' if margin > 0.25 else 'medium'
        
        explanation = (
            f"{home_team} es claramente superior a {away_team} con {margin:.1%} de ventaja. "
            f"Jugando en casa, debería ganar cómodamente."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='ClearFavoriteHomeWin'
        )

    @Rule(
        TeamFact(team=MATCH.home_team, attacking_strength=MATCH.h_attack, 
                defensive_strength=MATCH.h_defense, goals_per_match=MATCH.h_goals),
        TeamFact(team=MATCH.away_team, attacking_strength=MATCH.a_attack, 
                defensive_strength=MATCH.a_defense, goals_conceded_per_match=MATCH.a_conceded),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team, 
                   attacking_advantage=MATCH.att_adv),
        BetType(bet_type=BetType.TYPE_HOME_WIN, home_team=MATCH.home_team),        TEST(lambda h_attack, a_defense, h_goals, a_conceded, att_adv, home_team: 
             h_attack > 0.59 and a_defense < 0.32 and h_goals > 1.67 and 
             a_conceded > 1.3 and att_adv == home_team)
    )
    def strong_home_attack_vs_weak_away_defense(self, home_team, away_team, h_attack, 
                                               a_defense, h_goals, a_conceded):
        """
        REGLA HOME_WIN #2: Ataque local fuerte vs defensa visitante débil
        Combina múltiples factores: fuerza ofensiva, vulnerabilidad defensiva, historial.
        """        # Calcular factores de confianza
        attack_factor = h_attack > 0.72
        defense_factor = a_defense < 0.32  
        goals_factor = h_goals > 2.0
        conceded_factor = a_conceded > 1.5
        
        confidence_factors = sum([attack_factor, defense_factor, goals_factor, conceded_factor])
        confidence = 'high' if confidence_factors >= 3 else 'medium'
        
        explanation = (
            f"{home_team} presenta ventajas decisivas: ataque potente ({h_attack:.2f}), "
            f"excelente promedio goleador ({h_goals:.1f} goles/partido). "
            f"{away_team} es vulnerable: defensa débil ({a_defense:.2f}), "
            f"concede muchos goles ({a_conceded:.1f}/partido)."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='StrongHomeAttackVsWeakAwayDefense'
        )

    @Rule(
        TeamFact(team=MATCH.home_team, team_style=MATCH.h_style, 
                overall_strength=MATCH.h_strength),
        TeamFact(team=MATCH.away_team, team_style=MATCH.a_style, 
                overall_strength=MATCH.a_strength),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team),
        BetType(bet_type=BetType.TYPE_HOME_WIN, home_team=MATCH.home_team),
        TEST(lambda h_style, a_style, h_strength, a_strength: 
             h_style == "offensive" and a_style == "defensive" and 
             h_strength > a_strength + 0.1)
    )
    def offensive_home_vs_defensive_away(self, home_team, away_team, h_style, a_style, 
                                        h_strength, a_strength):
        """
        REGLA HOME_WIN #3: Estilo ofensivo local vs defensivo visitante
        Cuando un equipo ofensivo superior juega en casa contra un equipo defensivo.
        """
        strength_diff = h_strength - a_strength
        confidence = 'high' if strength_diff > 0.2 else 'medium'
        
        explanation = (
            f"{home_team} (estilo {h_style}) tiene ventaja táctica en casa contra "
            f"{away_team} (estilo {a_style}). Diferencia de nivel: {strength_diff:.2f}. "
            f"Los equipos ofensivos suelen aprovechar mejor el factor casa."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='OffensiveHomeVsDefensiveAway'
        )

    # ================================================================
    # REGLAS PARA AWAY_WIN (Victoria Visitante)
    # ================================================================
    
    @Rule(
        MatchupFact(clear_favorite=MATCH.clear_favorite, home_team=MATCH.home_team, 
                   away_team=MATCH.away_team, overall_margin=MATCH.margin),
        BetType(bet_type=BetType.TYPE_AWAY_WIN, away_team=MATCH.away_team),        TEST(lambda clear_favorite, away_team: 
             clear_favorite and clear_favorite == away_team)
    )
    def clear_favorite_away_win(self, clear_favorite, home_team, away_team, margin):
        """
        REGLA AWAY_WIN #1: Favorito claro visitante
        Si el equipo visitante es claramente superior, recomendar victoria visitante.
        Requiere mayor margen porque juega fuera de casa.
        """
        confidence = 'high' if margin > 0.3 else 'medium'
        
        explanation = (
            f"{away_team} es claramente superior a {home_team} con {margin:.1%} de ventaja. "
            f"A pesar de jugar fuera, su superioridad debería compensar la desventaja del campo."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_AWAY_WIN,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='ClearFavoriteAwayWin'
        )

    @Rule(
        TeamFact(team=MATCH.away_team, attacking_strength=MATCH.a_attack, 
                defensive_strength=MATCH.a_defense, overall_strength=MATCH.a_overall),
        TeamFact(team=MATCH.home_team, attacking_strength=MATCH.h_attack, 
                defensive_strength=MATCH.h_defense, overall_strength=MATCH.h_overall),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team),
        BetType(bet_type=BetType.TYPE_AWAY_WIN, away_team=MATCH.away_team),        TEST(lambda a_attack, a_defense, a_overall, h_overall: 
             a_attack > 0.72 and a_defense > 0.44 and a_overall > h_overall + 0.12)
    )
    def dominant_away_team(self, home_team, away_team, a_attack, a_defense, a_overall, h_overall):
        """
        REGLA AWAY_WIN #2: Visitante dominante en ambas fases
        Equipo visitante superior tanto en ataque como en defensa.
        """
        superiority = a_overall - h_overall
        confidence = 'high' if superiority > 0.25 else 'medium'
        
        explanation = (
            f"{away_team} domina en ambas fases: ataque excelente ({a_attack:.2f}) "
            f"y defensa sólida ({a_defense:.2f}). Superioridad global de {superiority:.2f} "
            f"sobre {home_team}. Calidad suficiente para ganar fuera de casa."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_AWAY_WIN,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='DominantAwayTeam'
        )

    # ================================================================
    # REGLAS PARA DRAW (Empate)
    # ================================================================
    
    @Rule(
        TeamFact(team=MATCH.home_team, overall_strength=MATCH.h_overall, 
                defensive_strength=MATCH.h_defense, cleansheet_rate=MATCH.h_clean),
        TeamFact(team=MATCH.away_team, overall_strength=MATCH.a_overall, 
                defensive_strength=MATCH.a_defense, cleansheet_rate=MATCH.a_clean),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team, 
                   overall_margin=MATCH.margin),
        BetType(bet_type=BetType.TYPE_DRAW, home_team=MATCH.home_team),        TEST(lambda h_overall, a_overall, margin, h_defense, a_defense, h_clean, a_clean: 
             margin < 0.10 and min(h_defense, a_defense) > 0.44 and 
             (h_clean + a_clean) > 0.4)
    )
    def balanced_defensive_teams_draw(self, home_team, away_team, h_overall, a_overall, 
                                     margin, h_defense, a_defense, h_clean, a_clean):
        """
        REGLA DRAW #1: Equipos equilibrados y defensivos
        Equipos similares en nivel con buenas defensas tienden al empate.
        """
        avg_defense = (h_defense + a_defense) / 2
        avg_cleansheets = (h_clean + a_clean) / 2
        
        confidence = 'medium' if margin < 0.06 and avg_defense > 0.44 else 'low'
        
        explanation = (
            f"Equipos muy equilibrados: diferencia mínima de {margin:.2f}. "
            f"Ambos son defensivamente sólidos (promedio: {avg_defense:.2f}) "
            f"con buena tasa de porterías a cero ({avg_cleansheets:.1%}). "
            f"Perfil típico para empate."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_DRAW,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='BalancedDefensiveTeamsDraw'
        )

    @Rule(
        TeamFact(team=MATCH.home_team, discipline_rating=MATCH.h_disc, 
                goal_difference_per_match=MATCH.h_diff),
        TeamFact(team=MATCH.away_team, discipline_rating=MATCH.a_disc, 
                goal_difference_per_match=MATCH.a_diff),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team),
        BetType(bet_type=BetType.TYPE_DRAW, home_team=MATCH.home_team),        TEST(lambda h_disc, a_disc, h_diff, a_diff: 
             min(h_disc, a_disc) > 0.74 and abs(h_diff) < 0.3 and abs(a_diff) < 0.3)
    )
    def disciplined_balanced_teams_draw(self, home_team, away_team, h_disc, a_disc, 
                                       h_diff, a_diff):
        """
        REGLA DRAW #2: Equipos disciplinados y equilibrados en diferencia de goles
        Equipos con alta disciplina y diferencias de gol neutrales tienden al empate.
        """
        avg_discipline = (h_disc + a_disc) / 2
        avg_diff = (abs(h_diff) + abs(a_diff)) / 2
        
        confidence = 'medium' if avg_discipline > 0.74 and avg_diff < 0.2 else 'low'
        
        explanation = (
            f"Ambos equipos muestran alta disciplina (promedio: {avg_discipline:.2f}) "
            f"y diferencias de gol equilibradas ({h_diff:.2f} vs {a_diff:.2f}). "
            f"Los equipos disciplinados evitan riesgos innecesarios, favoreciendo empates."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_DRAW,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='DisciplinedBalancedTeamsDraw'
        )

    # ================================================================
    # REGLAS PARA OVER (Más goles que threshold)
    # ================================================================
    
    @Rule(
        TeamFact(team=MATCH.home_team, attacking_strength=MATCH.h_attack, 
                goals_per_match=MATCH.h_goals, discipline_rating=MATCH.h_disc),
        TeamFact(team=MATCH.away_team, attacking_strength=MATCH.a_attack, 
                goals_per_match=MATCH.a_goals, defensive_strength=MATCH.a_defense),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team, 
                   match_type=MATCH.match_type),
        BetType(bet_type=BetType.TYPE_OVER, threshold=MATCH.threshold),        TEST(lambda h_attack, a_attack, h_goals, a_goals, threshold, match_type: 
             h_attack > 0.59 and a_attack > 0.59 and 
             (h_goals + a_goals) > (threshold + 0.3) and match_type == "attack_focused")
    )
    def offensive_teams_over(self, home_team, away_team, h_attack, a_attack, 
                            h_goals, a_goals, threshold, match_type, h_disc):
        """
        REGLA OVER #1: Equipos ofensivos con historial alto de goles
        Ambos equipos tienen buen ataque y promedios altos de goles.
        """
        total_goals_avg = h_goals + a_goals
        attack_combined = (h_attack + a_attack) / 2
        
        confidence = 'high' if total_goals_avg > threshold + 0.8 and attack_combined > 0.72 else 'medium'
        
        explanation = (
            f"Enfrentamiento altamente ofensivo: {home_team} ({h_attack:.2f} ataque, "
            f"{h_goals:.1f} goles/partido) vs {away_team} ({a_attack:.2f} ataque, "
            f"{a_goals:.1f} goles/partido). Promedio combinado: {total_goals_avg:.1f} goles, "
            f"muy superior al umbral {threshold}."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_OVER,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='OffensiveTeamsOver'
        )

    @Rule(
        TeamFact(team=MATCH.home_team, attacking_strength=MATCH.h_attack, 
                discipline_rating=MATCH.h_disc),
        TeamFact(team=MATCH.away_team, defensive_strength=MATCH.a_defense, 
                goals_conceded_per_match=MATCH.a_conceded),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team),
        BetType(bet_type=BetType.TYPE_OVER, threshold=MATCH.threshold),        TEST(lambda h_attack, a_defense, a_conceded, h_disc, threshold: 
             h_attack > 0.72 and a_defense < 0.32 and a_conceded > 1.8 and h_disc < 0.52)
    )
    def attack_vs_weak_defense_over(self, home_team, away_team, h_attack, a_defense, 
                                   a_conceded, h_disc, threshold):
        """
        REGLA OVER #2: Ataque fuerte vs defensa muy débil + factor disciplina
        Equipo local con ataque potente y poca disciplina vs defensa vulnerable.
        """
        confidence = 'high' if h_attack > 0.72 and a_defense < 0.32 else 'medium'
        
        explanation = (
            f"{home_team} tiene ataque letal ({h_attack:.2f}) y baja disciplina ({h_disc:.2f}), "
            f"lo que genera un juego más abierto. {away_team} es muy vulnerable "
            f"defensivamente ({a_defense:.2f}) y concede muchos goles ({a_conceded:.1f}/partido). "
            f"Combinación perfecta para superar {threshold} goles."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_OVER,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='AttackVsWeakDefenseOver'
        )

    # ================================================================    # REGLAS PARA UNDER (Menos goles que threshold)
    # ================================================================
    
    @Rule(
        TeamFact(team=MATCH.home_team, defensive_strength=MATCH.h_defense, 
                goals_conceded_per_match=MATCH.h_conceded, cleansheet_rate=MATCH.h_clean),
        TeamFact(team=MATCH.away_team, defensive_strength=MATCH.a_defense, 
                goals_conceded_per_match=MATCH.a_conceded, cleansheet_rate=MATCH.a_clean),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team, 
                   match_type=MATCH.match_type),
        BetType(bet_type=BetType.TYPE_UNDER, threshold=MATCH.threshold),
        TEST(lambda h_defense, a_defense, h_conceded, a_conceded, h_clean, a_clean, threshold: 
             min(h_defense, a_defense) > 0.44 and 
             max(h_conceded, a_conceded) < (threshold - 0.2) and 
             (h_clean + a_clean) > 0.4)
    )
    def strong_defenses_under(self, home_team, away_team, h_defense, a_defense, 
                             h_conceded, a_conceded, h_clean, a_clean, threshold):
        """
        REGLA UNDER #1: Defensas sólidas con historial bajo de goles concedidos
        Ambos equipos tienen buenas defensas y conceden pocos goles históricamenté.
        """
        avg_defense = (h_defense + a_defense) / 2
        avg_conceded = (h_conceded + a_conceded) / 2
        avg_cleansheets = (h_clean + a_clean) / 2
        
        confidence = ('high' if avg_defense > 0.50 and avg_conceded < threshold - 0.4 
                     else 'medium')
        
        explanation = (
            f"Enfrentamiento defensivo: ambos equipos tienen defensas sólidas "
            f"(promedio: {avg_defense:.2f}) y conceden pocos goles "
            f"({h_conceded:.1f} y {a_conceded:.1f}/partido). "
            f"Alta tasa de porterías a cero ({avg_cleansheets:.1%}). "
            f"Promedio combinado sugiere menos de {threshold} goles."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_UNDER,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='StrongDefensesUnder'
        )

    @Rule(
        TeamFact(team=MATCH.home_team, discipline_rating=MATCH.h_disc, 
                attacking_strength=MATCH.h_attack),
        TeamFact(team=MATCH.away_team, discipline_rating=MATCH.a_disc, 
                attacking_strength=MATCH.a_attack),
        MatchupFact(home_team=MATCH.home_team, away_team=MATCH.away_team),
        BetType(bet_type=BetType.TYPE_UNDER, threshold=MATCH.threshold),        TEST(lambda h_disc, a_disc, h_attack, a_attack: 
             min(h_disc, a_disc) > 0.74 and max(h_attack, a_attack) < 0.45)
    )
    def disciplined_low_attack_under(self, home_team, away_team, h_disc, a_disc, 
                                    h_attack, a_attack, threshold):
        """
        REGLA UNDER #2: Equipos muy disciplinados con poco poder ofensivo
        Alta disciplina + bajo poder ofensivo = pocos goles.
        """
        avg_discipline = (h_disc + a_disc) / 2
        avg_attack = (h_attack + a_attack) / 2
        
        confidence = 'medium' if avg_discipline > 0.74 and avg_attack < 0.40 else 'low'
        
        explanation = (
            f"Ambos equipos son muy disciplinados (promedio: {avg_discipline:.2f}) "
            f"pero con limitado poder ofensivo (promedio: {avg_attack:.2f}). "
            f"Combinación que típicamente produce partidos cerrados y de pocos goles, "
            f"quedando por debajo de {threshold} goles."
        )
        
        self._create_recommendation(
            bet_type=BetType.TYPE_UNDER,
            home_team=home_team,
            away_team=away_team,
            recommendation='recommended',
            confidence=confidence,
            explanation=explanation,
            rule_name='DisciplinedLowAttackUnder'
        )

    # ================================================================    # REGLAS DE SEGURIDAD Y WARNING
    # ================================================================
    
    @Rule(
        TeamFact(team=MATCH.team1, discipline_rating=MATCH.disc1),
        TeamFact(team=MATCH.team2, discipline_rating=MATCH.disc2),
        OR(
            MatchupFact(home_team=MATCH.team1, away_team=MATCH.team2),
            MatchupFact(home_team=MATCH.team2, away_team=MATCH.team1)
        ),
        TEST(lambda disc1, disc2: min(disc1, disc2) < 0.52)
    )
    def low_discipline_warning(self, team1, team2, disc1, disc2):
        """
        REGLA WARNING: Advertencia por baja disciplina
        Emite advertencias cuando algún equipo tiene disciplina muy baja.
        """
        low_discipline_team = team1 if disc1 < disc2 else team2
        disc_value = disc1 if disc1 < disc2 else disc2
        
        warning = (
            f"⚠️ ADVERTENCIA: {low_discipline_team} tiene disciplina muy baja ({disc_value:.2f}). "
            f"Alto riesgo de tarjetas y expulsiones que pueden alterar el resultado."
        )
        
        self.explanations[f"{team1}_vs_{team2}_discipline_warning"] = warning

    # ================================================================
    # MÉTODOS DE UTILIDAD
    # ================================================================
    
    def _create_recommendation(self, bet_type: str, home_team: str, away_team: str,
                              recommendation: str, confidence: str, explanation: str,
                              rule_name: str):
        """
        Método utilitario para crear recomendaciones de forma consistente.
        
        Args:
            bet_type: Tipo de apuesta
            home_team: Equipo local
            away_team: Equipo visitante  
            recommendation: 'recommended' o 'not_recommended'
            confidence: 'high', 'medium', 'low'
            explanation: Explicación detallada
            rule_name: Nombre de la regla que generó la recomendación
        """        # Tracking de reglas activadas
        if rule_name not in self.rules_fired_count:
            self.rules_fired_count[rule_name] = 0
        self.rules_fired_count[rule_name] += 1
        
        # Calcular probabilidad básica basada en la confianza
        probability_map = {
            'high': 0.75,
            'medium': 0.60,
            'low': 0.55
        }
        probability = probability_map.get(confidence, 0.50)
        
        # Crear la recomendación
        recommendation_fact = BetRecommendationFact.create(
            bet_type=bet_type,
            home_team=home_team,
            away_team=away_team,
            recommendation=recommendation,
            confidence=confidence,
            probability=probability,
            explanation=explanation,
            rules_fired=[rule_name]
        )
        
        # Declarar al motor de inferencia y almacenar
        self.declare(recommendation_fact)
        self.recommendations.append(recommendation_fact)

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Obtener todas las recomendaciones generadas.
        
        Returns:
            Lista de recomendaciones en formato diccionario.
        """
        return [self._fact_to_dict(rec) for rec in self.recommendations]
    
    def get_explanations(self) -> Dict[str, str]:
        """
        Obtener todas las explicaciones adicionales.
        
        Returns:
            Diccionario con explicaciones adicionales.
        """
        return self.explanations
    
    def get_rules_fired_summary(self) -> Dict[str, int]:
        """
        Obtener resumen de cuántas veces se activó cada regla.
        
        Returns:
            Diccionario con conteo de activaciones por regla.
        """
        return self.rules_fired_count

    def _fact_to_dict(self, fact):
        """
        Convertir un Fact a diccionario para facilitar su uso.
        
        Args:
            fact: Fact de experta a convertir
            
        Returns:
            Diccionario con los datos del Fact
        """
        result = {}
        for key in fact:
            value = fact[key]
            # Manejar diferentes tipos de datos
            if value is None:
                result[key] = None
            elif isinstance(value, datetime.datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, tuple)):
                result[key] = list(value)
            elif hasattr(value, '__iter__') and not isinstance(value, str):
                result[key] = list(value)
            else:
                result[key] = value
        return result

    def get_betting_analysis(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Obtener un análisis completo de apuestas para un enfrentamiento específico.
        
        Args:
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            
        Returns:
            Diccionario con análisis completo de todas las apuestas
        """
        # Filtrar recomendaciones para este enfrentamiento
        match_recommendations = [
            rec for rec in self.get_recommendations()
            if rec.get('home_team') == home_team and rec.get('away_team') == away_team
        ]
        
        # Organizar por tipo de apuesta
        analysis = {
            'match': f"{home_team} vs {away_team}",
            'recommendations_by_type': {},
            'summary': {
                'total_recommendations': len(match_recommendations),
                'high_confidence': len([r for r in match_recommendations if r.get('confidence') == 'high']),
                'medium_confidence': len([r for r in match_recommendations if r.get('confidence') == 'medium']),
                'low_confidence': len([r for r in match_recommendations if r.get('confidence') == 'low'])
            },
            'warnings': []
        }
        
        # Agrupar por tipo de apuesta
        for rec in match_recommendations:
            bet_type = rec.get('bet_type')
            if bet_type not in analysis['recommendations_by_type']:
                analysis['recommendations_by_type'][bet_type] = []
            analysis['recommendations_by_type'][bet_type].append(rec)
        
        # Agregar warnings específicos del enfrentamiento
        warning_key = f"{home_team}_vs_{away_team}_discipline_warning"
        if warning_key in self.explanations:
            analysis['warnings'].append(self.explanations[warning_key])
        
        return analysis