"""Fixtures comunes: BD SQLite temporal por prueba y cliente HTTP con sesión."""
import os
import tempfile

# Antes de importar la app: la BD por defecto apunta a un archivo temporal,
# así las pruebas nunca crean ni modifican data/licitaciones.db.
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "pytest.db").replace(os.sep, "/")

from datetime import datetime, timedelta
from decimal import Decimal

import pytest  # noqa: E402
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import crear_engine, get_db, init_db
from app.main import crear_app
from app.models import ESTADO_PUBLICADA, Licitacion
from app.security import crear_usuario

USUARIO_PRUEBA = "qa_tester"
PASSWORD_PRUEBA = "Clave-Sintetica-123"  # dato sintético solo para pruebas


@pytest.fixture
def db(tmp_path):
    engine = crear_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    init_db(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sesion = Sesion()
    sesion._fabrica = Sesion  # para el cliente HTTP
    yield sesion
    sesion.close()
    engine.dispose()


@pytest.fixture
def app_prueba(db):
    app = crear_app()

    def _get_db():
        s = db._fabrica()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    crear_usuario(db, USUARIO_PRUEBA, PASSWORD_PRUEBA)
    return app


@pytest.fixture
def cliente(app_prueba):
    """Cliente autenticado. raise_server_exceptions=False para ver la respuesta 500 real."""
    with TestClient(app_prueba, raise_server_exceptions=False) as c:
        r = c.post("/api/login", json={"usuario": USUARIO_PRUEBA, "password": PASSWORD_PRUEBA})
        assert r.status_code == 200
        yield c


@pytest.fixture
def crear_licitacion(db):
    """Crea una licitación directamente en BD (el módulo de Licitaciones es de Persona B)."""

    def _crear(codigo="LIC-2026-001", presupuesto="10000000.00", estado=ESTADO_PUBLICADA,
               cierre=None, titulo="Licitación de prueba"):
        lic = Licitacion(
            codigo=codigo,
            codigo_normalizado=codigo.strip().casefold(),
            titulo=titulo,
            presupuesto_crc=Decimal(presupuesto),
            cierre=cierre or datetime.now() + timedelta(hours=48),
            estado=estado,
        )
        db.add(lic)
        db.commit()
        return lic

    return _crear
