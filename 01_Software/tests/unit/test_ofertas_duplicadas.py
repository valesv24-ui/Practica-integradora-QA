"""CP-004 · REQ-006: un proveedor solo puede ofertar una vez por licitación."""
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Oferta
from app.services import ofertas as svc_ofertas
from app.services import proveedores as svc_proveedores
from app.services.errores import Conflicto

pytestmark = pytest.mark.unitaria


def test_cp004_segunda_oferta_mismo_proveedor_se_rechaza(db, crear_licitacion):
    lic = crear_licitacion()
    p1 = svc_proveedores.crear(db, "Tecnología Norte S.A.")
    svc_ofertas.registrar(db, lic.id, p1.id, "9000000.00")
    with pytest.raises(Conflicto):
        svc_ofertas.registrar(db, lic.id, p1.id, "8500000.00")
    assert db.query(Oferta).count() == 1


def test_cp004_otro_proveedor_en_la_misma_licitacion_si_puede(db, crear_licitacion):
    lic = crear_licitacion()
    p1 = svc_proveedores.crear(db, "Tecnología Norte S.A.")
    p2 = svc_proveedores.crear(db, "Servicios del Valle")
    svc_ofertas.registrar(db, lic.id, p1.id, "9000000.00")
    svc_ofertas.registrar(db, lic.id, p2.id, "9500000.00")
    assert db.query(Oferta).count() == 2


def test_cp004_bd_rechaza_duplicado_aunque_se_salte_el_servicio(db, crear_licitacion):
    lic = crear_licitacion()
    p1 = svc_proveedores.crear(db, "Tecnología Norte S.A.")
    ahora = datetime.now()
    db.add(Oferta(licitacion_id=lic.id, proveedor_id=p1.id, monto_crc=1, registrada_en=ahora))
    db.commit()
    db.add(Oferta(licitacion_id=lic.id, proveedor_id=p1.id, monto_crc=2, registrada_en=ahora))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
