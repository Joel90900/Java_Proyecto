# Lote A: fallas visibles y datos — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** corregir las fallas visibles del lote A (errores 500, datos importados, validaciones dispares, reportes y detalles) sin cambiar el formato JSON de la API.

**Architecture:** dos módulos nuevos que usan las tres entradas (web, panel y API):

- `core/normalizacion.py`: placa, tipo de placa y modelo.
- `core/validaciones.py`: reglas comunes que devuelven el mensaje de error.

Una migración de datos normaliza lo guardado y vuelve obligatorio `Sensor.nivel`. El resto son ajustes puntuales en vistas, plantillas y exportaciones.

**Tech Stack:** Django 6.1.2, PostgreSQL 18, Python 3.15 (el mismo proyecto).

**Spec:** `docs/superpowers/specs/2026-10-22-lote-a-fallas-visibles-design.md`. Las secciones se citan como §N.

## Global Constraints

- **Rama:** `correcciones-lote-a`. Pruebas con `.venv/Scripts/python manage.py test <módulo> -v 2`; la suite completa con `.venv/Scripts/python manage.py test`.
- **Commits:** en español y **sin** la línea `Co-Authored-By` (preferencia del usuario). Uno por tarea.
- **Formato de la API:** se mantiene (`{ok, mensaje, ...}`). Solo cambian los mensajes donde la spec lo dice.
- **Mensajes exactos:**
  - "Todos los campos son obligatorios."
  - "El correo no tiene un formato válido."
  - "La contraseña debe tener al menos 6 caracteres."
  - "El año debe ser un número válido."
  - "El año debe estar entre 1990 y 2030."
  - "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."
  - "Selecciona un tipo de placa válido."
  - "Ya existe un vehículo registrado con esa placa."
  - Correo duplicado en web y API: "El correo ya está registrado."
  - Correo duplicado en el panel: "Ya existe un cliente con ese correo." / "Ya existe un usuario con ese correo."
- **Tipos de placa canónicos:** `particular`, `publico`, `oficial`, `diplomatico`. Etiquetas en los formularios: Particular, Público, Oficial, Diplomático.
- **Modelo:** se guarda como `AAAA-01-01`, con el año entre 1990 y 2030.
- **Plantillas:** ahora se editan directamente en `templates/`, porque `referencia/` ya no existe.

## Review Focus

1. **La app envía el tipo de placa como texto libre** ("Público", " PUBLICO ", "oficial"): se acepta sin distinguir mayúsculas, tildes ni espacios, y se guarda en forma canónica. Pruebas en la Task 5: `test_tipo_placa_texto_libre_de_la_app`.
2. **Vehículos importados que no cumplen el formato** (`432fsfdf`): editarlos muestra el error de formato y no da 500. Prueba en la Task 4: `test_editar_placa_invalida_importada`.
3. **Volver a aplicar la normalización** sobre datos ya normalizados no cambia nada. Prueba en la Task 2: `test_normalizar_datos_es_idempotente`.
4. **Un nombre con comas o comillas en el CSV** se escapa y la fila conserva sus columnas. Prueba en la Task 8: `test_csv_escapa_comas_y_comillas`.
5. **Borrar un admin que es el único vinculado a clientes:** los clientes siguen existiendo y pueden iniciar sesión. Prueba en la Task 2: `test_borrar_admin_desvincula_clientes`.

---

### Task 1: Funciones de normalización

**Files:**
- Create: `core/normalizacion.py`
- Modify: `reportes/filtros.py` (importa `sin_tildes` desde `core.normalizacion`, en lugar de definirlo)
- Test: `core/tests/test_normalizacion.py`

**Interfaces:**
- Produces:
  - `TIPOS_PLACA = ("particular", "publico", "oficial", "diplomatico")`
  - `sin_tildes(texto: str | None) -> str`
  - `normalizar_placa(placa: str | None) -> str | None`
  - `normalizar_tipo_placa(tipo: str | None) -> str | None`: `None` si no es uno de los 4.
  - `normalizar_modelo(modelo: str | None) -> str | None`

