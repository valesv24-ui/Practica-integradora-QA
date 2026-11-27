# EV-013 · Pruebas manuales de la API (Swagger UI)

- **Ejecutora:** Valery Salas Vargas
- **Fecha:** 2026-11-27, de 14:26 a 15:08 (hora de Costa Rica, UTC-6). Las cabeceras `date` de las capturas están en GMT (+6 h).
- **Build:** `fb3d833` (`main`), aplicación local en `http://127.0.0.1:8000`, con la documentación interactiva en `/docs`.
- **Entorno:** Windows · Python 3.14.6 · uvicorn · navegador · BD SQLite local cargada con `scripts.seed --reset`.
- **Datos:** sintéticos. Proveedores 1 = Tecnología Norte S.A., 2 = Servicios del Valle, 3 = Averys Tec. Licitaciones 1 = LIC-2026-001 (presupuesto 10 000 000) y 5 = ESC-SIN-OFERTAS.
- **Excluidas:** las capturas del inicio de sesión exitoso, porque muestran la contraseña del usuario de prueba.

| Captura | Solicitud | Esperado | Obtenido | CP / RUN |
|---|---|---|---|---|
| 01 | GET /api/proveedores | 200 con la lista | 200, 3 proveedores | CP-001 · RUN-028 |
| 02 | GET /api/proveedores/3 | 200 | 200, Averys Tec | CP-001 · RUN-028 |
| 03 | GET /api/proveedores/99 | 404 controlado | 404 «Proveedor no encontrado.» | CP-009 · RUN-027 |
| 04 | POST /api/proveedores «Proveedor API» | 201 | 201, id 4 | CP-001 · RUN-028 |
| 05 | POST /api/proveedores «  PROVEEDOR   api » | 409 por nombre equivalente | 409 «Ya existe un proveedor con ese nombre.» | CP-001 · RUN-028 |
| 06 | POST /api/proveedores `<script>alert(1)</script>` | 422 | 422, caracteres no admitidos | CP-008 · RUN-026 |
| 07 | GET /api/ofertas?licitacion_id=1&proveedor_id=1 | 200 filtrado | 200, oferta de P1 en LIC-2026-001 | CP-005 · RUN-024 |
| 08 | POST /api/ofertas P1 en L1 (8 000 000) | 409 por duplicado | 409 | CP-005 · RUN-024 |
| 09 | POST /api/ofertas con cuerpo JSON mal formado | Error controlado sin traza | 422 «Datos inválidos.» sin traza | CP-009 · RUN-027 |
| 10 | POST /api/ofertas monto 0 | 422 | 422 «El monto de la oferta debe ser mayor que cero.» | CP-005 · RUN-024 |
| 11 | POST /api/ofertas Averys Tec en L1 (9 800 000) | 201 | 201, oferta id 7 | CP-005 · RUN-024 |
| 12 | Misma oferta otra vez | 409 | 409 | CP-005 · RUN-024 |
| 13 | POST /api/logout | 200 | 200 | CP-005 · RUN-024 |
| 14 | POST /api/login con datos incorrectos | 401 genérico | 401 «Usuario o contraseña incorrectos.» | CP-009 · RUN-027 |
| 15 | GET /api/proveedores sin sesión | 401 | 401 «Debe iniciar sesión.» | CP-005 · RUN-024 |
| 16 | POST /api/ofertas L1 con 10 000 000,01 | 422 | 422 «El monto de la oferta no puede superar el presupuesto de la licitación.» | CP-010 · RUN-025 |

**Observación:** con un JSON mal formado (captura 09) la respuesta es controlada y no expone trazas (REQ-012), pero el campo `campos` muestra una posición numérica («70») que no orienta al usuario. Es una mejora posible, no un defecto.

Después de las pruebas se restablecieron los datos con `python -m scripts.seed --reset`.
