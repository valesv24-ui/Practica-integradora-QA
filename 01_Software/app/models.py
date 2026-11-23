"""Modelos de datos.

Persona A (Valery): Usuario, Proveedor, Oferta.
Persona B (Maykel): Licitacion y TipoCambio. Licitacion se deja aquí con los
campos mínimos que necesita Ofertas; Maykel la completa con sus reglas
(REQ-002, REQ-003) sin cambiar los nombres de columnas.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ESTADO_BORRADOR = "Borrador"
ESTADO_PUBLICADA = "Publicada"
ESTADO_CERRADA = "Cerrada"


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
