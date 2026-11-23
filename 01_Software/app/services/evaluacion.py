"""Evaluación de licitaciones: mejor oferta, ahorro, clasificación y aprobador.

REQ-007, REQ-008, REQ-009 y REQ-010 (vista en USD). Las funciones de arriba son
puras (sin BD); `evaluar_licitacion` al final las une con la base de datos.
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.errores import ReglaNegocio

SIN_OFERTAS = "Sin ofertas válidas"

CLASIF_CONVENIENTE = "Conveniente"
CLASIF_ACEPTABLE = "Aceptable"
CLASIF_SIN_AHORRO = "Válida sin ahorro"

UMBRAL_CONVENIENTE = Decimal("10")  # % de ahorro (REQ-008)

# REQ-009: rangos configurables y sin traslape. (mínimo, máximo o None, aprobador)
RANGOS_APROBACION = [
    (Decimal("0.01"), Decimal("999999.99"), "Encargado de área"),
    (Decimal("1000000.00"), Decimal("9999999.99"), "Gerencia"),
    (Decimal("10000000.00"), None, "Junta Directiva"),
]

_CENTAVO = Decimal("0.01")


def validar_rangos(rangos=RANGOS_APROBACION) -> None:
    """Comprueba que los rangos estén ordenados y no se traslapen."""
    previo_max = None
    for minimo, maximo, _ in rangos:
        if maximo is not None and maximo < minimo:
            raise ValueError("Rango inválido: máximo menor que el mínimo.")
        if previo_max is not None and minimo <= previo_max:
            raise ValueError("Los rangos de aprobación se traslapan.")
        previo_max = maximo if maximo is not None else Decimal("Infinity")


def aprobador_para(monto_crc, rangos=RANGOS_APROBACION) -> str:
    """Aprobador según el monto de la mejor oferta válida (convención del enunciado)."""
    monto = Decimal(str(monto_crc)).quantize(_CENTAVO, rounding=ROUND_HALF_UP)
    if monto <= 0:
        raise ReglaNegocio("El monto debe ser mayor que cero.")
    for minimo, maximo, nombre in rangos:
        if monto >= minimo and (maximo is None or monto <= maximo):
            return nombre
    raise ReglaNegocio("El monto no corresponde a ningún rango de aprobación.")


def clasificar_ahorro(presupuesto, mejor_oferta) -> tuple[Decimal, str]:
    """Devuelve (ahorro %, clasificación).

    Ahorro = ((presupuesto − mejor oferta) / presupuesto) × 100.
    ≥ 10 % Conveniente · > 0 y < 10 % Aceptable · 0 % Válida sin ahorro.
    La clasificación se decide con aritmética exacta, no con el % redondeado.
    """
    presupuesto = Decimal(str(presupuesto))
    mejor = Decimal(str(mejor_oferta))
    if presupuesto <= 0:
        raise ReglaNegocio("El presupuesto debe ser mayor que cero.")
    if mejor <= 0 or mejor > presupuesto:
        raise ReglaNegocio("La mejor oferta debe ser mayor que cero y no superar el presupuesto.")
    ahorro = presupuesto - mejor
    porcentaje = (ahorro / presupuesto * 100).quantize(_CENTAVO, rounding=ROUND_HALF_UP)
    if ahorro * 100 >= presupuesto * UMBRAL_CONVENIENTE:
        return porcentaje, CLASIF_CONVENIENTE
    if ahorro > 0:
        return porcentaje, CLASIF_ACEPTABLE
    return porcentaje, CLASIF_SIN_AHORRO


def _clave_orden(oferta):
    # REQ-007: menor monto; en empate, la registrada primero (luego el id).
    return (Decimal(str(oferta.monto_crc)), oferta.registrada_en, oferta.id)


@dataclass
class Evaluacion:
    total_ofertas: int
    oferta_ganadora: object | None = None
    ahorro_crc: Decimal | None = None
    ahorro_porcentaje: Decimal | None = None
    clasificacion: str | None = None
    aprobador: str | None = None

    @property
    def tiene_ofertas(self) -> bool:
        return self.oferta_ganadora is not None


def evaluar_ofertas(presupuesto, ofertas) -> Evaluacion:
    """Evalúa una lista de ofertas (objetos con monto_crc, registrada_en e id)."""
    presupuesto = Decimal(str(presupuesto))
    validas = [o for o in ofertas if 0 < Decimal(str(o.monto_crc)) <= presupuesto]
    if not validas:
        return Evaluacion(total_ofertas=0)
    ganadora = min(validas, key=_clave_orden)
    monto = Decimal(str(ganadora.monto_crc))
    porcentaje, clasificacion = clasificar_ahorro(presupuesto, monto)
    return Evaluacion(
        total_ofertas=len(validas),
        oferta_ganadora=ganadora,
        ahorro_crc=presupuesto - monto,
        ahorro_porcentaje=porcentaje,
        clasificacion=clasificacion,
        aprobador=aprobador_para(monto),
    )


# ---------- Con base de datos ----------
def _fmt(valor) -> str:
    return f"{Decimal(str(valor)):.2f}"


def evaluar_licitacion(db, licitacion_id: int, moneda: str = "CRC") -> dict:
    """Resultado de evaluación listo para la API y la interfaz.

    Los importes se guardan siempre en CRC; la vista en USD solo convierte al
    mostrar y no modifica la base de datos (REQ-010).
    """
    from app.services import licitaciones as svc_lic
    from app.services import ofertas as svc_ofertas
    from app.services import tipo_cambio as svc_tc

    moneda = (moneda or "CRC").strip().upper()
    if moneda not in ("CRC", "USD"):
        raise ReglaNegocio("La moneda de visualización debe ser CRC o USD.")

    lic = svc_lic.obtener(db, licitacion_id)
    ev = evaluar_ofertas(lic.presupuesto_crc, svc_ofertas.listar(db, licitacion_id=lic.id))

    tasa = None
    if moneda == "USD":
        tasa = svc_tc.requerir_actual(db)

    def vista(monto_crc):
        if tasa is None:
            return _fmt(monto_crc)
        return _fmt(svc_tc.crc_a_usd(monto_crc, tasa.crc_por_usd))

    resultado = {
        "licitacion_id": lic.id,
        "codigo": lic.codigo,
        "titulo": lic.titulo,
        "estado": lic.estado,
        "moneda": moneda,
        "presupuesto": vista(lic.presupuesto_crc),
        "presupuesto_crc": _fmt(lic.presupuesto_crc),
        "total_ofertas": ev.total_ofertas,
        "resultado": "Mejor oferta" if ev.tiene_ofertas else SIN_OFERTAS,
        "mejor_oferta": None,
        "tipo_cambio": None,
    }
    if tasa is not None:
        resultado["tipo_cambio"] = {"crc_por_usd": f"{Decimal(tasa.crc_por_usd):.4f}", "fecha": tasa.fecha.isoformat()}
    if ev.tiene_ofertas:
        g = ev.oferta_ganadora
        resultado.update(
            mejor_oferta={
                "oferta_id": g.id,
                "proveedor_id": g.proveedor_id,
                "proveedor": g.proveedor.nombre,
                "monto": vista(g.monto_crc),
                "monto_crc": _fmt(g.monto_crc),
                "registrada_en": g.registrada_en.isoformat(),
            },
            ahorro=vista(ev.ahorro_crc),
            ahorro_porcentaje=f"{ev.ahorro_porcentaje:.2f}",
            clasificacion=ev.clasificacion,
            aprobador=ev.aprobador,
        )
    return resultado
