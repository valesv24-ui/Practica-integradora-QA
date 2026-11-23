"""Reglas puras de Licitaciones (sin base de datos): REQ-002 y REQ-003.

Persona B (Maykel). Se mantienen sin dependencias de SQLAlchemy para poder
probarlas como pruebas unitarias.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.services.errores import ReglaNegocio

ESTADO_BORRADOR = "Borrador"
ESTADO_PUBLICADA = "Publicada"
ESTADO_CERRADA = "Cerrada"

# REQ-003: Borrador -> Publicada/Cerrada y Publicada -> Cerrada. Nada más.
TRANSICIONES = {
    ESTADO_BORRADOR: {ESTADO_PUBLICADA, ESTADO_CERRADA},
    ESTADO_PUBLICADA: {ESTADO_CERRADA},
    ESTADO_CERRADA: set(),
}

LARGO_CODIGO = 40
LARGO_TITULO = 200
PRESUPUESTO_MAXIMO = Decimal("99999999999999.99")  # cabe en Numeric(16, 2)
_PATRON_CODIGO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


def limpiar_codigo(codigo: str) -> str:
    """Recorta espacios laterales (REQ-002)."""
    return (codigo or "").strip()


def normalizar_codigo(codigo: str) -> str:
    """Clave de unicidad: sin espacios laterales y sin distinguir mayúsculas."""
    return limpiar_codigo(codigo).casefold()


def validar_codigo(codigo: str) -> str:
    limpio = limpiar_codigo(codigo)
    if not limpio:
        raise ReglaNegocio("El código de la licitación es obligatorio.")
    if len(limpio) > LARGO_CODIGO:
        raise ReglaNegocio(f"El código no puede superar {LARGO_CODIGO} caracteres.")
    if not _PATRON_CODIGO.fullmatch(limpio):
        raise ReglaNegocio("El código solo admite letras, números, punto, guion, guion bajo y diagonal (sin espacios).")
    return limpio


def validar_titulo(titulo: str) -> str:
    limpio = " ".join((titulo or "").split())
    if not limpio:
        raise ReglaNegocio("El título de la licitación es obligatorio.")
    if len(limpio) > LARGO_TITULO:
        raise ReglaNegocio(f"El título no puede superar {LARGO_TITULO} caracteres.")
    return limpio


def convertir_presupuesto(valor) -> Decimal:
    """Entrada -> Decimal con máximo 2 decimales y mayor que cero (REQ-002)."""
    if valor is None or isinstance(valor, bool):
        raise ReglaNegocio("El presupuesto debe ser un número válido.")
    try:
        monto = Decimal(str(valor).strip())
    except InvalidOperation:
        raise ReglaNegocio("El presupuesto debe ser un número válido.") from None
    if not monto.is_finite():
        raise ReglaNegocio("El presupuesto debe ser un número válido.")
    if monto != monto.quantize(Decimal("0.01")):
        raise ReglaNegocio("El presupuesto admite como máximo 2 decimales.")
    monto = monto.quantize(Decimal("0.01"))
    if monto <= 0:
        raise ReglaNegocio("El presupuesto debe ser mayor que cero.")
    if monto > PRESUPUESTO_MAXIMO:
        raise ReglaNegocio("El presupuesto excede el máximo permitido.")
    return monto


def convertir_cierre(valor) -> datetime:
    """Acepta datetime o texto ISO (incluye 'AAAA-MM-DDTHH:MM' de los formularios).

    Se guarda como hora local sin zona, igual que el resto de la aplicación.
    """
    if isinstance(valor, datetime):
        dt = valor
    elif isinstance(valor, str):
        try:
            dt = datetime.fromisoformat(valor.strip())
        except ValueError:
            raise ReglaNegocio("La fecha y hora de cierre no es válida.") from None
    else:
        raise ReglaNegocio("La fecha y hora de cierre es obligatoria.")
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.replace(microsecond=0)


def validar_cierre_futuro(cierre: datetime, ahora: datetime) -> None:
    """REQ-002: el cierre debe ser posterior al instante actual."""
    if cierre <= ahora:
        raise ReglaNegocio("La fecha y hora de cierre debe ser futura.")


def validar_transicion(actual: str, nuevo: str) -> None:
    """REQ-003: solo las transiciones permitidas; no se reabre ni se regresa."""
    if nuevo not in TRANSICIONES:
        raise ReglaNegocio("Estado desconocido (Borrador, Publicada o Cerrada).")
    if nuevo not in TRANSICIONES[actual]:
        from app.services.errores import Conflicto

        raise Conflicto(f"Transición no permitida: {actual} → {nuevo}.")
