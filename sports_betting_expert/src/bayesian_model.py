"""
Red Bayesiana para el sistema experto de apuestas deportivas.
Complementa al motor de reglas con razonamiento probabilístico.
"""
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from typing import Dict, Any, List, Tuple
import numpy as np

class BettingBayesianNetwork:
    """
    Red Bayesiana para predicciones de apuestas deportivas.
    
    ESTRUCTURA DE LA RED:
    
    TeamStrength (Home/Away) -> MatchOutcome
    TeamStyle (Home/Away) -> MatchOutcome  
    GoalsTendency (Home/Away) -> TotalGoals
    MatchOutcome + TotalGoals -> BetRecommendation
    """
    
    def __init__(self):
        """Inicializar la red bayesiana."""
        self.model = None
        self.inference = None
        self._build_network()
        
    def _build_network(self):
        """Construir la estructura y CPDs de la red bayesiana."""
        print("🔨 Construyendo red bayesiana...")
        
        # 1. Definir estructura
        self.model = DiscreteBayesianNetwork([
            # Nodos padre -> Resultado del partido
            ('HomeStrength', 'MatchOutcome'),
            ('AwayStrength', 'MatchOutcome'),
            ('HomeStyle', 'MatchOutcome'),
            ('AwayStyle', 'MatchOutcome'),
            
            # Nodos padre -> Total de goles
            ('HomeGoalsTendency', 'TotalGoals'),
            ('AwayGoalsTendency', 'TotalGoals'),
            
            # Resultado + Goles -> Recomendación final
            ('MatchOutcome', 'HomeWinRecommendation'),
            ('MatchOutcome', 'AwayWinRecommendation'),
            ('MatchOutcome', 'DrawRecommendation'),
            ('TotalGoals', 'OverRecommendation'),
            ('TotalGoals', 'UnderRecommendation')
        ])
        
        # 2. Definir CPDs (Conditional Probability Distributions)
        self._define_cpds()
        
        # 3. Validar modelo
        if self.model.check_model():
            print("✅ Red bayesiana construida correctamente")
            self.inference = VariableElimination(self.model)
        else:
            raise ValueError("❌ Error en la construcción de la red bayesiana")
    
    def _define_cpds(self):
        """Definir todas las distribuciones de probabilidad condicional."""
        
        # CPD para HomeStrength (basado en overall_strength)
        # Estados: ['weak', 'medium', 'strong']
        cpd_home_strength = TabularCPD(
            variable='HomeStrength',
            variable_card=3,
            values=[[0.3], [0.4], [0.3]]  # Prior uniforme ajustado
        )
        
        # CPD para AwayStrength  
        cpd_away_strength = TabularCPD(
            variable='AwayStrength',
            variable_card=3,
            values=[[0.3], [0.4], [0.3]]
        )
        
        # CPD para HomeStyle
        # Estados: ['offensive', 'balanced', 'defensive']
        cpd_home_style = TabularCPD(
            variable='HomeStyle',
            variable_card=3,
            values=[[0.3], [0.4], [0.3]]
        )
        
        # CPD para AwayStyle
        cpd_away_style = TabularCPD(
            variable='AwayStyle', 
            variable_card=3,
            values=[[0.3], [0.4], [0.3]]
        )
        
        # CPD para HomeGoalsTendency
        # Estados: ['low', 'medium', 'high'] (basado en goals_per_match)
        cpd_home_goals = TabularCPD(
            variable='HomeGoalsTendency',
            variable_card=3,
            values=[[0.3], [0.4], [0.3]]
        )
        
        # CPD para AwayGoalsTendency
        cpd_away_goals = TabularCPD(
            variable='AwayGoalsTendency',
            variable_card=3,
            values=[[0.3], [0.4], [0.3]]
        )
        
        # CPD para MatchOutcome (depende de strength y style)
        # Estados: ['home_win', 'draw', 'away_win']
        # Condicionado por: HomeStrength, AwayStrength, HomeStyle, AwayStyle
        cpd_match_outcome = self._create_match_outcome_cpd()
        
        # CPD para TotalGoals (depende de tendencias goleadoras)
        # Estados: ['low', 'medium', 'high'] (correspondiente a under 2.5, around 2.5, over 2.5)
        cpd_total_goals = self._create_total_goals_cpd()
        
        # CPDs para recomendaciones (basadas en match outcome y total goals)
        cpd_home_win_rec = self._create_home_win_recommendation_cpd()
        cpd_away_win_rec = self._create_away_win_recommendation_cpd()
        cpd_draw_rec = self._create_draw_recommendation_cpd()
        cpd_over_rec = self._create_over_recommendation_cpd()
        cpd_under_rec = self._create_under_recommendation_cpd()
        
        # Agregar todas las CPDs al modelo
        self.model.add_cpds(
            cpd_home_strength, cpd_away_strength,
            cpd_home_style, cpd_away_style,
            cpd_home_goals, cpd_away_goals,
            cpd_match_outcome, cpd_total_goals,
            cpd_home_win_rec, cpd_away_win_rec, cpd_draw_rec,
            cpd_over_rec, cpd_under_rec
        )
    
    def _create_match_outcome_cpd(self) -> TabularCPD:
        """Crear CPD para MatchOutcome basado en strengths y styles."""
        # Matriz 3x3x3x3x3 = 243 combinaciones
        # Simplificamos usando lógica experta
        
        values = []
        # Para cada combinación de (HomeStrength, AwayStrength, HomeStyle, AwayStyle)
        for hs in range(3):  # HomeStrength: 0=weak, 1=medium, 2=strong
            for aws in range(3):  # AwayStrength: 0=weak, 1=medium, 2=strong  
                for hst in range(3):  # HomeStyle: 0=offensive, 1=balanced, 2=defensive
                    for ast in range(3):  # AwayStyle: 0=offensive, 1=balanced, 2=defensive
                        
                        # Lógica simplificada para calcular probabilidades
                        home_advantage = 0.1  # Ventaja de jugar en casa
                        
                        # Factor de fuerza (diferencia normalizada)
                        strength_diff = (hs - aws) * 0.2
                        
                        # Factor de estilo (offensive vs defensive bonus)
                        style_bonus = 0.0
                        if hst == 0 and ast == 2:  # home offensive vs away defensive
                            style_bonus = 0.15
                        elif hst == 2 and ast == 0:  # home defensive vs away offensive  
                            style_bonus = -0.1
                        
                        # Probabilidad base de victoria local
                        p_home = 0.4 + home_advantage + strength_diff + style_bonus
                        
                        # Ajustar probabilidades para que sumen 1
                        p_home = max(0.1, min(0.8, p_home))
                        p_away = max(0.1, min(0.6, 0.3 - strength_diff * 0.5))
                        p_draw = 1.0 - p_home - p_away
                        
                        # Asegurar que p_draw sea positivo
                        if p_draw < 0.1:
                            p_draw = 0.1
                            total = p_home + p_away + p_draw
                            p_home = p_home / total
                            p_away = p_away / total
                            p_draw = p_draw / total
                        
                        values.append([p_home, p_draw, p_away])
        
        # Convertir a formato requerido por pgmpy
        values_array = np.array(values).T
        
        return TabularCPD(
            variable='MatchOutcome',
            variable_card=3,
            values=values_array,
            evidence=['HomeStrength', 'AwayStrength', 'HomeStyle', 'AwayStyle'],
            evidence_card=[3, 3, 3, 3]
        )
    
    def _create_total_goals_cpd(self) -> TabularCPD:
        """Crear CPD para TotalGoals basado en tendencias goleadoras."""
        values = []
        
        for hg in range(3):  # HomeGoalsTendency: 0=low, 1=medium, 2=high
            for ag in range(3):  # AwayGoalsTendency: 0=low, 1=medium, 2=high
                
                # Lógica: más tendencia goleadora = más probabilidad de over
                goal_factor = (hg + ag) / 4.0  # Normalizado entre 0 y 1
                
                # Probabilidades para [low, medium, high] total goals
                p_low = max(0.1, 0.6 - goal_factor)
                p_high = max(0.1, 0.2 + goal_factor * 0.5)
                p_medium = 1.0 - p_low - p_high
                
                # Normalizar
                total = p_low + p_medium + p_high
                values.append([p_low/total, p_medium/total, p_high/total])
        
        values_array = np.array(values).T
        
        return TabularCPD(
            variable='TotalGoals',
            variable_card=3,
            values=values_array,
            evidence=['HomeGoalsTendency', 'AwayGoalsTendency'],
            evidence_card=[3, 3]
        )
    
    def _create_home_win_recommendation_cpd(self) -> TabularCPD:
        """CPD para recomendación de victoria local."""
        # Estados: ['not_recommended', 'recommended']
        # Condicionado por MatchOutcome: ['home_win', 'draw', 'away_win']
        
        values = [
            [0.1, 0.8, 0.9],  # not_recommended
            [0.9, 0.2, 0.1]   # recommended
        ]
        
        return TabularCPD(
            variable='HomeWinRecommendation',
            variable_card=2,
            values=values,
            evidence=['MatchOutcome'],
            evidence_card=[3]
        )
    
    def _create_away_win_recommendation_cpd(self) -> TabularCPD:
        """CPD para recomendación de victoria visitante."""
        values = [
            [0.9, 0.8, 0.1],  # not_recommended  
            [0.1, 0.2, 0.9]   # recommended
        ]
        
        return TabularCPD(
            variable='AwayWinRecommendation',
            variable_card=2,
            values=values,
            evidence=['MatchOutcome'],
            evidence_card=[3]
        )
    
    def _create_draw_recommendation_cpd(self) -> TabularCPD:
        """CPD para recomendación de empate."""
        values = [
            [0.8, 0.2, 0.8],  # not_recommended
            [0.2, 0.8, 0.2]   # recommended  
        ]
        
        return TabularCPD(
            variable='DrawRecommendation',
            variable_card=2,
            values=values,
            evidence=['MatchOutcome'],
            evidence_card=[3]
        )
    
    def _create_over_recommendation_cpd(self) -> TabularCPD:
        """CPD para recomendación Over 2.5."""
        values = [
            [0.8, 0.5, 0.2],  # not_recommended
            [0.2, 0.5, 0.8]   # recommended
        ]
        
        return TabularCPD(
            variable='OverRecommendation',
            variable_card=2,
            values=values,
            evidence=['TotalGoals'],
            evidence_card=[3]
        )
    
    def _create_under_recommendation_cpd(self) -> TabularCPD:
        """CPD para recomendación Under 2.5."""
        values = [
            [0.2, 0.5, 0.8],  # not_recommended
            [0.8, 0.5, 0.2]   # recommended
        ]
        
        return TabularCPD(
            variable='UnderRecommendation',
            variable_card=2,
            values=values,
            evidence=['TotalGoals'],
            evidence_card=[3]
        )
    
    def predict(self, evidence: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Realizar predicción con la red bayesiana.
        
        Args:
            evidence: Diccionario con evidencia observada
            
        Returns:
            Diccionario con probabilidades de cada recomendación
        """
        if not self.inference:
            raise ValueError("Red bayesiana no inicializada correctamente")
        
        # Convertir evidencia a formato de la red
        network_evidence = self._convert_evidence(evidence)
        
        # Realizar inferencia para cada tipo de recomendación
        recommendations = {}
        
        rec_variables = [
            'HomeWinRecommendation',
            'AwayWinRecommendation', 
            'DrawRecommendation',
            'OverRecommendation',
            'UnderRecommendation'
        ]
        
        for var in rec_variables:
            try:
                result = self.inference.query(variables=[var], evidence=network_evidence)
                probabilities = result.values
                
                # Convertir a formato legible
                rec_type = var.replace('Recommendation', '').lower()
                if rec_type == 'homewin':
                    rec_type = 'home_win'
                elif rec_type == 'awaywin':
                    rec_type = 'away_win'
                
                recommendations[rec_type] = {
                    'not_recommended': float(probabilities[0]),
                    'recommended': float(probabilities[1]),
                    'confidence': 'high' if probabilities[1] > 0.7 else 'medium' if probabilities[1] > 0.5 else 'low'
                }
                
            except Exception as e:
                print(f"⚠️ Error en inferencia para {var}: {e}")
                recommendations[rec_type] = {
                    'not_recommended': 0.5,
                    'recommended': 0.5,
                    'confidence': 'low'
                }
        
        return recommendations
    
    def _convert_evidence(self, evidence: Dict[str, Any]) -> Dict[str, int]:
        """Convertir evidencia del dominio a estados de la red."""
        network_evidence = {}
        
        # Convertir fuerza de equipos
        if 'home_strength' in evidence:
            network_evidence['HomeStrength'] = self._strength_to_state(evidence['home_strength'])
        
        if 'away_strength' in evidence:
            network_evidence['AwayStrength'] = self._strength_to_state(evidence['away_strength'])
        
        # Convertir estilos
        if 'home_style' in evidence:
            network_evidence['HomeStyle'] = self._style_to_state(evidence['home_style'])
            
        if 'away_style' in evidence:
            network_evidence['AwayStyle'] = self._style_to_state(evidence['away_style'])
        
        # Convertir tendencias goleadoras
        if 'home_goals_tendency' in evidence:
            network_evidence['HomeGoalsTendency'] = self._goals_to_state(evidence['home_goals_tendency'])
            
        if 'away_goals_tendency' in evidence:
            network_evidence['AwayGoalsTendency'] = self._goals_to_state(evidence['away_goals_tendency'])
        
        return network_evidence
    
    def _strength_to_state(self, strength: float) -> int:
        """Convertir fuerza numérica a estado categórico."""
        if strength < 0.4:
            return 0  # weak
        elif strength < 0.7:
            return 1  # medium  
        else:
            return 2  # strong
    
    def _style_to_state(self, style: str) -> int:
        """Convertir estilo de juego a estado categórico."""
        style_map = {
            'offensive': 0,
            'balanced': 1,
            'defensive': 2
        }
        return style_map.get(style, 1)  # Default: balanced
    
    def _goals_to_state(self, goals_per_match: float) -> int:
        """Convertir goles por partido a estado categórico."""
        if goals_per_match < 1.5:
            return 0  # low
        elif goals_per_match < 2.5:
            return 1  # medium
        else:
            return 2  # high