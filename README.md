# Sistema de Gestión de Licitaciones

Práctica Integradora de QA · **ISW-622 Pruebas de Software** · Grupo SC-02
Universidad Técnica Nacional (UTN) · Sede Regional de San Carlos · Ingeniería del Software

Aplicación web local para gestionar proveedores, licitaciones y ofertas, desarrollada con apoyo de IA y sometida a un ciclo completo de aseguramiento de la calidad (plan, ejecución, defectos, informe y registro de uso de IA).

## Equipo

| Rol | Integrante | Rama de trabajo |
|---|---|---|
| Persona A · Coordinadora | Valery Salas Vargas | `feature/proveedores-ofertas` |
| Persona B | Maykel Meoño González | `feature/licitaciones-evaluacion` |
| Docente | Andrés Joseph Jiménez Leandro | — |

## Alcance funcional

| Módulo | Qué hace | Responsable |
|---|---|---|
| Proveedores | Registrar, listar y editar; normaliza nombres, evita duplicados y restringe caracteres permitidos | A |
| Ofertas | Registrar y listar por licitación/proveedor; rechaza inválidas, duplicadas, superiores al presupuesto y fuera de plazo | A |
| Licitaciones | Registrar y listar con código, título, presupuesto en CRC y cierre; publicar y cerrar según reglas de estado | B |
| Evaluación | Mejor oferta, ahorro porcentual, clasificación y aprobador correspondiente | B |
| Tipo de cambio | Tasa CRC por USD (servicio externo) y alternancia de la vista sin alterar los importes guardados en CRC | B |
| Autenticación | Acceso con usuario y contraseña | A |

Además de la interfaz web, el sistema expone una API HTTP con al menos cuatro operaciones verificables (consulta, alta y escenarios negativos).

## Reglas de negocio principales

Los requisitos verificables (REQ-001 a REQ-014) provienen del enunciado y se trazan en el registro QA con los mismos IDs.

- **Proveedores:** nombres equivalentes (sin distinguir mayúsculas ni espacios) se rechazan como duplicados; solo se admiten letras, números, espacios, punto, coma y paréntesis.
- **Licitaciones:** código único; presupuesto CRC > 0; cierre en fecha futura. Transiciones válidas: Borrador → Publicada/Cerrada y Publicada → Cerrada.
- **Ofertas:** solo en licitaciones Publicadas y antes del cierre (exactamente en el cierre se rechaza); monto > 0 y ≤ presupuesto; una oferta por proveedor por licitación (también garantizado por la base de datos).
- **Evaluación:** gana la menor oferta válida (en empate, la registrada primero). Ahorro = ((presupuesto − mejor oferta) / presupuesto) × 100: ≥ 10 % conveniente, > 0 y < 10 % aceptable, 0 % válida sin ahorro.
- **Aprobación (sobre la mejor oferta):** 0,01–999 999,99 Encargado de área · 1 000 000–9 999 999,99 Gerencia · ≥ 10 000 000 Junta Directiva.
- **Moneda:** solo se persiste CRC; USD = CRC / (CRC por USD); se muestran la tasa y la fecha utilizadas.

## Tecnologías

| Componente | Elección |
|---|---|
| Lenguaje y framework | Python 3.10+ con FastAPI |
| Base de datos | SQLite (archivo local `01_Software/data/licitaciones.db`) con SQLAlchemy 2 |
| Interfaz web | Plantillas HTML con Jinja2 (servidas por FastAPI) |
| Pruebas automatizadas | pytest (unitarias, integración/API y seguridad) |
| Pruebas de API | Postman |
| Pruebas de rendimiento | JMeter |

## Instalación y ejecución

Todos los comandos se ejecutan dentro de `01_Software/`.

1. **Requisitos previos:** Python 3.10 o superior y Git.
2. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/valesv24-ui/Practica-integradora-QA.git
   cd Practica-integradora-QA/01_Software
   ```
3. **Instalar dependencias:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   # source .venv/bin/activate     # Linux / macOS
   pip install -r requirements.txt
   ```
4. **Configurar la base de datos:** no requiere migraciones; las tablas se crean solas al arrancar. Para usar otro archivo, definir `DATABASE_URL` (p. ej. `sqlite:///data/otra.db`).
5. **Cargar datos de prueba (seed):** `python -m scripts.seed` (idempotente: P1, P2, L1 con sus ofertas, escenarios aislados y tipo de cambio 500).
6. **Ejecutar la aplicación:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Interfaz web: http://127.0.0.1:8000 · Documentación de la API (Swagger): http://127.0.0.1:8000/docs
7. **Usuarios de prueba:** se crean localmente con `python -m scripts.crear_usuario <usuario>` (la contraseña se pide por teclado y no se guarda en el repositorio).

