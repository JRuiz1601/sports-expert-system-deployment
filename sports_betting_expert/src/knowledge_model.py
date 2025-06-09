"""
Modelo de conocimiento para el sistema experto de apuestas deportivas.
Define los hechos (Facts) que representarán el conocimiento del sistema.
"""
# IMPORTANTE: Aplicar fix de compatibilidad ANTES de importar experta
import collections
import collections.abc

# Fix para Python 3.10+ - experta necesita estos atributos en collections
if not hasattr(collections, 'Mapping'):
    collections.Mapping = collections.abc.Mapping
if not hasattr(collections, 'MutableMapping'):
    collections.MutableMapping = collections.abc.MutableMapping
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable
if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence

from experta import Fact, Field
from typing import Dict, Any, List, Optional, Union
import datetime




class TeamFact(Fact):
    """
    Representa los datos y estadísticas de un equipo.
    Compatible con el output de UCLDataProcessor.create_team_summary().
    """
    # Campos obligatorios
    team = Field(str, mandatory=True)
    attacking_strength = Field(float, mandatory=True)  # Valor entre 0 y 1
    defensive_strength = Field(float, mandatory=True)  # Valor entre 0 y 1
    overall_strength = Field(float, mandatory=True)    # Valor entre 0 y 1
    
    # Métricas de goles (importantes para over/under)
    goals_per_match = Field(float, default=1.5)
    goals_conceded_per_match = Field(float, default=1.0)
    goal_difference_per_match = Field(float, default=0.0)
    
    # Métricas adicionales para las 5 apuestas
    discipline_rating = Field(float, default=0.5)       # Valor entre 0 y 1, más alto = mejor disciplina
    team_style = Field(str, default="balanced")         # offensive, defensive, balanced, mixed
    
    # Campos opcionales para métricas detalladas
    total_goals = Field(int, default=0)
    yellow_cards = Field(int, default=0)
    red_cards = Field(int, default=0)
    cleansheets = Field(int, default=0)
    cleansheet_rate = Field(float, default=0.0)

    # Propiedades para acceso tipo atributo (compatibilidad con experta)
    @property
    def team_name(self) -> str:
        """Acceso al nombre del equipo como atributo."""
        return self['team']
    
    @property
    def attack_strength(self) -> float:
        """Acceso a attacking_strength como atributo.""" 
        return self['attacking_strength']
    
    @property
    def defense_strength(self) -> float:
        """Acceso a defensive_strength como atributo."""
        return self['defensive_strength']
    
    @property
    def total_strength(self) -> float:
        """Acceso a overall_strength como atributo."""
        return self['overall_strength']
    
    @property
    def goals_avg(self) -> float:
        """Acceso a goals_per_match como atributo."""
        return self['goals_per_match']
    
    @property
    def goals_conceded_avg(self) -> float:
        """Acceso a goals_conceded_per_match como atributo."""
        return self['goals_conceded_per_match']
    
    @property
    def goal_diff_avg(self) -> float:
        """Acceso a goal_difference_per_match como atributo."""
        return self['goal_difference_per_match']
    
    @property
    def discipline(self) -> float:
        """Acceso a discipline_rating como atributo."""
        return self['discipline_rating']
    
    @property
    def style(self) -> str:
        """Acceso a team_style como atributo."""
        return self['team_style']

    @classmethod
    def from_team_summary(cls, team_summary: Dict[str, Any]) -> 'TeamFact':
        """
        Crear un TeamFact a partir del summary de UCLDataProcessor.
        
        Args:
            team_summary: Diccionario devuelto por UCLDataProcessor.create_team_summary().
            
        Returns:
            TeamFact con los datos del equipo.
        """
        # Validar campos obligatorios
        required_fields = ['team', 'attacking_strength', 'defensive_strength', 'overall_strength']
        for field in required_fields:
            if field not in team_summary:
                raise ValueError(f"Campo obligatorio '{field}' no está presente en team_summary")
        
        # Normalizar valores entre 0 y 1 si es necesario
        normalized_data = team_summary.copy()
        for field in ['attacking_strength', 'defensive_strength', 'overall_strength', 'discipline_rating']:
            if field in normalized_data and normalized_data[field] is not None:
                normalized_data[field] = max(0.0, min(1.0, float(normalized_data[field])))
        
        # Extraer todos los campos relevantes del summary
        fact_data = {
            'team': normalized_data['team'],
            'attacking_strength': normalized_data['attacking_strength'],
            'defensive_strength': normalized_data['defensive_strength'],
            'overall_strength': normalized_data['overall_strength'],
            'goals_per_match': normalized_data.get('goals_per_match', 1.5),
            'goals_conceded_per_match': normalized_data.get('goals_conceded_per_match', 1.0),
            'goal_difference_per_match': normalized_data.get('goal_difference_per_match', 0.0),
            'discipline_rating': normalized_data.get('discipline_rating', 0.5),
            'team_style': normalized_data.get('team_style', 'balanced'),
            'total_goals': normalized_data.get('total_goals', 0),
            'yellow_cards': normalized_data.get('yellow_cards', 0),
            'red_cards': normalized_data.get('red_cards', 0),
            'cleansheets': normalized_data.get('cleansheets', 0),
            'cleansheet_rate': normalized_data.get('cleansheet_rate', 0.0)
        }
        
        return cls(**fact_data)
    
    @classmethod
    def from_dict(cls, team_dict: Dict[str, Any]) -> 'TeamFact':
        """
        Crear un TeamFact a partir de un diccionario (método de compatibilidad).
        
        Args:
            team_dict: Diccionario con datos del equipo.
            
        Returns:
            TeamFact con los datos del equipo.
        """
        return cls.from_team_summary(team_dict)









