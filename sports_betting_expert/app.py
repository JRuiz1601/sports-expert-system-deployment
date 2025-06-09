import streamlit as st
import os
import sys
import pandas as pd
from PIL import Image
import time

# Asegurarse que se pueden importar los módulos del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importar el sistema experto
from src.main import BettingExpertApp

# Configuración de la página
st.set_page_config(
    page_title="Sistema Experto de Apuestas Deportivas",
    page_icon="⚽",
    layout="wide",
)

# Estilo personalizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
    }
    .recommendation-box {
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .high-confidence {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 5px solid #4CAF50;
    }
    .medium-confidence {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 5px solid #FFC107;
    }
    .low-confidence {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 5px solid #F44336;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialización de la aplicación y variables de sesión
@st.cache_resource
def load_betting_app():
    """Cargar y cachear la aplicación de apuestas"""
    app = BettingExpertApp()
    initialized = app.initialize_system()
    return app if initialized else None

# Función para mostrar análisis de partido
def show_match_analysis(home_team, away_team):
    if not home_team or not away_team:
        st.warning("Por favor, selecciona ambos equipos para realizar el análisis.")
        return
    
    if home_team == away_team:
        st.warning("Por favor, selecciona equipos diferentes para el análisis.")
        return
    
    with st.spinner(f"Analizando: {home_team} vs {away_team}..."):
        # Realizar análisis
        analysis = betting_app.analyze_matchup_hybrid(home_team, away_team)
        
        # Mostrar resultados
        st.subheader(f"📊 Análisis: {home_team} vs {away_team}")
        
        # Información general de equipos
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🏠 Equipo Local")
            home_fact = analysis['home_fact']
            st.markdown(f"**Equipo:** {home_fact['team']}")
            st.markdown(f"**Fuerza general:** {home_fact['overall_strength']:.2f}")
            st.markdown(f"**Ataque:** {home_fact['attacking_strength']:.2f}")
            st.markdown(f"**Defensa:** {home_fact['defensive_strength']:.2f}")
            st.markdown(f"**Estilo:** {home_fact['team_style']}")
            
        with col2:
            st.markdown("### 🚌 Equipo Visitante")
            away_fact = analysis['away_fact']
            st.markdown(f"**Equipo:** {away_fact['team']}")
            st.markdown(f"**Fuerza general:** {away_fact['overall_strength']:.2f}")
            st.markdown(f"**Ataque:** {away_fact['attacking_strength']:.2f}")
            st.markdown(f"**Defensa:** {away_fact['defensive_strength']:.2f}")
            st.markdown(f"**Estilo:** {away_fact['team_style']}")
        
        # Recomendaciones
        st.markdown("## 🎯 Recomendaciones de Apuestas")
        recommendations = analysis['hybrid_recommendations']
        
        # Ordenar recomendaciones por confianza y mostrar solo las recomendadas
        recommended_bets = []
        for bet_type, rec in recommendations.items():
            if rec['recommendation'] == 'recommended':
                confidence_level = {"high": 3, "medium": 2, "low": 1}.get(rec['confidence'], 0)
                recommended_bets.append((bet_type, rec, confidence_level))
        
        # Ordenar por nivel de confianza (descendente)
        recommended_bets.sort(key=lambda x: (x[2], x[1]['probability']), reverse=True)
        
        if recommended_bets:
            for bet_type, rec, _ in recommended_bets:
                # Obtener nombre legible de la apuesta
                bet_name = _format_bet_name(bet_type, home_team, away_team)
                
                # Determinar clase de confianza para el estilo
                confidence_class = {
                    "high": "high-confidence",
                    "medium": "medium-confidence", 
                    "low": "low-confidence"
                }.get(rec['confidence'], "medium-confidence")
                
                # Crear caja de recomendación con estilo
                st.markdown(f"""
                <div class="recommendation-box {confidence_class}">
                    <h3>{bet_name}</h3>
                    <p><strong>Confianza:</strong> {rec['confidence'].upper()}</p>
                    <p><strong>Probabilidad:</strong> {rec['probability']:.1%}</p>
                    <p><strong>Justificación:</strong> {rec['explanation']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No hay apuestas recomendadas para este partido con suficiente confianza.")
        
        # Análisis adicional
        with st.expander("Ver análisis detallado"):
            st.markdown("### ⚽ Tendencia de Goles")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{home_team}:**")
                st.markdown(f"- Marca: {home_fact['goals_per_match']:.2f} por partido")
                st.markdown(f"- Recibe: {home_fact['goals_conceded_per_match']:.2f} por partido")
            with col2:
                st.markdown(f"**{away_team}:**")
                st.markdown(f"- Marca: {away_fact['goals_per_match']:.2f} por partido")
                st.markdown(f"- Recibe: {away_fact['goals_conceded_per_match']:.2f} por partido")
            
            combined = home_fact['goals_per_match'] + away_fact['goals_per_match']
            st.markdown(f"**Promedio combinado:** {combined:.2f} goles por partido")
            
            # Mostrar reglas que se activaron
            st.markdown("### 🧠 Reglas activadas")
            if 'rules_summary' in analysis and analysis['rules_summary']:
                for rule, count in analysis['rules_summary'].items():
                    st.markdown(f"- **{rule}**: {count} veces")
            else:
                st.info("No hay información sobre reglas activadas.")

# Función para mostrar estadísticas de equipo
def show_team_stats(team):
    if not team:
        st.warning("Por favor, selecciona un equipo para ver sus estadísticas.")
        return
    
    with st.spinner(f"Cargando estadísticas de {team}..."):
        # Obtener y mostrar estadísticas
        team_summary = betting_app.processor.create_team_summary(team)
        
        st.subheader(f"📊 Estadísticas de {team}")
        
        # Crear columnas para organizar información
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💪 Fortaleza general")
            # Determinar nivel de fortaleza
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
                
            st.markdown(f"{team} es un equipo **{strength_level}** con una valoración general de **{overall:.2f}**.")
            st.markdown(f"- **Fuerza ofensiva:** {team_summary['attacking_strength']:.2f}")
            st.markdown(f"- **Fuerza defensiva:** {team_summary['defensive_strength']:.2f}")
            
            # Estilo de juego
            style = team_summary['team_style']
            style_desc = {
                'balanced': "equilibrado entre ataque y defensa",
                'attacking': "ofensivo, prioriza el ataque",
                'offensive': "muy ofensivo",
                'defensive': "defensivo, prioriza mantener su portería a cero",
                'possessive': "de posesión, controla el balón",
                'counter': "de contraataque",
                'mixed': "mixto, adaptable según el rival"
            }.get(style, style)
            
            st.markdown(f"- **Estilo de juego:** {style_desc}")
        
        with col2:
            st.markdown("### ⚽ Estadísticas de goles")
            goals_per_match = team_summary['goals_per_match']
            goals_conceded = team_summary['goals_conceded_per_match']
            
            st.markdown(f"- **Goles anotados:** {goals_per_match:.2f} por partido")
            st.markdown(f"- **Goles recibidos:** {goals_conceded:.2f} por partido")
            st.markdown(f"- **Diferencia de goles:** {team_summary['goal_difference_per_match']:.2f} por partido")
            
            # Disciplina si está disponible
            if 'yellow_cards_per_match' in team_summary:
                st.markdown("### 🟨 Disciplina")
                st.markdown(f"- **Tarjetas amarillas:** {team_summary['yellow_cards_per_match']:.2f} por partido")
                st.markdown(f"- **Tarjetas rojas:** {team_summary['red_cards_per_match']:.2f} por partido")

# Función auxiliar para formatear nombres de apuestas
def _format_bet_name(bet_type, home_team, away_team):
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

# Función principal
def main():
    # Inicializar sistema experto
    global betting_app
    betting_app = load_betting_app()
    
    if not betting_app:
        st.error("❌ No se pudo inicializar el sistema experto. Por favor, verifica la instalación y los datos.")
        return
    
    # Encabezado
    st.markdown('<h1 class="main-header">Sistema Experto de Apuestas Deportivas</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">UEFA Champions League 2021/22</h2>', unsafe_allow_html=True)
    
    # Menú principal
    menu_options = ["Inicio", "Análisis de Partidos", "Estadísticas de Equipos", "Acerca del Sistema"]
    selected_menu = st.sidebar.selectbox("Menú", menu_options)
    
    # Lista de equipos disponibles
    available_teams = betting_app.available_teams
    
    # Página de inicio
    if selected_menu == "Inicio":
        st.markdown("""
        ## 👋 ¡Bienvenido al Sistema Experto de Apuestas Deportivas!
        
        Este sistema utiliza inteligencia artificial para analizar datos de fútbol y ofrecer recomendaciones
        de apuestas basadas en análisis estadísticos avanzados.
        
        ### ¿Qué puedes hacer aquí?
        
        - **Analizar partidos**: Compara dos equipos y recibe recomendaciones de apuestas
        - **Consultar estadísticas**: Obtén información detallada sobre cualquier equipo
        - **Explorar el sistema**: Conoce cómo funciona nuestro sistema experto
        
        ### ¿Cómo funciona?
        
        Combinamos un sistema experto basado en reglas con una red bayesiana para ofrecer
        análisis precisos sobre los posibles resultados de los partidos.
        """)
        
        # Botones rápidos
        st.subheader("Acceso rápido")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Ir a Análisis de Partidos"):
                st.session_state.menu_selection = "Análisis de Partidos"
                st.experimental_rerun()
        with col2:
            if st.button("📊 Ver Estadísticas de Equipos"):
                st.session_state.menu_selection = "Estadísticas de Equipos"
                st.experimental_rerun()
    
    # Análisis de partidos
    elif selected_menu == "Análisis de Partidos":
        st.markdown("## 🔍 Análisis de Partidos")
        st.markdown("Selecciona dos equipos para analizar su enfrentamiento y recibir recomendaciones de apuestas.")
        
        # Selección de equipos
        col1, col2 = st.columns(2)
        with col1:
            home_team = st.selectbox("Equipo Local", [""] + available_teams, index=0)
        with col2:
            # Filtrar el equipo local para evitar seleccionar el mismo
            away_options = [""] + [team for team in available_teams if team != home_team]
            away_team = st.selectbox("Equipo Visitante", away_options, index=0)
        
        # Botón de análisis
        if st.button("Analizar Partido"):
            show_match_analysis(home_team, away_team)
    
    # Estadísticas de equipos
    elif selected_menu == "Estadísticas de Equipos":
        st.markdown("## 📊 Estadísticas de Equipos")
        st.markdown("Selecciona un equipo para ver sus estadísticas detalladas.")
        
        # Selección de equipo
        team = st.selectbox("Equipo", [""] + available_teams, index=0)
        
        # Mostrar estadísticas
        if st.button("Ver Estadísticas"):
            show_team_stats(team)
    
    # Acerca del sistema
    elif selected_menu == "Acerca del Sistema":
        st.markdown("## ℹ️ Acerca del Sistema Experto")
        st.markdown("""
        ### 🧠 Arquitectura del Sistema
        
        Nuestro sistema experto combina dos tecnologías de IA complementarias:
        
        1. **Sistema basado en reglas**: Utiliza reglas heurísticas formuladas por expertos en fútbol y apuestas.
        2. **Red Bayesiana**: Modelo probabilístico que captura las relaciones causales entre diferentes factores.
        
        Esta arquitectura híbrida nos permite combinar el conocimiento experto con el análisis probabilístico,
        ofreciendo recomendaciones más robustas y explicables.
        
        ### 📊 Fuentes de Datos
        
        El sistema utiliza datos históricos de la UEFA Champions League 2021/22, incluyendo:
        
        - Resultados de partidos
        - Estadísticas de equipos (goles, posesión, disparos, etc.)
        - Rendimiento histórico
        
        ### 🎯 Tipos de Apuestas Analizadas
        
        - Victoria local/visitante/empate
        - Más/menos de 2.5 goles
        
        ### 👨‍💻 Desarrolladores
        
        Este sistema fue desarrollado como proyecto integrador para el curso de Algoritmos y Programación III.
        """)

if __name__ == "__main__":
    # Establecer el valor del menú desde la sesión si existe
    if 'menu_selection' in st.session_state:
        selected_menu = st.session_state.menu_selection
        # Limpiar para futuros usos
        del st.session_state.menu_selection
    
    main()