- [ ] **Step 1: Escribir las pruebas**

```python
class NormalizacionTests(SimpleTestCase):
    def test_placa(self):
        self.assertEqual([normalizar_placa(p) for p in (" emt262 ", "ABC-123", None)], ["EMT262", "ABC-123", None])
    def test_tipo_placa(self):
        casos = {"Público": "publico", " PARTICULAR ": "particular", "oficial": "oficial", "Diplomático": "diplomatico",
                 "taxi": None, "": None, None: None}
        for valor, esperado in casos.items():
            self.assertEqual(normalizar_tipo_placa(valor), esperado, valor)
    def test_modelo(self):
        self.assertEqual([normalizar_modelo(m) for m in ("2020", "2018-01-01", "abc", None)],
                         ["2020-01-01", "2018-01-01", "abc", None])
    def test_sin_tildes(self):
        self.assertEqual(sin_tildes("Público"), "publico")
```

- [ ] **Step 2: Verificar que falla.** Run: `.venv/Scripts/python manage.py test core.tests.test_normalizacion -v 2`. Expected: `ImportError`.
- [ ] **Step 3: Implementar.** `normalizar_modelo`: si cumple `fullmatch(r"\d{4}")`, devuelve `f"{modelo}-01-01"`; si no, lo deja igual. Mueve `sin_tildes` desde `reportes/filtros.py` sin cambiar cómo funciona.
- [ ] **Step 4: Verificar que pasa.** Expected: 4 OK. Ejecuta además `manage.py test reportes`: todo OK.
- [ ] **Step 5: Commit** — mensaje `"Normalización de placas, tipos de placa y modelo"`.

---

### Task 2: Migración de datos, nivel obligatorio, admin desvinculable e importador

**Files:**
- Create: `core/migrations/0002_normalizar_datos.py`, con la función `normalizar_datos(apps, schema_editor)` definida a nivel de módulo
- Modify:
  - `core/models.py`: `Sensor.nivel = IntegerField(default=0)` sin `null`/`blank`; `Cliente.usuario` con `on_delete=models.SET_NULL`.
  - `core/importador.py`: en `_crear_objeto`, para `Vehiculo` aplica `normalizar_placa`, `normalizar_tipo_placa` (si da `None`, conserva el valor original) y `normalizar_modelo`; para `Sensor` convierte un nivel `None` en 0.
  - Pruebas que creaban sensores con `nivel=None`: `reportes/tests/test_filtros.py` (`s4` pasa a `nivel=0`), `panel/tests/test_clientes_usuarios.py` (`test_totales_con_nivel_nulo` usa 0) y `panel/tests/test_vehiculos_sensores.py:57` (`nivel=0`).
- Test: `core/tests/test_migracion_datos.py` y ajustes en `core/tests/test_importador.py`.

**Interfaces:**
- Consumes: todo lo de la Task 1.
- Produces: `normalizar_datos(apps, schema_editor)`, que normaliza los vehículos y además hace `Sensor.objects.filter(nivel__isnull=True).update(nivel=0)`. La migración ejecuta `RunPython(normalizar_datos, RunPython.noop)` y después los dos `AlterField`.

- [ ] **Step 1: Escribir las pruebas**

