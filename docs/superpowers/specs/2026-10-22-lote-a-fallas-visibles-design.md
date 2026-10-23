# Lote A: fallas visibles y datos — Diseño

Fecha: 2026-10-22
Estado: aprobado en conversación, pendiente de revisión escrita
Rama: `correcciones-lote-a` (sale de `migracion-django`)

## 1. Contexto

La migración a Django (spec `2026-10-21-migracion-django-design.md`) conservó a propósito los defectos del proyecto Java. Ahora se corrigen en cuatro lotes: A (fallas visibles y datos), B (lógica de sensores), C (seguridad de la API) y D (rendimiento).

Este documento cubre **solo el lote A**. Ya no se busca fidelidad con Java: cada punto de este lote cambia el comportamiento a propósito.

**Criterio de éxito:** desaparecen los errores 500, los textos raros ("NONE"/"null") y las inconsistencias de validación y de datos de la lista. Las respuestas de la API conservan su formato JSON (`{ok, mensaje, ...}`), así que la app Android sigue funcionando sin cambios. Las 144 pruebas actuales se ajustan donde el comportamiento cambió a propósito y se añaden pruebas nuevas.

## 2. Decisiones tomadas con el usuario

| Tema | Decisión |
|---|---|
| Validaciones | Las mismas reglas en la web del cliente, el panel y la API |
| Datos guardados | Normalizar con una migración: placas y tipos de placa; el importador hace lo mismo |
| Tipos de placa | Los 4 (particular, público, oficial, diplomático) en todos lados |
| Nivel vacío | Columna obligatoria con 0 por defecto; los vacíos pasan a 0 |
| Borrar un admin con clientes | Se desvinculan los clientes (`Id_usuario` a NULL) y se borra el admin |

## 3. Datos y migraciones

**Funciones de normalización (`core/normalizacion.py`)**, compartidas por la migración de datos, el importador y las validaciones:

- `normalizar_placa(placa: str | None) -> str | None`: `strip()` y luego `upper()`; `None` se queda en `None`.
- `TIPOS_PLACA = ("particular", "publico", "oficial", "diplomatico")`.
- `normalizar_tipo_placa(tipo: str | None) -> str | None`:
  - Compara con `sin_tildes(tipo.strip())`. Si es uno de los 4, devuelve el valor canónico; si no, devuelve `None`.
  - `sin_tildes` pasa de `reportes/filtros.py` a `core/normalizacion.py`, y `reportes/filtros.py` lo importa desde allí.
- `normalizar_modelo(modelo: str | None) -> str | None`: `"2020"` pasa a `"2020-01-01"`. Lo que ya tiene la forma `AAAA-01-01` o no es un año se deja igual.

**Migración `core/0002_normalizar_datos.py`.** Primero un `RunPython` que:

- Aplica `normalizar_placa` a todos los vehículos.
- Aplica `normalizar_tipo_placa` a todos los vehículos (si devuelve `None`, deja el valor original).
- Aplica `normalizar_modelo` a todos los vehículos.
- Pone `nivel = 0` en los sensores con `nivel` NULL.

Después:

- `AlterField` de `Sensor.nivel` a `IntegerField(default=0)`, sin `null`.
- `AlterField` de `Cliente.usuario` con `on_delete=models.SET_NULL`.

**Importador:** al crear cada objeto aplica las mismas normalizaciones (placa, tipo de placa, modelo, y nivel `None` a 0).

## 4. Validaciones unificadas (`core/validaciones.py`)

Cada función devuelve `None` si todo está bien, o el **mensaje de error** que se mostraba hasta ahora. Las comprobaciones van en este orden:

**`validar_persona(obligatorios: list[str], correo: str, contrasena: str | None, contrasena_obligatoria: bool = True) -> str | None`** (los valores ya llegan recortados). `obligatorios` es `[nombre, apellido]` para clientes y `[nombre]` para administradores:

1. Si falta un campo obligatorio (en `obligatorios`, o el correo vacío): "Todos los campos son obligatorios.". La contraseña solo es obligatoria si `contrasena_obligatoria`.
2. Si el correo no cumple `fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+")`: "El correo no tiene un formato válido.".
3. Si hay contraseña y tiene menos de 6 caracteres: "La contraseña debe tener al menos 6 caracteres.".

**`validar_vehiculo(nombre, marca, modelo, color, placa, tipo_placa, modelo_obligatorio=True) -> str | None`** (`placa` ya normalizada):

1. Si falta un campo obligatorio: "Todos los campos son obligatorios.". El modelo solo es obligatorio si `modelo_obligatorio`.
2. Año, si hay modelo:
   - `entero_java(modelo)` es `None`: "El año debe ser un número válido.".
   - Fuera de 1990–2030: "El año debe estar entre 1990 y 2030.".
3. Si la placa no cumple `fullmatch(r"[A-Z]{3}-?[0-9]{3}")`: "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.".
4. Si `normalizar_tipo_placa(tipo_placa)` es `None`: "Selecciona un tipo de placa válido.".

**El duplicado lo comprueba quien llama, después de validar:**

- Placa: `igual_mysql(Vehiculo.objects.exclude(pk=<propio>), "placa", placa)`, con el mensaje único "Ya existe un vehículo registrado con esa placa.".
- Correo: se conservan los mensajes de cada entrada:
  - web y API: "El correo ya está registrado.";
  - panel: "Ya existe un cliente con ese correo." / "Ya existe un usuario con ese correo.".

