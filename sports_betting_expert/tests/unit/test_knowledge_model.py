"""
Tests para el modelo de conocimiento.
"""
import os
import sys
import unittest
import datetime

# Añadir el directorio src al path para poder importar nuestros módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # tests/
root_dir = os.path.dirname(parent_dir)     # sports_betting_expert/
sys.path.insert(0, root_dir)

# Importar el fix de experta
from src import experta_fix
from src.knowledge_model import TeamFact, MatchupFact, BetType, BetRecommendationFact

class TestTeamFact(unittest.TestCase):
    def test_team_fact_creation(self):
        """Probar la creación de un TeamFact a partir de un diccionario."""
        team_data = {
            'team': 'Real Madrid',
            'attacking_strength': 0.8,
            'defensive_strength': 0.7,
            'overall_strength': 0.75,
            'discipline_rating': 0.6,
            'total_goals': 25
        }
        
        fact = TeamFact.from_dict(team_data)
        
        self.assertEqual(fact['team'], 'Real Madrid')
        self.assertEqual(fact['attacking_strength'], 0.8)
        self.assertEqual(fact['defensive_strength'], 0.7)
        self.assertEqual(fact['overall_strength'], 0.75)
        self.assertEqual(fact['discipline_rating'], 0.6)
        self.assertEqual(fact['total_goals'], 25)
        
    def test_team_fact_missing_fields(self):
        """Probar que se lanza una excepción si faltan campos obligatorios."""
        incomplete_data = {
            'team': 'Barcelona',
            'attacking_strength': 0.9
            # Faltan defensive_strength y overall_strength
        }
        
        with self.assertRaises(ValueError):
            TeamFact.from_dict(incomplete_data)
    
    def test_team_fact_normalization(self):
        """Probar que los valores se normalizan correctamente."""
        team_data = {
            'team': 'Liverpool',
            'attacking_strength': 1.2,  # Debería normalizarse a 1.0
            'defensive_strength': -0.1,  # Debería normalizarse a 0.0
            'overall_strength': 0.65,
            'discipline_rating': 1.5  # Debería normalizarse a 1.0
        }
        
        fact = TeamFact.from_dict(team_data)
        
        self.assertEqual(fact['attacking_strength'], 1.0)
        self.assertEqual(fact['defensive_strength'], 0.0)
        self.assertEqual(fact['discipline_rating'], 1.0)


class TestMatchupFact(unittest.TestCase):
    def test_matchup_fact_creation(self):
        """Probar la creación de un MatchupFact a partir de una comparación."""
        comparison = {
            'teams': ['Real Madrid', 'Barcelona'],
            'attacking_advantage': 'Real Madrid',
            'attacking_advantage_margin': 0.15,
            'defensive_advantage': 'Barcelona',
            'defensive_advantage_margin': 0.05,
            'overall_advantage': 'Real Madrid',
            'overall_advantage_margin': 0.1,
            'clear_favorite': None
        }
        
        fact = MatchupFact.from_comparison(comparison)
        
        self.assertEqual(fact['home_team'], 'Real Madrid')
        self.assertEqual(fact['away_team'], 'Barcelona')
        self.assertEqual(fact['attacking_advantage'], 'Real Madrid')
        self.assertEqual(fact['attacking_margin'], 0.15)
        self.assertEqual(fact['defensive_advantage'], 'Barcelona')
        self.assertEqual(fact['defensive_margin'], 0.05)
        self.assertEqual(fact['overall_advantage'], 'Real Madrid')
        self.assertEqual(fact['overall_margin'], 0.1)
        self.assertIsNone(fact['clear_favorite'])
    
    def test_matchup_fact_missing_teams(self):
        """Probar que se lanza una excepción si faltan equipos."""
        incomplete_comparison = {
            'teams': ['Real Madrid'],  # Falta el segundo equipo
            'attacking_advantage': 'Real Madrid'
        }
        
        with self.assertRaises(ValueError):
            MatchupFact.from_comparison(incomplete_comparison)


class TestBetType(unittest.TestCase):
    def test_bet_type_creation(self):
        """Probar la creación de un BetType."""
        bet = BetType.create(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team='Real Madrid',
            away_team='Barcelona',
            odds=1.8
        )
        
        self.assertEqual(bet['bet_type'], 'home_win')
        self.assertEqual(bet['home_team'], 'Real Madrid')
        self.assertEqual(bet['away_team'], 'Barcelona')
        self.assertEqual(bet['odds'], 1.8)
        self.assertIsNone(bet['threshold'])
    
    def test_over_under_bet_default_threshold(self):
        """Probar que las apuestas over/under usan threshold por defecto si no se proporciona."""
        bet = BetType.create(
            bet_type=BetType.TYPE_OVER,
            home_team='Real Madrid',
            away_team='Barcelona',
            odds=1.9
            # No se proporciona threshold, debería usar 2.5 por defecto
        )
        
        self.assertEqual(bet['threshold'], 2.5)
    
    def test_invalid_bet_type(self):
        """Probar que se lanza una excepción para tipos de apuesta inválidos."""
        with self.assertRaises(ValueError):
            BetType.create(
                bet_type='invalid_type',
                home_team='Real Madrid',
                away_team='Barcelona'
            )


class TestBetRecommendationFact(unittest.TestCase):
    def test_bet_recommendation_creation(self):
        """Probar la creación de un BetRecommendationFact."""
        recommendation = BetRecommendationFact.create(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team='Real Madrid',
            away_team='Barcelona',
            recommendation='recommended',
            confidence=BetRecommendationFact.CONFIDENCE_HIGH,
            probability=0.75,
            explanation='Real Madrid tiene mejor forma general',
            rules_fired=['StrengthAdvantageRule']
        )
        
        self.assertEqual(recommendation['bet_type'], 'home_win')
        self.assertEqual(recommendation['home_team'], 'Real Madrid')
        self.assertEqual(recommendation['away_team'], 'Barcelona')
        self.assertEqual(recommendation['recommendation'], 'recommended')
        self.assertEqual(recommendation['confidence'], 'high')
        self.assertEqual(recommendation['probability'], 0.75)
        self.assertEqual(recommendation['explanation'], 'Real Madrid tiene mejor forma general')
        # Corregido: convertir a lista antes de comparar para manejar el tipo frozenlist
        self.assertEqual(list(recommendation['rules_fired']), ['StrengthAdvantageRule'])
        self.assertIsInstance(recommendation['timestamp'], datetime.datetime)
    
    def test_invalid_confidence(self):
        """Probar que se lanza una excepción para niveles de confianza inválidos."""
        with self.assertRaises(ValueError):
            BetRecommendationFact.create(
                bet_type=BetType.TYPE_HOME_WIN,
                home_team='Real Madrid',
                away_team='Barcelona',
                recommendation='recommended',
                confidence='invalid_confidence'
            )
    
    def test_invalid_recommendation(self):
        """Probar que se lanza una excepción para recomendaciones inválidas."""
        with self.assertRaises(ValueError):
            BetRecommendationFact.create(
                bet_type=BetType.TYPE_HOME_WIN,
                home_team='Real Madrid',
                away_team='Barcelona',
                recommendation='maybe',  # Inválido
                confidence=BetRecommendationFact.CONFIDENCE_MEDIUM
            )


if __name__ == '__main__':
    unittest.main()