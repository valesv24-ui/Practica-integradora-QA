"""Reglas puras de Ofertas.

CP-002 · REQ-005: límites de monto.
CP-003 · REQ-004: vencimiento exactamente en el cierre.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models import ESTADO_PUBLICADA
from app.services import ofertas as svc
from app.services.errores import ReglaNegocio

pytestmark = pytest.mark.unitaria

PRESUPUESTO = Decimal("10000000.00")
CIERRE = datetime(2026, 12, 1, 15, 0, 0)


# ---------- CP-002 · montos ----------
@pytest.mark.parametrize("monto", ["9000000.00", "0.01", "10000000.00"])
def test_cp002_montos_validos(monto):
    # Igual al presupuesto es válido (REQ-005)
    svc.validar_monto(Decimal(monto), PRESUPUESTO)


@pytest.mark.parametrize("monto", ["0", "0.00", "-1.00", "10000000.01"])
def test_cp002_montos_invalidos(monto):
    with pytest.raises(ReglaNegocio):
        svc.validar_monto(Decimal(monto), PRESUPUESTO)


@pytest.mark.parametrize("entrada", ["abc", "", "1.001", "NaN", "Infinity"])
def test_cp002_entrada_no_numerica_o_con_mas_de_dos_decimales(entrada):
    with pytest.raises(ReglaNegocio):
        svc.convertir_monto(entrada)


# ---------- CP-003 · plazo ----------
def test_cp003_un_segundo_antes_del_cierre_se_acepta():
    svc.validar_plazo(ESTADO_PUBLICADA, CIERRE, CIERRE - timedelta(seconds=1))


def test_cp003_exactamente_en_el_cierre_se_rechaza():
    with pytest.raises(ReglaNegocio):
        svc.validar_plazo(ESTADO_PUBLICADA, CIERRE, CIERRE)


def test_cp003_despues_del_cierre_se_rechaza():
    with pytest.raises(ReglaNegocio):
        svc.validar_plazo(ESTADO_PUBLICADA, CIERRE, CIERRE + timedelta(microseconds=1))
