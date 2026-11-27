"""Retest y regresión de BUG-001 (oferta aceptada exactamente en el cierre) · REQ-004.

Independiente de las pruebas de Persona A: las escribe y ejecuta Persona B para
verificar la corrección.

* RETEST: la oferta (y su retiro) exactamente en el instante de cierre se rechazan.
  Falla sobre la versión defectuosa (`ahora > cierre`) y pasa con la corrección (`ahora >= cierre`).
* REGRESIÓN 1 (REQ-004): el resto del borde de tiempo y de estado no cambió.
* REGRESIÓN 2 (REQ-005, REQ-006, REQ-007): montos límite, duplicados y mejor oferta no cambiaron.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models import Oferta
from app.services import evaluacion as svc_eval
from app.services import ofertas as svc
from app.services import proveedores as svc_prov
from app.services.errores import Conflicto, ReglaNegocio

pytestmark = pytest.mark.regresion

CIERRE = datetime(2026, 12, 1, 15, 0, 0)
UN_SEGUNDO = timedelta(seconds=1)


def _proveedor(db, nombre="Proveedor Uno"):
    return svc_prov.crear(db, nombre)


def _total_ofertas(db):
    return db.query(Oferta).count()


# ---------- RETEST · BUG-001 ----------
def test_retest_bug001_oferta_exactamente_en_el_cierre_se_rechaza(db, crear_licitacion):
    lic = crear_licitacion(cierre=CIERRE)
    prov = _proveedor(db)
    with pytest.raises(ReglaNegocio):
        svc.registrar(db, lic.id, prov.id, "9000000.00", ahora=CIERRE)
    assert _total_ofertas(db) == 0


def test_retest_bug001_retiro_exactamente_en_el_cierre_se_rechaza(db, crear_licitacion):
    lic = crear_licitacion(cierre=CIERRE)
    prov = _proveedor(db)
    oferta = svc.registrar(db, lic.id, prov.id, "9000000.00", ahora=CIERRE - timedelta(minutes=5))
    with pytest.raises(ReglaNegocio):
        svc.eliminar(db, oferta.id, ahora=CIERRE)
    assert _total_ofertas(db) == 1


# ---------- REGRESIÓN 1 · borde de tiempo y de estado ----------
def test_regresion1_un_segundo_antes_del_cierre_se_acepta(db, crear_licitacion):
    lic = crear_licitacion(cierre=CIERRE)
    prov = _proveedor(db)
    o = svc.registrar(db, lic.id, prov.id, "9000000.00", ahora=CIERRE - UN_SEGUNDO)
    assert o.monto_crc == Decimal("9000000.00")


@pytest.mark.parametrize("despues", [UN_SEGUNDO, timedelta(hours=1), timedelta(days=3)])
def test_regresion1_despues_del_cierre_se_rechaza(db, crear_licitacion, despues):
    lic = crear_licitacion(cierre=CIERRE)
    prov = _proveedor(db)
    with pytest.raises(ReglaNegocio):
        svc.registrar(db, lic.id, prov.id, "9000000.00", ahora=CIERRE + despues)
    assert _total_ofertas(db) == 0


@pytest.mark.parametrize("estado", ["Borrador", "Cerrada"])
def test_regresion1_licitacion_no_publicada_rechaza_ofertas(db, crear_licitacion, estado):
    lic = crear_licitacion(cierre=CIERRE, estado=estado)
    prov = _proveedor(db)
    with pytest.raises(ReglaNegocio):
        svc.registrar(db, lic.id, prov.id, "9000000.00", ahora=CIERRE - timedelta(hours=1))


# ---------- REGRESIÓN 2 · montos, duplicados y mejor oferta ----------
def test_regresion2_montos_limite_y_duplicado(db, crear_licitacion):
    lic = crear_licitacion(cierre=CIERRE, presupuesto="10000000.00")
    p1, p2 = _proveedor(db, "Proveedor Uno"), _proveedor(db, "Proveedor Dos")
    antes = CIERRE - timedelta(hours=1)

    with pytest.raises(ReglaNegocio):
        svc.registrar(db, lic.id, p1.id, "10000000.01", ahora=antes)   # un céntimo sobre el presupuesto
    with pytest.raises(ReglaNegocio):
        svc.registrar(db, lic.id, p1.id, "0", ahora=antes)

    svc.registrar(db, lic.id, p1.id, "10000000.00", ahora=antes)       # igual al presupuesto: válida
    with pytest.raises(Conflicto):
        svc.registrar(db, lic.id, p1.id, "9000000.00", ahora=antes)    # mismo proveedor, misma licitación
    svc.registrar(db, lic.id, p2.id, "9500000.00", ahora=antes)
    assert _total_ofertas(db) == 2


def test_regresion2_mejor_oferta_no_cambia(db, crear_licitacion):
    lic = crear_licitacion(cierre=CIERRE, presupuesto="10000000.00")
    p1, p2 = _proveedor(db, "Tecnología Norte S.A."), _proveedor(db, "Servicios del Valle")
    svc.registrar(db, lic.id, p1.id, "9000000.00", ahora=CIERRE - timedelta(hours=2))
    svc.registrar(db, lic.id, p2.id, "9500000.00", ahora=CIERRE - timedelta(hours=1))

    r = svc_eval.evaluar_licitacion(db, lic.id)
    assert r["mejor_oferta"]["proveedor"] == "Tecnología Norte S.A."
    assert (r["ahorro_porcentaje"], r["clasificacion"], r["aprobador"]) == ("10.00", "Conveniente", "Gerencia")
    assert r["total_ofertas"] == 2
