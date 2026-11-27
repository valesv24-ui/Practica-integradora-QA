# CP-018 · Sesión de usabilidad (REQ-013)

**Criterio:** con **2 personas ajenas al equipo**, al menos **3 de las 4 tareas** (registrar proveedor y ofertar) se completan **sin ayuda**.

> Registro lleno con datos reales de la sesión del 26-nov-2026. Los participantes están anonimizados («Participante 1» y «Participante 2»). Donde un dato no se midió o no se anotó, se dice así y no se estima.

## Preparación
- [x] Aplicación corriendo (base de datos propia de la sesión, `cp018.db`). Commit probado: `f470499` (el del resto de ejecuciones finales; no se anotó un `git rev-parse` aparte en esta sesión).
- [x] Datos reiniciados con `python -m scripts.seed --reset`: las capturas muestran P1, P2, LIC-2026-001 y las ofertas del seed cargadas a las 18:27:33.
- [x] Usuario de prueba creado; la clave se entregó solo de palabra y no se escribe aquí.
- [ ] Navegador abierto con la sesión cerrada y cronómetro: no se dejó constancia.
- Una persona del equipo observó y no ayudó.

## Guion para el participante
"Va a usar un sistema de licitaciones. Le pediré hacer algunas tareas. Evaluamos el sistema, no a usted. Puede pensar en voz alta. No le podremos ayudar durante las tareas."

## Tareas

| Tarea | Participante | Instrucción (se lee en voz alta) | Resultado correcto |
|---|---|---|---|
| T1 | 1 | Inicie sesión y registre un proveedor nuevo llamado «Constructora Los Robles». | Aparece en la lista de proveedores. |
| T2 | 1 | Registre una oferta de ₡9 800 000 de ese proveedor para la licitación LIC-2026-001. | Aparece en la lista de ofertas con ese monto. |
| T3 | 2 | Inicie sesión y registre un proveedor nuevo llamado «Servicios Andinos». | Aparece en la lista de proveedores. |
| T4 | 2 | Registre una oferta de ₡9 700 000 de ese proveedor para la licitación LIC-2026-001. | Aparece en la lista de ofertas con ese monto. |

## Registro de la sesión

Fecha de la sesión: 26-nov-2026 (hora de Costa Rica, UTC-6). Los tiempos por tarea son una **estimación del observador (alrededor de 70 s por tarea), no se cronometraron**.

| Tarea | Inicio | Fin | Tiempo (s) | ¿Completada sin ayuda? | Ayudas dadas | Errores | Obstáculos observados |
|---|---|---|---|---|---|---|---|
| T1 | ≈ 18:30 (inicio del Participante 1, según el observador) | No anotado | ≈ 70 (estimado) | Sí | Ninguna | Error del usuario: escribió «Constructora Robles» en lugar de «Constructora Los Robles»; el sistema lo registró con ese nombre (ID 3). | Ninguno anotado |
| T2 | No anotado | 18:32:56 (hora de registro de la oferta en el sistema) | ≈ 70 (estimado) | Sí | Ninguna | Ninguno | Ninguno anotado |
| T3 | No determinado (antes de 18:34:33) | No anotado | ≈ 70 (estimado) | Sí | Ninguna | Ninguno | Ninguno anotado |
| T4 | No anotado | 18:34:33 (hora de registro de la oferta en el sistema) | ≈ 70 (estimado) | Sí | Ninguna | Ninguno | Ninguno anotado |

Perfil Participante 1: estudiante de otro grupo (no conocía la aplicación).
Perfil Participante 2: estudiante de otro grupo (no conocía la aplicación).
Hora de inicio del Participante 2: el observador la recordó como 18:40, pero el sistema registró su oferta (T4) a las 18:34:33, por lo que esa hora no es posible; se usan las horas del sistema.
Evidencia: capturas de T1, T2 y T4 en esta carpeta (EV-010). No hay captura de T3.

## Resultado
- Tareas completadas sin ayuda: **4 de 4** → **CP-018: Aprobado** (aprobado si ≥ 3 de 4).
- Si T1 no se contara como completada por el nombre mal escrito, serían 3 de 4 y el resultado seguiría siendo Aprobado.
- Comentarios espontáneos de los participantes: no se anotaron.
- Mejoras sugeridas: ninguna anotada.

## Después de la sesión
- [ ] Pasar los datos a la hoja `14_Usabilidad` del Excel y al Word B3 (mismas cifras).
- [x] Guardar este archivo lleno y las capturas como evidencia EV-010.
- [ ] Reiniciar los datos con `python -m scripts.seed --reset`.