```python
class NormalizarDatosTests(TestCase):
    def test_normaliza_vehiculos_existentes(self):
        v = crear_vehiculo(crear_cliente(), placa=" emt262 ", tipo_placa="Público", modelo="2020")
        normalizar_datos(django_apps, None)
        v.refresh_from_db()
        self.assertEqual((v.placa, v.tipo_placa, v.modelo), ("EMT262", "publico", "2020-01-01"))
    def test_tipo_desconocido_se_conserva(self):  # no inventa datos
        v = crear_vehiculo(crear_cliente(), tipo_placa="Taxi")
        normalizar_datos(django_apps, None); v.refresh_from_db()
        self.assertEqual(v.tipo_placa, "Taxi")
    def test_normalizar_datos_es_idempotente(self):  # Review Focus 3
        v = crear_vehiculo(crear_cliente(), placa="ABC123", tipo_placa="particular", modelo="2020-01-01")
        normalizar_datos(django_apps, None); normalizar_datos(django_apps, None); v.refresh_from_db()
        self.assertEqual((v.placa, v.tipo_placa, v.modelo), ("ABC123", "particular", "2020-01-01"))
    def test_nivel_obligatorio_con_cero_por_defecto(self):
        self.assertFalse(Sensor._meta.get_field("nivel").null)
        self.assertEqual(Sensor.objects.create(vehiculo=crear_vehiculo(crear_cliente()), nombre_sensor="S",
                                               tipo_sensor="T").nivel, 0)
    def test_borrar_admin_desvincula_clientes(self):  # Review Focus 5
        admin = crear_usuario(); c = crear_cliente(); c.usuario = admin; c.save()
        admin.delete(); c.refresh_from_db()
        self.assertIsNone(c.usuario)
```

Cambios en `test_importador.py` (`test_importa_conservando_ids_y_valores`): el vehículo 4 queda `("Onix, el rojo", "EMT262", "publico", None)` y `Sensor.objects.get(pk=22).nivel == 0`.

- [ ] **Step 2: Verificar que fallan.** Run: `.venv/Scripts/python manage.py test core -v 2`. Expected: `ImportError` (la migración no existe) y fallos del importador.
- [ ] **Step 3: Implementar.** La migración se escribe a mano y `normalizar_datos` usa `apps.get_model("core", "Vehiculo")`. Después ejecuta `makemigrations --check`: no debe quedar nada pendiente.
- [ ] **Step 4: Verificar que pasa.** `manage.py test` (suite completa): OK. Luego `manage.py migrate` en la base de desarrollo y comprueba con `psql` que las placas quedan en mayúsculas y los tipos en `particular`/`publico`.
- [ ] **Step 5: Commit** — mensaje `"Migración: datos normalizados, nivel obligatorio y admin desvinculable"`.

---

### Task 3: Validaciones comunes

**Files:**
- Create: `core/validaciones.py`
- Test: `core/tests/test_validaciones.py`

**Interfaces:**
- Consumes: `normalizar_tipo_placa` (Task 1) y `entero_java`.
- Produces:
  - `validar_persona(obligatorios: list[str], correo: str, contrasena: str | None, contrasena_obligatoria: bool = True) -> str | None`
  - `validar_vehiculo(nombre: str, marca: str, modelo: str | None, color: str, placa: str, tipo_placa: str, modelo_obligatorio: bool = True) -> str | None`
  - Las dos reciben los textos ya recortados (y la placa ya normalizada) y comprueban en el orden de §4.

- [ ] **Step 1: Escribir las pruebas**

