# tests/test_crop.py
"""
Tests del modelo de cultivo: Kc, etapa fenológica y umbral por DAS.
"""

import datetime
import pytest
from core.config import UMBRAL_VEGETATIVO, UMBRAL_CRITICO
from core.crop import CropModel

SIEMBRA = datetime.date(2025, 9, 17)


@pytest.fixture
def crop():
    return CropModel(SIEMBRA)


class TestCropModel:
    def test_pre_siembra(self, crop):
        kc, stage = crop.get_kc_and_stage(SIEMBRA - datetime.timedelta(days=1))
        assert kc == 0.0
        assert stage == "Pre-siembra"
        assert crop.get_umbral_mm(SIEMBRA - datetime.timedelta(days=1)) == UMBRAL_VEGETATIVO

    def test_emergencia(self, crop):
        kc, stage = crop.get_kc_and_stage(SIEMBRA)
        assert kc == 0.09
        assert stage == "Emergencia"

    def test_pico_kc(self, crop):
        # DAS 100 (26/12) -> Kc 1.10, período crítico con umbral 72 mm
        fecha = SIEMBRA + datetime.timedelta(days=100)
        kc, stage = crop.get_kc_and_stage(fecha)
        assert kc == 1.10
        assert stage == "Desarrollo - PC"
        assert crop.get_umbral_mm(fecha) == UMBRAL_CRITICO

    def test_transicion_umbral_critico(self, crop):
        # El umbral crítico (72 mm) rige entre DAS 80 y 125
        assert crop.get_umbral_mm(SIEMBRA + datetime.timedelta(days=79)) == UMBRAL_VEGETATIVO
        assert crop.get_umbral_mm(SIEMBRA + datetime.timedelta(days=80)) == UMBRAL_CRITICO
        assert crop.get_umbral_mm(SIEMBRA + datetime.timedelta(days=125)) == UMBRAL_CRITICO
        assert crop.get_umbral_mm(SIEMBRA + datetime.timedelta(days=126)) == UMBRAL_VEGETATIVO

    def test_madurez(self, crop):
        fecha = SIEMBRA + datetime.timedelta(days=160)
        kc, stage = crop.get_kc_and_stage(fecha)
        assert kc == 0.05
        assert stage == "Madurez fisiológica"

    def test_acepta_fecha_string(self, crop):
        kc, _ = crop.get_kc_and_stage("2025-09-17")
        assert kc == 0.09

    def test_kc_ndvi_pendiente(self, crop):
        with pytest.raises(NotImplementedError):
            crop.get_kc_ndvi("San Martín", SIEMBRA)
