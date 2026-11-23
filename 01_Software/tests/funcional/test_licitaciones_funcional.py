"""CP-016 · REQ-003 (transiciones con BD) y CP-017 · REQ-007/008/009/010 (evaluación).

Flujos completos sobre servicios y base de datos temporal.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models import Oferta
from app.services import evaluacion as svc_eval
from app.services import licitaciones as svc
from app.services import ofertas as svc_ofertas
from app.services import proveedores as svc_prov
from app.services import tipo_cambio as svc_tc
from app.services.errores import Conflicto, ReglaNegocio

pytestmark = pytest.mark.funcional

AHORA = datetime(2026, 12, 1, 10, 0, 0)
CIERRE = AHORA + timedelta(hours=48)


def _licitacion(db, codigo="LIC-2026-001", presupuesto="10000000.00", publicar=True):
    lic = svc.crear(db, codigo, "Licitación de prueba", presupuesto, CIERRE, ahora=AHORA)
    if publicar:
        svc.publicar(db, lic.id, ahora=AHORA)
    return lic


def _ofertar(db, lic, nombre, monto, minutos):
    prov = db.query(svc_prov.Proveedor).filter_by(nombre_normalizado=nombre.casefold()).first() or svc_prov.crear(db, nombre)
    return svc_ofertas.registrar(db, lic.id, prov.id, monto, ahora=AHORA + timedelta(minutes=minutos))


# ---------- CP-016 · transiciones ----------
def test_cp016_flujo_borrador_publicada_cerrada(db):
    lic = _licitacion(db, publicar=False)
    assert lic.estado == "Borrador"
    assert svc.publicar(db, lic.id, ahora=AHORA).estado == "Publicada"
    assert svc.cerrar(db, lic.id, ahora=AHORA).estado == "Cerrada"


def test_cp016_borrador_puede_cerrarse_directamente(db):
    lic = _licitacion(db, publicar=False)
    assert svc.cerrar(db, lic.id, ahora=AHORA).estado == "Cerrada"


def test_cp016_no_vuelve_a_borrador_ni_se_reabre(db):
    lic = _licitacion(db)
    with pytest.raises(Conflicto):
        svc.cambiar_estado(db, lic.id, "Borrador", ahora=AHORA)
    svc.cerrar(db, lic.id, ahora=AHORA)
    with pytest.raises(Conflicto):
        svc.publicar(db, lic.id, ahora=AHORA)
    assert svc.obtener(db, lic.id).estado == "Cerrada"


def test_cp016_no_se_publica_con_cierre_vencido(db):
    lic = _licitacion(db, publicar=False)
    with pytest.raises(ReglaNegocio):
        svc.publicar(db, lic.id, ahora=CIERRE)  # exactamente en el cierre ya no es futuro
    assert svc.obtener(db, lic.id).estado == "Borrador"


def test_cp016_codigo_duplicado_sin_distinguir_mayusculas_ni_espacios(db):
    _licitacion(db, codigo="LIC-2026-001")
    with pytest.raises(Conflicto):
        svc.crear(db, "  lic-2026-001 ", "Otra", "1000", CIERRE, ahora=AHORA)


def test_cp016_solo_se_edita_y_elimina_en_borrador(db):
    lic = _licitacion(db)  # Publicada
    with pytest.raises(Conflicto):
        svc.editar(db, lic.id, "LIC-NUEVA", "Otro", "500", CIERRE, ahora=AHORA)
    with pytest.raises(Conflicto):
        svc.eliminar(db, lic.id)


def test_cp016_crud_en_borrador(db):
    lic = _licitacion(db, publicar=False)
    editada = svc.editar(db, lic.id, "LIC-EDITADA", "Nuevo título", "750000.50", CIERRE, ahora=AHORA)
    assert (editada.codigo, editada.titulo, editada.presupuesto_crc) == ("LIC-EDITADA", "Nuevo título", Decimal("750000.50"))
    svc.eliminar(db, lic.id)
    assert svc.listar(db) == []


# ---------- CP-017 · mejor oferta, empate y "Sin ofertas válidas" ----------
def test_cp017_l1_mejor_oferta_p1_ahorro_10_gerencia(db):
    lic = _licitacion(db)
    _ofertar(db, lic, "Tecnología Norte S.A.", "9000000.00", 1)
    _ofertar(db, lic, "Servicios del Valle", "9500000.00", 2)
    r = svc_eval.evaluar_licitacion(db, lic.id)
    assert r["resultado"] == "Mejor oferta"
    assert r["mejor_oferta"]["proveedor"] == "Tecnología Norte S.A."
    assert r["mejor_oferta"]["monto"] == "9000000.00"
    assert r["ahorro"] == "1000000.00"
    assert r["ahorro_porcentaje"] == "10.00"
    assert r["clasificacion"] == "Conveniente"
    assert r["aprobador"] == "Gerencia"
    assert r["total_ofertas"] == 2


def test_cp017_empate_gana_la_registrada_primero(db):
    lic = _licitacion(db)
    _ofertar(db, lic, "Servicios del Valle", "9000000.00", 5)     # llega primero
    _ofertar(db, lic, "Tecnología Norte S.A.", "9000000.00", 9)   # mismo monto, después
    r = svc_eval.evaluar_licitacion(db, lic.id)
    assert r["mejor_oferta"]["proveedor"] == "Servicios del Valle"


def test_cp017_sin_ofertas(db):
    lic = _licitacion(db)
    r = svc_eval.evaluar_licitacion(db, lic.id)
    assert r["resultado"] == "Sin ofertas válidas"
    assert r["mejor_oferta"] is None and r["total_ofertas"] == 0


def test_cp017_evaluar_ofertas_puro_menor_monto_y_desempate():
    t0 = datetime(2026, 12, 1, 10, 0, 0)
    ofertas = [
        SimpleNamespace(id=1, monto_crc=Decimal("950000"), registrada_en=t0),
        SimpleNamespace(id=2, monto_crc=Decimal("900000"), registrada_en=t0 + timedelta(minutes=3)),
        SimpleNamespace(id=3, monto_crc=Decimal("900000"), registrada_en=t0 + timedelta(minutes=1)),
    ]
    ev = svc_eval.evaluar_ofertas(Decimal("1000000"), ofertas)
    assert ev.oferta_ganadora.id == 3          # mismo monto: gana la registrada antes
    assert ev.aprobador == "Encargado de área"
    assert svc_eval.evaluar_ofertas(Decimal("1000000"), []).tiene_ofertas is False


def test_cp017_vista_usd_no_modifica_la_base_de_datos(db):
    lic = _licitacion(db)
    _ofertar(db, lic, "Tecnología Norte S.A.", "9000000.00", 1)
    svc_tc.registrar_tasa(db, "500", ahora=AHORA)
    r = svc_eval.evaluar_licitacion(db, lic.id, "USD")
    assert r["moneda"] == "USD"
    assert r["mejor_oferta"]["monto"] == "18000.00"
    assert r["presupuesto"] == "20000.00"
    assert r["tipo_cambio"]["crc_por_usd"] == "500.0000" and r["tipo_cambio"]["fecha"].startswith("2026-12-01")
    db.expire_all()
    assert db.query(Oferta).one().monto_crc == Decimal("9000000.00")   # el CRC guardado sigue intacto
    assert svc.obtener(db, lic.id).presupuesto_crc == Decimal("10000000.00")


def test_cp017_usd_sin_tasa_configurada_409(db):
    lic = _licitacion(db)
    with pytest.raises(Conflicto):
        svc_eval.evaluar_licitacion(db, lic.id, "USD")


def test_cp017_moneda_desconocida_rechazada(db):
    lic = _licitacion(db)
    with pytest.raises(ReglaNegocio):
        svc_eval.evaluar_licitacion(db, lic.id, "EUR")