class MatchupFact(Fact):
    """
    Representa un enfrentamiento entre dos equipos.
    """
    # Campos obligatorios
    home_team = Field(str, mandatory=True)
    away_team = Field(str, mandatory=True)
      # Ventajas derivadas
    attacking_advantage = Field(str, default="")   # Equipo con ventaja en ataque
    attacking_margin = Field(float, default=0.0)    # Magnitud de la ventaja en ataque
    defensive_advantage = Field(str, default="")   # Equipo con ventaja en defensa
    defensive_margin = Field(float, default=0.0)    # Magnitud de la ventaja en defensa
    overall_advantage = Field(str, default="")     # Equipo con ventaja general
    overall_margin = Field(float, default=0.0)      # Magnitud de la ventaja general
    
    # Clasificación
    clear_favorite = Field(str, default="")         # Equipo favorito claro (si hay)
    match_type = Field(str, default="balanced")     # tipos: "balanced", "attack_focused", "defense_focused"
    
    @classmethod
    def from_comparison(cls, comparison: Dict[str, Any]) -> 'MatchupFact':
        """
        Crear un MatchupFact a partir de una comparación entre equipos.
        
        Args:
            comparison: Diccionario con datos de comparación.
            
        Returns:
            MatchupFact con los datos de la comparación.
        """
        data = comparison.copy()
        
        # Verificar campos obligatorios
        if 'teams' not in data or len(data['teams']) < 2:
            raise ValueError("La comparación debe contener al menos dos equipos")
        
        # Extraer equipos
        home_team = data['teams'][0]
        away_team = data['teams'][1]
          # Crear instancia
        return cls(
            home_team=home_team,
            away_team=away_team,
            attacking_advantage=data.get('attacking_advantage', ""),
            attacking_margin=data.get('attacking_advantage_margin', 0.0),
            defensive_advantage=data.get('defensive_advantage', ""),
            defensive_margin=data.get('defensive_advantage_margin', 0.0),
            overall_advantage=data.get('overall_advantage', ""),
            overall_margin=data.get('overall_advantage_margin', 0.0),
            clear_favorite=data.get('clear_favorite', "")
        )











