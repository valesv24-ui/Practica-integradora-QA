"""CP-016 (reglas de estado) y CP-020 (bordes) · REQ-002, REQ-003.

Reglas puras, sin base de datos.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.services import reglas_licitaciones as r
from app.services.errores import Conflicto, ReglaNegocio

pytestmark = pytest.mark.unitaria

AHORA = datetime(2026, 12, 1, 10, 0, 0)


# ---------- CP-016 · REQ-003 ----------
@pytest.mark.parametrize("actual, nuevo", [
    (r.ESTADO_BORRADOR, r.ESTADO_PUBLICADA),
    (r.ESTADO_BORRADOR, r.ESTADO_CERRADA),
    (r.ESTADO_PUBLICADA, r.ESTADO_CERRADA),
])
def test_cp016_transiciones_permitidas(actual, nuevo):
    r.validar_transicion(actual, nuevo)


@pytest.mark.parametrize("actual, nuevo", [
    (r.ESTADO_PUBLICADA, r.ESTADO_BORRADOR),   # no se regresa a Borrador
    (r.ESTADO_CERRADA, r.ESTADO_PUBLICADA),    # no se reabre
    (r.ESTADO_CERRADA, r.ESTADO_BORRADOR),
    (r.ESTADO_BORRADOR, r.ESTADO_BORRADOR),
    (r.ESTADO_PUBLICADA, r.ESTADO_PUBLICADA),
    (r.ESTADO_CERRADA, r.ESTADO_CERRADA),
])
def test_cp016_transiciones_prohibidas(actual, nuevo):
    with pytest.raises(Conflicto):
        r.validar_transicion(actual, nuevo)


def test_cp016_estado_desconocido():
    with pytest.raises(ReglaNegocio):
        r.validar_transicion(r.ESTADO_BORRADOR, "Anulada")


# ---------- REQ-002 ----------
def test_codigo_se_normaliza_sin_mayusculas_ni_espacios_laterales():
    assert r.normalizar_codigo("  LIC-2026-001 ") == r.normalizar_codigo("lic-2026-001")


@pytest.mark.parametrize("codigo", ["", "   ", "LIC 001", "LIC<script>", "-LIC", "A" * 41])
def test_codigo_invalido(codigo):
    with pytest.raises(ReglaNegocio):
        r.validar_codigo(codigo)


@pytest.mark.parametrize("titulo", ["", "    "])
def test_titulo_vacio_rechazado(titulo):
    with pytest.raises(ReglaNegocio):
        r.validar_titulo(titulo)


# ---------- CP-020 · borde / negativo ----------
@pytest.mark.parametrize("valor", ["0", "0.00", "-1", "-0.01", "abc", "", "NaN", "10.001", None, False])
def test_cp020_presupuesto_invalido(valor):
    with pytest.raises(ReglaNegocio):
        r.convertir_presupuesto(valor)


@pytest.mark.parametrize("valor, esperado", [("0.01", "0.01"), ("10000000", "10000000.00"), (Decimal("5.5"), "5.50")])
def test_presupuesto_valido(valor, esperado):
    assert r.convertir_presupuesto(valor) == Decimal(esperado)


def test_cp020_cierre_en_el_pasado_rechazado():
    with pytest.raises(ReglaNegocio):
        r.validar_cierre_futuro(AHORA - timedelta(seconds=1), AHORA)


def test_cp020_cierre_exactamente_ahora_rechazado():
    with pytest.raises(ReglaNegocio):
        r.validar_cierre_futuro(AHORA, AHORA)


def test_cp020_cierre_un_segundo_futuro_aceptado():
    r.validar_cierre_futuro(AHORA + timedelta(seconds=1), AHORA)


@pytest.mark.parametrize("texto", ["no es fecha", "", "2026-13-45", None, 123])
def test_cierre_ilegible_rechazado(texto):
    with pytest.raises(ReglaNegocio):
        r.convertir_cierre(texto)


def test_cierre_acepta_formato_de_formulario():
    assert r.convertir_cierre("2026-12-01T10:00") == AHORA