Opcional: definir `SECRET_KEY` para que las sesiones sobrevivan a un reinicio del servidor.

## Datos de prueba

Todos los datos son sintéticos y reproducibles mediante el script de semilla. No se usan datos de personas ni empresas reales.

| Dato | Valor |
|---|---|
| Proveedor P1 | Tecnología Norte S.A. |
| Proveedor P2 | Servicios del Valle |
| Licitación L1 | LIC-2026-001 · presupuesto CRC 10 000 000,00 · cierre en ahora + 48 h |
| Ofertas de L1 | P1 = CRC 9 000 000,00 · P2 = CRC 9 500 000,00 |
| Tipo de cambio | CRC 500,00 por USD (P1 se visualiza como USD 18 000,00) |
| Escenarios aislados | Presupuesto CRC 1 000 000,00 con ofertas de 900 000 / 950 000 / 1 000 000 |

Para reiniciar los datos: `python -m scripts.seed --reset` (borra proveedores, licitaciones, ofertas y tipos de cambio, conserva los usuarios y vuelve a cargar el seed).

Escenarios aislados (presupuesto CRC 1 000 000): `ESC-AHORRO-10` (oferta 900 000), `ESC-AHORRO-05` (950 000), `ESC-AHORRO-00` (1 000 000) y `ESC-SIN-OFERTAS` (sin ofertas).

## Pruebas

- **Pruebas automatizadas (unitarias e integración/API):** dentro de `01_Software/`, ejecutar `pytest`. Por tipo: `pytest -m unitaria`, `pytest -m api`, `pytest -m seguridad`. Reporte para evidencias: `pytest --junitxml=reportes/pytest.xml`. Las pruebas usan una BD temporal y no modifican `data/licitaciones.db`.
- **Pruebas de API:** colección de Postman en _ruta por definir_
- **Rendimiento (CP-019):** plan de JMeter en `01_Software/rendimiento/lista_licitaciones.jmx` (5 usuarios virtuales, 30 s, solo sobre `localhost` y datos sintéticos). Instrucciones de ejecución y de medición de CPU/RAM en `01_Software/rendimiento/README.md`; resumen del `.jtl` con `python -m scripts.resumen_jtl <archivo.jtl>`.
- **Usabilidad (CP-018):** guion y registro de la sesión en `04_Evidencias/CP-018_usabilidad/registro_sesion.md`.

Variables de entorno opcionales: `TIPO_CAMBIO_URL` (servicio externo; debe devolver JSON con el campo `venta`).

Pruebas automatizadas de Persona A:

| Archivo (en `01_Software/`) | CP | REQ |
|---|---|---|
| `tests/unit/test_proveedores.py` | CP-001 | REQ-001 |
| `tests/unit/test_ofertas_reglas.py` | CP-002, CP-003 | REQ-005, REQ-004 |
| `tests/unit/test_ofertas_duplicadas.py` | CP-004 | REQ-006 |
| `tests/api/test_api_ofertas.py` | CP-005, CP-010 | REQ-011, REQ-005, REQ-004 |
| `tests/seguridad/test_seguridad.py` | CP-008, CP-009 | REQ-012 |

Pruebas automatizadas de Persona B:

| Archivo (en `01_Software/`) | CP | REQ |
|---|---|---|
| `tests/unit/test_evaluacion_ahorro.py` | CP-011 | REQ-008 |
| `tests/unit/test_aprobador.py` | CP-012 | REQ-009 |
| `tests/unit/test_conversion.py` | CP-013 | REQ-010 |
| `tests/api/test_api_licitaciones.py` | CP-014, CP-020 (parte API), RSK-001 | REQ-002, REQ-011, REQ-010 |
| `tests/api/test_persistencia.py` | CP-015 | REQ-011 |
| `tests/funcional/test_licitaciones_funcional.py` | CP-016, CP-017 | REQ-003, REQ-007, REQ-008, REQ-009, REQ-010 |
| `tests/unit/test_licitaciones_reglas.py` | CP-016 (reglas), CP-020 | REQ-002, REQ-003 |
| `tests/regresion/test_regresion_bug001.py` | Retest y regresión de BUG-001 | REQ-004, REQ-005, REQ-006, REQ-007 |

Los CP-018 (usabilidad) y CP-019 (rendimiento con JMeter) se ejecutan manualmente; sus guiones están en `04_Evidencias/CP-018_usabilidad/` y `01_Software/rendimiento/`, y los resultados se documentan en el registro QA.

Mínimos de la práctica: 14 REQ, 20 casos de prueba (CP), ≥ 23 ejecuciones (RUN), ≥ 8 pruebas automatizadas, 1 defecto controlado (BUG-001), ≥ 3 riesgos y ≥ 3 intervenciones de IA registradas.

## Estructura del repositorio

