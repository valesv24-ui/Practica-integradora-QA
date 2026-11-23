"""Interfaz web (HTML) de Persona B: Licitaciones, Evaluación y Tipo de cambio."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.web import _flash, _ir_login, _render, _usuario
from app.services import evaluacion as svc_evaluacion
from app.services import licitaciones as svc
from app.services import tipo_cambio as svc_tc
from app.services.errores import ErrorNegocio

router = APIRouter()


def _a_input_fecha(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M") if dt else ""


# ---------- Licitaciones ----------
@router.get("/licitaciones", response_class=HTMLResponse, include_in_schema=False)
def licitaciones(request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    return _render(request, "licitaciones.html", db, licitaciones=svc.listar(db))


@router.post("/licitaciones", include_in_schema=False)
def crear_licitacion(
    request: Request,
    codigo: str = Form(""),
    titulo: str = Form(""),
    presupuesto_crc: str = Form(""),
    cierre: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _usuario(request, db):
        return _ir_login()
    try:
        lic = svc.crear(db, codigo, titulo, presupuesto_crc, cierre)
        _flash(request, f"Licitación «{lic.codigo}» registrada en Borrador.")
    except ErrorNegocio as e:
        return _render(request, "licitaciones.html", db, licitaciones=svc.listar(db), error=e.mensaje,
                       form={"codigo": codigo, "titulo": titulo, "presupuesto_crc": presupuesto_crc, "cierre": cierre},
                       status_code=e.status_code)
    return RedirectResponse("/licitaciones", status_code=303)


@router.get("/licitaciones/{licitacion_id}/editar", response_class=HTMLResponse, include_in_schema=False)
def editar_form(licitacion_id: int, request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        lic = svc.obtener(db, licitacion_id)
    except ErrorNegocio as e:
        _flash(request, e.mensaje, "error")
        return RedirectResponse("/licitaciones", status_code=303)
    form = {"codigo": lic.codigo, "titulo": lic.titulo, "presupuesto_crc": f"{lic.presupuesto_crc:.2f}",
            "cierre": _a_input_fecha(lic.cierre)}
    return _render(request, "licitacion_editar.html", db, licitacion=lic, form=form)


@router.post("/licitaciones/{licitacion_id}/editar", include_in_schema=False)
def editar(
    licitacion_id: int,
    request: Request,
    codigo: str = Form(""),
    titulo: str = Form(""),
    presupuesto_crc: str = Form(""),
    cierre: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _usuario(request, db):
        return _ir_login()
    try:
        lic = svc.editar(db, licitacion_id, codigo, titulo, presupuesto_crc, cierre)
        _flash(request, f"Licitación «{lic.codigo}» actualizada.")
    except ErrorNegocio as e:
        try:
            lic = svc.obtener(db, licitacion_id)
        except ErrorNegocio:
            _flash(request, e.mensaje, "error")
            return RedirectResponse("/licitaciones", status_code=303)
        return _render(request, "licitacion_editar.html", db, licitacion=lic, error=e.mensaje,
                       form={"codigo": codigo, "titulo": titulo, "presupuesto_crc": presupuesto_crc, "cierre": cierre},
                       status_code=e.status_code)
    return RedirectResponse("/licitaciones", status_code=303)


def _accion_estado(licitacion_id: int, request: Request, db: Session, funcion, mensaje: str):
    if not _usuario(request, db):
        return _ir_login()
    try:
        lic = funcion(db, licitacion_id)
        _flash(request, f"Licitación «{lic.codigo}» {mensaje}.")
    except ErrorNegocio as e:
        _flash(request, e.mensaje, "error")
    return RedirectResponse("/licitaciones", status_code=303)


@router.post("/licitaciones/{licitacion_id}/publicar", include_in_schema=False)
def publicar(licitacion_id: int, request: Request, db: Session = Depends(get_db)):
    return _accion_estado(licitacion_id, request, db, svc.publicar, "publicada")


@router.post("/licitaciones/{licitacion_id}/cerrar", include_in_schema=False)
def cerrar(licitacion_id: int, request: Request, db: Session = Depends(get_db)):
    return _accion_estado(licitacion_id, request, db, svc.cerrar, "cerrada")


@router.post("/licitaciones/{licitacion_id}/eliminar", include_in_schema=False)
def eliminar(licitacion_id: int, request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        svc.eliminar(db, licitacion_id)
        _flash(request, "Licitación eliminada.")
    except ErrorNegocio as e:
        _flash(request, e.mensaje, "error")
    return RedirectResponse("/licitaciones", status_code=303)


# ---------- Evaluación ----------
@router.get("/evaluacion", response_class=HTMLResponse, include_in_schema=False)
def evaluacion(request: Request, licitacion_id: str | None = None, moneda: str = "CRC",
               db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    ctx = {"licitaciones": svc.listar(db), "moneda": moneda.upper() if moneda.upper() in ("CRC", "USD") else "CRC",
           "licitacion_id": int(licitacion_id) if licitacion_id and licitacion_id.isdigit() else None,
           "resultado": None}
    status = 200
    if ctx["licitacion_id"] is not None:
        try:
            ctx["resultado"] = svc_evaluacion.evaluar_licitacion(db, ctx["licitacion_id"], ctx["moneda"])
        except ErrorNegocio as e:
            ctx["error"], status = e.mensaje, e.status_code
    return _render(request, "evaluacion.html", db, status_code=status, **ctx)


# ---------- Tipo de cambio ----------
def _ctx_tc(db: Session):
    return {"actual": svc_tc.obtener_actual(db), "historial": svc_tc.historial(db)}


@router.get("/tipo-cambio", response_class=HTMLResponse, include_in_schema=False)
def tipo_cambio(request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    return _render(request, "tipo_cambio.html", db, **_ctx_tc(db))


@router.post("/tipo-cambio", include_in_schema=False)
def configurar_tipo_cambio(request: Request, crc_por_usd: str = Form(""), db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        t = svc_tc.registrar_tasa(db, crc_por_usd)
        _flash(request, f"Tipo de cambio registrado: ₡{t.crc_por_usd:.4f} por USD.")
    except ErrorNegocio as e:
        return _render(request, "tipo_cambio.html", db, **_ctx_tc(db), error=e.mensaje, valor=crc_por_usd,
                       status_code=e.status_code)
    return RedirectResponse("/tipo-cambio", status_code=303)


@router.post("/tipo-cambio/sincronizar", include_in_schema=False)
def sincronizar_tipo_cambio(request: Request, db: Session = Depends(get_db)):
    if not _usuario(request, db):
        return _ir_login()
    try:
        t = svc_tc.sincronizar_desde_servicio(db)
        _flash(request, f"Tipo de cambio actualizado desde el servicio: ₡{t.crc_por_usd:.4f} por USD.")
    except ErrorNegocio as e:
        return _render(request, "tipo_cambio.html", db, **_ctx_tc(db), error=e.mensaje, status_code=e.status_code)
    return RedirectResponse("/tipo-cambio", status_code=303)
