# Pendientes

La migración a Django reprodujo la lógica del proyecto Java tal como estaba. Después,
el **lote A** corrigió las fallas visibles: errores 500 por ID inexistente o por nivel
vacío, textos "NONE"/"null", validaciones distintas entre la web, el panel y la API,
placas y tipos de placa sin normalizar, el borrado de administradores con clientes, el
botón para eliminar vehículos, los CSV sin escapar, los totales de los reportes filtrados
y los enlaces a los informes imprimibles. El detalle está en
`docs/superpowers/specs/2026-10-22-lote-a-fallas-visibles-design.md`.

Lo que sigue está **pendiente**, agrupado por los lotes que quedan. Las rutas Java son
relativas a `src/main/java/com/example/sensores_vsc/` del proyecto Spring Boot (rama
`final-java` del repositorio).

## Lote B: lógica de sensores

| # | Comportamiento | Dónde está en Python | Dónde estaba en Java |
|---|---|---|---|
| 1 | El cálculo del nivel trata los valores **dentro** del rango normal como desgaste: TEMP 95 °C da 75 %, que cuenta como FALLA. ECT y MAP no tienen rango propio y caen en el genérico 0–100, así que ECT casi siempre sale en falla y MAP casi siempre en OK. | `api/obd2.py: calcular_nivel` | `controller/Obd2Controller.java:338-355` |
| 2 | Hay dos fuentes de "nivel" que no se sincronizan. `sensores.Nivel` lo usan el dashboard al recargar, `/sensores` y los reportes. `lecturas.Nivel` lo usa la telemetría. "Conectar Bluetooth" y `/api/obd2/lecturas` guardan lecturas pero no actualizan los sensores. | `api/views.py: conectar, guardar_lectura` | `controller/Obd2Controller.java:46-99, 217-296` |
| 3 | `/api/obd2/alertas/{id}` solo mira las 50 alertas más recientes de **todo** el sistema y después filtra por vehículo. | `api/views.py: alertas` | `controller/Obd2Controller.java:139-161` |
| 4 | "Conectar Bluetooth" usa siempre el primer vehículo del cliente. La telemetría web no se actualiza sola: el sondeo de 3 s devuelve las mismas lecturas. | `api/views.py: conectar`; `templates/paginas/dashboard.html` (script) | `controller/Obd2Controller.java:237`; `templates/paginas/dashboard.html` |
| 5 | Los umbrales 40/70 están escritos a mano en varios lugares, fuera del patrón Singleton. | `web/views.py: dashboard`, `api/views.py: datos_cliente_json`, `api/obd2.py`, `panel/views.py: estado_desde_nivel`, `reportes/exportar.py: csv_reporte`, `core/templatetags/autosen.py` | `DashboardController`, `ApiController`, `Obd2Controller`, `AdminController`, plantillas |
| 6 | `GET /api/obd2/vehiculo/{id}/elm` siempre responde `"conectado": false`. | `api/views.py: elm` | `controller/Obd2Controller.java:184-210` |

## Lote C: seguridad de la API

| # | Comportamiento | Dónde está en Python | Dónde estaba en Java |
|---|---|---|---|
| 7 | La API no comprueba que el correo o el ID pertenezcan a quien llama, porque no hay token. Cualquiera que conozca un correo puede consultar o modificar sus datos. | `api/views.py` (todas las vistas) | `controller/ApiController.java`, `controller/Obd2Controller.java` |
| 8 | Cuando el correo no existe, el login responde sin calcular bcrypt, así que el tiempo de respuesta revela qué correos están registrados. En la API, además, "Tu cuenta está bloqueada" solo aparece con la contraseña correcta, pero confirma que la cuenta existe. | `web/views.py: login`, `panel/views.py: login`, `api/views.py: login` | `formLogin` de Spring Security; `controller/ApiController.java` |

## Lote D: rendimiento

| # | Comportamiento | Dónde está en Python | Dónde estaba en Java |
|---|---|---|---|
| 9 | Consultas N+1: por cada cliente se cuenta `vehiculos` y por cada sensor se cargan su vehículo y su cliente, con una consulta por fila. Con pocos datos no se nota; con cientos de filas, el dashboard del panel, los reportes y las exportaciones se vuelven lentos. Se resuelve con `select_related`, `prefetch_related` y `annotate(Count(...))`. | `templates/admin/dashboard.html`, `templates/admin/reportes.html`, `reportes/exportar.py`, `reportes/views.py: vehiculos_con_fallas` | relaciones `LAZY` de JPA en los mismos lugares |

## Diferencias conocidas de la migración (no son errores de Java)

- **Con `DEBUG=True`**, Django muestra sus páginas técnicas de error en lugar de `error.html`. Tampoco redirige al login las rutas desconocidas. Para ver el comportamiento real, ejecuta con `DEBUG=False`.
- **PDF (reportlab)**: el contenido, las tablas y los colores son los de iText, pero no es idéntico píxel a píxel. Por ejemplo, los tres espacios de `Placa: X   |   Color` se muestran como uno.
- **Rutas con un ID que no es número** (p. ej. `/admin/cliente/abc/editar`): dan 404 en lugar del 400 que daba Spring.
- **Sesiones independientes (F2)**: cerrar la sesión de cliente no cierra la de administrador, ni al revés. En Java era una sola sesión.
- **Estáticos (S3)**: se sirven en `/static/...` en lugar de `/css/...` y `/js/...`.
- **`@EnableScheduling`**: estaba activado en Java pero no había tareas programadas, así que no se migró.
