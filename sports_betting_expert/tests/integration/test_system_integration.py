#!/usr/bin/env python3
"""
Tests de integración del sistema de apuestas deportivas.
Incluye tanto tests conceptuales como tests reales de integración.
"""

import os
import sys
import pytest
import datetime

# Añadir el directorio src al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# IMPORTANTE: Aplicar fix de compatibilidad ANTES de importar experta
import collections
import collections.abc

# Fix manual para compatibilidad con Python 3.10+
if not hasattr(collections, 'Mapping'):
    collections.Mapping = collections.abc.Mapping
if not hasattr(collections, 'MutableMapping'):
    collections.MutableMapping = collections.abc.MutableMapping
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable
if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence

print("✅ Fix de compatibilidad aplicado directamente")

try:
    from data_processor import UCLDataProcessor
    from knowledge_model import TeamFact, FactBuilder, BetType, MatchupFact
    IMPORTS_AVAILABLE = True
    print("✅ Importaciones de knowledge_model exitosas")
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    print(f"❌ Error importando módulos: {e}")

class TestKnowledgeModelIntegration:
    """Tests de integración entre knowledge_model.py y data_processor.py"""
    
    @pytest.fixture(scope="class")
    def processor(self):
        """Fixture para inicializar el procesador de datos."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"No se pueden importar los módulos: {IMPORT_ERROR}")
        
        try:
            processor = UCLDataProcessor()
            processor.load_data()
            return processor
        except Exception as e:
            pytest.skip(f"No se pueden cargar los datos: {e}")
    
    @pytest.fixture(scope="class") 
    def teams(self, processor):
        """Fixture para obtener la lista de equipos."""
        return processor.get_teams_list()

    def test_imports_successful(self):
        """Verificar que todas las importaciones son exitosas."""
        assert IMPORTS_AVAILABLE, f"Error de importación: {IMPORT_ERROR if not IMPORTS_AVAILABLE else 'N/A'}"

    def test_data_processor_loads_successfully(self, processor):
        """Verificar que el procesador de datos se inicializa correctamente."""
        assert processor is not None
        assert hasattr(processor, 'data')
        assert len(processor.data) > 0

    def test_team_facts_creation_individual(self, processor, teams):
        """Probar creación de TeamFacts individuales."""
        if not teams:
            pytest.skip("No hay equipos disponibles en el dataset")
        
        test_team = teams[0]
        
        # Obtener summary del procesador
        team_summary = processor.create_team_summary(test_team)
        assert isinstance(team_summary, dict)
        assert 'team' in team_summary
        assert 'attacking_strength' in team_summary
        assert 'defensive_strength' in team_summary
        assert 'overall_strength' in team_summary        # Crear TeamFact desde el summary
        team_fact = FactBuilder.create_team_fact(team_summary)
        assert isinstance(team_fact, TeamFact)
        assert team_fact['team'] == test_team  # Usar acceso tipo diccionario
        assert 0.0 <= team_fact['attacking_strength'] <= 1.0
        assert 0.0 <= team_fact['defensive_strength'] <= 1.0
        assert 0.0 <= team_fact['overall_strength'] <= 1.0
        assert team_fact['goals_per_match'] >= 0
        assert team_fact['team_style'] in ['offensive', 'defensive', 'balanced', 'mixed']

    def test_multiple_team_facts_creation(self, processor, teams):
        """Probar creación de múltiples TeamFacts."""
        if not teams:
            pytest.skip("No hay equipos disponibles en el dataset")
            
        all_team_facts = FactBuilder.create_all_team_facts_from_processor(processor)
        
        assert isinstance(all_team_facts, dict)
        assert len(all_team_facts) > 0
        assert len(all_team_facts) <= len(teams)  # Puede ser menor si algunos fallan
        
        for team_name, fact in all_team_facts.items():
            assert isinstance(fact, TeamFact)
            assert fact['team'] == team_name  # Usar acceso tipo diccionario
            assert 0.0 <= fact['overall_strength'] <= 1.0

    def test_bet_types_only_five_valid(self):
        """Verificar que solo se aceptan los 5 tipos de apuesta válidos."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"No se pueden importar los módulos: {IMPORT_ERROR}")
        
        valid_types = [
            BetType.TYPE_HOME_WIN,
            BetType.TYPE_AWAY_WIN, 
            BetType.TYPE_DRAW,
            BetType.TYPE_OVER,
            BetType.TYPE_UNDER
        ]        # Probar tipos válidos
        for bet_type in valid_types:
            threshold = 2.5 if bet_type in [BetType.TYPE_OVER, BetType.TYPE_UNDER] else None
            bet = BetType.create(bet_type, "Team A", "Team B", threshold=threshold)
            assert bet['bet_type'] == bet_type  # Usar acceso tipo diccionario
            assert bet['home_team'] == "Team A"
            assert bet['away_team'] == "Team B"
        
        # Probar que BTTS es rechazado
        with pytest.raises(ValueError, match="Tipo de apuesta inválido"):
            BetType.create("btts", "Team A", "Team B")

    def test_over_under_default_threshold(self):
        """Verificar que over/under usan threshold por defecto."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"No se pueden importar los módulos: {IMPORT_ERROR}")
          # Sin threshold especificado
        bet_over = BetType.create(BetType.TYPE_OVER, "Team A", "Team B")
        bet_under = BetType.create(BetType.TYPE_UNDER, "Team A", "Team B")
        
        assert bet_over['threshold'] == 2.5  # Usar acceso tipo diccionario
        assert bet_under['threshold'] == 2.5
        
        # Con threshold especificado
        bet_over_custom = BetType.create(BetType.TYPE_OVER, "Team A", "Team B", threshold=3.5)
        assert bet_over_custom['threshold'] == 3.5

    def test_matchup_fact_creation(self, processor, teams):
        """Probar creación de MatchupFact."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"No se pueden importar los módulos: {IMPORT_ERROR}")
        
        if len(teams) < 2:
            pytest.skip("Se necesitan al menos 2 equipos para crear un matchup")
        
        # Crear TeamFacts
        all_team_facts = FactBuilder.create_all_team_facts_from_processor(processor)
        team_names = list(all_team_facts.keys())
        
        if len(team_names) < 2:
            pytest.skip("No se pudieron crear suficientes TeamFacts")
        
        home_team = team_names[0]
        away_team = team_names[1]
        home_fact = all_team_facts[home_team]
        away_fact = all_team_facts[away_team]
          # Crear MatchupFact
        matchup = FactBuilder.create_matchup_fact(home_team, away_team, home_fact, away_fact)
        assert isinstance(matchup, MatchupFact)
        assert matchup['home_team'] == home_team  # Usar acceso tipo diccionario
        assert matchup['away_team'] == away_team
        assert matchup['match_type'] in ['balanced', 'attack_focused', 'defense_focused']
        assert isinstance(matchup['attacking_margin'], float)
        assert isinstance(matchup['defensive_margin'], float)
        assert isinstance(matchup['overall_margin'], float)

    def test_integration_complete_workflow(self, processor, teams):
        """Test de flujo completo de integración."""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"No se pueden importar los módulos: {IMPORT_ERROR}")
        
        if len(teams) < 2:
            pytest.skip("Se necesitan al menos 2 equipos para el flujo completo")
        
        # 1. Crear TeamFacts
        all_team_facts = FactBuilder.create_all_team_facts_from_processor(processor)
        assert len(all_team_facts) > 0
        
        # 2. Crear MatchupFact
        team_names = list(all_team_facts.keys())
        if len(team_names) >= 2:
            home_fact = all_team_facts[team_names[0]]
            away_fact = all_team_facts[team_names[1]]
            matchup = FactBuilder.create_matchup_fact(
                team_names[0], team_names[1], home_fact, away_fact
            )
            assert matchup is not None
        
        # 3. Crear BetTypes para los 5 tipos
        valid_bet_types = [
            BetType.TYPE_HOME_WIN,
            BetType.TYPE_AWAY_WIN,
            BetType.TYPE_DRAW,
            BetType.TYPE_OVER,
            BetType.TYPE_UNDER
        ]
        
        bets = []
        for bet_type in valid_bet_types:
            threshold = 2.5 if bet_type in [BetType.TYPE_OVER, BetType.TYPE_UNDER] else None
            bet = BetType.create(bet_type, team_names[0], team_names[1], threshold=threshold)
            bets.append(bet)
        
        assert len(bets) == 5
        
        # Verificar que el flujo completo funcionó
        print(f"\n✅ Integración completa exitosa:")
        print(f"   - {len(all_team_facts)} TeamFacts creados")
        print(f"   - MatchupFact creado")
        print(f"   - {len(bets)} tipos de apuesta soportados")


