"""CP-008 · REQ-012: caracteres no admitidos y cadenas HTML/script.
CP-009 · REQ-012: errores controlados sin traza interna.
"""
import pytest

from app.services import proveedores as svc_proveedores

pytestmark = pytest.mark.seguridad

TRAZAS = ("Traceback", "File \"", "sqlalchemy", "sqlite3", "Exception", ".py")


@pytest.mark.parametrize(
    "nombre",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "Proveedor; DROP TABLE proveedores;--",
        "Tecnología Norte S.A. @",
        "Servicios del Valle & Cía",
        "Nombre con \"comillas\"",
    ],
)
def test_cp008_nombre_no_admitido_rechazado(cliente, nombre):
    r = cliente.post("/api/proveedores", json={"nombre": nombre})
    assert r.status_code == 422
    assert cliente.get("/api/proveedores").json() == []


def test_cp008_nombres_validos_con_caracteres_permitidos(cliente):
    for nombre in ["Tecnología Norte S.A.", "Servicios del Valle (Sede 2), Ltda."]:
        assert cliente.post("/api/proveedores", json={"nombre": nombre}).status_code == 201


def test_cp008_html_no_se_ejecuta_en_la_ui(cliente):
    # Al rechazar el script, la página de error muestra el valor escapado, nunca como etiqueta.
    r = cliente.post("/proveedores", data={"nombre": "<script>alert(1)</script>"})
    assert r.status_code == 422
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_cp009_error_de_validacion_sin_traza(cliente):
    r = cliente.post("/api/ofertas", json={"licitacion_id": "abc"})
    assert r.status_code == 422
    assert not any(t in r.text for t in TRAZAS)


def test_cp009_error_interno_sin_traza_ni_credenciales(cliente, monkeypatch):
    def _falla(*_a, **_k):
        raise RuntimeError("fallo simulado de conexión sqlite3 password=secreto")

    monkeypatch.setattr(svc_proveedores, "listar", _falla)
    r = cliente.get("/api/proveedores")
    assert r.status_code == 500
    assert r.json() == {"error": "Error interno. Intente de nuevo más tarde."}
    assert "secreto" not in r.text and not any(t in r.text for t in TRAZAS)


def test_cp009_login_incorrecto_no_revela_cual_dato_fallo(app_prueba):
    from fastapi.testclient import TestClient

    with TestClient(app_prueba) as c:
        r1 = c.post("/api/login", json={"usuario": "no_existe", "password": "x"})
        r2 = c.post("/api/login", json={"usuario": "qa_tester", "password": "incorrecta"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()
