"""Servicio de Licitaciones (REQ-002, REQ-003): alta, edición, estados y baja."""
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Licitacion, Oferta
from app.services import reglas_licitaciones as reglas
from app.services.errores import Conflicto, NoEncontrado


def _validar_datos(codigo, titulo, presupuesto, cierre, ahora):
    codigo_ok = reglas.validar_codigo(codigo)
    titulo_ok = reglas.validar_titulo(titulo)
    presupuesto_ok = reglas.convertir_presupuesto(presupuesto)
    cierre_ok = reglas.convertir_cierre(cierre)
    reglas.validar_cierre_futuro(cierre_ok, ahora)
    return codigo_ok, titulo_ok, presupuesto_ok, cierre_ok


def _existe_codigo(db: Session, normalizado: str, excluir_id: int | None = None) -> bool:
    q = db.query(Licitacion).filter(Licitacion.codigo_normalizado == normalizado)
    if excluir_id is not None:
        q = q.filter(Licitacion.id != excluir_id)
    return db.query(q.exists()).scalar()


def _guardar(db: Session, lic: Licitacion) -> Licitacion:
    try:
        db.commit()
    except IntegrityError:  # el UNIQUE de la BD también impide el duplicado
        db.rollback()
        raise Conflicto("Ya existe una licitación con ese código.") from None
    db.refresh(lic)
    return lic


def crear(db: Session, codigo, titulo, presupuesto, cierre, ahora: datetime | None = None) -> Licitacion:
    ahora = ahora or datetime.now()
    codigo_ok, titulo_ok, presupuesto_ok, cierre_ok = _validar_datos(codigo, titulo, presupuesto, cierre, ahora)
    normalizado = reglas.normalizar_codigo(codigo_ok)
    if _existe_codigo(db, normalizado):
        raise Conflicto("Ya existe una licitación con ese código.")
    lic = Licitacion(
        codigo=codigo_ok,
        codigo_normalizado=normalizado,
        titulo=titulo_ok,
        presupuesto_crc=presupuesto_ok,
        cierre=cierre_ok,
        estado=reglas.ESTADO_BORRADOR,
    )
    db.add(lic)
    return _guardar(db, lic)


def obtener(db: Session, licitacion_id: int) -> Licitacion:
    lic = db.get(Licitacion, licitacion_id)
    if lic is None:
        raise NoEncontrado("Licitación no encontrada.")
    return lic


def listar(db: Session) -> list[Licitacion]:
    return db.query(Licitacion).order_by(Licitacion.codigo_normalizado, Licitacion.id).all()


def editar(db: Session, licitacion_id: int, codigo, titulo, presupuesto, cierre,
           ahora: datetime | None = None) -> Licitacion:
    """Solo se editan licitaciones en Borrador."""
    ahora = ahora or datetime.now()
    lic = obtener(db, licitacion_id)
    if lic.estado != reglas.ESTADO_BORRADOR:
        raise Conflicto(f"Solo se pueden editar licitaciones en Borrador (estado actual: {lic.estado}).")
    codigo_ok, titulo_ok, presupuesto_ok, cierre_ok = _validar_datos(codigo, titulo, presupuesto, cierre, ahora)
    normalizado = reglas.normalizar_codigo(codigo_ok)
    if _existe_codigo(db, normalizado, excluir_id=lic.id):
        raise Conflicto("Ya existe una licitación con ese código.")
    lic.codigo, lic.codigo_normalizado = codigo_ok, normalizado
    lic.titulo, lic.presupuesto_crc, lic.cierre = titulo_ok, presupuesto_ok, cierre_ok
    return _guardar(db, lic)


def cambiar_estado(db: Session, licitacion_id: int, nuevo: str, ahora: datetime | None = None) -> Licitacion:
    ahora = ahora or datetime.now()
    lic = obtener(db, licitacion_id)
    reglas.validar_transicion(lic.estado, nuevo)
    if nuevo == reglas.ESTADO_PUBLICADA:
        reglas.validar_cierre_futuro(lic.cierre, ahora)  # REQ-002: también al publicar
    lic.estado = nuevo
    db.commit()
    db.refresh(lic)
    return lic


def publicar(db: Session, licitacion_id: int, ahora: datetime | None = None) -> Licitacion:
    return cambiar_estado(db, licitacion_id, reglas.ESTADO_PUBLICADA, ahora)


def cerrar(db: Session, licitacion_id: int, ahora: datetime | None = None) -> Licitacion:
    return cambiar_estado(db, licitacion_id, reglas.ESTADO_CERRADA, ahora)


def eliminar(db: Session, licitacion_id: int) -> None:
    """Solo en Borrador y sin ofertas."""
    lic = obtener(db, licitacion_id)
    if lic.estado != reglas.ESTADO_BORRADOR:
        raise Conflicto("Solo se pueden eliminar licitaciones en Borrador.")
    if db.query(db.query(Oferta).filter(Oferta.licitacion_id == lic.id).exists()).scalar():
        raise Conflicto("No se puede eliminar una licitación con ofertas.")
    db.delete(lic)
    db.commit()
