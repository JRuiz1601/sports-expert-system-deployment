"""
Tests unitarios para el motor de reglas de apuestas deportivas.
"""
import os
import sys
import unittest
import datetime
from unittest.mock import Mock, patch

# Añadir el directorio src al path para poder importar nuestros módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # tests/
root_dir = os.path.dirname(parent_dir)     # sports_betting_expert/
sys.path.insert(0, root_dir)

# Importar el fix de experta
from src import experta_fix
from src.rules_engine import BettingExpertSystem
from src.knowledge_model import TeamFact, MatchupFact, BetType, BetRecommendationFact


class TestBettingExpertSystem(unittest.TestCase):
    """Tests para la clase BettingExpertSystem."""
    
    def setUp(self):
        """Configurar el sistema experto para cada test."""
        self.expert_system = BettingExpertSystem()
        self.expert_system.reset()  # Evitar warning de experta
        
        # Crear facts de ejemplo para pruebas
        self.strong_home_team = TeamFact(
            team="Real Madrid",
            attacking_strength=0.75,
            defensive_strength=0.65,
            overall_strength=0.70,
            goals_per_match=2.8,
            goals_conceded_per_match=1.1,
            goal_difference_per_match=1.7,
            team_style="offensive",
            discipline_rating=0.80,
            cleansheet_rate=0.35,
            total_goals=28,
            total_goals_conceded=11,
            matches_played=10,
            wins=7,
            draws=2,
            losses=1
        )
        
        self.weak_away_team = TeamFact(
            team="Getafe",
            attacking_strength=0.35,
            defensive_strength=0.25,
            overall_strength=0.30,
            goals_per_match=0.9,
            goals_conceded_per_match=2.1,
            goal_difference_per_match=-1.2,
            team_style="defensive",
            discipline_rating=0.45,
            cleansheet_rate=0.15,
            total_goals=9,
            total_goals_conceded=21,
            matches_played=10,
            wins=1,
            draws=2,
            losses=7
        )
        
        self.balanced_team_1 = TeamFact(
            team="Atletico Madrid",
            attacking_strength=0.52,
            defensive_strength=0.58,
            overall_strength=0.55,
            goals_per_match=1.6,
            goals_conceded_per_match=1.2,
            goal_difference_per_match=0.4,
            team_style="balanced",
            discipline_rating=0.85,
            cleansheet_rate=0.45,
            total_goals=16,
            total_goals_conceded=12,
            matches_played=10,
            wins=4,
            draws=5,
            losses=1
        )
        
        self.balanced_team_2 = TeamFact(
            team="Sevilla",
            attacking_strength=0.48,
            defensive_strength=0.55,
            overall_strength=0.52,
            goals_per_match=1.5,
            goals_conceded_per_match=1.3,
            goal_difference_per_match=0.2,
            team_style="balanced",
            discipline_rating=0.78,
            cleansheet_rate=0.40,
            total_goals=15,
            total_goals_conceded=13,
            matches_played=10,
            wins=4,
            draws=4,
            losses=2
        )


