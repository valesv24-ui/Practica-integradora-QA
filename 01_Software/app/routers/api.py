"""API HTTP de Persona A: autenticación, Proveedores y Ofertas.

Todas las rutas usan los mismos servicios que la interfaz web, así la API
no acepta valores que la UI rechazaría (REQ-011).
"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Oferta, Proveedor
from app.security import autenticar, usuario_actual
from app.services import ofertas as svc_ofertas
from app.services import proveedores as svc_proveedores
from app.services.errores import ErrorNegocio

router = APIRouter(prefix="/api")


# ---------- Esquemas ----------
class LoginIn(BaseModel):
    usuario: str
    password: str


class ProveedorIn(BaseModel):
    nombre: str


class ProveedorOut(BaseModel):
    id: int
    nombre: str


class OfertaIn(BaseModel):
    licitacion_id: int
    proveedor_id: int
    monto_crc: Decimal


class OfertaOut(BaseModel):
    id: int
    licitacion_id: int
    licitacion_codigo: str
    proveedor_id: int
    proveedor_nombre: str
    monto_crc: str
    registrada_en: datetime


def _proveedor_out(p: Proveedor) -> ProveedorOut:
    return ProveedorOut(id=p.id, nombre=p.nombre)


def _oferta_out(o: Oferta) -> OfertaOut:
    return OfertaOut(
        id=o.id,
        licitacion_id=o.licitacion_id,
        licitacion_codigo=o.licitacion.codigo,
        proveedor_id=o.proveedor_id,
        proveedor_nombre=o.proveedor.nombre,
        monto_crc=f"{Decimal(o.monto_crc):.2f}",
        registrada_en=o.registrada_en,
    )


# ---------- Autenticación ----------
@router.post("/login")
def login(datos: LoginIn, request: Request, db: Session = Depends(get_db)):
    u = autenticar(db, datos.usuario, datos.password)
    if u is None:
        return _error(401, "Usuario o contraseña incorrectos.")
    request.session["uid"] = u.id
    return {"usuario": u.usuario}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


# ---------- Proveedores ----------
@router.get("/proveedores", response_model=list[ProveedorOut])
def listar_proveedores(db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return [_proveedor_out(p) for p in svc_proveedores.listar(db)]


@router.get("/proveedores/{proveedor_id}", response_model=ProveedorOut)
def obtener_proveedor(proveedor_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _proveedor_out(svc_proveedores.obtener(db, proveedor_id))


@router.post("/proveedores", response_model=ProveedorOut, status_code=201)
def crear_proveedor(datos: ProveedorIn, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _proveedor_out(svc_proveedores.crear(db, datos.nombre))


@router.put("/proveedores/{proveedor_id}", response_model=ProveedorOut)
def editar_proveedor(proveedor_id: int, datos: ProveedorIn, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    return _proveedor_out(svc_proveedores.editar(db, proveedor_id, datos.nombre))


@router.delete("/proveedores/{proveedor_id}", status_code=204)
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    svc_proveedores.eliminar(db, proveedor_id)
    return Response(status_code=204)


# ---------- Ofertas ----------
@router.get("/ofertas", response_model=list[OfertaOut])
def listar_ofertas(
    licitacion_id: int | None = None,
    proveedor_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(usuario_actual),
):
    return [_oferta_out(o) for o in svc_ofertas.listar(db, licitacion_id, proveedor_id)]


@router.post("/ofertas", response_model=OfertaOut, status_code=201)
def registrar_oferta(datos: OfertaIn, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    o = svc_ofertas.registrar(db, datos.licitacion_id, datos.proveedor_id, datos.monto_crc)
    return _oferta_out(o)


@router.delete("/ofertas/{oferta_id}", status_code=204)
def eliminar_oferta(oferta_id: int, db: Session = Depends(get_db), _=Depends(usuario_actual)):
    svc_ofertas.eliminar(db, oferta_id)
    return Response(status_code=204)


def _error(status: int, mensaje: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status, content={"error": mensaje})


__all__ = ["router", "ErrorNegocio"]
