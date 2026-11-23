"""Conexión a la base de datos (SQLite por defecto).

La ruta se puede cambiar con la variable de entorno DATABASE_URL,
por ejemplo para usar una BD aislada en las pruebas.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / "data" / "licitaciones.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")


class Base(DeclarativeBase):
    pass


def crear_engine(url: str):
    engine = create_engine(url, connect_args={"check_same_thread": False})

    # SQLite no aplica llaves foráneas si no se activan en cada conexión.
    @event.listens_for(engine, "connect")
    def _activar_fk(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return engine


engine = crear_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(bind=None):
    from app import models  # noqa: F401  (registra las tablas)

    Base.metadata.create_all(bind=bind or engine)
