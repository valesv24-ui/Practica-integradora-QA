"""CP-014 · licitación inválida rechazada por la API (REQ-011, REQ-002).
CP-020 · borde: tipo de cambio 0/negativo y cierre en el pasado (REQ-010, REQ-002).
RSK-001 · servicio externo de tipo de cambio caído → 503 controlado.
"""
from datetime import datetime, timedelta

import pytest

pytestmark = pytest.mark.api


def _futuro(horas=48):
    return (datetime.now() + timedelta(hours=horas)).replace(microsecond=0).isoformat()


def _cuerpo(**cambios):
    base = {"codigo": "LIC-2026-001", "titulo": "Licitación de prueba", "presupuesto_crc": "10000000.00", "cierre": _futuro()}
    base.update(cambios)
    return base


# ---------- CP-014 ----------
def test_cp014_licitacion_valida_201_y_consultable(cliente):
    r = cliente.post("/api/licitaciones", json=_cuerpo())
    assert r.status_code == 201
    datos = r.json()
    assert datos["estado"] == "Borrador" and datos["presupuesto_crc"] == "10000000.00"
    assert cliente.get(f"/api/licitaciones/{datos['id']}").json()["codigo"] == "LIC-2026-001"
    assert len(cliente.get("/api/licitaciones").json()) == 1


@pytest.mark.parametrize("cambios", [
    {"presupuesto_crc": "0"},
    {"presupuesto_crc": "-100"},
    {"presupuesto_crc": "abc"},
    {"presupuesto_crc": "10.001"},
    {"codigo": ""},
    {"codigo": "LIC <script>"},
    {"titulo": "   "},
    {"cierre": "2020-01-01T10:00:00"},
    {"cierre": "no-es-fecha"},
])
def test_cp014_licitacion_invalida_rechazada_422(cliente, cambios):
    r = cliente.post("/api/licitaciones", json=_cuerpo(**cambios))
    assert r.status_code == 422
    assert "error" in r.json()
    assert "Traceback" not in r.text
    assert cliente.get("/api/licitaciones").json() == []   # no se guardó nada


def test_cp014_faltan_campos_422(cliente):
    assert cliente.post("/api/licitaciones", json={}).status_code == 422


def test_cp014_codigo_duplicado_con_otra_capitalizacion_409(cliente):
    assert cliente.post("/api/licitaciones", json=_cuerpo()).status_code == 201
    r = cliente.post("/api/licitaciones", json=_cuerpo(codigo="  lic-2026-001  "))
    assert r.status_code == 409


def test_cp014_estados_por_api(cliente):
    lic = cliente.post("/api/licitaciones", json=_cuerpo()).json()
    assert cliente.post(f"/api/licitaciones/{lic['id']}/publicar").json()["estado"] == "Publicada"
    assert cliente.post(f"/api/licitaciones/{lic['id']}/cerrar").json()["estado"] == "Cerrada"
    assert cliente.post(f"/api/licitaciones/{lic['id']}/publicar").status_code == 409   # no se reabre
    assert cliente.put(f"/api/licitaciones/{lic['id']}", json=_cuerpo(codigo="OTRO")).status_code == 409
    assert cliente.delete(f"/api/licitaciones/{lic['id']}").status_code == 409


def test_cp014_licitacion_inexistente_404(cliente):
    assert cliente.get("/api/licitaciones/9999").status_code == 404
    assert cliente.get("/api/licitaciones/9999/evaluacion").status_code == 404


def test_cp014_sin_sesion_401(app_prueba):
    from fastapi.testclient import TestClient

    with TestClient(app_prueba) as anonimo:
        assert anonimo.get("/api/licitaciones").status_code == 401
        assert anonimo.post("/api/licitaciones", json=_cuerpo()).status_code == 401
        assert anonimo.get("/api/tipo-cambio").status_code == 401