class BetType(Fact):
    """
    Representa un tipo de apuesta a evaluar.
    Solo soporta los 5 tipos de apuesta requeridos por el sistema.
    """
    TYPE_HOME_WIN = "home_win"
    TYPE_AWAY_WIN = "away_win"
    TYPE_DRAW = "draw"
    TYPE_OVER = "over"
    TYPE_UNDER = "under"
      # Campos obligatorios    bet_type = Field(str, mandatory=True)
    home_team = Field(str, mandatory=True)
    away_team = Field(str, mandatory=True)
      # Campos opcionales - con valores por defecto None para compatibilidad con tests
    odds = Field(float, default=None)  # Cuota ofrecida
    threshold = Field(float, default=None)  # Umbral para over/under
    
    # Propiedades para acceso tipo atributo
    @property
    def type(self) -> str:
        """Acceso al tipo de apuesta como atributo."""
        return self['bet_type']
    
    @property
    def home(self) -> str:
        """Acceso al equipo local como atributo."""
        return self['home_team']
    
    @property
    def away(self) -> str:
        """Acceso al equipo visitante como atributo."""
        return self['away_team']
    
    @property
    def bet_odds(self) -> Optional[float]:
        """Acceso a las cuotas como atributo."""
        return self['odds']
    
    @property
    def goal_threshold(self) -> float:
        """Acceso al threshold para over/under como atributo."""
        return self['threshold']
    
    @classmethod
    def create(cls, bet_type: str, home_team: str, away_team: str, 
               odds: Optional[float] = None, threshold: Optional[float] = None) -> 'BetType':
        """
        Crear una instancia de BetType.
        
        Args:
            bet_type: Tipo de apuesta (home_win, away_win, draw, over, under).
            home_team: Nombre del equipo local.
            away_team: Nombre del equipo visitante.
            odds: Cuota ofrecida por la casa de apuestas.
            threshold: Umbral para apuestas over/under (por defecto 2.5).
            
        Returns:
            BetType con los datos especificados.
        """
        # Validar tipo de apuesta - solo 5 tipos válidos
        valid_types = [cls.TYPE_HOME_WIN, cls.TYPE_AWAY_WIN, cls.TYPE_DRAW, 
                       cls.TYPE_OVER, cls.TYPE_UNDER]
        
        if bet_type not in valid_types:
            raise ValueError(f"Tipo de apuesta inválido: {bet_type}. "
                            f"Debe ser uno de: {', '.join(valid_types)}")
          # Para over/under, usar threshold por defecto si no se proporciona
        if bet_type in [cls.TYPE_OVER, cls.TYPE_UNDER] and threshold is None:
            threshold = 2.5  # Umbral estándar para over/under
        
        # Crear diccionario con campos requeridos
        fact_data = {
            'bet_type': bet_type,
            'home_team': home_team,
            'away_team': away_team
        }
        
        # Agregar campos opcionales solo si no son None
        if odds is not None:
            fact_data['odds'] = odds
        if threshold is not None:
            fact_data['threshold'] = threshold
            
        return cls(**fact_data)