```python
class ValidarPersonaTests(SimpleTestCase):
    def test_orden_y_mensajes(self):
        self.assertEqual(validar_persona(["Ana", ""], "a@b.co", "secreto"), "Todos los campos son obligatorios.")
        self.assertEqual(validar_persona(["Ana"], "", "secreto"), "Todos los campos son obligatorios.")
        self.assertEqual(validar_persona(["Ana"], "a@b.co", ""), "Todos los campos son obligatorios.")
        for malo in ("abc", "a@b", "a b@c.co", "@b.co"):
            self.assertEqual(validar_persona(["Ana"], malo, "secreto"), "El correo no tiene un formato válido.", malo)
        self.assertEqual(validar_persona(["Ana"], "a@b.co", "12345"), "La contraseña debe tener al menos 6 caracteres.")
        self.assertIsNone(validar_persona(["Ana", "Paz"], "ana@test.com", "secreto"))
    def test_contrasena_opcional(self):
        self.assertIsNone(validar_persona(["Ana"], "a@b.co", "", contrasena_obligatoria=False))
        self.assertIsNone(validar_persona(["Ana"], "a@b.co", None, contrasena_obligatoria=False))
        self.assertEqual(validar_persona(["Ana"], "a@b.co", "123", contrasena_obligatoria=False),
                         "La contraseña debe tener al menos 6 caracteres.")

class ValidarVehiculoTests(SimpleTestCase):
    BASE = dict(nombre="Onix", marca="Chevrolet", modelo="2020", color="Negro", placa="ABC123", tipo_placa="particular")
    def test_orden_y_mensajes(self):
        casos = [({"marca": ""}, "Todos los campos son obligatorios."), ({"modelo": ""}, "Todos los campos son obligatorios."),
                 ({"modelo": "20x0"}, "El año debe ser un número válido."), ({"modelo": "1989"}, "El año debe estar entre 1990 y 2030."),
                 ({"placa": "AB1234"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."),
                 ({"tipo_placa": "taxi"}, "Selecciona un tipo de placa válido.")]
        for cambio, mensaje in casos:
            self.assertEqual(validar_vehiculo(**{**self.BASE, **cambio}), mensaje, cambio)
        self.assertIsNone(validar_vehiculo(**{**self.BASE, "tipo_placa": "Público", "placa": "ABC-123"}))
    def test_modelo_opcional(self):
        self.assertIsNone(validar_vehiculo(**{**self.BASE, "modelo": None}, modelo_obligatorio=False))
        self.assertEqual(validar_vehiculo(**{**self.BASE, "modelo": "1800"}, modelo_obligatorio=False),
                         "El año debe estar entre 1990 y 2030.")
```

- [ ] **Step 2: Verificar que falla.** Expected: `ImportError`.
- [ ] **Step 3: Implementar.** Para el correo usa `re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo)`; para la placa, `re.fullmatch(r"[A-Z]{3}-?[0-9]{3}", placa)`.
- [ ] **Step 4: Verificar que pasa.** Expected: 4 OK.
- [ ] **Step 5: Commit** — mensaje `"Validaciones comunes de personas y vehículos"`.

---

### Task 4: Web del cliente: registro, login, vehículos y botón eliminar

**Files:**
- Modify:
  - `web/views.py`: `login`, `register`, `vehiculo_crear`, `vehiculo_editar`.
  - `templates/paginas/mis-vehiculos.html`: añade el formulario de eliminar en `.vehicle-actions`, después de "Ver sensores".
- Test: `web/tests/test_validaciones_web.py` (nuevo), más ajustes en `web/tests/test_autenticacion.py` y `web/tests/test_vehiculos.py`.

**Interfaces:**
- Consumes: `validar_persona`, `validar_vehiculo` y las funciones de normalización.

**Comportamiento:**
- **`login`:** `correo = request.POST.get("correo", "").strip()`.
- **`register`:**
  1. Recorta los 4 campos.
  2. `validar_persona([nombre, apellido], correo, contrasena)`.
  3. Duplicado con `igual_mysql`: "El correo ya está registrado.".
  4. Crea el cliente con los valores recortados.
- **`vehiculo_crear`:**
  1. Recorta nombre, marca, modelo y color.
  2. `placa = normalizar_placa(placa)`.
  3. `validar_vehiculo(...)`.
  4. Duplicado con `igual_mysql`.
  5. Guarda `tipo_placa=normalizar_tipo_placa(tipo)` y `modelo=normalizar_modelo(modelo)`.
- **`vehiculo_editar`:** igual que crear, pero con `modelo=None, modelo_obligatorio=False` y el duplicado sobre `Vehiculo.objects.exclude(pk=vehiculo.pk)`.
- **Botón eliminar:**
  ```html
  <form method="post" action="{% url 'vehiculo_eliminar' v.id_vehiculo %}" onsubmit="return confirm('¿Eliminar este vehículo y sus sensores?')">{% csrf_token %}<button type="submit" class="btn-mini btn-mini-edit">Eliminar</button></form>
  ```

