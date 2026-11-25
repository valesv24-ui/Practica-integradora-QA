"""Resume un archivo .jtl (CSV) de JMeter contra el criterio de REQ-014.

Uso:
    python -m scripts.resumen_jtl ../04_Evidencias/CP-019_rendimiento/resultados.jtl

Solo cuenta las peticiones GET del listado (excluye el login). Imprime muestras,
errores, promedio, p95 (rango más cercano), máximo y rendimiento, y dice si se
cumple: p95 <= 1500 ms y errores <= 5 %. Solo usa la biblioteca estándar.
"""
import csv
import math
import sys

P95_MAXIMO_MS = 1500
ERRORES_MAXIMO_PCT = 5.0


def percentil(valores: list[int], p: float) -> int:
    """Percentil por rango más cercano (valores ya ordenados)."""
    rango = max(1, math.ceil(p / 100 * len(valores)))
    return valores[rango - 1]


def resumir(ruta: str, etiqueta: str = "GET /api/licitaciones") -> dict:
    tiempos, errores, inicios = [], 0, []
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["label"] != etiqueta:
                continue
            tiempos.append(int(fila["elapsed"]))
            inicios.append(int(fila["timeStamp"]))
            if fila["success"].strip().lower() != "true":
                errores += 1
    if not tiempos:
        raise SystemExit(f"No hay muestras con la etiqueta '{etiqueta}' en {ruta}")
    tiempos.sort()
    duracion_s = (max(inicios) - min(inicios)) / 1000 or 1
    return {
        "muestras": len(tiempos),
        "errores": errores,
        "errores_pct": errores / len(tiempos) * 100,
        "promedio_ms": sum(tiempos) / len(tiempos),
        "p95_ms": percentil(tiempos, 95),
        "maximo_ms": tiempos[-1],
        "rendimiento_por_s": len(tiempos) / duracion_s,
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python -m scripts.resumen_jtl <resultados.jtl>")
    r = resumir(sys.argv[1])
    print(f"Muestras:        {r['muestras']}")
    print(f"Errores:         {r['errores']} ({r['errores_pct']:.2f} %)")
    print(f"Promedio:        {r['promedio_ms']:.0f} ms")
    print(f"p95:             {r['p95_ms']} ms")
    print(f"Máximo:          {r['maximo_ms']} ms")
    print(f"Rendimiento:     {r['rendimiento_por_s']:.1f} peticiones/s")
    cumple = r["p95_ms"] <= P95_MAXIMO_MS and r["errores_pct"] <= ERRORES_MAXIMO_PCT
    print(f"REQ-014 (p95 <= {P95_MAXIMO_MS} ms y errores <= {ERRORES_MAXIMO_PCT:.0f} %): {'CUMPLE' if cumple else 'NO CUMPLE'}")


if __name__ == "__main__":
    main()
