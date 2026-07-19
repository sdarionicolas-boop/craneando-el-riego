# tests/test_balance.py
"""
Tests del motor de balance hídrico diario y de la lluvia efectiva.
"""

import pytest
from core.balance import calculate_lluvia_efectiva, DailyWaterBalance


class TestLluviaEfectiva:
    def test_sin_lluvia(self):
        assert calculate_lluvia_efectiva(0.0) == 0.0
        assert calculate_lluvia_efectiva(None) == 0.0
        assert calculate_lluvia_efectiva(-5.0) == 0.0

    @pytest.mark.parametrize("lluvia,esperado", [
        (10.0, 10.0),      # < 15 -> 100%
        (14.9, 14.9),      # < 15 -> 100%
        (15.0, 12.75),     # 15-30 -> 85% (borde inferior inclusivo)
        (30.0, 25.5),      # 15-30 -> 85% (borde superior inclusivo)
        (30.1, 21.07),     # 30-60 -> 70%
        (60.0, 42.0),      # 30-60 -> 70% (borde superior inclusivo)
        (61.0, 33.55),     # > 60 -> 55%
        (100.0, 55.0),     # > 60 -> 55%
    ])
    def test_rangos(self, lluvia, esperado):
        assert calculate_lluvia_efectiva(lluvia) == pytest.approx(esperado)

    def test_coef_override(self):
        assert calculate_lluvia_efectiva(20.0, coef_override=0.5) == 10.0
        # El override tiene prioridad sobre los rangos
        assert calculate_lluvia_efectiva(100.0, coef_override=1.0) == 100.0


class TestDailyWaterBalance:
    def setup_method(self):
        self.engine = DailyWaterBalance(techo_sistema=120.0)

    def test_dia_planilla_fila_2(self):
        # Primera fila de la planilla El Trébol: AU 90, ETP 2.4, Kc 0.09 -> 89.784
        res = self.engine.calculate_next_day(
            au_prev=90.0, au_secano_prev=90.0, riego=0.0, lluvia=0.0, etp=2.4, kc=0.09
        )
        assert res["etc"] == pytest.approx(0.216)
        assert res["au_riego"] == pytest.approx(89.784)
        assert res["au_secano"] == pytest.approx(89.784)

    def test_techo_sistema(self):
        # La planilla capea AU en el techo (fila 31: 108.939 + 20 - 1.275 -> 120)
        res = self.engine.calculate_next_day(
            au_prev=108.939, au_secano_prev=90.0, riego=20.0, lluvia=0.0, etp=1.275, kc=1.0
        )
        assert res["au_riego"] == 120.0

    def test_piso_cero(self):
        res = self.engine.calculate_next_day(
            au_prev=1.0, au_secano_prev=1.0, riego=0.0, lluvia=0.0, etp=10.0, kc=1.0
        )
        assert res["au_riego"] == 0.0
        assert res["au_secano"] == 0.0

    def test_secano_no_recibe_riego(self):
        res = self.engine.calculate_next_day(
            au_prev=80.0, au_secano_prev=80.0, riego=20.0, lluvia=0.0, etp=0.0, kc=0.0
        )
        assert res["au_riego"] == 100.0
        assert res["au_secano"] == 80.0

    def test_valores_nulos(self):
        res = self.engine.calculate_next_day(
            au_prev=90.0, au_secano_prev=90.0, riego=None, lluvia=None, etp=None, kc=None
        )
        assert res["au_riego"] == 90.0
        assert res["au_secano"] == 90.0
