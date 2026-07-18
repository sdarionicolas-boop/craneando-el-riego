# core/balance.py
"""
Módulo del motor matemático del balance hídrico diario.
"""

from core.config import LLUVIA_EFECTIVA_RANGOS

def calculate_lluvia_efectiva(lluvia: float, coef_override: float = None) -> float:
    """
    Calcula la lluvia efectiva en mm basándose en rangos predefinidos o un coeficiente override.
    
    Lógica de rangos:
    - PP < 15 mm -> Coef = 1.00
    - PP 15-30 mm -> Coef = 0.85
    - PP 30-60 mm -> Coef = 0.70
    - PP > 60 mm -> Coef = 0.55
    """
    if lluvia is None or lluvia <= 0:
        return 0.0
    
    if coef_override is not None:
        return round(lluvia * coef_override, 4)
        
    # Lógica por rangos (de config.py)
    coef = 1.00
    for limite, c in LLUVIA_EFECTIVA_RANGOS:
        if lluvia <= limite:
            coef = c
            break
            
    return round(lluvia * coef, 4)


class DailyWaterBalance:
    def __init__(self, techo_sistema: float):
        self.techo = techo_sistema

    def calculate_next_day(
        self,
        au_prev: float,
        au_secano_prev: float,
        riego: float,
        lluvia: float,
        etp: float,
        kc: float,
        coef_override: float = None
    ) -> dict:
        """
        Calcula el balance hídrico del día siguiente para ambos escenarios (Riego y Secano).
        
        Retorna un diccionario con:
        - etc: Evapotranspiración del cultivo (mm)
        - lluvia_ef: Lluvia efectiva (mm)
        - au_riego: Nuevo balance con riego (mm)
        - au_secano: Nuevo balance de secano (mm)
        """
        # Asegurar valores no nulos
        riego_val = riego if riego is not None else 0.0
        lluvia_val = lluvia if lluvia is not None else 0.0
        etp_val = etp if etp is not None else 0.0
        kc_val = kc if kc is not None else 0.0
        
        # Evapotranspiración del cultivo
        etc = round(etp_val * kc_val, 4)
        
        # Lluvia efectiva
        lluvia_ef = calculate_lluvia_efectiva(lluvia_val, coef_override)
        
        # 1. Balance con Riego (Actual)
        au_riego_raw = au_prev + riego_val + lluvia_ef - etc
        au_riego = round(max(0.0, min(self.techo, au_riego_raw)), 4)
        
        # 2. Balance Secano (Testigo sin riego)
        au_secano_raw = au_secano_prev + lluvia_ef - etc
        au_secano = round(max(0.0, min(self.techo, au_secano_raw)), 4)
        
        return {
            "etc": etc,
            "lluvia_ef": lluvia_ef,
            "au_riego": au_riego,
            "au_secano": au_secano
        }
