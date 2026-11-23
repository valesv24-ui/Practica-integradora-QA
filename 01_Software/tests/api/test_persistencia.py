"""CP-015 · REQ-011: los datos persisten al reiniciar (se abre otra conexión al mismo archivo)."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.database import crear_engine, init_db
from app.services import licitaciones as svc
from app.services import ofertas as svc_ofertas
from app.services import proveedores as svc_prov
from app.services import tipo_cambio as svc_tc

pytestmark = pytest.mark.api


def _sesion(url):
    engine = crear_engine(url)
    init_db(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()


def test_cp015_datos_persisten_al_reiniciar(tmp_path):
    url = f"sqlite:///{(tmp_path / 'persistencia.db').as_posix()}"
    ahora = datetime.now().replace(microsecond=0)

    # Primera "ejecución" de la aplicación: se registran datos y se cierra todo.
    engine1, db1 = _sesion(url)
    lic = svc.crear(db1, "LIC-2026-001", "Licitación L1", "10000000.00", ahora + timedelta(hours=48), ahora=ahora)
    svc.publicar(db1, lic.id, ahora=ahora)
    prov = svc_prov.crear(db1, "Tecnología Norte S.A.")
    svc_ofertas.registrar(db1, lic.id, prov.id, "9000000.00", ahora=ahora)
    svc_tc.registrar_tasa(db1, "500", ahora=ahora)
    db1.close()
    engine1.dispose()

    # Segunda ejecución: nueva conexión al mismo archivo.
    engine2, db2 = _sesion(url)
    try:
        recuperada = svc.listar(db2)
        assert [(x.codigo, x.estado, x.presupuesto_crc) for x in recuperada] == [("LIC-2026-001", "Publicada", Decimal("10000000.00"))]
        assert [p.nombre for p in svc_prov.listar(db2)] == ["Tecnología Norte S.A."]
        assert [o.monto_crc for o in svc_ofertas.listar(db2)] == [Decimal("9000000.00")]
        assert svc_tc.obtener_actual(db2).crc_por_usd == Decimal("500.0000")
    finally:
        db2.close()
        engine2.dispose()