class TestHomeWinRules(TestBettingExpertSystem):
    """Tests específicos para las reglas de victoria local."""
    
    def test_clear_favorite_home_win_high_confidence(self):
        """Test regla: favorito claro local con alta confianza."""
        # Crear matchup donde local es favorito claro con gran margen
        matchup = MatchupFact(
            home_team="Real Madrid",
            away_team="Getafe",
            clear_favorite="Real Madrid",
            overall_margin=0.35,  # 35% de ventaja -> alta confianza
            attacking_advantage="Real Madrid",
            attacking_margin=0.40,
            defensive_advantage="Real Madrid",
            defensive_margin=0.40,
            match_type="attack_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Real Madrid",
            away_team="Getafe"
        )
        
        # Ejecutar motor de reglas
        self.expert_system.declare(self.strong_home_team)
        self.expert_system.declare(self.weak_away_team)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        # Verificar resultados
        recommendations = self.expert_system.get_recommendations()
        self.assertGreater(len(recommendations), 0, "Debería generar al menos una recomendación")
        
        home_win_recs = [r for r in recommendations if r['bet_type'] == 'home_win']
        self.assertGreater(len(home_win_recs), 0, "Debería recomendar victoria local")
        
        # Buscar la recomendación específica de ClearFavoriteHomeWin
        clear_fav_rec = None
        for rec in home_win_recs:
            if 'ClearFavoriteHomeWin' in rec['rules_fired']:
                clear_fav_rec = rec
                break
        
        self.assertIsNotNone(clear_fav_rec, "Debería activar la regla ClearFavoriteHomeWin")
        self.assertEqual(clear_fav_rec['recommendation'], 'recommended')
        self.assertEqual(clear_fav_rec['confidence'], 'high', "Debería tener alta confianza con margen > 0.25")
        self.assertIn('ClearFavoriteHomeWin', clear_fav_rec['rules_fired'])
    
    def test_clear_favorite_home_win_medium_confidence(self):
        """Test regla: favorito claro local con confianza media."""
        matchup = MatchupFact(
            home_team="Real Madrid",
            away_team="Getafe",
            clear_favorite="Real Madrid",
            overall_margin=0.18,  # 18% de ventaja -> confianza media
            attacking_advantage="Real Madrid",
            attacking_margin=0.20,
            defensive_advantage="Real Madrid",
            defensive_margin=0.15,
            match_type="balanced"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Real Madrid",
            away_team="Getafe"
        )
        
        self.expert_system.declare(self.strong_home_team)
        self.expert_system.declare(self.weak_away_team)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        home_win_recs = [r for r in recommendations if r['bet_type'] == 'home_win']
        self.assertGreater(len(home_win_recs), 0)
        
        # Buscar la recomendación específica de ClearFavoriteHomeWin
        clear_fav_rec = None
        for rec in home_win_recs:
            if 'ClearFavoriteHomeWin' in rec['rules_fired']:
                clear_fav_rec = rec
                break
        
        self.assertIsNotNone(clear_fav_rec, "Debería activar la regla ClearFavoriteHomeWin")
        self.assertEqual(clear_fav_rec['confidence'], 'medium', "Debería tener confianza media con margen < 0.25")
    
    def test_strong_home_attack_vs_weak_away_defense(self):
        """Test regla: ataque local fuerte vs defensa visitante débil."""
        # Crear equipos que activen esta regla específica
        strong_attack_home = TeamFact(
            team="Ajax",
            attacking_strength=0.75,  # > 0.59 ✓
            defensive_strength=0.50,
            overall_strength=0.62,
            goals_per_match=2.8,      # > 1.67 ✓
            goals_conceded_per_match=1.3,
            goal_difference_per_match=1.5,
            team_style="offensive",
            discipline_rating=0.70,
            cleansheet_rate=0.30,
            total_goals=28,
            total_goals_conceded=13,
            matches_played=10,
            wins=6,
            draws=2,
            losses=2
        )
        
        weak_defense_away = TeamFact(
            team="Club Brugge",
            attacking_strength=0.40,
            defensive_strength=0.28,  # < 0.32 ✓
            overall_strength=0.34,
            goals_per_match=1.2,
            goals_conceded_per_match=2.5,  # > 1.3 ✓
            goal_difference_per_match=-1.3,
            team_style="balanced",
            discipline_rating=0.65,
            cleansheet_rate=0.10,
            total_goals=12,
            total_goals_conceded=25,
            matches_played=10,
            wins=2,
            draws=1,
            losses=7
        )
        
        matchup = MatchupFact(
            home_team="Ajax",
            away_team="Club Brugge",
            clear_favorite="Ajax",
            overall_margin=0.28,
            attacking_advantage="Ajax",  # attacking_advantage == home_team ✓
            attacking_margin=0.35,
            defensive_advantage="Ajax",
            defensive_margin=0.22,
            match_type="attack_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Ajax",
            away_team="Club Brugge"
        )
        
        self.expert_system.declare(strong_attack_home)
        self.expert_system.declare(weak_defense_away)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        home_win_recs = [r for r in recommendations if r['bet_type'] == 'home_win']
        self.assertGreater(len(home_win_recs), 0)
        
        # Buscar la recomendación específica de esta regla
        attack_vs_defense_rec = None
        for rec in home_win_recs:
            if 'StrongHomeAttackVsWeakAwayDefense' in rec['rules_fired']:
                attack_vs_defense_rec = rec
                break
        
        self.assertIsNotNone(attack_vs_defense_rec, "Debería activar la regla StrongHomeAttackVsWeakAwayDefense")
        self.assertEqual(attack_vs_defense_rec['recommendation'], 'recommended')
    
    def test_offensive_home_vs_defensive_away(self):
        """Test regla: estilo ofensivo local vs defensivo visitante."""
        offensive_home = TeamFact(
            team="Liverpool",
            attacking_strength=0.72,
            defensive_strength=0.58,
            overall_strength=0.65,
            goals_per_match=2.4,
            goals_conceded_per_match=1.2,
            goal_difference_per_match=1.2,
            team_style="offensive",  # offensive ✓
            discipline_rating=0.75,
            cleansheet_rate=0.35,
            total_goals=24,
            total_goals_conceded=12,
            matches_played=10,
            wins=6,
            draws=3,
            losses=1
        )
        
        defensive_away = TeamFact(
            team="Atletico Madrid",
            attacking_strength=0.45,
            defensive_strength=0.65,
            overall_strength=0.52,  # home_strength > away_strength + 0.1 ✓
            goals_per_match=1.3,
            goals_conceded_per_match=0.8,
            goal_difference_per_match=0.5,
            team_style="defensive",  # defensive ✓
            discipline_rating=0.88,
            cleansheet_rate=0.55,
            total_goals=13,
            total_goals_conceded=8,
            matches_played=10,
            wins=4,
            draws=5,
            losses=1
        )
        
        matchup = MatchupFact(
            home_team="Liverpool",
            away_team="Atletico Madrid",
            clear_favorite="Liverpool",
            overall_margin=0.13,
            attacking_advantage="Liverpool",
            attacking_margin=0.27,
            defensive_advantage="Atletico Madrid",
            defensive_margin=0.07,
            match_type="balanced"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Liverpool",
            away_team="Atletico Madrid"
        )
        
        self.expert_system.declare(offensive_home)
        self.expert_system.declare(defensive_away)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        home_win_recs = [r for r in recommendations if r['bet_type'] == 'home_win']
        
        # Buscar la recomendación específica de esta regla
        style_advantage_rec = None
        for rec in home_win_recs:
            if 'OffensiveHomeVsDefensiveAway' in rec['rules_fired']:
                style_advantage_rec = rec
                break
        
        self.assertIsNotNone(style_advantage_rec, "Debería activar la regla OffensiveHomeVsDefensiveAway")
        self.assertEqual(style_advantage_rec['recommendation'], 'recommended')


