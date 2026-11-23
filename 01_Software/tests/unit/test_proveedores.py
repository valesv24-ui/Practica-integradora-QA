"""CP-001 · REQ-001: normalización de nombres y rechazo de duplicados equivalentes."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Proveedor
from app.services import proveedores as svc
from app.services.errores import Conflicto

pytestmark = pytest.mark.unitaria


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("  Tecnología Norte S.A.  ", "tecnología norte s.a."),
        ("TECNOLOGÍA    NORTE   S.A.", "tecnología norte s.a."),
        ("tecnología norte s.a.", "tecnología norte s.a."),
        ("Servicios\tdel   Valle", "servicios del valle"),
    ],
)
def test_cp001_normalizar_nombre(entrada, esperado):
    # Oráculo: REQ-001 (recortar, compactar espacios, comparar sin mayúsculas)
    assert svc.normalizar_nombre(entrada) == esperado


def test_cp001_limpiar_conserva_mayusculas_para_mostrar():
    assert svc.limpiar_nombre("  Tecnología   Norte S.A. ") == "Tecnología Norte S.A."


def test_cp001_duplicado_con_otra_capitalizacion_y_espacios(db):
    svc.crear(db, "Tecnología Norte S.A.")
    with pytest.raises(Conflicto):
        svc.crear(db, "  TECNOLOGÍA   norte s.a. ")
    assert db.query(Proveedor).count() == 1


def test_cp001_editar_a_nombre_equivalente_de_otro_se_rechaza(db):
    svc.crear(db, "Tecnología Norte S.A.")
    p2 = svc.crear(db, "Servicios del Valle")
    with pytest.raises(Conflicto):
        svc.editar(db, p2.id, "  tecnología NORTE s.a. ")


def test_cp001_editar_mismo_proveedor_cambiando_mayusculas_es_valido(db):
    p = svc.crear(db, "Servicios del Valle")
    editado = svc.editar(db, p.id, "SERVICIOS DEL VALLE")
    assert editado.nombre == "SERVICIOS DEL VALLE"


def test_cp001_bd_rechaza_duplicado_normalizado(db):
    # Aunque se salte el servicio, la restricción UNIQUE de la BD lo impide.
    db.add(Proveedor(nombre="Servicios del Valle", nombre_normalizado="servicios del valle"))
    db.commit()
    db.add(Proveedor(nombre="SERVICIOS DEL VALLE", nombre_normalizado="servicios del valle"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
