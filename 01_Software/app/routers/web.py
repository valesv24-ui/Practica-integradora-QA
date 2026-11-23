"""Interfaz web (HTML) de Persona A: login, Proveedores y Ofertas."""
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Licitacion, Usuario
from app.security import autenticar
from app.services import ofertas as svc_ofertas
from app.services import proveedores as svc_proveedores
from app.services.errores import ErrorNegocio

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _usuario(request: Request, db: Session) -> Usuario | None:
    uid = request.session.get("uid")
    return db.get(Usuario, uid) if uid else None


def _flash(request: Request, mensaje: str, tipo: str = "ok") -> None:
    request.session["flash"] = {"mensaje": mensaje, "tipo": tipo}


def _render(request: Request, plantilla: str, db: Session, **ctx):
    ctx["usuario"] = _usuario(request, db)
    ctx["flash"] = request.session.pop("flash", None)
    return templates.TemplateResponse(request, plantilla, ctx, status_code=ctx.pop("status_code", 200))


def _ir_login():
    return RedirectResponse("/login", status_code=303)


# ---------- Login ----------
@router.get("/", include_in_schema=False)
def inicio(request: Request, db: Session = Depends(get_db)):
    return RedirectResponse("/proveedores" if _usuario(request, db) else "/login", status_code=303)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_form(request: Request, db: Session = Depends(get_db)):
    return _render(request, "login.html", db)


@router.post("/login", include_in_schema=False)
def login(request: Request, usuario: str = Form(""), password: str = Form(""), db: Session = Depends(get_db)):
    u = autenticar(db, usuario, password)
    if u is None:
        return _render(request, "login.html", db, error="Usuario o contraseña incorrectos.", status_code=401)
    request.session["uid"] = u.id
    return RedirectResponse("/proveedores", status_code=303)


@router.post("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.clear()
    return _ir_login()


# ---------- Proveedores ----------
@router.get("/proveedores", response_class=HTMLResponse, include_in_schema=False)
def proveedores(request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    return _render(request, "proveedores.html", db, proveedores=svc_proveedores.listar(db))


@router.post("/proveedores", include_in_schema=False)
def crear_proveedor(request: Request, nombre: str = Form(""), db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        p = svc_proveedores.crear(db, nombre)
        _flash(request, f"Proveedor «{p.nombre}» registrado.")
    except ErrorNegocio as e:
        return _render(request, "proveedores.html", db, proveedores=svc_proveedores.listar(db),
                       error=e.mensaje, valor=nombre, status_code=e.status_code)
    return RedirectResponse("/proveedores", status_code=303)


@router.get("/proveedores/{proveedor_id}/editar", response_class=HTMLResponse, include_in_schema=False)
def editar_form(proveedor_id: int, request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        p = svc_proveedores.obtener(db, proveedor_id)
    except ErrorNegocio as e:
        _flash(request, e.mensaje, "error")
        return RedirectResponse("/proveedores", status_code=303)
    return _render(request, "proveedor_editar.html", db, proveedor=p, valor=p.nombre)


@router.post("/proveedores/{proveedor_id}/editar", include_in_schema=False)
def editar(proveedor_id: int, request: Request, nombre: str = Form(""), db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        p = svc_proveedores.editar(db, proveedor_id, nombre)
        _flash(request, f"Proveedor «{p.nombre}» actualizado.")
    except ErrorNegocio as e:
        p = db.get(svc_proveedores.Proveedor, proveedor_id)
        if p is None:
            _flash(request, e.mensaje, "error")
            return RedirectResponse("/proveedores", status_code=303)
        return _render(request, "proveedor_editar.html", db, proveedor=p, valor=nombre,
                       error=e.mensaje, status_code=e.status_code)
    return RedirectResponse("/proveedores", status_code=303)


@router.post("/proveedores/{proveedor_id}/eliminar", include_in_schema=False)
def eliminar_proveedor(proveedor_id: int, request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        svc_proveedores.eliminar(db, proveedor_id)
        _flash(request, "Proveedor eliminado.")
    except ErrorNegocio as e:
        _flash(request, e.mensaje, "error")
    return RedirectResponse("/proveedores", status_code=303)


# ---------- Ofertas ----------
def _ctx_ofertas(db: Session, licitacion_id: int | None):
    return {
        "ofertas": svc_ofertas.listar(db, licitacion_id=licitacion_id),
        "licitaciones": db.query(Licitacion).order_by(Licitacion.codigo).all(),
        "proveedores": svc_proveedores.listar(db),
        "filtro_licitacion": licitacion_id,
    }


@router.get("/ofertas", response_class=HTMLResponse, include_in_schema=False)
def ofertas(request: Request, licitacion_id: str | None = None, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    filtro = int(licitacion_id) if licitacion_id and licitacion_id.isdigit() else None
    return _render(request, "ofertas.html", db, **_ctx_ofertas(db, filtro))


@router.post("/ofertas", include_in_schema=False)
def registrar_oferta(
    request: Request,
    licitacion_id: str = Form(""),
    proveedor_id: str = Form(""),
    monto_crc: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _usuario(request, db):
        return _ir_login()
    try:
        if not licitacion_id.isdigit() or not proveedor_id.isdigit():
            raise svc_ofertas.ReglaNegocio("Seleccione una licitación y un proveedor.")
        o = svc_ofertas.registrar(db, int(licitacion_id), int(proveedor_id), monto_crc)
        _flash(request, f"Oferta registrada: {o.proveedor.nombre} en {o.licitacion.codigo}.")
    except ErrorNegocio as e:
        return _render(request, "ofertas.html", db, **_ctx_ofertas(db, None), error=e.mensaje,
                       form={"licitacion_id": licitacion_id, "proveedor_id": proveedor_id, "monto_crc": monto_crc},
                       status_code=e.status_code)
    return RedirectResponse("/ofertas", status_code=303)


@router.post("/ofertas/{oferta_id}/eliminar", include_in_schema=False)
def eliminar_oferta(oferta_id: int, request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        svc_ofertas.eliminar(db, oferta_id)
        _flash(request, "Oferta retirada.")
    except ErrorNegocio as e:
        _flash(request, e.mensaje, "error")
    return RedirectResponse("/ofertas", status_code=303)
