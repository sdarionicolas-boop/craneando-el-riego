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


def fetch_and_parse_dg_hy_os(url: str) -> dict:
    """
    Descarga y parsea el archivo de reporte NOAA en formato texto de la DGHyOS.
    Retorna un diccionario de {date_obj: {'rain': float, 'et': float}} o None si falla.
    """
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"Error {response.status_code} al descargar reporte NOAA de: {url}")
            return None
        content = response.text
    except Exception as e:
        print(f"Excepción al descargar reporte NOAA de {url}: {e}")
        return None

    lines = content.splitlines()
    separator_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith('----') and len(line.strip()) > 50:
            separator_idx = idx
            break
            
    if separator_idx == -1:
        print(f"No se encontró línea divisoria en el reporte de: {url}")
        return None
        
    header_line = lines[separator_idx - 1]
    
    # Mapear dinámicamente las columnas para tolerar diferencias de orden/nombres
    import re
    tokens = []
    for match in re.finditer(r'\S+', header_line):
        tokens.append({
            'name': match.group(),
            'start': match.start(),
            'end': match.end()
        })
        
    date_col_idx = -1
    rain_col_idx = -1
    et_col_idx = -1
    
    for idx, t in enumerate(tokens):
        name_lower = t['name'].lower()
        if name_lower in ['fecha', 'date']:
            date_col_idx = idx
        elif name_lower == 'rain':
            rain_col_idx = idx
        elif name_lower == 'et':
            et_col_idx = idx
            
    if date_col_idx == -1 or rain_col_idx == -1 or et_col_idx == -1:
        print(f"Columnas requeridas no encontradas en {url}. Fecha/Date Col: {date_col_idx}, Rain Col: {rain_col_idx}, ET Col: {et_col_idx}")
        return None
        
    daily_data = {}
    
    for r in range(separator_idx + 1, len(lines)):
        line = lines[r]
        if not line.strip():
            continue
            
        if any(keyword in line.upper() for keyword in ["MONTHLY", "AVERAGE", "TOTAL", "MAX", "MIN", "MEAN"]):
            break
            
        row_tokens = line.split()
        if len(row_tokens) < max(date_col_idx, rain_col_idx, et_col_idx) + 1:
            continue
            
        date_str = row_tokens[date_col_idx]
        if not re.match(r'^\d{2}/\d{2}/\d{2}$', date_str):
            continue
            
        # Parsear fecha
        try:
            date_obj = datetime.datetime.strptime(date_str, "%d/%m/%y").date()
        except Exception:
            continue
            
        # Extraer lluvia y ET manejando guiones y valores no numéricos
        rain_str = row_tokens[rain_col_idx]
        et_str = row_tokens[et_col_idx]
        
        rain_val = 0.0
        if rain_str != '---':
            try:
                rain_val = float(rain_str)
            except ValueError:
                pass
                
        et_val = 0.0
        if et_str != '---':
            try:
                et_val = float(et_str)
            except ValueError:
                pass
                
        if date_obj not in daily_data:
            daily_data[date_obj] = {
                'rain': 0.0,
                'et': 0.0
            }
            
        daily_data[date_obj]['rain'] += rain_val
        daily_data[date_obj]['et'] += et_val
        
    return daily_data


def get_realtime_weather_last_7_days(lat: float = LATITUDE, lon: float = LONGITUDE) -> tuple:
    """
    Obtiene la lluvia y ET de los últimos 7 días usando como fuente principal Urdinarrain (DGHyOS),
    con fallback a Concepción del Uruguay y fallback secundario a NASA POWER (Open-Meteo Archive).
    Retorna una tupla (lista_diccionarios, active_source_str).
    """
    sources_to_try = [
        ("https://www.hidraulica.gob.ar/ema/ema-urdinarrain/downld08.txt", "DGHyOS Estación Urdinarrain"),
        ("https://www.hidraulica.gob.ar/ema/ema-curuguay/downld08.txt", "DGHyOS Estación Concepción del Uruguay (Fallback)")
    ]
    
    parsed_data = None
    active_source = "Ninguna"
    
    for url, source_name in sources_to_try:
        print(f"Intentando obtener datos climáticos de: {source_name}...")
        data = fetch_and_parse_dg_hy_os(url)
        if data:
            # Validación de cordura de ET (para evitar fallas de lectura de datos erráticos)
            # Calculamos el promedio diario de ET. Si es ridículo (ej: < 0.2 mm o > 12.0 mm), descartamos la fuente.
            avg_et = sum(v['et'] for v in data.values()) / len(data) if data else 0.0
            if 0.2 <= avg_et <= 12.0:
                parsed_data = data
                active_source = source_name
                break
            else:
                print(f"DATOS CLIMÁTICOS RECHAZADOS: {source_name} arrojó promedio de ET inválido ({avg_et:.2f} mm/día). Activando fallback...")
        else:
            print(f"FALLBACK ACTIVADO: La estación {source_name} falló al descargar o parsear.")
            
    if parsed_data:
        # Convertir a lista de diccionarios ordenada
        result = []
        for d in sorted(parsed_data.keys()):
            result.append({
                "fecha": d,
                "lluvia": parsed_data[d]["rain"],
                "etp": parsed_data[d]["et"]
            })
        return result, active_source
        
    # FALLBACK SECUNDARIO: Open-Meteo Archive
    print("Iniciando Fallback Secundario (Open-Meteo Archive)...")
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=7)
    end_date = today - datetime.timedelta(days=1)
    
    url_meteo = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}&daily=precipitation_sum,et0_fao_evapotranspiration&timezone=America/Argentina/Buenos_Aires"
    
    try:
        response = requests.get(url_meteo, timeout=5)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            precip = daily.get("precipitation_sum", [])
            et0 = daily.get("et0_fao_evapotranspiration", [])
            
            result = []
            for i in range(len(dates)):
                f_date = datetime.datetime.strptime(dates[i], "%Y-%m-%d").date()
                result.append({
                    "fecha": f_date,
                    "lluvia": float(precip[i]) if precip[i] is not None else 0.0,
                    "etp": float(et0[i]) if et0[i] is not None else 2.5
                })
            return result, "Open-Meteo Historical Archive (Fallback Secundario)"
    except Exception as e:
        print(f"Error consultando Open-Meteo Archive: {e}")
        
    # Último Fallback: Generación estática según temporada
    print("Último Fallback: Generando datos simulados basados en promedios históricos...")
    result = []
    is_summer = today.month in [11, 12, 1, 2, 3]
    default_et = 5.5 if is_summer else 2.0
    for i in range(7, 0, -1):
        f_date = today - datetime.timedelta(days=i)
        result.append({
            "fecha": f_date,
            "lluvia": 0.0,
            "etp": default_et
        })
    return result, "Promedios Históricos Estacionales (Último Fallback)"