class TestAwayWinRules(TestBettingExpertSystem):
    """Tests específicos para las reglas de victoria visitante."""
    
    def test_clear_favorite_away_win(self):
        """Test regla: favorito claro visitante."""
        matchup = MatchupFact(
            home_team="Getafe",
            away_team="Real Madrid",
            clear_favorite="Real Madrid",  # Visitante es favorito ✓
            overall_margin=0.32,  # > 0.3 -> alta confianza
            attacking_advantage="Real Madrid",
            attacking_margin=0.40,
            defensive_advantage="Real Madrid",
            defensive_margin=0.40,
            match_type="attack_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_AWAY_WIN,
            home_team="Getafe",
            away_team="Real Madrid"
        )
        
        self.expert_system.declare(self.weak_away_team)  # Getafe como local
        self.expert_system.declare(self.strong_home_team)  # Real Madrid como visitante
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        away_win_recs = [r for r in recommendations if r['bet_type'] == 'away_win']
        self.assertGreater(len(away_win_recs), 0, "Debería recomendar victoria visitante")
        
        # Buscar la recomendación específica de ClearFavoriteAwayWin
        clear_fav_away_rec = None
        for rec in away_win_recs:
            if 'ClearFavoriteAwayWin' in rec['rules_fired']:
                clear_fav_away_rec = rec
                break
        
        self.assertIsNotNone(clear_fav_away_rec, "Debería activar la regla ClearFavoriteAwayWin")
        self.assertEqual(clear_fav_away_rec['recommendation'], 'recommended')
        self.assertEqual(clear_fav_away_rec['confidence'], 'high')
        self.assertIn('ClearFavoriteAwayWin', clear_fav_away_rec['rules_fired'])
    
    def test_dominant_away_team(self):
        """Test regla: visitante dominante en ambas fases."""
        dominant_away = TeamFact(
            team="Manchester City",
            attacking_strength=0.78,  # > 0.72 ✓
            defensive_strength=0.68,  # > 0.44 ✓
            overall_strength=0.73,
            goals_per_match=2.9,
            goals_conceded_per_match=0.8,
            goal_difference_per_match=2.1,
            team_style="offensive",
            discipline_rating=0.82,
            cleansheet_rate=0.50,
            total_goals=29,
            total_goals_conceded=8,
            matches_played=10,
            wins=8,
            draws=1,
            losses=1
        )
        
        weaker_home = TeamFact(
            team="Brighton",
            attacking_strength=0.42,
            defensive_strength=0.38,
            overall_strength=0.40,  # away_overall > home_overall + 0.12 ✓
            goals_per_match=1.4,
            goals_conceded_per_match=1.8,
            goal_difference_per_match=-0.4,
            team_style="balanced",
            discipline_rating=0.70,
            cleansheet_rate=0.25,
            total_goals=14,
            total_goals_conceded=18,
            matches_played=10,
            wins=3,
            draws=3,
            losses=4
        )
        
        matchup = MatchupFact(
            home_team="Brighton",
            away_team="Manchester City",
            clear_favorite="Manchester City",
            overall_margin=0.33,
            attacking_advantage="Manchester City",
            attacking_margin=0.36,
            defensive_advantage="Manchester City",
            defensive_margin=0.30,
            match_type="attack_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_AWAY_WIN,
            home_team="Brighton",
            away_team="Manchester City"
        )
        
        self.expert_system.declare(weaker_home)
        self.expert_system.declare(dominant_away)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        away_win_recs = [r for r in recommendations if r['bet_type'] == 'away_win']
        
        # Buscar la recomendación específica de esta regla
        dominant_rec = None
        for rec in away_win_recs:
            if 'DominantAwayTeam' in rec['rules_fired']:
                dominant_rec = rec
                break
        
        self.assertIsNotNone(dominant_rec, "Debería activar la regla DominantAwayTeam")
        self.assertEqual(dominant_rec['recommendation'], 'recommended')


