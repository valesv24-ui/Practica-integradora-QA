# Sistema de Gestión de Licitaciones

Práctica Integradora de QA · **ISW-622 Pruebas de Software** · Grupo 02
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

> _Por definir por el equipo antes de programar. Completar esta sección con la opción elegida._

| Componente | Elección |
|---|---|
| Lenguaje y framework | _Por definir_ (ruta .NET / ASP.NET Core o alternativa Python con FastAPI/Flask) |
| Base de datos | _Por definir_ (SQLite o PostgreSQL) |
| Interfaz web | _Por definir_ |
| Pruebas automatizadas | _Por definir_ (xUnit/NUnit/MSTest o pytest) |
| Pruebas de API | Postman |
| Pruebas de rendimiento | JMeter |

## Instalación y ejecución

> _Se completará cuando se defina el stack. Debe incluir los comandos exactos de cada paso._

1. **Requisitos previos:** _por definir_
2. **Clonar el repositorio:**
   ```bash
   git clone <URL-del-repositorio>
   cd <carpeta-del-repositorio>
   ```
3. **Instalar dependencias:** _por definir_
4. **Configurar la base de datos y aplicar migraciones:** _por definir_
5. **Cargar datos de prueba (seed):** _por definir_
6. **Ejecutar la aplicación:** _por definir_
7. **Usuarios de prueba:** _por definir (solo credenciales ficticias; no publicar contraseñas reales)_

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

Para reiniciar los datos: _por definir (comando del script de reseteo)_.

## Pruebas

> _Completar con los comandos reales al definir el stack._

- **Pruebas automatizadas (unitarias e integración/API):** _comando por definir_
- **Pruebas de API:** colección de Postman en _ruta por definir_
- **Rendimiento:** plan de JMeter en _ruta por definir_ (5 usuarios virtuales, 30 s, solo sobre `localhost` y datos sintéticos)

Mínimos de la práctica: 14 REQ, 20 casos de prueba (CP), ≥ 23 ejecuciones (RUN), ≥ 8 pruebas automatizadas, 1 defecto controlado (BUG-001), ≥ 3 riesgos y ≥ 3 intervenciones de IA registradas.

## Estructura del repositorio

> _Ajustar a la estructura real del proyecto._

```
.
├── 01_Software/        Código fuente, configuración de ejemplo, migraciones y datos semilla
├── 02_Plan_Informe_QA/ Plan e informe de pruebas (Word y PDF)
├── 03_Registro_QA/     Registro QA/SQA (Excel)
├── 04_Evidencias/      Salidas reales de pruebas, capturas, logs y reportes (nombradas con ID EV-###)
├── 05_IA/              Prompts y respuestas saneadas, versión utilizada y cambios humanos (IA-###)
└── README.md
```

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
