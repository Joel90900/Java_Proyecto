# Pendientes: comportamientos del proyecto Java que se conservaron a propósito

La migración a Django reproduce la lógica del proyecto Java tal como estaba. Solo se
corrigieron los defectos que bloqueaban el uso (F1–F6 y S1–S3 en la especificación,
`docs/superpowers/specs/2026-10-21-migracion-django-design.md`, sección 3).

Lo siguiente se **conservó a propósito**, para que la migración fuera fiel. Queda
anotado para que el equipo decida si lo corrige más adelante. Las rutas Java son
relativas a `referencia/proyecto-java/src/main/java/com/example/sensores_vsc/`.

| # | Comportamiento | Dónde está en Python | Dónde estaba en Java |
|---|---|---|---|
| 1 | El cálculo del nivel trata los valores **dentro** del rango normal como desgaste: TEMP 95 °C da 75 %, que cuenta como FALLA. ECT y MAP no tienen rango propio y caen en el genérico 0–100, así que ECT casi siempre sale en falla y MAP casi siempre en OK. | `api/obd2.py: calcular_nivel` | `controller/Obd2Controller.java:338-355` |
| 2 | Hay dos fuentes de "nivel" que no se sincronizan. `sensores.Nivel` lo usan el dashboard al recargar, `/sensores` y los reportes. `lecturas.Nivel` lo usa la telemetría. "Conectar Bluetooth" y `/api/obd2/lecturas` guardan lecturas pero no actualizan los sensores. | `api/views.py: conectar, guardar_lectura` | `controller/Obd2Controller.java:46-99, 217-296` |
| 3 | La API no comprueba que el correo o el ID pertenezcan a quien llama, porque no hay token. Cualquiera que conozca un correo puede consultar o modificar sus datos. | `api/views.py` (todas las vistas) | `controller/ApiController.java`, `controller/Obd2Controller.java` |
| 4 | `/api/obd2/alertas/{id}` solo mira las 50 alertas más recientes de **todo** el sistema y después filtra por vehículo. | `api/views.py: alertas` | `controller/Obd2Controller.java:139-161` |
| 5 | "Conectar Bluetooth" usa siempre el primer vehículo del cliente. La telemetría web no se actualiza sola: el sondeo de 3 s devuelve las mismas lecturas. | `api/views.py: conectar`; `templates/paginas/dashboard.html` (script) | `controller/Obd2Controller.java:237`; `templates/paginas/dashboard.html` |
| 6 | Un ID inexistente en la URL da error 500 (el `orElseThrow` de Java). | `web/views.py`, `panel/views.py`, `reportes/views.py` (`Modelo.objects.get`) | `orElseThrow()` en los controladores |
| 7 | El registro web no recorta espacios ni valida el formato del correo; el registro de la API sí recorta. | `web/views.py: register`; `api/views.py: registrar` | `controller/AuthController.java:30-51`; `controller/ApiController.java:44-66` |
| 8 | Al crear un vehículo se busca la placa duplicada **antes** de validar el formato, y sin recortar espacios. Editar un vehículo desde la web del cliente no valida el formato de la placa. | `web/views.py: vehiculo_crear, vehiculo_editar`; `api/views.py: crear_vehiculo` | `controller/VehiculoController.java:56-64, 138-144`; `controller/ApiController.java:173-183` |
| 9 | Los CSV no escapan las comas: un nombre con coma desordena las columnas. | `reportes/exportar.py: csv_reporte` | `controller/AdminController.java:523-577` |
| 10 | Los umbrales 40/70 están escritos a mano en varios lugares, fuera del patrón Singleton. | `web/views.py: dashboard`, `api/views.py: datos_cliente_json`, `api/obd2.py`, `panel/views.py: estado_desde_nivel`, `reportes/exportar.py: csv_reporte`, `core/templatetags/autosen.py` | `DashboardController`, `ApiController`, `Obd2Controller`, `AdminController`, plantillas |
| 11 | Los valores de tipo de placa no son consistentes: los datos importados tienen `Particular`/`Público` y los formularios usan `particular`/`publico`. El filtro de reportes compara sin tildes ni mayúsculas (F5), pero los datos no se normalizan. | datos importados; `templates/paginas/crear-vehiculo.html`, `templates/admin/crear-vehiculo.html` | dump MySQL; plantillas Thymeleaf |
| 12 | No se puede borrar un administrador si algún cliente lo referencia en `Id_usuario`: da error 500. | `panel/views.py: usuario_eliminar` (`Cliente.usuario` con `PROTECT`) | `controller/AdminController.java:827-838` (clave foránea de MySQL) |
| 13 | El cliente no tiene botón para eliminar vehículos, aunque la ruta `/vehiculos/{id}/eliminar` existe. | `templates/paginas/mis-vehiculos.html`; `web/urls.py` | `templates/paginas/mis-vehiculos.html`; `controller/VehiculoController.java:156-168` |
| 14 | Ninguna página enlaza los informes imprimibles `/admin/reportes-pdf` y `/admin/reporte-cliente-pdf/{id}`. | `reportes/urls.py` | `controller/ReporteController.java:129-190` |
| 15 | En `/admin/reportes-filtrado`, los totales de vehículos, los vehículos con fallas y los clientes bloqueados no respetan los filtros. | `reportes/views.py: reportes_filtrado` | `controller/ReporteController.java:91-104` |
| 16 | `GET /api/obd2/vehiculo/{id}/elm` siempre responde `"conectado": false`. | `api/views.py: elm` | `controller/Obd2Controller.java:184-210` |
| 17 | `@EnableScheduling` estaba activado pero no había tareas programadas; no se migró. | — | `SensoresVscApplication.java` |
| 18 | Un sensor con `Nivel` NULL (posible en datos importados) provoca un error 500 en estos lugares: el dashboard del cliente, `/api/cliente/{correo}`, `/api/bluetooth/simular` y los CSV de sensores y fallas. | `web/views.py: dashboard`; `api/views.py: datos_cliente_json, simular`; `reportes/exportar.py: csv_reporte` | `DashboardController.java:43-45`; `ApiController.java:107-109, 225`; `AdminController.java:542, 553` |
| 19 | **Afecta a los datos reales:** el cliente no puede editar un vehículo importado con placa en minúsculas (`emt262`, `432fsfdf`, `gmf322`). Al guardar sin cambiar la placa recibe "Ya existe un vehículo con esa placa.". El motivo: compara la placa en mayúsculas con la guardada en minúsculas y luego la encuentra a sí misma. **Solución sin tocar código:** un administrador corrige la placa desde el panel (que la guarda en mayúsculas). | `web/views.py: vehiculo_editar` | `controller/VehiculoController.java:138-144` (con la intercalación de MySQL) |
| 20 | **Afecta a los datos reales:** al editar un vehículo importado con tipo de placa `Particular` o `Público`, el desplegable no preselecciona nada, así que al guardar se escribe `particular` sin avisar. | `templates/paginas/editar-vehiculo.html`, `templates/admin/editar-vehiculo.html` | las mismas plantillas Thymeleaf |

## Diferencias conocidas de la migración (no son errores de Java)

- **Con `DEBUG=True`**, Django muestra sus páginas técnicas de error en lugar de `error.html`. Tampoco redirige al login las rutas desconocidas. Para ver el comportamiento real, ejecuta con `DEBUG=False`.
- **PDF (reportlab)**: el contenido, las tablas y los colores son los de iText, pero no es idéntico píxel a píxel. Por ejemplo, los tres espacios de `Placa: X   |   Color` se muestran como uno.
- **Rutas con un ID que no es número** (p. ej. `/admin/cliente/abc/editar`): dan 404 en lugar del 400 que daba Spring.
- **Sesiones independientes (F2)**: cerrar la sesión de cliente no cierra la de administrador, ni al revés. En Java era una sola sesión.
- **Estáticos (S3)**: se sirven en `/static/...` en lugar de `/css/...` y `/js/...`.