class TestDrawRules(TestBettingExpertSystem):
    """Tests específicos para las reglas de empate."""
    
    def test_balanced_defensive_teams_draw(self):
        """Test regla: equipos equilibrados y defensivos."""
        defensive_team_1 = TeamFact(
            team="Atletico Madrid",
            attacking_strength=0.48,
            defensive_strength=0.62,  # > 0.44 ✓
            overall_strength=0.55,
            goals_per_match=1.4,
            goals_conceded_per_match=0.9,
            goal_difference_per_match=0.5,
            team_style="defensive",
            discipline_rating=0.85,
            cleansheet_rate=0.50,  # Combined > 0.4 ✓
            total_goals=14,
            total_goals_conceded=9,
            matches_played=10,
            wins=4,
            draws=5,
            losses=1
        )
        
        defensive_team_2 = TeamFact(
            team="Juventus",
            attacking_strength=0.45,
            defensive_strength=0.58,  # > 0.44 ✓
            overall_strength=0.52,
            goals_per_match=1.3,
            goals_conceded_per_match=1.0,
            goal_difference_per_match=0.3,
            team_style="defensive",
            discipline_rating=0.82,
            cleansheet_rate=0.45,  # Combined > 0.4 ✓
            total_goals=13,
            total_goals_conceded=10,
            matches_played=10,
            wins=4,
            draws=4,
            losses=2
        )
        
        matchup = MatchupFact(
            home_team="Atletico Madrid",
            away_team="Juventus",
            clear_favorite="",  # Sin favorito claro
            overall_margin=0.03,  # < 0.10 ✓
            attacking_advantage="Atletico Madrid",
            attacking_margin=0.03,
            defensive_advantage="Atletico Madrid",
            defensive_margin=0.04,
            match_type="defense_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_DRAW,
            home_team="Atletico Madrid",
            away_team="Juventus"
        )
        
        self.expert_system.declare(defensive_team_1)
        self.expert_system.declare(defensive_team_2)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        draw_recs = [r for r in recommendations if r['bet_type'] == 'draw']
        
        # Buscar la recomendación específica de esta regla
        balanced_def_rec = None
        for rec in draw_recs:
            if 'BalancedDefensiveTeamsDraw' in rec['rules_fired']:
                balanced_def_rec = rec
                break
        
        self.assertIsNotNone(balanced_def_rec, "Debería activar la regla BalancedDefensiveTeamsDraw")
        self.assertEqual(balanced_def_rec['recommendation'], 'recommended')
    
    def test_disciplined_balanced_teams_draw(self):
        """Test regla: equipos disciplinados y equilibrados."""
        disciplined_team_1 = TeamFact(
            team="Real Sociedad",
            attacking_strength=0.52,
            defensive_strength=0.55,
            overall_strength=0.54,
            goals_per_match=1.6,
            goals_conceded_per_match=1.4,
            goal_difference_per_match=0.2,  # < 0.3 ✓
            team_style="balanced",
            discipline_rating=0.88,  # > 0.74 ✓
            cleansheet_rate=0.35,
            total_goals=16,
            total_goals_conceded=14,
            matches_played=10,
            wins=4,
            draws=4,
            losses=2
        )
        
        disciplined_team_2 = TeamFact(
            team="Valencia",
            attacking_strength=0.49,
            defensive_strength=0.52,
            overall_strength=0.51,
            goals_per_match=1.5,
            goals_conceded_per_match=1.3,
            goal_difference_per_match=0.2,  # < 0.3 ✓
            team_style="balanced",
            discipline_rating=0.85,  # > 0.74 ✓
            cleansheet_rate=0.40,
            total_goals=15,
            total_goals_conceded=13,
            matches_played=10,
            wins=4,
            draws=5,
            losses=1
        )
        
        matchup = MatchupFact(
            home_team="Real Sociedad",
            away_team="Valencia",
            clear_favorite="",
            overall_margin=0.03,
            attacking_advantage="Real Sociedad",
            attacking_margin=0.03,
            defensive_advantage="Real Sociedad",
            defensive_margin=0.03,
            match_type="balanced"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_DRAW,
            home_team="Real Sociedad",
            away_team="Valencia"
        )
        
        self.expert_system.declare(disciplined_team_1)
        self.expert_system.declare(disciplined_team_2)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        draw_recs = [r for r in recommendations if r['bet_type'] == 'draw']
        
        # Buscar la recomendación específica de esta regla
        disciplined_rec = None
        for rec in draw_recs:
            if 'DisciplinedBalancedTeamsDraw' in rec['rules_fired']:
                disciplined_rec = rec
                break
        
        self.assertIsNotNone(disciplined_rec, "Debería activar la regla DisciplinedBalancedTeamsDraw")
        self.assertEqual(disciplined_rec['recommendation'], 'recommended')


