# core/soil.py
"""
Módulo para el cálculo de constantes hídricas del suelo (CC, PMP, Agua Útil).
"""

class SoilProfile:
    def __init__(self, name: str, horizontes: list, factor_ajuste: float, techo_sistema: float, infiltracion_max: float, caudal_pivote: float = 1.4, eficiencia_riego: float = 0.90):
        self.name = name
        self.horizontes = horizontes
        self.factor_ajuste = factor_ajuste
        self.techo_sistema = techo_sistema
        self.infiltracion_max = infiltracion_max
        self.caudal_pivote = caudal_pivote
        self.eficiencia_riego = eficiencia_riego

    @classmethod
    def from_config(cls, name: str, config_dict: dict):
        """Crea una instancia a partir del diccionario de configuración."""
        cfg = config_dict[name]
        return cls(
            name=name,
            horizontes=cfg["horizontes"],
            factor_ajuste=cfg["factor_ajuste"],
            techo_sistema=cfg["techo_sistema"],
            infiltracion_max=cfg["infiltracion_max"],
            caudal_pivote=cfg.get("caudal_pivote", 1.4),
            eficiencia_riego=cfg.get("eficiencia_riego", 0.90)
        )

    def calculate_au_horizon(self, CC: float, PMP: float, DA: float, espesor_dm: float) -> float:
        """
        Calcula el Agua Útil de un horizonte en mm.
        Fórmula: AU = (CC - PMP) / 100 * DA * (espesor_dm * 10) * 10
        Simplificado: AU = (CC - PMP) * DA * espesor_dm
        """
        return (CC - PMP) * DA * espesor_dm

    def calculate_au_total(self) -> float:
        """Calcula la capacidad de Agua Útil total sin corregir (mm)."""
        total = 0.0
        for h in self.horizontes:
            total += self.calculate_au_horizon(h["cc"], h["pmp"], h["da"], h["espesor_dm"])
        return round(total, 3)

    def calculate_au_corregida(self) -> float:
        """Calcula el Agua Útil corregida por el factor de raíces (mm)."""
        return round(self.calculate_au_total() * self.factor_ajuste, 3)

    def calculate_au_from_vwc(self, vwc_list: list) -> float:
        """
        Convierte una lista de humedades volumétricas (% VWC) por horizonte
        a Agua Útil corregida total en mm.
        La lista vwc_list debe contener el % VWC en el mismo orden que self.horizontes.
        """
        total_au = 0.0
        for i, h in enumerate(self.horizontes):
            if i >= len(vwc_list) or vwc_list[i] is None:
                continue
            vwc = vwc_list[i]
            # Limitar al rango físico [PMP, CC]
            vwc_limited = max(h["pmp"], min(h["cc"], vwc))
            # Calcular mm de AU para este horizonte
            au_horizon = (vwc_limited - h["pmp"]) * h["da"] * h["espesor_dm"]
            total_au += au_horizon
            
        return round(total_au * self.factor_ajuste, 4)
