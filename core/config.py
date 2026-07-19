# core/config.py
"""
Configuración centralizada para el MVP del sistema de recomendación de riego.
Contiene parámetros de suelo, umbrales absolutos y tablas independientes para Kc y etapas/umbrales.
"""

import datetime

# --- CONFIGURACIÓN DE LOTES ---
# Por el momento, usamos los datos de "El Trébol" como placeholder para "San Martín"
SUELO_CONFIG = {
    "San Martín": {
        "horizontes": [
            {"nombre": "H1", "espesor_dm": 2.0, "cc": 25.7, "pmp": 14.8, "da": 1.31}, # 0-20 cm
            {"nombre": "H2", "espesor_dm": 2.0, "cc": 22.6, "pmp": 15.1, "da": 1.35}, # 20-40 cm
            {"nombre": "H3", "espesor_dm": 6.0, "cc": 31.3, "pmp": 19.8, "da": 1.40}, # 40-80 cm
        ],
        "factor_ajuste": 0.75,     # Factor de corrección radicular/efectivo
        "techo_sistema": 120.0,    # Capacidad máxima del sistema (mm)
        "infiltracion_max": 15.0,  # Capacidad de infiltración límite por aplicación (mm) - Estimado por bibliografía para Vertisol (rango 2-15 mm/h)
        "caudal_pivote": 1.4,      # Caudal de diseño del pivote (mm/hora)
        "eficiencia_riego": 0.90,  # Eficiencia del sistema de pivote
    }
}

# --- UMBRALES DE RIEGO ABSOLUTOS ---
UMBRAL_VEGETATIVO = 60.0  # mm
UMBRAL_CRITICO = 72.0     # mm

# --- CURVA DE KC POR DAS (Días Desde Emergencia) ---
# Estructura: (DAS_inicio, DAS_fin, Kc)
KC_DAS_TABLE = [
    (0, 7, 0.09),
    (8, 13, 0.14),
    (14, 21, 0.18),
    (22, 30, 0.25),
    (31, 37, 0.44),
    (38, 44, 0.51),
    (45, 51, 0.64),
    (52, 61, 0.77),
    (62, 68, 0.84),
    (69, 82, 0.96),
    (83, 91, 1.00),
    (92, 105, 1.10),
    (106, 112, 1.00),
    (113, 122, 0.95),
    (123, 129, 0.87),
    (130, 136, 0.77),
    (137, 144, 0.56),
    (145, 150, 0.35),
    (151, 999, 0.05)
]

# --- ETAPAS FENOLÓGICAS Y UMBRALES POR DAS ---
# Estructura: (DAS_inicio, DAS_fin, "Nombre Etapa", Umbral_mm)
# Refleja con precisión las transiciones de la planilla de Mariano
STAGE_DAS_TABLE = [
    (0, 0, "Emergencia", UMBRAL_VEGETATIVO),
    (1, 30, "Inicial", UMBRAL_VEGETATIVO),
    (31, 74, "Crecimiento", UMBRAL_VEGETATIVO),
    (75, 79, "Desarrollo - PC", UMBRAL_VEGETATIVO),
    (80, 125, "Desarrollo - PC", UMBRAL_CRITICO), # Periodo de umbral crítico 72mm
    (126, 135, "Desarrollo - PC", UMBRAL_VEGETATIVO),
    (136, 150, "Hacia madurez fisiológica", UMBRAL_VEGETATIVO),
    (151, 999, "Madurez fisiológica", UMBRAL_VEGETATIVO)
]

# --- LLUVIA EFECTIVA ---
# Coeficientes de lluvia efectiva por rango de precipitación
LLUVIA_EFECTIVA_RANGOS = [
    (15.0, 1.00),  # < 15 mm -> 100%
    (30.0, 0.85),  # 15–30 mm -> 85%
    (60.0, 0.70),  # 30–60 mm -> 70%
    (999.0, 0.55), # > 60 mm -> 55%
]