class TestOverUnderRules(TestBettingExpertSystem):
    """Tests específicos para las reglas Over/Under."""
    
    def test_offensive_teams_over(self):
        """Test regla: equipos ofensivos para Over."""
        offensive_team_1 = TeamFact(
            team="Ajax",
            attacking_strength=0.82,  # > 0.59 ✓
            defensive_strength=0.45,
            overall_strength=0.64,
            goals_per_match=2.8,  # Combined > threshold + 0.3 ✓
            goals_conceded_per_match=1.5,
            goal_difference_per_match=1.3,
            team_style="offensive",
            discipline_rating=0.72,
            cleansheet_rate=0.25,
            total_goals=28,
            total_goals_conceded=15,
            matches_played=10,
            wins=7,
            draws=2,
            losses=1
        )
        
        offensive_team_2 = TeamFact(
            team="Atalanta",
            attacking_strength=0.76,  # > 0.59 ✓
            defensive_strength=0.42,
            overall_strength=0.59,
            goals_per_match=2.3,  # Combined > threshold + 0.3 ✓
            goals_conceded_per_match=1.8,
            goal_difference_per_match=0.5,
            team_style="offensive",
            discipline_rating=0.68,
            cleansheet_rate=0.20,
            total_goals=23,
            total_goals_conceded=18,
            matches_played=10,
            wins=6,
            draws=2,
            losses=2
        )
        
        matchup = MatchupFact(
            home_team="Ajax",
            away_team="Atalanta",
            clear_favorite="Ajax",
            overall_margin=0.05,
            attacking_advantage="Ajax",
            attacking_margin=0.06,
            defensive_advantage="Ajax",
            defensive_margin=0.03,
            match_type="attack_focused"  # attack_focused ✓
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_OVER,
            home_team="Ajax",
            away_team="Atalanta",
            threshold=2.5
        )
        
        self.expert_system.declare(offensive_team_1)
        self.expert_system.declare(offensive_team_2)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        over_recs = [r for r in recommendations if r['bet_type'] == 'over']
        
        # Buscar la recomendación específica de esta regla
        offensive_over_rec = None
        for rec in over_recs:
            if 'OffensiveTeamsOver' in rec['rules_fired']:
                offensive_over_rec = rec
                break
        
        self.assertIsNotNone(offensive_over_rec, "Debería activar la regla OffensiveTeamsOver")
        self.assertEqual(offensive_over_rec['recommendation'], 'recommended')
    
    def test_strong_defenses_under(self):
        """Test regla: defensas fuertes para Under."""
        defensive_team_1 = TeamFact(
            team="Atletico Madrid",
            attacking_strength=0.48,
            defensive_strength=0.68,  # > 0.44 ✓
            overall_strength=0.58,
            goals_per_match=1.2,
            goals_conceded_per_match=0.6,  # < threshold - 0.2 ✓
            goal_difference_per_match=0.6,
            team_style="defensive",
            discipline_rating=0.88,
            cleansheet_rate=0.60,  # Combined > 0.4 ✓
            total_goals=12,
            total_goals_conceded=6,
            matches_played=10,
            wins=5,
            draws=4,
            losses=1
        )
        
        defensive_team_2 = TeamFact(
            team="Inter Milan",
            attacking_strength=0.52,
            defensive_strength=0.65,  # > 0.44 ✓
            overall_strength=0.59,
            goals_per_match=1.4,
            goals_conceded_per_match=0.7,  # < threshold - 0.2 ✓
            goal_difference_per_match=0.7,
            team_style="defensive",
            discipline_rating=0.85,
            cleansheet_rate=0.55,  # Combined > 0.4 ✓
            total_goals=14,
            total_goals_conceded=7,
            matches_played=10,
            wins=6,
            draws=3,
            losses=1
        )
        
        matchup = MatchupFact(
            home_team="Atletico Madrid",
            away_team="Inter Milan",
            clear_favorite="",
            overall_margin=0.01,
            attacking_advantage="Inter Milan",
            attacking_margin=0.04,
            defensive_advantage="Atletico Madrid",
            defensive_margin=0.03,
            match_type="defense_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_UNDER,
            home_team="Atletico Madrid",
            away_team="Inter Milan",
            threshold=2.5
        )
        
        self.expert_system.declare(defensive_team_1)
        self.expert_system.declare(defensive_team_2)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        under_recs = [r for r in recommendations if r['bet_type'] == 'under']
        
        # Buscar la recomendación específica de esta regla
        strong_def_under_rec = None
        for rec in under_recs:
            if 'StrongDefensesUnder' in rec['rules_fired']:
                strong_def_under_rec = rec
                break
        
        self.assertIsNotNone(strong_def_under_rec, "Debería activar la regla StrongDefensesUnder")
        self.assertEqual(strong_def_under_rec['recommendation'], 'recommended')


