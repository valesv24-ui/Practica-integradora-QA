# CP-018 · Sesión de usabilidad (REQ-013)

**Criterio:** con **2 personas ajenas al equipo**, al menos **3 de las 4 tareas** (registrar proveedor y ofertar) se completan **sin ayuda**.

> Plantilla vacía. Se llena durante la sesión real; no se inventan datos. No se anotan nombres ni datos personales: se usa "Participante 1" y "Participante 2" con un perfil general (por ejemplo, "estudiante de otra carrera").

## Preparación (antes de la sesión)
- [ ] Aplicación corriendo en la versión a evaluar (commit: `__________`).
- [ ] Datos reiniciados con `python -m scripts.seed --reset` (existen P1, P2 y la licitación LIC-2026-001 Publicada, presupuesto CRC 10 000 000).
- [ ] Usuario de prueba creado; se entrega la clave solo de palabra. **No** se escribe aquí.
- [ ] Navegador abierto en http://127.0.0.1:8000 con la sesión **cerrada**.
- [ ] Cronómetro listo. Una persona del equipo observa y **no ayuda**; otra anota.

## Guion para el participante
"Va a usar un sistema de licitaciones. Le pediré hacer algunas tareas. Evaluamos el sistema, no a usted. Puede pensar en voz alta. No le podremos ayudar durante las tareas."

## Tareas

| Tarea | Participante | Instrucción (se lee en voz alta) | Resultado correcto |
|---|---|---|---|
| T1 | 1 | Inicie sesión y registre un proveedor nuevo llamado «Constructora Los Robles». | Aparece en la lista de proveedores. |
| T2 | 1 | Registre una oferta de ₡9 800 000 de ese proveedor para la licitación LIC-2026-001. | Aparece en la lista de ofertas con ese monto. |
| T3 | 2 | Inicie sesión y registre un proveedor nuevo llamado «Servicios Andinos». | Aparece en la lista de proveedores. |
| T4 | 2 | Registre una oferta de ₡9 700 000 de ese proveedor para la licitación LIC-2026-001. | Aparece en la lista de ofertas con ese monto. |

(Los nombres son ficticios. No hay que explicar dónde está cada pantalla.)

## Registro de la sesión

| Tarea | Inicio | Fin | Tiempo (s) | ¿Completada sin ayuda? (Sí/No) | Ayudas dadas | Errores del sistema o del usuario | Obstáculos observados |
|---|---|---|---|---|---|---|---|
| T1 | | | | | | | |
| T2 | | | | | | | |
| T3 | | | | | | | |
| T4 | | | | | | | |

Perfil Participante 1: ______________________  Perfil Participante 2: ______________________
Fecha y hora de la sesión: ______________________  Commit probado: ______________________

## Resultado
- Tareas completadas sin ayuda: ____ de 4  → **CP-018: Aprobado / Fallido** (aprobado si ≥ 3 de 4).
- Comentarios espontáneos de los participantes: 
- Mejoras sugeridas (si aplica, registrar como observación o defecto):

## Después de la sesión
- [ ] Pasar los datos a la hoja `14_Usabilidad` del Excel y al Word B3 (mismas cifras).
- [ ] Guardar este archivo lleno y fotos o capturas (sin rostros ni datos personales) como evidencia `EV-0xx`.
- [ ] Reiniciar los datos con `python -m scripts.seed --reset`.