- [ ] **Step 1: Escribir las pruebas**

```python
class RegistroValidadoTests(TestCase):
    def test_recorta_y_valida(self):
        r = self.client.post("/register", {"nombre": " Ana ", "apellido": " Paz ", "correo": " ana@test.com ", "contrasena": "secreto"})
        self.assertRedirects(r, "/login", fetch_redirect_response=False)
        self.assertEqual(Cliente.objects.get(correo="ana@test.com").nombre_cliente, "Ana")
    def test_mensajes(self):
        base = {"nombre": "A", "apellido": "B", "correo": "a@b.co", "contrasena": "secreto"}
        for cambio, mensaje in (({"correo": "abc"}, "El correo no tiene un formato válido."),
                                ({"contrasena": "123"}, "La contraseña debe tener al menos 6 caracteres.")):
            self.assertContains(self.client.post("/register", {**base, **cambio}), mensaje)

class VehiculosValidadosTests(Base):  # Base de test_vehiculos (sesión de cliente)
    def test_editar_vehiculo_importado_con_placa_minuscula(self):
        v = crear_vehiculo(self.cliente, placa="emt262", tipo_placa="publico")
        r = self.client.post(f"/vehiculos/{v.pk}/editar", {"nombreVehiculo": "Onix", "marca": "Chevrolet", "color": "Negro",
                                                           "placa": "emt262", "tipoPlaca": "publico"})
        self.assertRedirects(r, "/vehiculos", fetch_redirect_response=False)
        v.refresh_from_db(); self.assertEqual(v.placa, "EMT262")
    def test_editar_placa_invalida_importada(self):  # Review Focus 2
        v = crear_vehiculo(self.cliente, placa="432fsfdf")
        r = self.client.post(f"/vehiculos/{v.pk}/editar", {"nombreVehiculo": "Onix", "marca": "Chevrolet", "color": "Negro",
                                                           "placa": "432fsfdf", "tipoPlaca": "particular"})
        self.assertContains(r, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")
    def test_tipo_placa_invalido(self):
        self.assertContains(self.client.post("/vehiculos/crear", {**DATOS, "tipoPlaca": "taxi"}), "Selecciona un tipo de placa válido.")
    def test_boton_eliminar(self):
        v = crear_vehiculo(self.cliente)
        r = self.client.get("/vehiculos")
        self.assertContains(r, f'action="/vehiculos/{v.pk}/eliminar"')
        self.assertContains(r, "¿Eliminar este vehículo y sus sensores?")
```

Ajustes en pruebas existentes:
- `test_registro_sin_recortar_espacios` pasa a esperar `"Ana"`; renómbrala `test_registro_recorta_espacios`.
- En `test_validaciones_en_el_orden_de_java`, el caso de placa `"XYZ"` ahora espera el mensaje de formato; renómbrala `test_validaciones_en_orden`.
- En `test_editar_errores`, el duplicado espera "Ya existe un vehículo registrado con esa placa." y la placa vacía "Todos los campos son obligatorios.".
- Añade `test_login_web_con_espacio_inicial` (`" joel@test.com"` lleva a `/dashboard`).

- [ ] **Step 2: Verificar que fallan.** Run: `.venv/Scripts/python manage.py test web -v 2`.
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Verificar que pasan.** Run: `manage.py test web`: OK.
- [ ] **Step 5: Commit** — mensaje `"Web del cliente: validaciones comunes, edición de importados y botón eliminar"`.

---

### Task 5: API de la app: registro y crear vehículo

**Files:**
- Modify: `api/views.py` (`registrar`, `crear_vehiculo`)
- Test: `api/tests/test_api_cliente.py`

**Comportamiento:**
- **`registrar`:** los mismos pasos que el registro web. Responde `{"ok": False, "mensaje": <mensaje>}` en cada error.
- **`crear_vehiculo`:**
  1. Cliente inexistente: "Cliente no encontrado." (primero, como hoy).
  2. Luego `validar_vehiculo`.
  3. Luego el duplicado.
  4. Guarda el tipo y el modelo normalizados.

