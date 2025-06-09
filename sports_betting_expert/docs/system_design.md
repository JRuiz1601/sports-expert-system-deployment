# Diseño del Sistema Experto para Consejos de Apuestas Deportivas

## Visión General de la Arquitectura

Este documento describe el diseño arquitectónico del sistema experto para consejos de apuestas deportivas, basado en el dataset de la UEFA Champions League 2021/22.

## Componentes Principales

### 1. Procesamiento de Datos
- **UCLDataProcessor**: Clase encargada de cargar, limpiar y transformar los datos de la UCL.
- **DataPreprocessor**: Componente que prepara los datos para su uso en el sistema experto.

### 2. Modelo de Conocimiento
Basado en el dataset de la UCL, definiremos los siguientes Facts:

- **MatchFact**: Representa un partido con sus características principales.
  - Equipos (local y visitante)
  - Fase de la competición (grupo, octavos, cuartos, etc.)
  - Estadísticas relevantes (posesión, tiros, faltas, etc.)

- **TeamFact**: Representa información sobre un equipo.
  - Nombre del equipo
  - Forma reciente (últimos N partidos)
  - Rendimiento en la competición
  - Jugadores clave y su disponibilidad

- **BetTypeFact**: Representa el tipo de apuesta a evaluar.
  - Tipo (victoria local, empate, victoria visitante, over/under)
  - Cuotas (si están disponibles)

### 3. Motor de Reglas
Basado en patrones observados en los datos de la UCL, definiremos reglas como:

- **FormAdvantageRule**: Si la forma reciente del equipo local es significativamente mejor que la del visitante, entonces hay una ventaja para el equipo local.

- **KnockoutStageRule**: En fases eliminatorias, los partidos tienen dinámicas diferentes a los de fase de grupos.

- **HomeAdvantageRule**: El factor local influye de manera diferente según el equipo y la fase de la competición.

### 4. Red Bayesiana
La red bayesiana modelará relaciones probabilísticas entre:

- La forma de los equipos
- La fase de la competición
- El historial de enfrentamientos directos
- El resultado del partido

### 5. Sistema de Integración y Explicación
Este componente combinará las conclusiones del motor de reglas y la red bayesiana para:

- Clasificar la apuesta como "segura" o "arriesgada"
- Asignar un nivel de confianza
- Generar explicaciones comprensibles

### 6. Interfaz de Usuario
Una interfaz por consola que permitirá:

- Consultar recomendaciones para partidos específicos
- Ver explicaciones detalladas del razonamiento
- Explorar estadísticas relevantes

## Flujo de Datos

1. El usuario introduce los datos del partido a analizar
2. El sistema carga datos históricos relevantes
3. Los datos se transforman en Facts para el motor de reglas
4. Se aplican las reglas y se actualiza la red bayesiana
5. Se integran los resultados para generar una recomendación
6. Se presenta la recomendación con explicación al usuario

## Consideraciones de Diseño

- **Extensibilidad**: El sistema debe ser fácilmente extensible a otras competiciones y deportes.
- **Mantenibilidad**: Las reglas y el modelo bayesiano deben ser fácilmente actualizables.
- **Explicabilidad**: Las recomendaciones deben incluir explicaciones claras y comprensibles.