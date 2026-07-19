# tests/test_soil.py
"""
Tests del cálculo de constantes hídricas del suelo.
"""

import pytest
from core.config import SUELO_CONFIG
from core.soil import SoilProfile


@pytest.fixture
def perfil():
    return SoilProfile.from_config("San Martín", SUELO_CONFIG)


class TestSoilProfile:
    def test_au_horizonte(self, perfil):
        # H1: (25.7 - 14.8) * 1.31 * 2.0 = 28.558 mm
        assert perfil.calculate_au_horizon(25.7, 14.8, 1.31, 2.0) == pytest.approx(28.558)

    def test_au_total(self, perfil):
        # H1 28.558 + H2 20.25 + H3 96.6 = 145.408 mm
        assert perfil.calculate_au_total() == pytest.approx(145.408)

    def test_au_corregida(self, perfil):
        # 145.408 * 0.75 = 109.056 mm
        assert perfil.calculate_au_corregida() == pytest.approx(109.056)

    def test_vwc_en_cc_equivale_au_corregida(self, perfil):
        # Sensores marcando CC en los 3 horizontes -> AU corregida completa
        vwc_cc = [h["cc"] for h in perfil.horizontes]
        assert perfil.calculate_au_from_vwc(vwc_cc) == pytest.approx(perfil.calculate_au_corregida())

    def test_vwc_en_pmp_da_cero(self, perfil):
        vwc_pmp = [h["pmp"] for h in perfil.horizontes]
        assert perfil.calculate_au_from_vwc(vwc_pmp) == 0.0

    def test_vwc_fuera_de_rango_se_limita(self, perfil):
        # Lecturas por encima de CC se recortan a CC; por debajo de PMP, a PMP
        assert perfil.calculate_au_from_vwc([99.0, 99.0, 99.0]) == pytest.approx(perfil.calculate_au_corregida())
        assert perfil.calculate_au_from_vwc([1.0, 1.0, 1.0]) == 0.0

    def test_vwc_lista_incompleta(self, perfil):
        # Horizontes sin lectura se omiten sin fallar
        assert perfil.calculate_au_from_vwc([20.0]) > 0.0
        assert perfil.calculate_au_from_vwc([]) == 0.0
