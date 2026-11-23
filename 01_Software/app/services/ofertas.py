"""Reglas de negocio de Ofertas (REQ-004, REQ-005, REQ-006)."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import ESTADO_PUBLICADA, Licitacion, Oferta, Proveedor
from app.services.errores import Conflicto, NoEncontrado, ReglaNegocio

DOS_DECIMALES = Decimal("0.01")


def convertir_monto(valor) -> Decimal:
    """Convierte la entrada a Decimal con máximo 2 decimales."""
    try:
        monto = Decimal(str(valor).strip().replace(" ", ""))
    except (InvalidOperation, AttributeError):
        raise ReglaNegocio("El monto debe ser un número válido.") from None
    if not monto.is_finite():
        raise ReglaNegocio("El monto debe ser un número válido.")
    if monto != monto.quantize(DOS_DECIMALES):
        raise ReglaNegocio("El monto admite como máximo 2 decimales.")
    return monto.quantize(DOS_DECIMALES)


def validar_monto(monto: Decimal, presupuesto_crc: Decimal) -> None:
    """REQ-005: 0 < monto <= presupuesto. Igual al presupuesto es válido."""
    if monto <= 0:
        raise ReglaNegocio("El monto de la oferta debe ser mayor que cero.")
    if monto > Decimal(presupuesto_crc):
        raise ReglaNegocio("El monto de la oferta no puede superar el presupuesto de la licitación.")


def validar_plazo(estado: str, cierre: datetime, ahora: datetime) -> None:
    """REQ-004: solo licitaciones Publicadas y antes del instante de cierre.

    Exactamente en el cierre (ahora == cierre) se rechaza.
    """
    if estado != ESTADO_PUBLICADA:
        raise ReglaNegocio(f"Solo se aceptan ofertas en licitaciones Publicadas (estado actual: {estado}).")
    if ahora > cierre:  # BUG-001 (defecto inducido): deberia ser >=
        raise ReglaNegocio("La licitación ya cerró: no se aceptan ofertas en o después de la hora de cierre.")


def registrar(db: Session, licitacion_id: int, proveedor_id: int, monto, ahora: datetime | None = None) -> Oferta:
    ahora = ahora or datetime.now()
    licitacion = db.get(Licitacion, licitacion_id)
    if licitacion is None:
        raise NoEncontrado("Licitación no encontrada.")
    if db.get(Proveedor, proveedor_id) is None:
        raise NoEncontrado("Proveedor no encontrado.")

    monto_dec = convertir_monto(monto)
    validar_plazo(licitacion.estado, licitacion.cierre, ahora)
    validar_monto(monto_dec, licitacion.presupuesto_crc)

    duplicada = (
        db.query(Oferta)
        .filter(Oferta.licitacion_id == licitacion_id, Oferta.proveedor_id == proveedor_id)
        .first()
    )
    if duplicada:
        raise Conflicto("Este proveedor ya presentó una oferta para esta licitación.")

    oferta = Oferta(
        licitacion_id=licitacion_id,
        proveedor_id=proveedor_id,
        monto_crc=monto_dec,
        registrada_en=ahora,
    )
    db.add(oferta)
    try:
        db.commit()
    except IntegrityError:  # la restricción UNIQUE de la BD también lo impide
        db.rollback()
        raise Conflicto("Este proveedor ya presentó una oferta para esta licitación.") from None
    db.refresh(oferta)
    return oferta


def listar(db: Session, licitacion_id: int | None = None, proveedor_id: int | None = None) -> list[Oferta]:
    q = db.query(Oferta).options(joinedload(Oferta.licitacion), joinedload(Oferta.proveedor))
    if licitacion_id is not None:
        q = q.filter(Oferta.licitacion_id == licitacion_id)
    if proveedor_id is not None:
        q = q.filter(Oferta.proveedor_id == proveedor_id)
    return q.order_by(Oferta.registrada_en, Oferta.id).all()


def obtener(db: Session, oferta_id: int) -> Oferta:
    o = db.get(Oferta, oferta_id)
    if o is None:
        raise NoEncontrado("Oferta no encontrada.")
    return o


def eliminar(db: Session, oferta_id: int, ahora: datetime | None = None) -> None:
    """Retirar una oferta solo mientras la licitación siga abierta."""
    o = obtener(db, oferta_id)
    validar_plazo(o.licitacion.estado, o.licitacion.cierre, ahora or datetime.now())
    db.delete(o)
    db.commit()