class BetRecommendationFact(Fact):
    """
    Representa una recomendación de apuesta generada por el sistema.
    """
    # Clasificación del nivel de confianza
    CONFIDENCE_HIGH = "high"
    CONFIDENCE_MEDIUM = "medium"
    CONFIDENCE_LOW = "low"
    
    # Campos obligatorios
    bet_type = Field(str, mandatory=True)
    home_team = Field(str, mandatory=True)
    away_team = Field(str, mandatory=True)
    recommendation = Field(str, mandatory=True)  # "recommended" o "not_recommended"
    confidence = Field(str, mandatory=True)  # "high", "medium", "low"
      # Campos opcionales
    probability = Field(float, default=0.5)     # Probabilidad calculada (default 50%)
    explanation = Field(str, default="")        # Explicación de la recomendación
    rules_fired = Field(list, default=list)     # Lista de reglas activadas
    timestamp = Field(datetime.datetime, default=None)
    
    @classmethod
    def create(cls, bet_type: str, home_team: str, away_team: str, 
               recommendation: str, confidence: str, probability: Optional[float] = None,
               explanation: str = "", rules_fired: Optional[List[str]] = None) -> 'BetRecommendationFact':
        """
        Crear una instancia de BetRecommendationFact.
        
        Args:
            bet_type: Tipo de apuesta.
            home_team: Nombre del equipo local.
            away_team: Nombre del equipo visitante.
            recommendation: "recommended" o "not_recommended".
            confidence: Nivel de confianza ("high", "medium", "low").
            probability: Probabilidad calculada.
            explanation: Explicación de la recomendación.
            rules_fired: Lista de reglas que se activaron para esta recomendación.
            
        Returns:
            BetRecommendationFact con los datos especificados.
        """
        if confidence not in [cls.CONFIDENCE_HIGH, cls.CONFIDENCE_MEDIUM, cls.CONFIDENCE_LOW]:
            raise ValueError(f"Nivel de confianza inválido: {confidence}")
            
        if recommendation not in ["recommended", "not_recommended"]:
            raise ValueError(f"Recomendación inválida: {recommendation}")
            
        if rules_fired is None:
            rules_fired = []
            
        return cls(
            bet_type=bet_type, 
            home_team=home_team, 
            away_team=away_team,
            recommendation=recommendation, 
            confidence=confidence,
            probability=probability,
            explanation=explanation,
            rules_fired=rules_fired,
            timestamp=datetime.datetime.now()
        )