class TestWarningRules(TestBettingExpertSystem):
    """Tests específicos para las reglas de advertencia."""
    
    def test_low_discipline_warning(self):
        """Test regla: advertencia por baja disciplina."""
        disciplined_team = TeamFact(
            team="Bayern Munich",
            attacking_strength=0.75,
            defensive_strength=0.68,
            overall_strength=0.72,
            goals_per_match=2.5,
            goals_conceded_per_match=1.0,
            goal_difference_per_match=1.5,
            team_style="offensive",
            discipline_rating=0.85,  # Alta disciplina
            cleansheet_rate=0.45,
            total_goals=25,
            total_goals_conceded=10,
            matches_played=10,
            wins=7,
            draws=2,
            losses=1
        )
        
        undisciplined_team = TeamFact(
            team="Napoli",
            attacking_strength=0.68,
            defensive_strength=0.52,
            overall_strength=0.60,
            goals_per_match=2.1,
            goals_conceded_per_match=1.4,
            goal_difference_per_match=0.7,
            team_style="offensive",
            discipline_rating=0.45,  # < 0.52 ✓ Baja disciplina
            cleansheet_rate=0.30,
            total_goals=21,
            total_goals_conceded=14,
            matches_played=10,
            wins=5,
            draws=3,
            losses=2
        )
        
        matchup = MatchupFact(
            home_team="Bayern Munich",
            away_team="Napoli",
            clear_favorite="Bayern Munich",
            overall_margin=0.12,
            attacking_advantage="Bayern Munich",
            attacking_margin=0.07,
            defensive_advantage="Bayern Munich",
            defensive_margin=0.16,
            match_type="balanced"
        )
        
        # No declaramos BetType porque solo queremos probar la advertencia
        self.expert_system.declare(disciplined_team)
        self.expert_system.declare(undisciplined_team)
        self.expert_system.declare(matchup)
        self.expert_system.run()
        
        explanations = self.expert_system.get_explanations()
        warning_key = "Bayern Munich_vs_Napoli_discipline_warning"
        
        self.assertIn(warning_key, explanations, "Debería generar advertencia por baja disciplina")
        warning_text = explanations[warning_key]
        self.assertIn("Napoli", warning_text, "La advertencia debería mencionar al equipo indisciplinado")
        self.assertIn("disciplina muy baja", warning_text)