```
.
├── 01_Software/        Código fuente, configuración y datos semilla
│   ├── app/            main.py, database.py, models.py, security.py
│   │   ├── services/   Reglas de negocio (proveedores, ofertas, licitaciones, evaluación, tipo de cambio)
│   │   ├── routers/    api.py y api_licitaciones.py (JSON); web.py y web_licitaciones.py (HTML)
│   │   └── templates/  Vistas Jinja
│   ├── scripts/        crear_usuario, seed (datos semilla), resumen_jtl (resumen de JMeter)
│   ├── rendimiento/    Plan JMeter (CP-019) e instrucciones
│   ├── tests/          unit / api / funcional / seguridad
│   └── data/           BD local SQLite (ignorada por Git)
├── 02_Plan_Informe_QA/ Plan e informe de pruebas (Word y PDF)
├── 03_Registro_QA/     Registro QA/SQA (Excel)
├── 04_Evidencias/      Salidas reales de pruebas, capturas, logs y reportes (nombradas con ID EV-###)
├── 05_IA/              Prompts y respuestas saneadas, versión utilizada y cambios humanos (IA-###)
└── README.md
```

### API HTTP (Proveedores, Ofertas y autenticación)

Todas las rutas requieren sesión: primero `POST /api/login` con `{"usuario": "...", "password": "..."}`.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/login` · `/api/logout` | Iniciar / cerrar sesión |
| GET | `/api/proveedores` · `/api/proveedores/{id}` | Listar / consultar |
| POST | `/api/proveedores` | Registrar (`{"nombre": "..."}`) |
| PUT | `/api/proveedores/{id}` | Editar |
| DELETE | `/api/proveedores/{id}` | Eliminar (solo sin ofertas) |
| GET | `/api/ofertas?licitacion_id=&proveedor_id=` | Listar con filtros |
| POST | `/api/ofertas` | Registrar (`{"licitacion_id", "proveedor_id", "monto_crc"}`) |
| DELETE | `/api/ofertas/{id}` | Retirar (solo con la licitación abierta) |

Códigos: `201` creado · `401` sin sesión · `404` no existe · `409` duplicado o estado incompatible · `422` dato inválido · `503` servicio externo no disponible · `500` error interno sin traza.

### API HTTP (Licitaciones, Evaluación y Tipo de cambio)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/licitaciones` · `/api/licitaciones/{id}` | Listar / consultar |
| POST | `/api/licitaciones` | Registrar en Borrador (`{"codigo", "titulo", "presupuesto_crc", "cierre"}`) |
| PUT | `/api/licitaciones/{id}` | Editar (solo en Borrador) |
| DELETE | `/api/licitaciones/{id}` | Eliminar (solo en Borrador y sin ofertas) |
| POST | `/api/licitaciones/{id}/publicar` · `/cerrar` | Borrador → Publicada/Cerrada, Publicada → Cerrada |
| GET | `/api/licitaciones/{id}/evaluacion?moneda=CRC\|USD` | Mejor oferta, ahorro, clasificación y aprobador (`USD` solo cambia la vista) |
| GET | `/api/tipo-cambio` | Tasa vigente (409 si no hay ninguna) |
| POST | `/api/tipo-cambio` | Configurar la tasa (`{"crc_por_usd": "500"}`, debe ser > 0) |
| POST | `/api/tipo-cambio/sincronizar` | Consultar el servicio externo (503 si falla) |

Interfaz web: `/licitaciones`, `/evaluacion` y `/tipo-cambio`.

## Flujo de trabajo con Git

- `main` es la rama estable; **no se trabaja directo en ella** (solo el commit inicial con este README).
- Cada integrante trabaja en su rama de funcionalidad y la integra a `main` mediante **Pull Request**, revisado por la otra persona.
- Los commits se alternan entre integrantes (mínimo 2 commits no consecutivos por persona).
- El defecto inducido (BUG-001) se introduce en una rama de laboratorio; se conservan los hashes del commit defectuoso y del commit de corrección. La versión final **no** conserva el defecto.

## Uso de IA y transparencia

La IA se utiliza como apoyo para generar o mejorar código y pruebas. La validación, ejecución, corrección y aceptación final son responsabilidad humana. Cada intervención se registra (herramienta, modelo/versión, fecha, finalidad, prompt, salida y partes incorporadas) en `05_IA/` y en las hojas `09_IA_Usos` y `10_Revision_IA` del registro QA. No se incluyen secretos, contraseñas ni datos personales en prompts ni evidencias.

## Seguridad y ámbito de las pruebas

Las pruebas se limitan a la aplicación del equipo ejecutada en `localhost`, con datos sintéticos y sin explotación destructiva. No se prueban sistemas de la UTN, servicios externos ni terceros.

## Licencia y uso

Proyecto académico del curso ISW-622 de la UTN, Sede San Carlos. Uso exclusivamente educativo.