class FactBuilder:
    """
    Clase responsable de crear Facts (hechos) a partir de datos procesados.
    Esta clase actúa como el puente entre UCLDataProcessor y el sistema experto.
    """
    
    @staticmethod
    def create_team_fact(team_summary: Dict[str, Any]) -> TeamFact:
        """
        Crear un TeamFact a partir del summary de UCLDataProcessor.
        
        Args:
            team_summary: Diccionario devuelto por UCLDataProcessor.create_team_summary().
            
        Returns:
            TeamFact con los datos del equipo.
        """
        return TeamFact.from_team_summary(team_summary)
    
    @staticmethod
    def create_team_facts_from_processor(processor, team_names: Optional[List[str]] = None) -> Dict[str, TeamFact]:
        """
        Crear TeamFacts para múltiples equipos usando UCLDataProcessor.
        
        Args:
            processor: Instancia de UCLDataProcessor.
            team_names: Lista de nombres de equipos. Si es None, procesa todos.
            
        Returns:
            Diccionario con TeamFacts para cada equipo.
        """
        if team_names is None:
            team_names = processor.get_teams_list()
        
        team_facts = {}
        for team_name in team_names:
            try:
                # Usar create_team_summary() que es el método correcto del procesador
                team_summary = processor.create_team_summary(team_name)
                
                # Crear el TeamFact directamente desde el summary
                team_facts[team_name] = FactBuilder.create_team_fact(team_summary)
                
            except Exception as e:
                print(f"Warning: No se pudo crear TeamFact para {team_name}: {e}")
                # Crear un TeamFact básico como fallback
                team_facts[team_name] = TeamFact(
                    team=team_name,
                    attacking_strength=0.5,
                    defensive_strength=0.5,
                    overall_strength=0.5,
                    goals_per_match=1.5,
                    goals_conceded_per_match=1.0,
                    goal_difference_per_match=0.0
                )
        
        return team_facts
    
    @staticmethod
    def create_all_team_facts_from_processor(processor) -> Dict[str, TeamFact]:
        """
        Crear TeamFacts para todos los equipos en el dataset.
        
        Args:
            processor: Instancia de UCLDataProcessor.
            
        Returns:
            Diccionario con TeamFacts para todos los equipos.
        """
        try:
            # Usar get_all_team_summaries() para obtener todos de una vez
            all_summaries = processor.get_all_team_summaries()
            team_facts = {}
            
            for team_name, summary in all_summaries.items():
                try:
                    team_facts[team_name] = FactBuilder.create_team_fact(summary)
                except Exception as e:
                    print(f"Warning: Error creando TeamFact para {team_name}: {e}")
                    # Fallback básico
                    team_facts[team_name] = TeamFact(
                        team=team_name,
                        attacking_strength=0.5,
                        defensive_strength=0.5,
                        overall_strength=0.5,
                        goals_per_match=1.5,
                        goals_conceded_per_match=1.0,
                        goal_difference_per_match=0.0                    )
            
            return team_facts
            
        except Exception as e:
            print(f"Error obteniendo summaries del procesador: {e}")
            # Fallback: usar método individual
            return FactBuilder.create_team_facts_from_processor(processor)
    
    @staticmethod
    def create_matchup_fact(home_team: str, away_team: str, 
                          home_facts: TeamFact, away_facts: TeamFact) -> MatchupFact:
        """
        Crear un MatchupFact comparando dos TeamFacts.
        
        Args:
            home_team: Nombre del equipo local.
            away_team: Nombre del equipo visitante.
            home_facts: TeamFact del equipo local.
            away_facts: TeamFact del equipo visitante.
            
        Returns:
            MatchupFact con la comparación entre equipos.
        """
        # Calcular ventajas usando acceso tipo diccionario (experta Facts)
        attacking_diff = home_facts['attacking_strength'] - away_facts['attacking_strength']
        defensive_diff = home_facts['defensive_strength'] - away_facts['defensive_strength']
        overall_diff = home_facts['overall_strength'] - away_facts['overall_strength']
          # Determinar ventajas (umbral mínimo del 5% para considerar ventaja)
        attacking_advantage = ""
        if abs(attacking_diff) > 0.05:
            attacking_advantage = home_team if attacking_diff > 0 else away_team
            
        defensive_advantage = ""
        if abs(defensive_diff) > 0.05:
            defensive_advantage = home_team if defensive_diff > 0 else away_team
            
        overall_advantage = ""
        clear_favorite = ""
        if abs(overall_diff) > 0.05:
            overall_advantage = home_team if overall_diff > 0 else away_team
            # Favorito claro si la diferencia es significativa (>15%)
            if abs(overall_diff) > 0.15:
                clear_favorite = overall_advantage
        
        # Determinar tipo de partido basado en estilos y fortalezas
        match_type = "balanced"
        avg_attacking = (home_facts['attacking_strength'] + away_facts['attacking_strength']) / 2
        avg_defensive = (home_facts['defensive_strength'] + away_facts['defensive_strength']) / 2
        
        if avg_attacking > avg_defensive + 0.1:
            match_type = "attack_focused"
        elif avg_defensive > avg_attacking + 0.1:
            match_type = "defense_focused"
        
        # Considerar también los estilos de equipo
        home_style = home_facts['team_style']
        away_style = away_facts['team_style']
        
        if (home_style == "offensive" or away_style == "offensive"):
            if match_type == "balanced":
                match_type = "attack_focused"
        elif (home_style == "defensive" and away_style == "defensive"):
            match_type = "defense_focused"
        
        return MatchupFact(
            home_team=home_team,
            away_team=away_team,
            attacking_advantage=attacking_advantage,
            attacking_margin=abs(attacking_diff),
            defensive_advantage=defensive_advantage,
            defensive_margin=abs(defensive_diff),
            overall_advantage=overall_advantage,
            overall_margin=abs(overall_diff),
            clear_favorite=clear_favorite,
            match_type=match_type
        )