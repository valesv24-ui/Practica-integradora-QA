"""Datos sintéticos reproducibles (enunciado, sección 4).

Uso:
    python -m scripts.seed            # agrega lo que falte (idempotente)
    python -m scripts.seed --reset    # borra proveedores, licitaciones, ofertas y
                                      # tipos de cambio, y vuelve a cargar (conserva usuarios)

Carga: P1 y P2; L1 (LIC-2026-001, CRC 10 000 000, cierre ahora + 48 h, Publicada)
con ofertas P1 = 9 000 000 y P2 = 9 500 000; tipo de cambio CRC 500 por USD;
escenarios aislados (presupuesto CRC 1 000 000) para el 10 %, 5 % y 0 % de ahorro;
y una licitación publicada sin ofertas ("Sin ofertas válidas").
"""
import sys
from datetime import datetime, timedelta

from app.database import SessionLocal, init_db
from app.models import Licitacion, Oferta, Proveedor, TipoCambio
from app.services import licitaciones as svc_lic
from app.services import ofertas as svc_ofertas
from app.services import proveedores as svc_prov
from app.services import tipo_cambio as svc_tc

P1 = "Tecnología Norte S.A."
P2 = "Servicios del Valle"

# (código, título, presupuesto, [(proveedor, monto)])
LICITACIONES = [
    ("LIC-2026-001", "Licitación de prueba L1", "10000000.00", [(P1, "9000000.00"), (P2, "9500000.00")]),
    ("ESC-AHORRO-10", "Escenario aislado: ahorro 10 %", "1000000.00", [(P1, "900000.00")]),
    ("ESC-AHORRO-05", "Escenario aislado: ahorro 5 %", "1000000.00", [(P1, "950000.00")]),
    ("ESC-AHORRO-00", "Escenario aislado: sin ahorro", "1000000.00", [(P1, "1000000.00")]),
    ("ESC-SIN-OFERTAS", "Escenario aislado: sin ofertas", "1000000.00", []),
]


def reiniciar(db) -> None:
    for modelo in (Oferta, Licitacion, Proveedor, TipoCambio):
        db.query(modelo).delete()
    db.commit()


def _proveedor(db, nombre) -> Proveedor:
    existente = db.query(Proveedor).filter(Proveedor.nombre_normalizado == svc_prov.normalizar_nombre(nombre)).first()
    return existente or svc_prov.crear(db, nombre)


def sembrar(db, ahora: datetime | None = None) -> None:
    ahora = ahora or datetime.now().replace(microsecond=0)
    proveedores = {n: _proveedor(db, n) for n in (P1, P2)}

    for codigo, titulo, presupuesto, ofertas in LICITACIONES:
        lic = db.query(Licitacion).filter(Licitacion.codigo_normalizado == codigo.casefold()).first()
        if lic is None:
            lic = svc_lic.crear(db, codigo, titulo, presupuesto, ahora + timedelta(hours=48), ahora=ahora)
            svc_lic.publicar(db, lic.id, ahora=ahora)
        for i, (nombre, monto) in enumerate(ofertas):
            ya = db.query(Oferta).filter(Oferta.licitacion_id == lic.id,
                                         Oferta.proveedor_id == proveedores[nombre].id).first()
            if ya is None:
                # Un segundo de diferencia entre ofertas para que el orden de registro sea claro.
                svc_ofertas.registrar(db, lic.id, proveedores[nombre].id, monto, ahora=ahora + timedelta(seconds=i + 1))

    if svc_tc.obtener_actual(db) is None:
        svc_tc.registrar_tasa(db, "500.00", ahora=ahora)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        if "--reset" in sys.argv:
            reiniciar(db)
            print("Datos anteriores eliminados (los usuarios se conservan).")
        sembrar(db)
        print("Datos de prueba listos: P1, P2, LIC-2026-001 (con ofertas), escenarios aislados y tipo de cambio 500.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