class TestUtilityMethods(TestBettingExpertSystem):
    """Tests para los métodos de utilidad del sistema experto."""
    
    def test_reset_method(self):
        """Test del método reset."""
        # Generar algunas recomendaciones primero
        matchup = MatchupFact(
            home_team="Real Madrid",
            away_team="Barcelona",
            clear_favorite="Real Madrid",
            overall_margin=0.15,
            attacking_advantage="Real Madrid",
            attacking_margin=0.10,
            defensive_advantage="Real Madrid",
            defensive_margin=0.05,
            match_type="balanced"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Real Madrid",
            away_team="Barcelona"
        )
        
        self.expert_system.declare(self.strong_home_team)
        self.expert_system.declare(self.weak_away_team)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        # Verificar que hay datos
        self.assertGreater(len(self.expert_system.get_recommendations()), 0)
        
        # Resetear
        self.expert_system.reset()
        
        # Verificar que todo se limpió
        self.assertEqual(len(self.expert_system.get_recommendations()), 0)
        self.assertEqual(len(self.expert_system.get_explanations()), 0)
        self.assertEqual(len(self.expert_system.get_rules_fired_summary()), 0)
    
    def test_get_betting_analysis(self):
        """Test del método get_betting_analysis."""
        # Configurar enfrentamiento
        matchup = MatchupFact(
            home_team="Real Madrid",
            away_team="Barcelona",
            clear_favorite="Real Madrid",
            overall_margin=0.20,
            attacking_advantage="Real Madrid",
            attacking_margin=0.15,
            defensive_advantage="Real Madrid",
            defensive_margin=0.10,
            match_type="attack_focused"
        )
        
        # Declarar varios tipos de apuesta
        bet_types = [
            BetType(bet_type=BetType.TYPE_HOME_WIN, home_team="Real Madrid", away_team="Barcelona"),
            BetType(bet_type=BetType.TYPE_AWAY_WIN, home_team="Real Madrid", away_team="Barcelona"),
            BetType(bet_type=BetType.TYPE_OVER, home_team="Real Madrid", away_team="Barcelona", threshold=2.5)
        ]
        
        self.expert_system.declare(self.strong_home_team)
        self.expert_system.declare(self.weak_away_team)
        self.expert_system.declare(matchup)
        for bet in bet_types:
            self.expert_system.declare(bet)
        self.expert_system.run()
        
        # Obtener análisis
        analysis = self.expert_system.get_betting_analysis("Real Madrid", "Barcelona")
        
        # Verificar estructura del análisis
        self.assertIn('match', analysis)
        self.assertIn('recommendations_by_type', analysis)
        self.assertIn('summary', analysis)
        self.assertIn('warnings', analysis)
        
        self.assertEqual(analysis['match'], "Real Madrid vs Barcelona")
        self.assertIsInstance(analysis['recommendations_by_type'], dict)
        self.assertIsInstance(analysis['summary'], dict)
        self.assertIsInstance(analysis['warnings'], list)
        
        # Verificar que el summary tiene los campos correctos
        summary = analysis['summary']
        self.assertIn('total_recommendations', summary)
        self.assertIn('high_confidence', summary)
        self.assertIn('medium_confidence', summary)
        self.assertIn('low_confidence', summary)
    
    def test_rules_fired_count(self):
        """Test del tracking de reglas activadas."""
        # Configurar para activar múltiples reglas
        matchup = MatchupFact(
            home_team="Real Madrid",
            away_team="Getafe",
            clear_favorite="Real Madrid",
            overall_margin=0.35,
            attacking_advantage="Real Madrid",
            attacking_margin=0.40,
            defensive_advantage="Real Madrid",
            defensive_margin=0.40,
            match_type="attack_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Real Madrid",
            away_team="Getafe"
        )
        
        self.expert_system.declare(self.strong_home_team)
        self.expert_system.declare(self.weak_away_team)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        rules_summary = self.expert_system.get_rules_fired_summary()
        
        # Verificar que se registraron reglas activadas
        self.assertIsInstance(rules_summary, dict)
        if len(rules_summary) > 0:
            # Verificar que los valores son conteos válidos
            for rule_name, count in rules_summary.items():
                self.assertIsInstance(rule_name, str)
                self.assertIsInstance(count, int)
                self.assertGreater(count, 0)
    
    def test_probability_calculation(self):
        """Test del cálculo de probabilidades basado en confianza."""
        matchup = MatchupFact(
            home_team="Real Madrid",
            away_team="Getafe",
            clear_favorite="Real Madrid",
            overall_margin=0.35,  # Alta confianza
            attacking_advantage="Real Madrid",
            attacking_margin=0.40,
            defensive_advantage="Real Madrid",
            defensive_margin=0.40,
            match_type="attack_focused"
        )
        
        bet_type = BetType(
            bet_type=BetType.TYPE_HOME_WIN,
            home_team="Real Madrid",
            away_team="Getafe"
        )
        
        self.expert_system.declare(self.strong_home_team)
        self.expert_system.declare(self.weak_away_team)
        self.expert_system.declare(matchup)
        self.expert_system.declare(bet_type)
        self.expert_system.run()
        
        recommendations = self.expert_system.get_recommendations()
        if len(recommendations) > 0:
            rec = recommendations[0]
            
            # Verificar que tiene probabilidad
            self.assertIn('probability', rec)
            self.assertIsInstance(rec['probability'], float)
            self.assertGreaterEqual(rec['probability'], 0.0)
            self.assertLessEqual(rec['probability'], 1.0)
            
            # Verificar mapeo de confianza a probabilidad
            if rec['confidence'] == 'high':
                self.assertEqual(rec['probability'], 0.75)
            elif rec['confidence'] == 'medium':
                self.assertEqual(rec['probability'], 0.60)
            elif rec['confidence'] == 'low':
                self.assertEqual(rec['probability'], 0.55)


if __name__ == '__main__':
    unittest.main()
