# data/sensor.py
"""
Módulo de interfaz para el sensor de humedad de suelo (AGSENSE / Valley).
NOTA: Este módulo es un STUB/MOCK. La integración real con la API o exportación CSV
de AGSENSE queda marcada como una dependencia externa pendiente (Bloqueante Fase 1).
"""

import pandas as pd
import datetime

def get_humidity_data(lote: str, fecha_desde, fecha_hasta) -> pd.DataFrame:
    """
    Retorna los datos de humedad del sensor para un rango de fechas.
    
    === DEPENDENCIA EXTERNA PENDIENTE ===
    Actualmente no hay API ni CSV real provisto. Retorna datos mockeados basados
    en la dinámica del suelo para permitir el desarrollo del frontend.
    
    Retorna un DataFrame con las columnas:
    - fecha: datetime.date
    - humedad_0_20: float (% contenido volumétrico de agua - VWC)
    - humedad_20_40: float (% VWC)
    - humedad_40_80: float (% VWC)
    - bateria_v: float (voltaje de la batería del sensor)
    """
    # Convertir fechas a objetos date
    if isinstance(fecha_desde, str):
        fecha_desde = pd.to_datetime(fecha_desde).date()
    elif hasattr(fecha_desde, "date"):
        fecha_desde = fecha_desde.date()
        
    if isinstance(fecha_hasta, str):
        fecha_hasta = pd.to_datetime(fecha_hasta).date()
    elif hasattr(fecha_hasta, "date"):
        fecha_hasta = fecha_hasta.date()
        
    records = []
    curr = fecha_desde
    
    # Simular datos basados en ciclos de secado y riego típicos
    # CC es ~25%, PMP es ~15% para horizontes superficiales
    # Simular que oscila entre 16% y 24%
    while curr <= fecha_hasta:
        # Generar una oscilación senoidal simulada que parezca consumo de agua
        day_val = curr.day
        hum_0_20 = 20.0 + 3.0 * (day_val % 7) / 7.0
        hum_20_40 = 21.0 + 2.0 * (day_val % 10) / 10.0
        hum_40_80 = 24.0 + 1.0 * (day_val % 15) / 15.0
        
        records.append({
            "fecha": curr,
            "humedad_0_20": round(hum_0_20, 1),
            "humedad_20_40": round(hum_20_40, 1),
            "humedad_40_80": round(hum_40_80, 1),
            "bateria_v": 3.65 # voltaje de batería normal
        })
        curr += datetime.timedelta(days=1)
        
    return pd.DataFrame(records)
