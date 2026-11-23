"""CP-012 · REQ-009: rangos del aprobador, sin traslape.

Oráculo: 0,01–999 999,99 Encargado de área · 1 000 000–9 999 999,99 Gerencia ·
≥ 10 000 000 Junta Directiva (sobre el monto de la mejor oferta válida).
"""
from decimal import Decimal

import pytest

from app.services.errores import ReglaNegocio
from app.services.evaluacion import RANGOS_APROBACION, aprobador_para, validar_rangos

pytestmark = pytest.mark.unitaria


@pytest.mark.parametrize(
    "monto, esperado",
    [
        ("0.01", "Encargado de área"),
        ("500000.00", "Encargado de área"),
        ("999999.99", "Encargado de área"),
        ("1000000.00", "Gerencia"),            # frontera inferior de Gerencia
        ("9000000.00", "Gerencia"),            # monto de L1
        ("9999999.99", "Gerencia"),
        ("10000000.00", "Junta Directiva"),    # frontera inferior de Junta
        ("250000000.00", "Junta Directiva"),
    ],
)
def test_cp012_rangos_del_aprobador(monto, esperado):
    assert aprobador_para(Decimal(monto)) == esperado


@pytest.mark.parametrize("monto", ["0", "0.00", "-1.00"])
def test_cp012_monto_no_positivo_rechazado(monto):
    with pytest.raises(ReglaNegocio):
        aprobador_para(Decimal(monto))


def test_cp012_rangos_por_defecto_no_se_traslapan():
    validar_rangos(RANGOS_APROBACION)


def test_cp012_rangos_traslapados_se_detectan():
    malos = [(Decimal("0.01"), Decimal("2000000"), "A"), (Decimal("1000000"), None, "B")]
    with pytest.raises(ValueError):
        validar_rangos(malos)


def test_cp012_rangos_son_configurables():
    otros = [(Decimal("0.01"), Decimal("99.99"), "Chico"), (Decimal("100"), None, "Grande")]
    assert aprobador_para(Decimal("99.99"), otros) == "Chico"
    assert aprobador_para(Decimal("100"), otros) == "Grande"
