# data/weather.py
"""
Módulo para ingesta de datos climáticos: clima histórico local y pronóstico a 7 días.
"""

import requests
import datetime
import pandas as pd
import numpy as np

# Coordenadas aproximadas para San Martín / Urdinarrain (Entre Ríos, Argentina)
LATITUDE = -32.687
LONGITUDE = -58.885

def get_7day_forecast(lat: float = LATITUDE, lon: float = LONGITUDE) -> list:
    """
    Obtiene el pronóstico de 7 días (lluvia y ETP aproximada) usando la API de Open-Meteo.
    Retorna una lista de diccionarios con la fecha, lluvia proyectada (mm) y ETP proyectada (mm).
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,et0_fao_evapotranspiration&timezone=America/Argentina/Buenos_Aires"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            precip = daily.get("precipitation_sum", [])
            et0 = daily.get("et0_fao_evapotranspiration", [])
            
            forecast = []
            for i in range(len(dates)):
                f_date = datetime.datetime.strptime(dates[i], "%Y-%m-%d").date()
                forecast.append({
                    "fecha": f_date,
                    "lluvia": float(precip[i]) if precip[i] is not None else 0.0,
                    "etp": float(et0[i]) if et0[i] is not None else 4.0 # default 4mm ETP
                })
            return forecast
    except Exception as e:
        print(f"Error consultando el pronóstico en Open-Meteo: {e}. Usando fallback...")
    
    # Fallback si falla la API
    today = datetime.date.today()
    forecast = []
    # Simular una serie de 7 días con clima veraniego promedio para Entre Ríos
    # Lluvias esporádicas y ETP promedio de 5mm en diciembre/enero
    for i in range(1, 8):
        f_date = today + datetime.timedelta(days=i)
        # 10% de probabilidad de lluvia
        lluvia_sim = 15.0 if i == 3 else 0.0 # lluvia simulada el día 3
        forecast.append({
            "fecha": f_date,
            "lluvia": lluvia_sim,
            "etp": 5.2 # promedio verano
        })
    return forecast


import os

class WeatherHistory:
    def __init__(self, excel_path: str = None):
        if excel_path is None:
            # Ubicar el archivo en la raíz del proyecto para compatibilidad local y cloud (Linux/Windows)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.excel_path = os.path.join(base_dir, "Balance hidrico - Maiz - El Trebol.xlsx")
        else:
            self.excel_path = excel_path
        self._cache_data = None

    def load_from_excel(self) -> pd.DataFrame:
        """Carga y procesa los datos históricos de clima de la planilla Excel de referencia."""
        if self._cache_data is not None:
            return self._cache_data
            
        import openpyxl
        wb = openpyxl.load_workbook(self.excel_path, data_only=True)
        sheet = wb["ET - SGR"]
        
        records = []
        for r in range(2, 154):
            date_val = sheet.cell(r, 1).value
            if date_val is None or str(date_val).strip() == "Total":
                break
            
            # Si el valor de la fecha viene como datetime, lo convertimos
            if isinstance(date_val, datetime.datetime):
                fecha = date_val.date()
            else:
                fecha = pd.to_datetime(date_val).date()
                
            lluvia = sheet.cell(r, 4).value
            coef = sheet.cell(r, 5).value
            etp = sheet.cell(r, 8).value
            riego = sheet.cell(r, 3).value
            
            records.append({
                "fecha": fecha,
                "lluvia": float(lluvia) if lluvia is not None else 0.0,
                "coef_lluvia": float(coef) if coef is not None else 1.0,
                "etp": float(etp) if etp is not None else 0.0,
                "riego": float(riego) if riego is not None else 0.0
            })
            
        df = pd.DataFrame(records)
        self._cache_data = df
        return df
