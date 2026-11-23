"""CP-011 · REQ-008: clasificación del ahorro en la frontera 10 % / 5 % / 0 %.

Oráculo: fórmula del enunciado, ahorro = ((presupuesto − mejor oferta)/presupuesto)×100;
≥ 10 % conveniente, > 0 y < 10 % aceptable, 0 % válida sin ahorro.
"""
from decimal import Decimal

import pytest

from app.services.errores import ReglaNegocio
from app.services.evaluacion import (CLASIF_ACEPTABLE, CLASIF_CONVENIENTE, CLASIF_SIN_AHORRO,
                                     clasificar_ahorro)

pytestmark = pytest.mark.unitaria

PRESUPUESTO = Decimal("1000000.00")


@pytest.mark.parametrize(
    "mejor, porcentaje, clasificacion",
    [
        ("900000.00", "10.00", CLASIF_CONVENIENTE),    # justo en el 10 %
        ("950000.00", "5.00", CLASIF_ACEPTABLE),       # 5 %
        ("1000000.00", "0.00", CLASIF_SIN_AHORRO),     # igual al presupuesto: 0 %
        ("899999.99", "10.00", CLASIF_CONVENIENTE),    # apenas sobre el 10 %
        ("900000.01", "10.00", CLASIF_ACEPTABLE),      # un céntimo bajo el 10 %: se muestra 10.00 pero NO es conveniente
        ("999999.99", "0.00", CLASIF_ACEPTABLE),       # ahorro de un céntimo: > 0 %
    ],
)
def test_cp011_clasificacion_en_fronteras(mejor, porcentaje, clasificacion):
    pct, clasif = clasificar_ahorro(PRESUPUESTO, Decimal(mejor))
    assert f"{pct:.2f}" == porcentaje
    assert clasif == clasificacion


def test_cp011_caso_l1_ahorro_10_por_ciento():
    pct, clasif = clasificar_ahorro(Decimal("10000000.00"), Decimal("9000000.00"))
    assert pct == Decimal("10.00") and clasif == CLASIF_CONVENIENTE


@pytest.mark.parametrize("presupuesto, mejor", [("0", "1"), ("1000000", "0"), ("1000000", "-1"), ("1000000", "1000000.01")])
def test_cp011_entradas_invalidas_rechazadas(presupuesto, mejor):
    with pytest.raises(ReglaNegocio):
        clasificar_ahorro(Decimal(presupuesto), Decimal(mejor))
