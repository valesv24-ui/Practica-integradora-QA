# CP-019 · Prueba de rendimiento (REQ-014)

**Criterio:** 5 usuarios virtuales durante 30 s sobre `GET /api/licitaciones`, en local. Debe cumplirse **p95 ≤ 1 500 ms** y **errores ≤ 5 %**. Se registran también CPU y RAM y la configuración del equipo.

Autorizado solo sobre la aplicación del equipo en `localhost`, con datos sintéticos (carga máxima: 5 VU y 30 s).

## 1. Preparar
1. Instalar Apache JMeter 5.6 o superior (requiere Java 8+) y comprobar que `jmeter -v` funciona.
2. En `01_Software/`, con el entorno activado: `python -m scripts.seed --reset` para partir de datos conocidos.
3. Arrancar la aplicación **sin** `--reload` (el recargador distorsiona la medición):
   ```
   uvicorn app.main:app
   ```
4. Anotar el commit que se está probando: `git rev-parse --short HEAD`. Debe ser la versión final (después de la corrección del BUG-001).

## 2. Ejecutar (en otra terminal, desde `01_Software/`)
```
jmeter -n -t rendimiento/lista_licitaciones.jmx -Jusuario=<usuario> -Jpassword=<clave> ^
  -l ../04_Evidencias/CP-019_rendimiento/resultados.jtl ^
  -e -o ../04_Evidencias/CP-019_rendimiento/reporte
```
(`^` es el salto de línea de CMD; en PowerShell es `` ` `` y en Git Bash `\`.) La carpeta `reporte` no debe existir antes de ejecutar. La clave se pasa por línea de comandos: **no** se guarda en el repositorio.

Parámetros opcionales: `-Jhost=127.0.0.1` y `-Jport=8000`.

## 3. Registrar CPU y RAM (mientras corre JMeter)
En PowerShell, durante los 30 s (35 lecturas, una por segundo):
```
typeperf "\Processor(_Total)\% Processor Time" "\Memory\Available MBytes" -si 1 -sc 35 -o ..\04_Evidencias\CP-019_rendimiento\cpu_ram.csv
```
Anotar el máximo y el promedio de CPU y la RAM disponible mínima.

Configuración del equipo (para la hoja 15 y el Word B3):
```
systeminfo | findstr /C:"Nombre del SO" /C:"Procesador" /C:"Memoria física total"
python --version
```
Anotar también la versión de JMeter y de Java, y el commit probado.

## 4. Resumir
```
python -m scripts.resumen_jtl ../04_Evidencias/CP-019_rendimiento/resultados.jtl
```
Imprime muestras, errores, promedio, p95 y si **CUMPLE** o **NO CUMPLE**. Comparar con el reporte HTML de JMeter (`reporte/index.html`); el p95 puede diferir ligeramente porque cada herramienta lo calcula distinto. En el informe se cita el valor del reporte de JMeter.

## 5. Evidencias a conservar (en `04_Evidencias/CP-019_rendimiento/`)
`resultados.jtl`, `reporte/`, `cpu_ram.csv` y una captura del resumen. Nombrarlas con el ID de evidencia (`EV-0xx`) en el registro QA.

Los resultados deben salir de una ejecución real: si no se cumple el criterio, se registra tal cual y se documenta como defecto o desviación.