def test_cp014_flujo_l1_evaluacion_por_api(cliente):
    """L1: P1 = 9 000 000, P2 = 9 500 000 → mejor P1, ahorro 10 %, Gerencia; vista USD con tasa 500."""
    lic = cliente.post("/api/licitaciones", json=_cuerpo()).json()
    cliente.post(f"/api/licitaciones/{lic['id']}/publicar")
    p1 = cliente.post("/api/proveedores", json={"nombre": "Tecnología Norte S.A."}).json()
    p2 = cliente.post("/api/proveedores", json={"nombre": "Servicios del Valle"}).json()
    for prov, monto in ((p1, "9000000.00"), (p2, "9500000.00")):
        r = cliente.post("/api/ofertas", json={"licitacion_id": lic["id"], "proveedor_id": prov["id"], "monto_crc": monto})
        assert r.status_code == 201

    ev = cliente.get(f"/api/licitaciones/{lic['id']}/evaluacion").json()
    assert ev["mejor_oferta"]["proveedor"] == "Tecnología Norte S.A."
    assert (ev["ahorro_porcentaje"], ev["clasificacion"], ev["aprobador"]) == ("10.00", "Conveniente", "Gerencia")

    assert cliente.get(f"/api/licitaciones/{lic['id']}/evaluacion?moneda=USD").status_code == 409   # sin tasa
    assert cliente.post("/api/tipo-cambio", json={"crc_por_usd": "500"}).status_code == 201
    usd = cliente.get(f"/api/licitaciones/{lic['id']}/evaluacion?moneda=USD").json()
    assert usd["mejor_oferta"]["monto"] == "18000.00" and usd["mejor_oferta"]["monto_crc"] == "9000000.00"
    assert cliente.get("/api/ofertas").json()[0]["monto_crc"] in ("9000000.00", "9500000.00")  # BD sigue en CRC


# ---------- CP-020 ----------
@pytest.mark.parametrize("tasa", ["0", "-1", "-500.5", "abc", "", "500.12345"])
def test_cp020_tipo_cambio_invalido_422(cliente, tasa):
    r = cliente.post("/api/tipo-cambio", json={"crc_por_usd": tasa})
    assert r.status_code == 422
    assert cliente.get("/api/tipo-cambio").status_code == 409   # nada quedó guardado


def test_cp020_tipo_cambio_valido_y_consulta(cliente):
    r = cliente.post("/api/tipo-cambio", json={"crc_por_usd": "500"})
    assert r.status_code == 201 and r.json()["crc_por_usd"] == "500.0000"
    actual = cliente.get("/api/tipo-cambio").json()
    assert actual["crc_por_usd"] == "500.0000" and actual["fuente"] == "manual" and actual["fecha"]


def test_cp020_cierre_en_el_pasado_422(cliente):
    r = cliente.post("/api/licitaciones", json=_cuerpo(cierre=(datetime.now() - timedelta(minutes=1)).isoformat()))
    assert r.status_code == 422


# ---------- RSK-001 · servicio externo ----------
def test_rsk001_servicio_externo_caido_503_sin_traza(cliente, monkeypatch):
    def caido():
        raise ConnectionError("sin red")

    monkeypatch.setattr("app.services.tipo_cambio.proveedor_http", caido)
    r = cliente.post("/api/tipo-cambio/sincronizar")
    assert r.status_code == 503
    assert "ConnectionError" not in r.text and "Traceback" not in r.text


def test_rsk001_servicio_externo_devuelve_tasa_invalida_503(cliente, monkeypatch):
    monkeypatch.setattr("app.services.tipo_cambio.proveedor_http", lambda: 0)
    assert cliente.post("/api/tipo-cambio/sincronizar").status_code == 503


def test_rsk001_servicio_externo_ok_se_guarda(cliente, monkeypatch):
    monkeypatch.setattr("app.services.tipo_cambio.proveedor_http", lambda: "512.35")
    r = cliente.post("/api/tipo-cambio/sincronizar")
    assert r.status_code == 201 and r.json()["fuente"] == "servicio"
    assert cliente.get("/api/tipo-cambio").json()["crc_por_usd"] == "512.3500"
