"""Modelos de datos.

Persona A (Valery): Usuario, Proveedor, Oferta.
Persona B (Maykel): Licitacion y TipoCambio. Los nombres de columnas de
Licitacion no cambiaron; las reglas (REQ-002, REQ-003) viven en
app/services/reglas_licitaciones.py.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.services.reglas_licitaciones import ESTADO_BORRADOR, ESTADO_CERRADA, ESTADO_PUBLICADA  # noqa: F401


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    # Clave normalizada (recortada, espacios compactados, sin mayúsculas).
    # El UNIQUE hace que la BD también rechace duplicados (REQ-001).
    nombre_normalizado: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="proveedor")


class Licitacion(Base):
    __tablename__ = "licitaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    codigo_normalizado: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    presupuesto_crc: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    cierre: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=ESTADO_BORRADOR)

    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="licitacion")


class TipoCambio(Base):
    """Tasa CRC por USD con su fecha (historial). Solo sirve para mostrar USD (REQ-010)."""
    __tablename__ = "tipos_cambio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crc_por_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fuente: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")


class Oferta(Base):
    __tablename__ = "ofertas"
    # REQ-006: un proveedor solo puede ofertar una vez por licitación, también a nivel de BD.
    __table_args__ = (UniqueConstraint("licitacion_id", "proveedor_id", name="uq_oferta_licitacion_proveedor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    licitacion_id: Mapped[int] = mapped_column(ForeignKey("licitaciones.id"), nullable=False)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    monto_crc: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    # Instante de registro: lo usa Evaluación para desempatar (REQ-007).
    registrada_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    licitacion: Mapped[Licitacion] = relationship(back_populates="ofertas")
    proveedor: Mapped[Proveedor] = relationship(back_populates="ofertas")