- [ ] **Step 1: Escribir las pruebas**

```python
class ApiValidacionesTests(TestCase):
    def test_registro_valida_correo_y_contrasena(self):
        for datos, mensaje in (({"correo": "abc", "contrasena": "secreto"}, "El correo no tiene un formato válido."),
                               ({"correo": "a@b.co", "contrasena": "12"}, "La contraseña debe tener al menos 6 caracteres.")):
            r = self.client.post("/api/auth/register", {"nombre": "A", "apellido": "B", **datos})
            self.assertEqual(r.json(), {"ok": False, "mensaje": mensaje})
    def test_tipo_placa_texto_libre_de_la_app(self):  # Review Focus 1
        crear_cliente()
        base = {"correo": "joel@test.com", "nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": "2020", "color": "Negro"}
        for i, tipo in enumerate(("Público", " PARTICULAR ", "oficial")):
            r = self.client.post("/api/vehiculos/crear", {**base, "placa": f"ABC12{i}", "tipoPlaca": tipo})
            self.assertTrue(r.json()["ok"], tipo)
        self.assertEqual(sorted(Vehiculo.objects.values_list("tipo_placa", flat=True)), ["oficial", "particular", "publico"])
        r = self.client.post("/api/vehiculos/crear", {**base, "placa": "ABC999", "tipoPlaca": "taxi"})
        self.assertEqual(r.json(), {"ok": False, "mensaje": "Selecciona un tipo de placa válido."})
```

El registro existente (`test_registro`) usa la contraseña `"x1"`: cámbiala a `"secreto1"`. En `test_mensajes_en_orden`, el orden pasa a cliente, vacíos, año, formato, tipo y duplicado; las listas de casos actuales siguen valiendo.

- [ ] **Step 2: Verificar que falla.** Run: `manage.py test api -v 2`.
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Verificar que pasa.** Run: `manage.py test api`: OK.
- [ ] **Step 5: Commit** — mensaje `"API: mismas validaciones de registro y vehículos"`.

---

### Task 6: Panel admin: clientes, usuarios, vehículos y tipos de placa

**Files:**
- Modify:
  - `panel/views.py` (login, cliente_crear/editar, usuario_crear/editar, vehiculo_crear/editar)
  - `templates/admin/crear-vehiculo.html`: el campo modelo pasa a `type="number" min="1990" max="2030" required`; el select ofrece los 4 tipos.
  - `templates/admin/editar-vehiculo.html`: el select ofrece los 4 tipos, con su `selected`.
- Test: `panel/tests/test_clientes_usuarios.py`, `panel/tests/test_vehiculos_sensores.py`

**Comportamiento:**
- **Login:** recorta el correo.
- **Clientes:** `validar_persona([nombre, apellido], correo, contrasena)`; al editar, `contrasena_obligatoria=False`.
- **Usuarios:** `validar_persona([nombre], correo, contrasena)`; al editar, `contrasena_obligatoria=False`.
- **Vehículos:**
  - Crear: `validar_vehiculo` con modelo obligatorio.
  - Editar: `modelo_obligatorio=False`; si el modelo llega vacío, se conserva el actual.
  - Duplicado excluyendo el propio vehículo.
  - "Selecciona un cliente válido." va después del duplicado, como hoy.
  - Guarda el tipo y el modelo normalizados.

- [ ] **Step 1: Ajustar y escribir las pruebas**

Cambios en `panel/tests/test_vehiculos_sensores.py`:
- `datos()` usa `"modelo": "2020"`.
- `test_crear_sin_sensores_por_defecto` espera `modelo == "2020-01-01"`.
- `test_validaciones_en_orden`:
  - El caso `{"marca": " "}` espera "Todos los campos son obligatorios.".
  - El duplicado espera "Ya existe un vehículo registrado con esa placa.".
  - Añade `({"modelo": ""}, "Todos los campos son obligatorios.")` y `({"tipoPlaca": "taxi"}, "Selecciona un tipo de placa válido.")`.

