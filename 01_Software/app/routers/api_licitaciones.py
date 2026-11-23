"""API HTTP de Persona B: Licitaciones, Evaluación y Tipo de cambio.

Usa los mismos servicios que la interfaz web, así la API no acepta valores que
la UI rechazaría (REQ-011). Todas las rutas requieren sesión (POST /api/login).
"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Licitacion, TipoCambio
from app.security import usuario_actual
from app.services import evaluacion as svc_evaluacion
from app.services import licitaciones as svc
from app.services import tipo_cambio as svc_tc

router = APIRouter(prefix="/api")


# ---------- Esquemas ----------
class LicitacionIn(BaseModel):
    codigo: str
    titulo: str
    presupuesto_crc: Decimal
    cierre: datetime


class LicitacionOut(BaseModel):
    id: int
    codigo: str
    titulo: str
    presupuesto_crc: str
    cierre: datetime
    estado: str


class TipoCambioIn(BaseModel):
    crc_por_usd: Decimal


class TipoCambioOut(BaseModel):
    id: int
    crc_por_usd: str
    fecha: datetime
    fuente: str


def _lic_out(lic: Licitacion) -> LicitacionOut:
    return LicitacionOut(
        id=lic.id,
        codigo=lic.codigo,
        titulo=lic.titulo,
        presupuesto_crc=f"{Decimal(lic.presupuesto_crc):.2f}",
        cierre=lic.cierre,
        estado=lic.estado,
    )


def _tc_out(t: TipoCambio) -> TipoCambioOut:
    return TipoCambioOut(id=t.id, crc_por_usd=f"{Decimal(t.crc_por_usd):.4f}", fecha=t.fecha, fuente=t.fuente)


# ---------- Licitaciones ----------
@router.get("/licitaciones", response_model=list[LicitacionOut])
def listar_licitaciones(db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return [_lic_out(x) for x in svc.listar(db)]


@router.get("/licitaciones/{licitacion_id}", response_model=LicitacionOut)
def obtener_licitacion(licitacion_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _lic_out(svc.obtener(db, licitacion_id))


@router.post("/licitaciones", response_model=LicitacionOut, status_code=201)
def crear_licitacion(datos: LicitacionIn, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _lic_out(svc.crear(db, datos.codigo, datos.titulo, datos.presupuesto_crc, datos.cierre))


@router.put("/licitaciones/{licitacion_id}", response_model=LicitacionOut)
def editar_licitacion(licitacion_id: int, datos: LicitacionIn, db: Session = Depends(get_db),
                      _=Depends(usuario_actual)):
    return _lic_out(svc.editar(db, licitacion_id, datos.codigo, datos.titulo, datos.presupuesto_crc, datos.cierre))


@router.delete("/licitaciones/{licitacion_id}", status_code=204)
def eliminar_licitacion(licitacion_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    svc.eliminar(db, licitacion_id)
    return Response(status_code=204)


@router.post("/licitaciones/{licitacion_id}/publicar", response_model=LicitacionOut)
def publicar_licitacion(licitacion_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _lic_out(svc.publicar(db, licitacion_id))


@router.post("/licitaciones/{licitacion_id}/cerrar", response_model=LicitacionOut)
def cerrar_licitacion(licitacion_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _lic_out(svc.cerrar(db, licitacion_id))


# ---------- Evaluación ----------
@router.get("/licitaciones/{licitacion_id}/evaluacion")
def evaluar_licitacion(licitacion_id: int, moneda: str = "CRC", db: Session = Depends(get_db),
                       _=Depends(usuario_actual)):
    """Mejor oferta, ahorro, clasificación y aprobador. `moneda=USD` solo cambia la vista."""
    return svc_evaluacion.evaluar_licitacion(db, licitacion_id, moneda)


# ---------- Tipo de cambio ----------
@router.get("/tipo-cambio", response_model=TipoCambioOut)
def tipo_cambio_actual(db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _tc_out(svc_tc.requerir_actual(db))


@router.post("/tipo-cambio", response_model=TipoCambioOut, status_code=201)
def configurar_tipo_cambio(datos: TipoCambioIn, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _tc_out(svc_tc.registrar_tasa(db, datos.crc_por_usd))


@router.post("/tipo-cambio/sincronizar", response_model=TipoCambioOut, status_code=201)
def sincronizar_tipo_cambio(db: Session = Depends(get_db), _=Depends(usuario_actual)):
    """Consulta el servicio externo (TIPO_CAMBIO_URL). Si falla responde 503 controlado."""
    return _tc_out(svc_tc.sincronizar_desde_servicio(db))