**Dónde se aplica cada validación:**

| Entrada | Cliente | Vehículo |
|---|---|---|
| Web: `/register` | `validar_persona` (recorta antes; antes no recortaba) | — |
| Web: `/vehiculos/crear` | — | `validar_vehiculo` (modelo obligatorio) |
| Web: `/vehiculos/{id}/editar` | — | `validar_vehiculo` con `modelo_obligatorio=False` (el formulario no tiene año; se conserva el guardado) |
| API: `/api/auth/register` | `validar_persona` | — |
| API: `/api/vehiculos/crear` | — | `validar_vehiculo` (modelo obligatorio) |
| Panel: crear/editar cliente | `validar_persona`; al editar, contraseña opcional | — |
| Panel: crear vehículo | — | `validar_vehiculo` (modelo obligatorio; el campo del formulario pasa a numérico, 1990–2030, requerido) |
| Panel: editar vehículo | — | `validar_vehiculo` con `modelo_obligatorio=False` (vacío conserva el actual) |
| Panel: crear/editar usuario | `validar_persona([nombre], …)` (sin apellido) | — |

**Al guardar:**

- Placa con `normalizar_placa`.
- Tipo de placa con `normalizar_tipo_placa`.
- Modelo como `AAAA-01-01`.
- Login (web y panel): se recorta el correo antes de buscar.

**Formularios:** los `<select>` de tipo de placa del panel (crear y editar) y de la web (crear y editar) muestran los 4 tipos, con estas etiquetas: Particular, Público, Oficial, Diplomático. El filtro de reportes (`tiposPlaca`) también lista los 4.

## 5. Pantallas, reportes y detalles

| # | Cambio | Dónde |
|---|---|---|
| 10 | Un ID inexistente da 404: `get_object_or_404` en lugar de `Modelo.objects.get` | `web/views.py`, `panel/views.py`, `reportes/views.py` |
| 13 | Al borrar un admin con clientes, los clientes quedan con `Id_usuario` NULL (`SET_NULL`) | migración §3 |
| 14 | Botón "Eliminar" con `confirm('¿Eliminar este vehículo y sus sensores?')` en cada tarjeta de "Mis vehículos": un formulario POST a `vehiculo_eliminar` con `{% csrf_token %}`, al estilo del botón "Editar" | `templates/paginas/mis-vehiculos.html` |
| 18 | CSV con el módulo `csv` (comillas cuando hacen falta) y BOM UTF-8 al inicio (`﻿`); separador de línea `\r\n` | `reportes/exportar.py` |
| 19 | En `/admin/reportes-filtrado`: `totalVehiculos` = vehículos de los clientes filtrados; `vehiculosConFallas` = vehículos de los clientes filtrados con algún sensor **filtrado** en falla; `clientesBloqueados` = clientes filtrados en estado bloqueado | `reportes/views.py: reportes_filtrado` |
| 20 | Botón "Vista imprimible" (a `admin_reportes_pdf_vista`) junto a "Descargar PDF completo", y enlace "Ficha" (a `admin_reporte_cliente_vista`) junto al PDF de cada cliente | `templates/admin/reportes.html` |
| 21 | "NONE": `{{ cliente.estado\|default_if_none:""\|upper }}`. Placas vacías: `default_if_none:""` donde Thymeleaf mostraba vacío | `templates/admin/reporte-cliente-pdf.html`, `reportes.html`, `reportes-pdf.html` |
| 23 | `CSRF_FAILURE_VIEW = "core.errores.error_csrf"`, que llama a `render_error(request, 403)` | `autosen/settings.py`, `core/errores.py` |
| 24 | Silenciar el aviso de WhiteNoise sobre `staticfiles/` con `warnings.filterwarnings("ignore", message="No directory at", module="whitenoise.base")` | `autosen/settings.py` |

## 6. Pruebas

- **Se mantienen** las pruebas de espacios finales de la revisión anterior: recortar antes de buscar da el mismo resultado.
- **Validaciones:** pruebas unitarias de `core/validaciones.py` y `core/normalizacion.py`. En cada entrada (web, API y panel), una prueba de los mensajes nuevos: correo inválido, contraseña corta, tipo de placa inválido y año en el panel.
- **Edición:** un vehículo con placa `emt262` se edita sin error de duplicado y queda `EMT262`.
- **Migración de datos:** se prueba la función del `RunPython` contra datos creados en la prueba, más el importador con valores en minúsculas, `Público` y nivel NULL.
- **Pruebas que esperaban el comportamiento Java y se actualizan:**
  - 500 por ID inexistente, que ahora da 404.
  - Orden duplicado/formato y mensajes de editar.
  - CSV exacto, que ahora lleva BOM y comillas.
  - Registro sin recortar.
  - Panel de vehículo con modelo opcional.
- **Nuevas para:** botón eliminar, totales filtrados, enlaces a las vistas imprimibles, CSRF en español y borrar un admin con clientes.
- **Al cerrar el lote:** se pide a Codex una segunda revisión de la rama; luego se actualiza `docs/PENDIENTES.md`, dejando solo lo de los lotes B, C y D.

## 7. Fuera de alcance

Los lotes B, C y D, y cambios en la app Android.
