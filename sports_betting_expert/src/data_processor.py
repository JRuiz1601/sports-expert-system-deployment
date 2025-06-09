"""
Módulo refactorizado para procesar los datos de la UEFA Champions League 2021/22.
Responsabilidades ÚNICAMENTE de procesamiento de datos:
- Cargar y limpiar datos CSV
- Agregar estadísticas por equipo
- Calcular métricas básicas de rendimiento
- Devolver diccionarios de Python (NO crea Facts)
"""
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class UCLDataProcessor:
    """
    Clase para procesar datos de la UEFA Champions League 2021/22.
    Se enfoca únicamente en la carga, limpieza y agregación de datos.
    NO crea Facts - solo retorna diccionarios de Python.
    """
    
    def __init__(self, data_path: str = None):
        """
        Inicializar el procesador de datos.
        
        Args:
            data_path: Ruta a los datos. Si es None, se usa la ruta por defecto.
        """
        if data_path is None:
            self.data_path = os.path.join('data', 'raw')
        else:
            self.data_path = data_path
        
        # Para almacenar los dataframes cargados
        self.data = {}
        # Para almacenar datos agregados por equipo
        self.team_data = {}
    
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """
        Cargar todos los archivos CSV del directorio de datos.
        
        Returns:
            Diccionario con los dataframes cargados.
        """
        # Verificar si el directorio existe
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"El directorio {self.data_path} no existe.")
        
        # Listar archivos esperados (mantenemos el nombre original del dataset)
        expected_files = [
            'attacking.csv', 
            'attempts.csv', 
            'defending.csv', 
            'disciplinary.csv', 
            'distributon.csv',  # Mantenemos el nombre original del dataset
            'goalkeeping.csv', 
            'goals.csv', 
            'key_stats.csv'
        ]
        
        # Verificar que todos los archivos necesarios existen
        missing_files = []
        for file in expected_files:
            file_path = os.path.join(self.data_path, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            raise FileNotFoundError(f"Faltan los siguientes archivos: {', '.join(missing_files)}")
          # Cargar cada archivo
        for file in expected_files:
            name = os.path.splitext(file)[0]  # Nombre del archivo sin extensión
            file_path = os.path.join(self.data_path, file)
            
            try:
                df = pd.read_csv(file_path)
                
                # CORRECCIÓN ESPECIAL PARA DISCIPLINARY: Intercambiar columnas red y yellow
                # Los datos originales están mal etiquetados: red=amarillas, yellow=rojas
                if name == 'disciplinary' and 'red' in df.columns and 'yellow' in df.columns:
                    # Intercambiar las columnas para corregir el error del dataset
                    df['red'], df['yellow'] = df['yellow'].copy(), df['red'].copy()
                    print(f"Archivo {file} cargado con corrección de tarjetas (red<->yellow intercambiadas).")
                else:
                    print(f"Archivo {file} cargado correctamente.")
                
                self.data[name] = df
            except Exception as e:
                print(f"Error al cargar {file}: {str(e)}")
        
        return self.data
    
    def get_teams_list(self) -> List[str]:
        """
        Obtener la lista de todos los equipos en el dataset.
        
        Returns:
            Lista de nombres de equipos.
        """
        if not self.data:
            self.load_data()
        
        # Buscar una tabla que contenga nombres de equipos
        teams = set()
        for df in self.data.values():
            if 'club' in df.columns:
                teams.update(df['club'].dropna().unique())
        
        return sorted(list(teams))
    
    def aggregate_team_data(self):
        """
        Agrega los datos por equipo, combinando estadísticas de todos los jugadores.
        
        Returns:
            Diccionario con datos agregados por equipo.
        """
        if not self.data:
            self.load_data()
        
        # Obtener todos los equipos
        teams = self.get_teams_list()
        
        # Inicializar el diccionario de datos por equipo
        self.team_data = {team: {} for team in teams}
        
        # Procesar cada dataset
        for dataset_name, df in self.data.items():
            if 'club' not in df.columns:
                continue
                
            # Identificar columnas numéricas para agregar (excluir serial, nombres, etc.)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col not in ['serial']]
            
            if not numeric_cols:
                continue
                
            # Agregar datos por equipo
            for team in teams:
                team_df = df[df['club'] == team]
                if team_df.empty:
                    continue
                    
                # Calcular suma y promedio de estadísticas
                sum_stats = team_df[numeric_cols].sum().to_dict()
                mean_stats = team_df[numeric_cols].mean().to_dict()
                  # Guardar en el diccionario de equipos
                self.team_data[team][dataset_name] = {
                    'sum': sum_stats,
                    'mean': mean_stats,
                    'player_count': len(team_df)                }
        
        return self.team_data
    
    def calculate_team_attack_strength(self, team: str) -> float:
        """
        Calcula la fortaleza de ataque de un equipo basándose en datos reales.
        CORREGIDO: Usa el método correcto para calcular estadísticas del equipo.
        
        Combina múltiples métricas:
        - Goles por partido (corregido)
        - Intentos totales y precisión (on_target)
        - Asistencias y regates
        
        Args:
            team: Nombre del equipo.
            
        Returns:
            Valor normalizado de fortaleza de ataque (0.0 a 1.0).
        """
        if not self.data:
            self.load_data()
            
        # Verificar si el equipo existe en los datos
        team_exists = False
        for dataset_name in ['goals', 'attempts', 'attacking', 'key_stats']:
            if dataset_name in self.data:
                if not self.data[dataset_name][self.data[dataset_name]['club'] == team].empty:
                    team_exists = True
                    break
        
        if not team_exists:
            return 0.5  # Valor por defecto si el equipo no existe
            
        attack_score = 0.0
        components = []
        
        # 1. GOLES: Métrica más importante (peso 40%)
        goals_per_match = self.calculate_goals_per_match_avg(team)
        # Normalizar: 0-3 goles por partido -> 0.0-1.0
        goals_component = min(goals_per_match / 3.0, 1.0)
        components.append(('goals_per_match', goals_component, 0.4))
        
        # Bonus por eficiencia en el área
        if 'goals' in self.data:
            team_goals_df = self.data['goals'][self.data['goals']['club'] == team]
            if not team_goals_df.empty:
                total_goals = team_goals_df['goals'].sum()
                inside_area = team_goals_df['inside_area'].sum()
                if total_goals > 0:
                    area_efficiency = inside_area / total_goals
                    efficiency_bonus = area_efficiency * 0.1  # Máximo 10% bonus
                    components.append(('area_efficiency', efficiency_bonus, 0.1))
        
        # 2. INTENTOS Y PRECISIÓN: (peso 30%)
        if 'attempts' in self.data:
            team_attempts_df = self.data['attempts'][self.data['attempts']['club'] == team]
            if not team_attempts_df.empty:
                total_attempts = team_attempts_df['total_attempts'].sum()
                on_target = team_attempts_df['on_target'].sum()
                team_matches = team_attempts_df['match_played'].max()
                
                if team_matches > 0:
                    # Intentos por partido
                    attempts_per_match = total_attempts / team_matches
                    attempts_component = min(attempts_per_match / 20.0, 1.0)  # 0-20 intentos -> 0-1
                    
                    # Precisión (% de intentos on target)
                    precision = (on_target / max(total_attempts, 1)) if total_attempts > 0 else 0
                    
                    # Combinar intentos y precisión
                    shooting_quality = (attempts_component + precision) / 2
                    components.append(('shooting_quality', shooting_quality, 0.3))
          # 3. CREATIVIDAD: Asistencias y regates (peso 20%)
        if 'attacking' in self.data:
            team_attacking_df = self.data['attacking'][self.data['attacking']['club'] == team]
            if not team_attacking_df.empty:
                # Verificar si existen las columnas antes de usarlas
                assists = team_attacking_df['assists'].sum() if 'assists' in team_attacking_df.columns else 0
                dribbles = team_attacking_df['dribbles'].sum() if 'dribbles' in team_attacking_df.columns else 0
                team_matches = team_attacking_df['match_played'].max()
                
                if team_matches > 0:
                    assists_per_match = assists / team_matches
                    dribbles_per_match = dribbles / team_matches
                    
                    # Normalizar
                    assists_component = min(assists_per_match / 2.0, 1.0)  # 0-2 asistencias -> 0-1
                    dribbles_component = min(dribbles_per_match / 10.0, 1.0)  # 0-10 regates -> 0-1
                    
                    creativity = (assists_component + dribbles_component) / 2
                    components.append(('creativity', creativity, 0.2))
        
        # 4. CONSISTENCIA: Basada en key_stats (peso 10%)
        if 'key_stats' in self.data:
            team_key_df = self.data['key_stats'][self.data['key_stats']['club'] == team]
            if not team_key_df.empty:
                avg_minutes = team_key_df['minutes_played'].mean()
                # Equipos que juegan más minutos son más consistentes
                consistency = min(avg_minutes / 90.0, 1.0)
                components.append(('consistency', consistency, 0.1))        # Calcular puntuación final ponderada
        if components:
            attack_score = sum(score * weight for _, score, weight in components)
            # Aplicar límites
            attack_score = max(0.1, min(0.9, attack_score))  # Entre 0.1 y 0.9
        else:
            attack_score = 0.5  # Valor por defecto si no hay datos
        
        return attack_score
    
    def calculate_team_defense_strength(self, team: str) -> float:
        """
        Calcula la fortaleza defensiva de un equipo basándose en datos reales.
        CORREGIDO: Usa el método correcto para calcular estadísticas del equipo.
        
        Combina múltiples métricas:
        - Goles concedidos por partido (corregido)
        - Porterías a cero (cleansheets)
        - Paradas del portero
        - Tackles y recuperaciones defensivas
        
        Args:
            team: Nombre del equipo.
            
        Returns:
            Valor normalizado de fortaleza defensiva (0.0 a 1.0).
        """
        if not self.data:
            self.load_data()
            
        # Verificar si el equipo existe en los datos
        team_exists = False
        for dataset_name in ['goalkeeping', 'defending', 'disciplinary']:
            if dataset_name in self.data:
                if not self.data[dataset_name][self.data[dataset_name]['club'] == team].empty:
                    team_exists = True
                    break
        
        if not team_exists:
            return 0.5  # Valor por defecto si el equipo no existe
            
        defense_score = 0.0
        components = []
        
        # 1. PORTERÍA: Goles concedidos y cleansheets (peso 50%)
        goals_conceded_per_match = self.calculate_goals_conceded_per_match(team)
        
        # Convertir a puntuación: 0 goles = 1.0, 3+ goles = 0.0
        conceded_score = max(0, 1.0 - (goals_conceded_per_match / 3.0))
        components.append(('conceded_goals', conceded_score, 0.4))
        
        # Cleansheets y paradas adicionales
        if 'goalkeeping' in self.data:
            team_gk_df = self.data['goalkeeping'][self.data['goalkeeping']['club'] == team]
            if not team_gk_df.empty:
                cleansheets = team_gk_df['cleansheets'].sum() if 'cleansheets' in team_gk_df.columns else 0
                saved = team_gk_df['saved'].sum() if 'saved' in team_gk_df.columns else 0
                team_matches = team_gk_df['match_played'].max()
                
                if team_matches > 0:
                    # Cleansheets como % de partidos
                    cleansheet_rate = cleansheets / team_matches
                    
                    # Eficiencia de paradas
                    total_conceded = team_gk_df['conceded'].sum() if 'conceded' in team_gk_df.columns else 0
                    total_shots_faced = saved + total_conceded
                    save_rate = saved / max(total_shots_faced, 1) if total_shots_faced > 0 else 0.7
                    
                    # Combinar métricas de portería
                    goalkeeping_quality = (cleansheet_rate * 0.6 + save_rate * 0.4)
                    components.append(('goalkeeping', goalkeeping_quality, 0.3))
        
        # 2. DEFENSA DE CAMPO: Tackles y recuperaciones (peso 20%)
        if 'defending' in self.data:
            team_def_df = self.data['defending'][self.data['defending']['club'] == team]
            if not team_def_df.empty:
                # Verificar si existen las columnas, si no, usar 0
                tackles_won = team_def_df['t_won'].sum() if 't_won' in team_def_df.columns else 0
                tackles_lost = team_def_df['t_lost'].sum() if 't_lost' in team_def_df.columns else 0
                balls_recovered = team_def_df['balls_recoverd'].sum() if 'balls_recoverd' in team_def_df.columns else 0
                team_matches = team_def_df['match_played'].max()
                
                if team_matches > 0:
                    # Eficiencia en tackles
                    total_tackles = tackles_won + tackles_lost
                    tackle_success_rate = tackles_won / max(total_tackles, 1) if total_tackles > 0 else 0.5
                    
                    # Recuperaciones por partido
                    recoveries_per_match = balls_recovered / team_matches
                    recovery_score = min(recoveries_per_match / 80.0, 1.0)  # 0-80 recuperaciones -> 0-1
                    
                    # Combinar métricas defensivas
                    defending_quality = (tackle_success_rate * 0.6 + recovery_score * 0.4)
                    components.append(('defending', defending_quality, 0.2))
        
        # 3. DISCIPLINA: Menos faltas = mejor defensa (peso 10%)
        if 'disciplinary' in self.data:
            team_disc_df = self.data['disciplinary'][self.data['disciplinary']['club'] == team]
            if not team_disc_df.empty:
                # Verificar si existen las columnas, si no, usar 0
                fouls_committed = team_disc_df['fouls_committed'].sum() if 'fouls_committed' in team_disc_df.columns else 0
                red_cards = team_disc_df['red'].sum() if 'red' in team_disc_df.columns else 0
                yellow_cards = team_disc_df['yellow'].sum() if 'yellow' in team_disc_df.columns else 0
                team_matches = team_disc_df['match_played'].max()
                
                if team_matches > 0:
                    # Faltas por partido (inverso: menos faltas = mejor)
                    fouls_per_match = fouls_committed / team_matches
                    foul_discipline = max(0, 1.0 - (fouls_per_match / 20.0))  # 0-20 faltas -> 1-0
                    
                    # Penalización por tarjetas
                    cards_penalty = (red_cards * 0.1 + yellow_cards * 0.02)  # Máximo ~0.3 de penalización
                    discipline_score = max(0, foul_discipline - cards_penalty)
                    
                    components.append(('discipline', discipline_score, 0.1))
        
        # Calcular puntuación final ponderada
        if components:
            defense_score = sum(score * weight for _, score, weight in components)
            # Aplicar límites
            defense_score = max(0.1, min(0.9, defense_score))  # Entre 0.1 y 0.9
        else:
            defense_score = 0.5  # Valor por defecto si no hay datos
            
        return defense_score
    
    def calculate_goals_per_match_avg(self, team: str) -> float:
        """
        Calcula el promedio de goles por partido de un equipo.
        CORREGIDO: Calcula correctamente usando los datos individuales de jugadores.
        
        Los datos son por jugador individual. Para obtener goles del equipo por partido:
        1. Sumar todos los goles de todos los jugadores del equipo
        2. Calcular el número real de partidos del equipo (máximo de partidos jugados por cualquier jugador)
        
        Args:
            team: Nombre del equipo.
            
        Returns:
            Promedio de goles por partido del equipo.
        """
        if not self.data:
            self.load_data()
            
        if 'goals' not in self.data:
            return 1.5
            
        # Obtener datos individuales de jugadores del equipo
        team_goals_df = self.data['goals'][self.data['goals']['club'] == team]
        
        if team_goals_df.empty:
            return 1.5
            
        # Total de goles del equipo = suma de goles de todos los jugadores
        total_team_goals = team_goals_df['goals'].sum()
          # Número real de partidos del equipo = máximo de partidos jugados por cualquier jugador
        # (asumiendo que al menos un jugador jugó todos los partidos del equipo)
        team_matches = team_goals_df['match_played'].max()
        
        if team_matches == 0:
            return 1.5
            
        return total_team_goals / team_matches
    
    def calculate_goals_conceded_per_match(self, team: str) -> float:
        """
        Calcula el promedio de goles concedidos por partido.
        CORREGIDO: Usa datos reales de porteros del equipo.
        
        Args:
            team: Nombre del equipo.
            
        Returns:
            Promedio de goles concedidos por partido.
        """
        if not self.data:
            self.load_data()
            
        if 'goalkeeping' not in self.data:
            return 1.0
            
        # Obtener datos de porteros del equipo
        team_gk_df = self.data['goalkeeping'][self.data['goalkeeping']['club'] == team]
        
        if team_gk_df.empty:
            return 1.0
            
        # Total de goles concedidos por todos los porteros del equipo
        total_conceded = team_gk_df['conceded'].sum()
        
        # Número real de partidos del equipo = máximo de partidos jugados por cualquier portero
        team_matches = team_gk_df['match_played'].max()
        
        if team_matches == 0:
            return 1.0
            
        return total_conceded / team_matches
    
    def create_team_summary(self, team_name: str) -> Dict[str, Any]:
        """
        Crear un resumen completo de estadísticas para un equipo.
        Retorna solo diccionarios de Python - NO crea Facts.
        
        Args:
            team_name: Nombre del equipo.
            
        Returns:
            Diccionario con todas las estadísticas del equipo.
        """
        if not self.team_data:
            self.aggregate_team_data()
        
        # Métricas principales
        attacking_strength = self.calculate_team_attack_strength(team_name)
        defensive_strength = self.calculate_team_defense_strength(team_name)
        goals_per_match = self.calculate_goals_per_match_avg(team_name)
        goals_conceded_per_match = self.calculate_goals_conceded_per_match(team_name)
        
        # Crear el resumen base
        summary = {
            'team': team_name,
            'attacking_strength': attacking_strength,
            'defensive_strength': defensive_strength,
            'overall_strength': (attacking_strength + defensive_strength) / 2,
            'goals_per_match': goals_per_match,
            'goals_conceded_per_match': goals_conceded_per_match,
            'goal_difference_per_match': goals_per_match - goals_conceded_per_match
        }
        
        # Añadir métricas detalladas de goles
        if team_name in self.team_data and 'goals' in self.team_data[team_name]:
            goals_data = self.team_data[team_name]['goals'].get('sum', {})
            matches_played = goals_data.get('match_played', 1)
            
            summary.update({
                'total_goals': goals_data.get('goals', 0),
                'penalties_scored': goals_data.get('penalties', 0),
                'goals_inside_area': goals_data.get('inside_area', 0),
                'goals_outside_area': goals_data.get('outside_areas', 0),
                'header_goals': goals_data.get('headers', 0),
                'right_foot_goals': goals_data.get('right_foot', 0),
                'left_foot_goals': goals_data.get('left_foot', 0)
            })
            
            # Calcular eficiencia de finalización
            if 'attempts' in self.team_data[team_name]:
                attempts_data = self.team_data[team_name]['attempts'].get('sum', {})
                total_attempts = attempts_data.get('total_attempts', 0)
                if total_attempts > 0:
                    summary['finishing_efficiency'] = goals_data.get('goals', 0) / total_attempts
                else:
                    summary['finishing_efficiency'] = 0.0
        
        # Añadir métricas de portería
        if team_name in self.team_data and 'goalkeeping' in self.team_data[team_name]:
            gk_data = self.team_data[team_name]['goalkeeping'].get('sum', {})
            matches_played = gk_data.get('match_played', 1)
            
            summary.update({
                'cleansheets': gk_data.get('cleansheets', 0),
                'cleansheet_rate': gk_data.get('cleansheets', 0) / max(matches_played, 1),
                'saves_made': gk_data.get('saved', 0),
                'penalties_saved': gk_data.get('saved_penalties', 0)
            })
          # Añadir métricas de disciplina
        if team_name in self.team_data and 'disciplinary' in self.team_data[team_name]:
            disc_data = self.team_data[team_name]['disciplinary'].get('sum', {})
            # CORREGIDO: Usar max partidos jugados del dataset original, no la suma
            if 'disciplinary' in self.data:
                team_disc_df = self.data['disciplinary'][self.data['disciplinary']['club'] == team_name]
                matches_played = team_disc_df['match_played'].max() if not team_disc_df.empty else 1
            else:
                matches_played = 1
            
            yellow_cards = disc_data.get('yellow', 0)
            red_cards = disc_data.get('red', 0)
            
            summary.update({
                'yellow_cards': yellow_cards,
                'red_cards': red_cards,
                'yellow_cards_per_match': yellow_cards / max(matches_played, 1),
                'red_cards_per_match': red_cards / max(matches_played, 1),
                'discipline_rating': 1.0 - min((yellow_cards * 0.02 + red_cards * 0.1), 1.0)
            })
        
        # Añadir métricas de distribución/pases
        if team_name in self.team_data and 'distributon' in self.team_data[team_name]:
            dist_data = self.team_data[team_name]['distributon'].get('sum', {})
            
            pass_attempted = dist_data.get('pass_attempted', 0)
            pass_completed = dist_data.get('pass_completed', 0)
            
            if pass_attempted > 0:
                summary['pass_accuracy'] = pass_completed / pass_attempted
            else:
                summary['pass_accuracy'] = 0.0
                
            summary.update({
                'passes_attempted': pass_attempted,
                'passes_completed': pass_completed
            })
        
        # Clasificar al equipo según sus fortalezas (útil para reglas)
        if attacking_strength > 0.7:
            summary['team_style'] = 'offensive'
        elif defensive_strength > 0.7:
            summary['team_style'] = 'defensive'
        elif abs(attacking_strength - defensive_strength) < 0.1:
            summary['team_style'] = 'balanced'
        else:
            summary['team_style'] = 'mixed'
        
        return summary
    
    def get_all_team_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Crea resúmenes de estadísticas para todos los equipos.
        
        Returns:
            Diccionario con resúmenes para todos los equipos.
        """
        if not self.team_data:
            self.aggregate_team_data()
            
        teams = self.get_teams_list()
        all_summaries = {}
        
        for team in teams:
            all_summaries[team] = self.create_team_summary(team)
            
        return all_summaries
    
    def get_team_statistics_summary(self, team: str) -> Dict[str, Any]:
        """
        Obtiene un resumen estadístico básico de un equipo.
        
        Args:
            team: Nombre del equipo.
            
        Returns:
            Diccionario con estadísticas básicas del equipo.
        """
        if not self.team_data:
            self.aggregate_team_data()
            
        if team not in self.team_data:
            return {'error': f'Equipo {team} no encontrado en el dataset'}
        
        summary_data = self.create_team_summary(team)
        
        # Clasificación del equipo
        strength = summary_data['overall_strength']
        if strength > 0.75:
            tier = 'Elite'
        elif strength > 0.6:
            tier = 'Strong'
        elif strength > 0.45:
            tier = 'Average'
        else:
            tier = 'Weak'
        
        summary = {
            'team_name': team,
            'tier': tier,
            'overall_strength': round(strength, 3),
            'style': summary_data.get('team_style', 'unknown'),
            'key_metrics': {
                'goals_per_match': round(summary_data['goals_per_match'], 2),
                'goals_conceded_per_match': round(summary_data['goals_conceded_per_match'], 2),
                'attacking_strength': round(summary_data['attacking_strength'], 3),
                'defensive_strength': round(summary_data['defensive_strength'], 3),
                'discipline_rating': round(summary_data.get('discipline_rating', 0.5), 3)
            }
        }
        
        return summary
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """
        Valida la calidad de los datos cargados.
        
        Returns:
            Diccionario con información sobre la calidad de los datos.
        """
        if not self.data:
            self.load_data()
        
        validation_report = {
            'files_loaded': len(self.data),
            'teams_found': len(self.get_teams_list()),
            'data_quality': {},
            'issues': []
        }
        
        # Verificar cada dataset
        for name, df in self.data.items():
            quality_info = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': df.isnull().sum().sum(),
                'duplicate_rows': df.duplicated().sum()
            }
            
            # Verificar columnas esperadas
            if 'club' not in df.columns:
                validation_report['issues'].append(f"Dataset {name} no tiene columna 'club'")
            
            validation_report['data_quality'][name] = quality_info
        
        return validation_report
    
    def analyze_betting_data_coverage(self) -> Dict[str, Any]:
        """
        Analiza qué datos están disponibles para las 5 categorías de apuestas:
        1. Victoria local (home_win)
        2. Victoria visitante (away_win) 
        3. Empate (draw)
        4. Más de X goles (over)
        5. Menos de X goles (under)
        
        Returns:
            Diccionario con análisis de cobertura de datos.
        """
        if not self.team_data:
            self.aggregate_team_data()
        
        coverage_analysis = {
            'bet_types_coverage': {},
            'data_quality_for_bets': {},
            'recommendations': []
        }
        
        teams = self.get_teams_list()
        if not teams:
            coverage_analysis['recommendations'].append("No se encontraron equipos en el dataset")
            return coverage_analysis
        
        sample_team = teams[0]
        
        # 1. Análisis para victorias (home_win, away_win)
        victory_data = []
        if sample_team in self.team_data:
            if 'goals' in self.team_data[sample_team]:
                victory_data.append('✓ Datos de goles disponibles')
            if 'attacking' in self.team_data[sample_team]:
                victory_data.append('✓ Estadísticas de ataque disponibles')
            if 'defending' in self.team_data[sample_team]:
                victory_data.append('✓ Estadísticas defensivas disponibles')
            if 'goalkeeping' in self.team_data[sample_team]:
                victory_data.append('✓ Estadísticas de portería disponibles')
                
        coverage_analysis['bet_types_coverage']['victory_bets'] = {
            'applicable_to': ['home_win', 'away_win'],
            'data_available': victory_data,
            'key_metrics': ['attacking_strength', 'defensive_strength', 'overall_strength'],
            'coverage_score': len(victory_data) / 4  # 4 tipos de datos esperados
        }
        
        # 2. Análisis para empates (draw)
        draw_data = []
        if sample_team in self.team_data:
            if 'goals' in self.team_data[sample_team]:
                draw_data.append('✓ Datos de goles para calcular diferencias')
            if 'goalkeeping' in self.team_data[sample_team]:
                draw_data.append('✓ Datos de portería para empates (cleansheets)')
            if 'disciplinary' in self.team_data[sample_team]:
                draw_data.append('✓ Datos disciplinarios (equipos conservadores)')
                
        coverage_analysis['bet_types_coverage']['draw_bets'] = {
            'applicable_to': ['draw'],
            'data_available': draw_data,
            'key_metrics': ['goal_difference_per_match', 'defensive_strength', 'discipline_rating'],
            'coverage_score': len(draw_data) / 3
        }
        
        # 3. Análisis para over/under goles
        goals_data = []
        if sample_team in self.team_data:
            if 'goals' in self.team_data[sample_team]:
                goals_data.append('✓ Histórico de goles marcados')
            if 'goalkeeping' in self.team_data[sample_team]:
                goals_data.append('✓ Histórico de goles concedidos')
            if 'attempts' in self.team_data[sample_team]:
                goals_data.append('✓ Estadísticas de intentos y precisión')
                
        coverage_analysis['bet_types_coverage']['goals_bets'] = {
            'applicable_to': ['over', 'under'],
            'data_available': goals_data,
            'key_metrics': ['goals_per_match', 'goals_conceded_per_match', 'finishing_efficiency'],
            'coverage_score': len(goals_data) / 3
        }
        
        # 4. Análisis de calidad general de datos
        total_teams_with_goals = sum(1 for team in teams if team in self.team_data and 'goals' in self.team_data[team])
        total_teams_with_defense = sum(1 for team in teams if team in self.team_data and 'defending' in self.team_data[team])
        total_teams_with_gk = sum(1 for team in teams if team in self.team_data and 'goalkeeping' in self.team_data[team])
        
        coverage_analysis['data_quality_for_bets'] = {
            'total_teams': len(teams),
            'teams_with_goal_data': total_teams_with_goals,
            'teams_with_defense_data': total_teams_with_defense,
            'teams_with_goalkeeping_data': total_teams_with_gk,
            'overall_completeness': min(total_teams_with_goals, total_teams_with_defense, total_teams_with_gk) / len(teams)
        }
        
        # 5. Recomendaciones basadas en el análisis
        if coverage_analysis['data_quality_for_bets']['overall_completeness'] > 0.8:
            coverage_analysis['recommendations'].append("✅ Excelente cobertura de datos para todos los tipos de apuesta")
        elif coverage_analysis['data_quality_for_bets']['overall_completeness'] > 0.6:
            coverage_analysis['recommendations'].append("⚠️ Buena cobertura de datos, pero algunos equipos pueden tener datos incompletos")
        else:
            coverage_analysis['recommendations'].append("❌ Cobertura de datos limitada, considerar usar datos adicionales")
            
        # Recomendaciones específicas por tipo de apuesta
        for bet_category, data in coverage_analysis['bet_types_coverage'].items():
            if data['coverage_score'] >= 0.8:
                coverage_analysis['recommendations'].append(f"✅ {bet_category}: Datos suficientes para predicciones confiables")
            elif data['coverage_score'] >= 0.6:
                coverage_analysis['recommendations'].append(f"⚠️ {bet_category}: Datos aceptables, considerar métricas adicionales")
            else:
                coverage_analysis['recommendations'].append(f"❌ {bet_category}: Datos insuficientes, necesita mejoras")
        
        return coverage_analysis

