"""CP-013 · REQ-010: conversión CRC → USD (y viceversa) con tasa positiva.

Oráculo: USD = CRC / (CRC por USD). Con la tasa 500, CRC 9 000 000 = USD 18 000,00.
"""
from decimal import Decimal

import pytest

from app.services.errores import ReglaNegocio
from app.services.tipo_cambio import crc_a_usd, usd_a_crc, validar_tasa

pytestmark = pytest.mark.unitaria


def test_cp013_p1_se_visualiza_como_18000_usd():
    assert crc_a_usd(Decimal("9000000.00"), Decimal("500")) == Decimal("18000.00")


@pytest.mark.parametrize(
    "crc, tasa, usd",
    [
        ("500.00", "500", "1.00"),
        ("1000.00", "3", "333.33"),      # redondeo a céntimo
        ("2.50", "500", "0.01"),         # 0,005 sube (half-up)
        ("0.01", "500", "0.00"),
        ("9500000.00", "500.5000", "18981.02"),
    ],
)
def test_cp013_conversion_y_redondeo(crc, tasa, usd):
    assert crc_a_usd(Decimal(crc), Decimal(tasa)) == Decimal(usd)


def test_cp013_conversion_inversa():
    assert usd_a_crc(Decimal("18000.00"), Decimal("500")) == Decimal("9000000.00")


@pytest.mark.parametrize("tasa", ["0", "-1", "-0.0001", "abc", "", "NaN", "Infinity", "500.12345", None, True])
def test_cp013_tasa_invalida_rechazada(tasa):
    with pytest.raises(ReglaNegocio):
        crc_a_usd(Decimal("1000"), tasa)


def test_cp013_tasa_valida_se_normaliza_a_4_decimales():
    assert validar_tasa("500") == Decimal("500.0000")
