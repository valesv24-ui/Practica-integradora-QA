"""Datos sintéticos mínimos para probar Ofertas mientras no exista el seed completo.

TEMPORAL: Persona B (Maykel) reemplaza esto por el script de datos semilla
oficial (P1, P2, L1, tipo de cambio y escenarios aislados).

Uso:  python -m scripts.demo_licitacion
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import SessionLocal, init_db
from app.models import ESTADO_PUBLICADA, Licitacion, Proveedor


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        if not db.query(Licitacion).filter(Licitacion.codigo_normalizado == "lic-2026-001").first():
            db.add(Licitacion(
                codigo="LIC-2026-001",
                codigo_normalizado="lic-2026-001",
                titulo="Licitación de prueba L1",
                presupuesto_crc=Decimal("10000000.00"),
                cierre=datetime.now().replace(microsecond=0) + timedelta(hours=48),
                estado=ESTADO_PUBLICADA,
            ))
        for nombre in ["Tecnología Norte S.A.", "Servicios del Valle"]:
            norm = " ".join(nombre.split()).casefold()
            if not db.query(Proveedor).filter(Proveedor.nombre_normalizado == norm).first():
                db.add(Proveedor(nombre=nombre, nombre_normalizado=norm))
        db.commit()
        print("Datos demo listos: L1 (Publicada, cierre +48 h), P1 y P2.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
