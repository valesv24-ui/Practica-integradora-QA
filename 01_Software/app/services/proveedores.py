"""Reglas de negocio de Proveedores (REQ-001, REQ-012)."""
import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Oferta, Proveedor
from app.services.errores import Conflicto, NoEncontrado, ReglaNegocio

# REQ-012: solo letras (incluye tildes y ñ), números, espacios, punto, coma y paréntesis.
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,()]+$")
LARGO_MAXIMO = 120


def limpiar_nombre(nombre: str) -> str:
    """Recorta los extremos y compacta los espacios internos a uno solo."""
    return " ".join((nombre or "").split())


def normalizar_nombre(nombre: str) -> str:
    """Clave de comparación: limpia y sin distinguir mayúsculas (REQ-001)."""
    return limpiar_nombre(nombre).casefold()


def validar_nombre(nombre: str) -> str:
    """Devuelve el nombre limpio o lanza ReglaNegocio si no es válido."""
    limpio = limpiar_nombre(nombre)
    if not limpio:
        raise ReglaNegocio("El nombre del proveedor es obligatorio.")
    if len(limpio) > LARGO_MAXIMO:
        raise ReglaNegocio(f"El nombre no puede superar {LARGO_MAXIMO} caracteres.")
    if not _PATRON_NOMBRE.fullmatch(limpio):
        raise ReglaNegocio(
            "El nombre solo admite letras, números, espacios, punto, coma y paréntesis."
        )
    return limpio


def _guardar(db: Session, proveedor: Proveedor) -> Proveedor:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflicto("Ya existe un proveedor con ese nombre.") from None
    db.refresh(proveedor)
    return proveedor


def _existe_otro(db: Session, normalizado: str, excluir_id: int | None = None) -> bool:
    q = db.query(Proveedor).filter(Proveedor.nombre_normalizado == normalizado)
    if excluir_id is not None:
        q = q.filter(Proveedor.id != excluir_id)
    return db.query(q.exists()).scalar()


def crear(db: Session, nombre: str) -> Proveedor:
    limpio = validar_nombre(nombre)
    normalizado = limpio.casefold()
    if _existe_otro(db, normalizado):
        raise Conflicto("Ya existe un proveedor con ese nombre.")
    p = Proveedor(nombre=limpio, nombre_normalizado=normalizado)
    db.add(p)
    return _guardar(db, p)


def obtener(db: Session, proveedor_id: int) -> Proveedor:
    p = db.get(Proveedor, proveedor_id)
    if p is None:
        raise NoEncontrado("Proveedor no encontrado.")
    return p


def listar(db: Session) -> list[Proveedor]:
    return db.query(Proveedor).order_by(Proveedor.nombre).all()


def editar(db: Session, proveedor_id: int, nombre: str) -> Proveedor:
    p = obtener(db, proveedor_id)
    limpio = validar_nombre(nombre)
    normalizado = limpio.casefold()
    if _existe_otro(db, normalizado, excluir_id=p.id):
        raise Conflicto("Ya existe un proveedor con ese nombre.")
    p.nombre = limpio
    p.nombre_normalizado = normalizado
    return _guardar(db, p)


def eliminar(db: Session, proveedor_id: int) -> None:
    p = obtener(db, proveedor_id)
    if db.query(Oferta).filter(Oferta.proveedor_id == p.id).first():
        raise Conflicto("No se puede eliminar un proveedor que tiene ofertas registradas.")
    db.delete(p)
    db.commit()
