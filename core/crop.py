# core/crop.py
"""
Módulo para administrar el Kc (Coeficiente de Cultivo) e interpolación por DAS.
También incluye la interfaz stub para el Kc basado en NDVI.
"""

from core.config import KC_DAS_TABLE, STAGE_DAS_TABLE, UMBRAL_VEGETATIVO

class CropModel:
    def __init__(self, siembra_date):
        self.siembra_date = siembra_date

    def get_das(self, current_date) -> int:
        """Calcula los Días Desde Emergencia/Siembra (DAS)."""
        if isinstance(current_date, str):
            import pandas as pd
            current_date = pd.to_datetime(current_date).date()
        elif hasattr(current_date, "date"): # handles datetime objects
            current_date = current_date.date()
        
        siembra = self.siembra_date.date() if hasattr(self.siembra_date, "date") else self.siembra_date
        return (current_date - siembra).days

    def get_kc_and_stage(self, current_date) -> tuple:
        """
        Retorna el Kc y el Nombre del Estado Fenológico para una fecha dada,
        basado en las tablas de DAS en config.
        """
        das = self.get_das(current_date)
        if das < 0:
            # Antes de la siembra o emergencia, Kc = 0.0, etapa = Pre-siembra
            return 0.0, "Pre-siembra"
        
        # 1. Obtener Kc
        kc = 0.05
        for start, end, k in KC_DAS_TABLE:
            if start <= das <= end:
                kc = k
                break
                
        # 2. Obtener Etapa
        stage = "Madurez fisiológica"
        for start, end, name, _ in STAGE_DAS_TABLE:
            if start <= das <= end:
                stage = name
                break
                
        return kc, stage

    def get_umbral_mm(self, current_date) -> float:
        """Retorna el umbral en mm absoluto para una fecha dada."""
        das = self.get_das(current_date)
        if das < 0:
            return UMBRAL_VEGETATIVO
            
        for start, end, _, umbral in STAGE_DAS_TABLE:
            if start <= das <= end:
                return umbral
                
        return UMBRAL_VEGETATIVO

    def get_kc_ndvi(self, lote: str, date) -> float:
        """
        Interfaz stub para el cálculo de Kc basado en NDVI ( Mauricio's GEE workflow ).
        Fórmula teórica: Kc_NDVI = 1.44 * NDVI - 0.1
        
        Esta interfaz está marcada como PENDIENTE. Retorna una excepción o mock controlado
        para no dar un falso verde antes de resolver la ingesta de NDVI (GEE vs CSV).
        """
        # Explicación: No implementar completamente para evitar un falso verde y asegurar validación real posterior.
        raise NotImplementedError(
            "La ingesta de datos de NDVI (GEE o CSV histórico) está pendiente. "
            "Esta función debe configurarse con datos de satélite reales en la Fase v2."
        )
