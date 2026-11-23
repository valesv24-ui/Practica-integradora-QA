"""Tipo de cambio CRC por USD (REQ-010).

Solo se persisten importes en CRC. La tasa se guarda con su fecha (historial) y
sirve únicamente para mostrar importes en USD: USD = CRC / (CRC por USD).
La tasa puede configurarse a mano o consultarse a un servicio externo.
"""
import json
import os
import urllib.request
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.services.errores import Conflicto, ErrorNegocio, ReglaNegocio

TASA_MAXIMA = Decimal("99999999.9999")  # cabe en Numeric(12, 4)
_CENTAVO = Decimal("0.01")
_CUATRO = Decimal("0.0001")


class ServicioNoDisponible(ErrorNegocio):
    """El servicio externo de tipo de cambio falló o devolvió datos inválidos."""
    status_code = 503


def validar_tasa(valor) -> Decimal:
    """Tasa positiva, finita y con máximo 4 decimales."""
    if valor is None or isinstance(valor, bool):
        raise ReglaNegocio("El tipo de cambio debe ser un número mayor que cero.")
    try:
        tasa = Decimal(str(valor).strip())
    except InvalidOperation:
        raise ReglaNegocio("El tipo de cambio debe ser un número mayor que cero.") from None
    if not tasa.is_finite() or tasa <= 0:
        raise ReglaNegocio("El tipo de cambio debe ser un número mayor que cero.")
    if tasa != tasa.quantize(_CUATRO):
        raise ReglaNegocio("El tipo de cambio admite como máximo 4 decimales.")
    if tasa > TASA_MAXIMA:
        raise ReglaNegocio("El tipo de cambio excede el máximo permitido.")
    return tasa.quantize(_CUATRO)


def crc_a_usd(monto_crc, crc_por_usd) -> Decimal:
    """USD = CRC / (CRC por USD), redondeado a céntimo (half-up)."""
    tasa = validar_tasa(crc_por_usd)
    return (Decimal(str(monto_crc)) / tasa).quantize(_CENTAVO, rounding=ROUND_HALF_UP)


def usd_a_crc(monto_usd, crc_por_usd) -> Decimal:
    """CRC = USD × (CRC por USD), redondeado a céntimo (half-up)."""
    tasa = validar_tasa(crc_por_usd)
    return (Decimal(str(monto_usd)) * tasa).quantize(_CENTAVO, rounding=ROUND_HALF_UP)


# ---------- Servicio externo ----------
def proveedor_http() -> object:
    """Consulta TIPO_CAMBIO_URL (JSON con el campo 'venta'). Solo se usa al sincronizar."""
    url = os.environ.get("TIPO_CAMBIO_URL")
    if not url:
        raise RuntimeError("TIPO_CAMBIO_URL no está configurada")
    with urllib.request.urlopen(url, timeout=3) as r:  # noqa: S310 (URL configurada por el equipo)
        return json.loads(r.read().decode("utf-8"))["venta"]


def consultar_servicio_externo(proveedor=None) -> Decimal:
    """Obtiene la tasa del servicio; cualquier falla se traduce a un 503 controlado."""
    try:
        bruto = (proveedor or proveedor_http)()
    except Exception:
        raise ServicioNoDisponible("El servicio de tipo de cambio no está disponible. Configure la tasa manualmente.") from None
    try:
        return validar_tasa(bruto)
    except ReglaNegocio:
        raise ServicioNoDisponible("El servicio de tipo de cambio devolvió una tasa inválida.") from None


# ---------- Con base de datos ----------
def registrar_tasa(db, valor, fuente: str = "manual", ahora: datetime | None = None):
    from app.models import TipoCambio

    tasa = TipoCambio(crc_por_usd=validar_tasa(valor), fecha=ahora or datetime.now(), fuente=fuente)
    db.add(tasa)
    db.commit()
    db.refresh(tasa)
    return tasa


def sincronizar_desde_servicio(db, proveedor=None, ahora: datetime | None = None):
    tasa = consultar_servicio_externo(proveedor)
    return registrar_tasa(db, tasa, fuente="servicio", ahora=ahora)


def obtener_actual(db):
    from app.models import TipoCambio

    return db.query(TipoCambio).order_by(TipoCambio.id.desc()).first()


def requerir_actual(db):
    actual = obtener_actual(db)
    if actual is None:
        raise Conflicto("No hay tipo de cambio configurado. Regístrelo antes de ver importes en USD.")
    return actual


def historial(db, limite: int = 10):
    from app.models import TipoCambio

    return db.query(TipoCambio).order_by(TipoCambio.id.desc()).limit(limite).all()