Pruebas nuevas:

```python
    def test_editar_tipo_importado_se_preselecciona(self):
        v = crear_vehiculo(self.cliente, tipo_placa="oficial")
        self.assertContains(self.client.get(f"/admin/vehiculo/{v.pk}/editar"), '<option value="oficial" selected')
    def test_crear_cliente_y_usuario_validan_formato(self):
        self.assertContains(self.client.post("/admin/cliente/crear", {"nombre": "A", "apellido": "B", "correo": "a@b",
                            "contrasena": "secreto"}), "El correo no tiene un formato válido.")
        self.assertContains(self.client.post("/admin/usuario/crear", {"nombre": "A", "correo": "a b@c.co",
                            "contrasena": "secreto", "rol": "ADMIN"}), "El correo no tiene un formato válido.")
```

En `test_validaciones_crear` de clientes, el correo `"abco"` sigue esperando el mensaje de formato.

- [ ] **Step 2: Verificar que fallan.** Run: `manage.py test panel -v 2`.
- [ ] **Step 3: Implementar.** Para el `selected` del tipo de placa usa `{% if vehiculo.tipo_placa == 'oficial' %}selected{% endif %}`, igual que las dos opciones que ya existen.
- [ ] **Step 4: Verificar que pasa.** Run: `manage.py test panel`: OK.
- [ ] **Step 5: Commit** — mensaje `"Panel: validaciones comunes y los cuatro tipos de placa"`.

---

### Task 7: 404 por ID inexistente, CSRF en español y aviso de WhiteNoise

**Files:**
- Modify:
  - `web/views.py:163,191`, `panel/views.py` (las 10 llamadas a `.objects.get(pk=...)`), `reportes/views.py:125,173`: pasan a `get_object_or_404`.
  - `core/errores.py`: `error_csrf(request, reason="")` devuelve `render_error(request, 403)`.
  - `autosen/settings.py`: `CSRF_FAILURE_VIEW = "core.errores.error_csrf"` y `warnings.filterwarnings("ignore", message="No directory at", module="whitenoise.base")`.
- Test: actualiza `panel/tests/test_clientes_usuarios.py: test_id_inexistente_da_500` → `test_id_inexistente_da_404` (status 404) y en `reportes/tests/test_vistas.py` el 9999 espera 404; nuevo `core/tests/test_errores.py: test_csrf_fallido_muestra_error_html`.

- [ ] **Step 1: Escribir las pruebas**

```python
    def test_csrf_fallido_muestra_error_html(self):
        r = Client(enforce_csrf_checks=True).post("/login", {"correo": "x@y.co", "contrasena": "z"})
        self.assertContains(r, "ACCESO", status_code=403)
        self.assertContains(r, "Código: 403", status_code=403)
    def test_id_inexistente_web_da_404(self):  # en web/tests/test_vehiculos.py, clase Base
        self.assertEqual(self.client.get("/vehiculos/9999/editar").status_code, 404)
```

- [ ] **Step 2: Verificar que fallan.**
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Verificar que pasan.** Suite completa: OK. Además, al arrancar `manage.py check`, el aviso de WhiteNoise ya no aparece.
- [ ] **Step 5: Commit** — mensaje `"404 por ID inexistente, página CSRF propia y sin aviso de WhiteNoise"`.

---

### Task 8: Reportes: CSV, totales filtrados, enlaces imprimibles y textos vacíos