# Tests conceptuales - Funcionalidad futura
class TestConceptualBehavior:
    """Tests conceptuales para funcionalidad futura."""

    def test_system_should_classify_match_bet(self):
        """
        Test conceptual: El sistema debe clasificar una apuesta en un partido como 'segura' o 'arriesgada'
        basándose en los datos históricos y variables contextuales.
        """
        # Este test fallará inicialmente hasta que implementemos la funcionalidad
        pytest.skip("Funcionalidad aún no implementada")
        
        # Concepto de cómo debería funcionar
        # match_data = {
        #     'home_team': 'Team A',
        #     'away_team': 'Team B',
        #     'home_form': [1, 1, 0, 1, 1],  # 1=victoria, 0=derrota, 0.5=empate
        #     'away_form': [0, 0, 1, 0, 0],
        #     'home_position': 3,
        #     'away_position': 15,
        #     'importance': 'high',
        #     'bet_type': 'home_win'
        # }
        # 
        # result = betting_advisor.classify_bet(match_data)
        # assert result['classification'] in ['safe', 'risky']
        # assert 'confidence' in result
        # assert 'explanation' in result

    def test_system_should_explain_reasoning(self):
        """
        Test conceptual: El sistema debe explicar su razonamiento para la clasificación,
        mencionando tanto reglas activadas como probabilidades calculadas.
        """
        pytest.skip("Funcionalidad aún no implementada")
        
        # Concepto de cómo debería funcionar
        # match_data = {...}  # Datos del partido
        # 
        # result = betting_advisor.classify_bet(match_data)
        # explanation = result['explanation']
        # 
        # assert isinstance(explanation, str)
        # assert len(explanation) > 0
        # assert "rule:" in explanation.lower() or "probability:" in explanation.lower()

    def test_system_should_handle_missing_data(self):
        """
        Test conceptual: El sistema debe manejar datos faltantes de manera adecuada,
        ya sea estimando valores o indicando la incertidumbre adicional.
        """
        pytest.skip("Funcionalidad aún no implementada")
        
        # Concepto de cómo debería funcionar
        # match_data = {...}  # Datos del partido con algunos valores faltantes
        # 
        # result = betting_advisor.classify_bet(match_data)
        # assert 'data_completeness' in result
        # assert result['data_completeness'] < 1.0  # Indica que faltan datos