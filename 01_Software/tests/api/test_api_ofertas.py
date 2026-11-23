"""CP-005 · REQ-011/REQ-005: la API rechaza lo mismo que la UI.
CP-010 · borde: un céntimo sobre el presupuesto y licitaciones no Publicadas.
"""
import pytest

from app.models import ESTADO_BORRADOR, ESTADO_CERRADA

pytestmark = pytest.mark.api


@pytest.fixture
def datos_base(cliente, crear_licitacion):
    lic = crear_licitacion(presupuesto="10000000.00")
    p1 = cliente.post("/api/proveedores", json={"nombre": "Tecnología Norte S.A."}).json()
    return lic, p1


def test_cp005_oferta_valida_201_y_persistida(cliente, datos_base):
    lic, p1 = datos_base
    r = cliente.post("/api/ofertas", json={"licitacion_id": lic.id, "proveedor_id": p1["id"], "monto_crc": "9000000.00"})
    assert r.status_code == 201
    assert r.json()["monto_crc"] == "9000000.00"
    listado = cliente.get(f"/api/ofertas?licitacion_id={lic.id}").json()
    assert len(listado) == 1


@pytest.mark.parametrize("monto", ["0", "-500", "abc"])
def test_cp005_monto_invalido_rechazado_por_api(cliente, datos_base, monto):
    lic, p1 = datos_base
    r = cliente.post("/api/ofertas", json={"licitacion_id": lic.id, "proveedor_id": p1["id"], "monto_crc": monto})
    assert r.status_code == 422
    assert "error" in r.json()
    assert cliente.get("/api/ofertas").json() == []


def test_cp005_oferta_duplicada_409(cliente, datos_base):
    lic, p1 = datos_base
    cuerpo = {"licitacion_id": lic.id, "proveedor_id": p1["id"], "monto_crc": "9000000.00"}
    assert cliente.post("/api/ofertas", json=cuerpo).status_code == 201
    assert cliente.post("/api/ofertas", json=cuerpo).status_code == 409


def test_cp005_sin_sesion_401(app_prueba):
    from fastapi.testclient import TestClient

    with TestClient(app_prueba) as anonimo:
        assert anonimo.get("/api/ofertas").status_code == 401
        assert anonimo.post("/api/proveedores", json={"nombre": "Prueba"}).status_code == 401


# ---------- CP-010 · bordes ----------
def test_cp010_un_centimo_sobre_presupuesto_422(cliente, datos_base):
    lic, p1 = datos_base
    r = cliente.post("/api/ofertas", json={"licitacion_id": lic.id, "proveedor_id": p1["id"], "monto_crc": "10000000.01"})
    assert r.status_code == 422


def test_cp010_igual_al_presupuesto_201(cliente, datos_base):
    lic, p1 = datos_base
    r = cliente.post("/api/ofertas", json={"licitacion_id": lic.id, "proveedor_id": p1["id"], "monto_crc": "10000000.00"})
    assert r.status_code == 201


@pytest.mark.parametrize("estado", [ESTADO_BORRADOR, ESTADO_CERRADA])
def test_cp010_licitacion_no_publicada_422(cliente, crear_licitacion, estado):
    lic = crear_licitacion(codigo=f"LIC-{estado}", estado=estado)
    p = cliente.post("/api/proveedores", json={"nombre": "Servicios del Valle"}).json()
    r = cliente.post("/api/ofertas", json={"licitacion_id": lic.id, "proveedor_id": p["id"], "monto_crc": "1000.00"})
    assert r.status_code == 422