**Files:**
- Modify:
  - `reportes/exportar.py: csv_reporte`: usa `csv.writer(salida, lineterminator="\r\n")`, `None` se escribe vacío y el texto empieza con `"﻿"`.
  - `reportes/views.py: reportes_filtrado` (§5 #19).
  - `reportes/views.py` y `reportes/filtros.py`: `TIPOS_PLACA` se importa de `core.normalizacion`.
  - `templates/admin/reportes.html`: botón "Vista imprimible" y enlace "Ficha".
  - `templates/admin/reportes.html`, `reportes-pdf.html`: las placas usan `|default_if_none:""` en lugar de `|java`.
  - `templates/admin/reporte-cliente-pdf.html`: el estado usa `|default_if_none:""|upper`.
- Test: `reportes/tests/test_exportar.py`, `reportes/tests/test_vistas.py`

- [ ] **Step 1: Ajustar y escribir las pruebas**

Las pruebas de CSV existentes esperan ahora `"﻿"` al inicio del contenido. `test_csv_estado_null` espera `",ana@test.com,,1\r\n"`. Como el nivel ya no puede ser NULL, se quitan los `self.s4.delete()`, y la fila de `Prueba` aparece en el CSV de sensores con nivel 0 y estado OK.

```python
    def test_csv_escapa_comas_y_comillas(self):  # Review Focus 4
        Cliente.objects.filter(pk=self.ana.pk).update(apellido_cliente='Paz, "Jr"')
        filas = list(csv.reader(io.StringIO(self.client.get("/admin/reportes/csv/clientes").content.decode("utf-8-sig"))))
        self.assertEqual(filas[2], [str(self.ana.pk), 'Ana Paz, "Jr"', "ana@test.com", "bloqueado", "1"])
    def test_totales_respetan_filtros(self):  # test_vistas
        r = self.client.get("/admin/reportes-filtrado?tipoPlaca=publico")
        self.assertEqual((r.context["totalVehiculos"], r.context["vehiculosConFallas"], r.context["clientesBloqueados"]), (1, [], []))
        r = self.client.get("/admin/reportes-filtrado?estadoSensor=optimo")
        self.assertEqual(r.context["vehiculosConFallas"], [])
        r = self.client.get("/admin/reportes-filtrado")
        self.assertEqual([v.placa for v in r.context["vehiculosConFallas"]], ["KIA111"])
    def test_enlaces_a_vistas_imprimibles(self):
        r = self.client.get("/admin/reportes")
        self.assertContains(r, 'href="/admin/reportes-pdf"')
        self.assertContains(r, f'href="/admin/reporte-cliente-pdf/{self.joel.pk}"')
    def test_reporte_cliente_estado_vacio(self):
        Cliente.objects.filter(pk=self.joel.pk).update(estado=None)
        self.assertNotContains(self.client.get(f"/admin/reporte-cliente-pdf/{self.joel.pk}"), "NONE")
```

`test_reportes` ahora espera `tiposPlaca == ["particular", "publico", "oficial", "diplomatico"]`.

- [ ] **Step 2: Verificar que fallan.** Run: `manage.py test reportes -v 2`.
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Verificar que pasa.** Suite completa: OK.
- [ ] **Step 5: Commit** — mensaje `"Reportes: CSV escapado con BOM, totales filtrados y enlaces imprimibles"`.

---

### Task 9: Pendientes, revisión con Codex y cierre

**Files:**
- Modify: `docs/PENDIENTES.md`, que se reescribe dejando solo lo de los lotes B (nivel, sincronización, telemetría, alertas, ELM, umbrales), C (API sin token, tiempos del login), D (consultas N+1) y la sección "Diferencias conocidas", que se conserva tal cual.

- [ ] **Step 1:** Reescribir `docs/PENDIENTES.md`.
- [ ] **Step 2:** Revisión con Codex (`codex:rescue`) de la rama `correcciones-lote-a` contra la spec, en modo solo lectura. Se corrigen los hallazgos importantes, con prueba RED→GREEN.
- [ ] **Step 3:** Ejecutar la suite completa y `makemigrations --check`. Expected: OK y "No changes detected".
- [ ] **Step 4: Commit** — mensaje `"Pendientes actualizados tras el lote A"`.
