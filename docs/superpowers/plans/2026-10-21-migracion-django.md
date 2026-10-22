# Migración de AutoSen a Django — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** reproducir en Django 6.1 + PostgreSQL 18 el backend Spring Boot de AutoSen (web de cliente, panel admin, reportes y API de la app Android) con la misma lógica, aplicando solo las desviaciones F1–F6 y S1–S3 de la especificación.

**Architecture:** un proyecto Django (`autosen/`) con cinco apps:

- `core`: modelos, autenticación, utilidades, patrones e importador.
- `web`, `panel`, `reportes` y `api`: una vista por método de controlador Java, con las mismas rutas.

No usa `django.contrib.auth`. Hay dos sesiones independientes (`cliente_id` y `admin_id`), y la API responde con `JsonResponse`, con el mismo orden de claves que Java.

**Tech Stack:** Python 3.15, Django 6.1.2, psycopg 3.3.6, bcrypt 5.0.0, reportlab 5.0.1, openpyxl 3.1.5, python-dotenv 1.2.4, whitenoise 6.12.0, PostgreSQL 18.6.

**Spec:** `docs/superpowers/specs/2026-10-21-migracion-django-design.md`. Léela antes de empezar; las secciones se citan como §N. El código Java de referencia está en `referencia/proyecto-java/src/main/` (abreviado `J/`).

## Global Constraints

- **Regla de fidelidad:** cada vista reproduce el método Java citado en su tarea: mismas validaciones, en el mismo orden, con los mismos mensajes (copiados literalmente de `J/`), las mismas redirecciones y los mismos datos de contexto. Solo se permiten las desviaciones F1–F6 y S1–S3 de §3.
- **Equivalencias Java → Python obligatorias:**
  - `Math.round(x)` → `redondear_java(x)` (`math.floor(x + 0.5)`). Nunca `round()`.
  - `String.matches(re)` → `re.fullmatch(re, s)`.
  - `Integer.parseInt(s)` → `entero_java(s)`.
  - Valor `null` dentro de una concatenación o un `printf` → `texto_java(v)` (devuelve `"null"`).
  - `String.valueOf(Double)` → `double_java(v)`.
  - `String.valueOf(LocalDateTime)` → `fecha_java(dt)`.
  - `isBlank()` → `s.strip() == ""`; `trim()` → `s.strip()`.
- **Búsquedas por texto en la base de datos:** `findByCorreo` y `findByPlaca` → `__iexact` (§5).
- **Orden:** cada modelo lleva `Meta.ordering = [<pk>]`, y las consultas `…OrderBy…Desc` usan `order_by("-<pk>")`.
- **Fechas nuevas:** `ahora()`, que devuelve la hora local sin microsegundos. `USE_TZ = False`.
- **URLs:** sin barra final y con `APPEND_SLASH = False`. Rutas exactamente como en §7.
- **Formularios web:** todo `<form method="post">` lleva `{% csrf_token %}`. Toda vista de `api/` lleva `@csrf_exempt`.
- **Parámetros de petición:** siempre con `core.http.parametro(...)`. Un parámetro obligatorio ausente, o un número inválido, da 400.
- **Errores 500 en pruebas:** las pruebas que esperan 500 usan `Client(raise_request_exception=False)`.
- **JSON:** `JsonResponse(datos, json_dumps_params={"ensure_ascii": False})`, con diccionarios en el orden de claves de Java.
- **Plantillas:** las claves de contexto conservan los nombres Java (`totalSensores`, `sensoresOk`, `vehiculosConFallas`…). Los atributos de modelo dentro de las plantillas usan los nombres Python (`c.nombre_cliente`, `v.sensores.all`).
- **Idioma:** identificadores, comentarios, docstrings y documentación en español. El docstring de cada vista nombra el método Java (`"""Equivale a VehiculoController.crear."""`).
- **Pruebas:** `TestCase`/`SimpleTestCase` de Django, en `<app>/tests/`. Se ejecutan con `.venv/Scripts/python manage.py test <módulo> -v 2`.
- **Commits:** uno por tarea, mensaje en español, terminado en la línea `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Se trabaja en la rama `migracion-django`. No se hace `push`.

## Review Focus

1. **Datos importados que no cumplen las validaciones actuales** (placa `emt262`, tipo de placa `Público`, estado NULL): deben mostrarse en todas las pantallas, reportes y exportaciones sin romper nada. Pruebas: Task 8 `test_paginas_con_datos_importados`, Task 14 `test_tipo_placa_sin_tildes`, Task 15 `test_csv_estado_null`.
2. **Sensor con `Nivel` NULL** (posible en datos importados): el panel admin y los reportes lo tratan como 0/óptimo, como en Java. Pruebas: Task 12 `test_totales_con_nivel_nulo`, Task 14 (sensor `s4` en todos los filtros).
3. **Texto no ASCII** (tildes, ñ, °C, guion largo): debe salir legible en el JSON (sin `ó`), el CSV, el Excel y el PDF. Pruebas: Task 10 `test_json_utf8_sin_escapar`, Task 15 `test_pdf_con_texto_unicode`.
4. **Campos numéricos vacíos en los filtros de reportes** (`nivelMin=`): se tratan como "sin filtro", no como error 400. Prueba: Task 14 `test_numeros_vacios_son_sin_filtro`.
5. **La app Android manda `unidad` vacía o no la manda** en `/api/obd2/lecturas`: hay que guardarla y armar el mensaje de alerta como en Java. Pruebas: Task 11 `test_sin_unidad` y `test_unidad_vacia`.

---

### Task 1: Esqueleto del proyecto, configuración y base de datos

**Files:**
- Create: `requirements.txt`, `.env.example`, `manage.py`, `autosen/__init__.py`, `autosen/settings.py`, `autosen/urls.py`, `autosen/wsgi.py`, `autosen/asgi.py`
- Create: `core/`, `web/`, `panel/`, `reportes/`, `api/`, cada una con `__init__.py`, `apps.py`, `urls.py` (`urlpatterns = []`) y `tests/__init__.py`
- Create: `static/images/.gitkeep`
- Test: `core/tests/test_configuracion.py`

**Interfaces:**
- Produces: proyecto que arranca. `autosen/urls.py` incluye `web.urls`, `panel.urls`, `reportes.urls` y `api.urls` en la raíz (cada app escribe sus rutas completas, p. ej. `"admin/cliente/nuevo"`). Base `vehiculos` creada.

- [ ] **Step 1: Crear la rama y el entorno**

```bash
git switch -c migracion-django
python -m venv .venv
```

Crear `requirements.txt`:

```
Django==6.1.2
psycopg[binary]==3.3.6
bcrypt==5.0.0
reportlab==5.0.1
openpyxl==3.1.5
python-dotenv==1.2.4
whitenoise==6.12.0
```

Run: `.venv/Scripts/pip install -r requirements.txt`, y después `.venv/Scripts/python -m django --version`.
Expected: `6.1.2`. Si la instalación o el import fallan por la versión de Python, instalar 3.14 (`py install 3.14`), recrear el entorno con `py -V:3.14 -m venv .venv` y repetir.

- [ ] **Step 2: Crear la base de datos**

```bash
PGPASSWORD="$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)" "/c/Program Files/PostgreSQL/18/bin/createdb.exe" -h 127.0.0.1 -U postgres -E UTF8 -T template0 vehiculos
```

Expected: sin salida. `.env` ya existe; no tocarlo. Crear `.env.example` con las mismas claves (`SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `ALLOWED_HOSTS_EXTRA`) y valores de ejemplo, sin la contraseña real.

- [ ] **Step 3: Escribir la prueba de configuración**

```python
# core/tests/test_configuracion.py
from django.conf import settings
from django.db import connection
from django.test import TestCase

class ConfiguracionTests(TestCase):
    def test_base_de_datos_es_postgresql(self):
        self.assertEqual(connection.vendor, "postgresql")

    def test_ajustes_de_fidelidad(self):
        self.assertFalse(settings.USE_TZ)
        self.assertEqual(settings.TIME_ZONE, "America/Bogota")
        self.assertEqual(settings.LANGUAGE_CODE, "es")
        self.assertFalse(settings.APPEND_SLASH)
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertNotIn("django.contrib.auth", settings.INSTALLED_APPS)
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)
        for host in ("localhost", "127.0.0.1", "10.0.2.2"):
            self.assertIn(host, settings.ALLOWED_HOSTS)
        self.assertEqual(settings.STATIC_URL, "/static/")
        self.assertTrue(settings.WHITENOISE_USE_FINDERS)
```

- [ ] **Step 4: Ejecutar y verificar que falla**

Run: `.venv/Scripts/python manage.py test core.tests.test_configuracion -v 2`
Expected: FAIL o error de importación (todavía no hay `manage.py` ni `settings`).

- [ ] **Step 5: Escribir `manage.py`, `autosen/*` y las apps**

En `settings.py`:

- `load_dotenv(BASE_DIR / ".env")`. `SECRET_KEY = os.environ["SECRET_KEY"]`. `DEBUG = os.environ.get("DEBUG", "False") == "True"`.
- `ALLOWED_HOSTS = ["localhost", "127.0.0.1", "10.0.2.2"]` más `ALLOWED_HOSTS_EXTRA` separado por comas.
- `INSTALLED_APPS = ["django.contrib.sessions", "django.contrib.staticfiles", "core", "web", "panel", "reportes", "api"]`.
- `MIDDLEWARE`: `SecurityMiddleware`, `whitenoise.middleware.WhiteNoiseMiddleware`, `SessionMiddleware`, `CommonMiddleware`, `CsrfViewMiddleware`, `XFrameOptionsMiddleware`.
- `TEMPLATES`: `DIRS=[BASE_DIR / "templates"]`, `APP_DIRS=True`, context processors `django.template.context_processors.request`.
- `DATABASES`: `django.db.backends.postgresql` con `DB_*`, valores por defecto según §12.
- `LANGUAGE_CODE="es"`, `TIME_ZONE="America/Bogota"`, `USE_I18N=True`, `USE_TZ=False`.
- `STATIC_URL="/static/"`, `STATICFILES_DIRS=[BASE_DIR / "static"]`, `STATIC_ROOT=BASE_DIR / "staticfiles"`, `WHITENOISE_USE_FINDERS=True`.
- Sesiones según §6. `APPEND_SLASH=False`. `DEFAULT_AUTO_FIELD="django.db.models.AutoField"`.
- `LOGGING`: handler de consola, logger `autosen` en INFO.

- [ ] **Step 6: Ejecutar y verificar que pasa**

Run: `.venv/Scripts/python manage.py check` y luego `.venv/Scripts/python manage.py test core.tests.test_configuracion -v 2`
Expected: `System check identified no issues` y 2 pruebas OK.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "Esqueleto del proyecto Django y configuración" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Utilidades de equivalencia Java y contraseñas

**Files:**
- Create: `core/utilidades.py`, `core/auth.py` (solo la parte de contraseñas; las sesiones van en la Task 7)
- Test: `core/tests/test_utilidades.py`, `core/tests/test_contrasenas.py`

**Interfaces:**
- Produces (`core/utilidades.py`):
  - `redondear_java(x: float) -> int`
  - `entero_java(s: str) -> int | None`: regex `[+-]?[0-9]+` con `fullmatch` y sin `strip`; devuelve `None` si no es válido.
  - `texto_java(v) -> str`
  - `double_java(v: float) -> str`
  - `fecha_java(dt: datetime | None) -> str`
  - `ahora() -> datetime`
- Produces (`core/auth.py`):
  - `verificar_contrasena(plano: str, hash_guardado: str | None) -> bool`
  - `cifrar_contrasena(plano: str) -> str`

- [ ] **Step 1: Escribir las pruebas**

```python
# core/tests/test_utilidades.py
from datetime import datetime
from django.test import SimpleTestCase
from core.utilidades import redondear_java, entero_java, texto_java, double_java, fecha_java, ahora

class UtilidadesJavaTests(SimpleTestCase):
    def test_redondear_java_es_mitad_hacia_arriba(self):
        self.assertEqual([redondear_java(x) for x in (2.5, 0.5, -0.5, 22.5, 1.4999)], [3, 1, 0, 23, 1])

    def test_entero_java(self):
        self.assertEqual(entero_java("2020"), 2020)
        self.assertEqual(entero_java("+2020"), 2020)
        self.assertEqual(entero_java("-5"), -5)
        for invalido in (" 2020", "2020 ", "20.5", "", "abc", "2_020"):
            self.assertIsNone(entero_java(invalido), invalido)

    def test_texto_java(self):
        self.assertEqual([texto_java(None), texto_java("x"), texto_java(5)], ["null", "x", "5"])

    def test_double_java(self):
        casos = {95.0: "95.0", 2345.0: "2345.0", 0.12: "0.12", 0.0: "0.0", -3.5: "-3.5",
                 0.0005: "5.0E-4", 12345678.0: "1.2345678E7", 0.001: "0.001"}
        for valor, esperado in casos.items():
            self.assertEqual(double_java(valor), esperado)

    def test_fecha_java(self):
        self.assertEqual(fecha_java(datetime(2026, 10, 21, 19, 45, 12)), "2026-10-21T19:45:12")
        self.assertEqual(fecha_java(datetime(2026, 10, 21, 19, 45, 0)), "2026-10-21T19:45")
        self.assertEqual(fecha_java(None), "null")

    def test_ahora_sin_microsegundos(self):
        self.assertEqual(ahora().microsecond, 0)
```

```python
# core/tests/test_contrasenas.py
import bcrypt
from django.test import SimpleTestCase
from core.auth import cifrar_contrasena, verificar_contrasena

class ContrasenasTests(SimpleTestCase):
    def test_cifrar_produce_2a_costo_10(self):
        h = cifrar_contrasena("clave123")
        self.assertTrue(h.startswith("$2a$10$"))
        self.assertEqual(len(h), 60)
        self.assertTrue(verificar_contrasena("clave123", h))

    def test_verificar_acepta_prefijos_2a_2b_2y(self):
        h = bcrypt.hashpw(b"clave123", bcrypt.gensalt(rounds=4)).decode()
        for prefijo in ("$2a$", "$2b$", "$2y$"):
            self.assertTrue(verificar_contrasena("clave123", prefijo + h[4:]), prefijo)
        self.assertFalse(verificar_contrasena("otra", h))

    def test_hash_invalido_devuelve_false(self):
        self.assertFalse(verificar_contrasena("x", "no-es-un-hash"))
        self.assertFalse(verificar_contrasena("x", None))
        self.assertFalse(verificar_contrasena("x", ""))
```

- [ ] **Step 2: Ejecutar y verificar que fallan**

Run: `.venv/Scripts/python manage.py test core.tests.test_utilidades core.tests.test_contrasenas -v 2`
Expected: `ImportError`.

- [ ] **Step 3: Implementar**

- `double_java`:
  - Si `v == 0` o `1e-3 <= |v| < 1e7`, devuelve `repr(float(v))` (que ya termina en `.0` cuando es entero).
  - Si no, usa notación `d.dddE±n`: los dígitos más cortos de `repr` (vía `Decimal(repr(abs(v))).as_tuple()`), con un dígito antes del punto, al menos un decimal (`5.0E-4`) y el signo del exponente solo si es negativo.
- `fecha_java`: devuelve `dt.strftime("%Y-%m-%dT%H:%M")`, y añade `":%S"` solo si `dt.second or dt.microsecond`.
- `ahora`: devuelve `datetime.now().replace(microsecond=0)`.
- `verificar_contrasena`:
  - Normaliza el prefijo `$2y$` a `$2b$` y llama a `bcrypt.checkpw`.
  - Ante `ValueError`, `TypeError` o un hash vacío o `None`, devuelve `False`. Spring también devuelve `false` con un hash inválido.
- `cifrar_contrasena`: `bcrypt.hashpw(plano.encode(), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode()`.

- [ ] **Step 4: Ejecutar y verificar que pasan**

Run: el mismo comando del Step 2. Expected: 9 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Utilidades de equivalencia Java y contraseñas bcrypt"`.

---

### Task 3: Modelos, migración inicial y fábricas de prueba

**Files:**
- Create: `core/models.py`, `core/migrations/0001_initial.py` (generada), `core/tests/fabricas.py`
- Test: `core/tests/test_modelos.py`

**Interfaces:**
- Consumes: `cifrar_contrasena` (Task 2).
- Produces:
  - Modelos `Usuario`, `Cliente`, `Vehiculo`, `Sensor`, `Lectura` y `Alerta`, con los campos de la tabla §5 (nombres de campo Python exactamente como allí). `related_name`: `Cliente.vehiculos` y `Vehiculo.sensores`.
  - `core/tests/fabricas.py`:
    - `CLAVE = "clave123"`
    - `hash_clave() -> str`: se calcula una vez y se guarda en caché.
    - `crear_usuario(correo="admin@autosen.com", nombre="Admin", rol="admin") -> Usuario`
    - `crear_cliente(correo="joel@test.com", nombre="Joel", apellido="Moncaleano", estado="activo") -> Cliente`
    - `crear_vehiculo(cliente, placa="ABC123", nombre="Onix", marca="Chevrolet", modelo="2020-01-01", color="Negro", tipo_placa="particular", elm_mac=None) -> Vehiculo`
    - `crear_sensor(vehiculo, nivel=0, tipo="MAF", nombre="Sensor MAF", tipo_dano="Falla en flujo de aire", estado=None) -> Sensor`
    - `crear_lectura(id_vehiculo, nivel=0, valor=1.0, fecha=None, **campos) -> Lectura`
    - `crear_alerta(id_vehiculo, nivel=50, fecha=None, **campos) -> Alerta`
    - Las dos últimas usan por defecto `fecha=ahora()`, `nombre_sensor="S"`, `tipo_sensor="T"`, `tipo="advertencia"` y `mensaje="m"`.

- [ ] **Step 1: Escribir las pruebas**

```python
# core/tests/test_modelos.py
from django.db import models
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from core.models import Usuario, Cliente, Vehiculo, Sensor, Lectura, Alerta
from core.tests.fabricas import crear_cliente, crear_vehiculo, crear_sensor, crear_lectura, crear_alerta

class EsquemaTests(TestCase):
    def test_nombres_de_tablas(self):
        self.assertEqual([m._meta.db_table for m in (Usuario, Cliente, Vehiculo, Sensor, Lectura, Alerta)],
                         ["usuario", "cliente", "vehiculo", "sensores", "lecturas", "alertas"])

    def test_columnas_conservan_nombres_mysql(self):
        self.assertEqual(Sensor._meta.get_field("tipo_dano").column, "Tipo_daño")
        self.assertEqual(Vehiculo._meta.get_field("cliente").column, "Id_cliente")
        self.assertEqual(Cliente._meta.get_field("usuario").column, "Id_usuario")
        self.assertEqual(Vehiculo._meta.get_field("elm_mac").column, "elm_mac")
        self.assertEqual(Alerta._meta.get_field("fecha_alerta").column, "Fecha_alerta")

    def test_lecturas_y_alertas_sin_clave_foranea(self):  # F3
        for modelo in (Lectura, Alerta):
            campo = modelo._meta.get_field("id_vehiculo")
            self.assertIsInstance(campo, models.IntegerField)
            self.assertFalse(campo.is_relation)
            self.assertTrue(campo.db_index)

class ComportamientoTests(TestCase):
    def test_valores_por_defecto(self):
        c = Cliente.objects.create(nombre_cliente="A", apellido_cliente="B", contrasena="h", correo="a@b.c")
        self.assertEqual(c.estado, "activo")
        v = crear_vehiculo(c)
        s = Sensor.objects.create(vehiculo=v, nombre_sensor="S", tipo_sensor="T")
        self.assertEqual(s.nivel, 0)
        l = crear_lectura(v.pk)
        self.assertEqual((l.unidad, l.estado), ("", "OK"))
        self.assertEqual(crear_alerta(v.pk).leida, 0)

    def test_sensor_sin_tipo_dano(self):  # F4
        s = crear_sensor(crear_vehiculo(crear_cliente()), tipo_dano=None)
        self.assertIsNone(Sensor.objects.get(pk=s.pk).tipo_dano)

    def test_borrar_vehiculo_borra_sensores_y_conserva_historial(self):  # F3
        v = crear_vehiculo(crear_cliente())
        crear_sensor(v); crear_lectura(v.pk); crear_alerta(v.pk)
        v.delete()
        self.assertEqual((Sensor.objects.count(), Lectura.objects.count(), Alerta.objects.count()), (0, 1, 1))

    def test_cliente_con_vehiculos_esta_protegido(self):
        c = crear_cliente(); crear_vehiculo(c)
        with self.assertRaises(ProtectedError):
            c.delete()

    def test_related_names_y_orden_por_pk(self):
        c = crear_cliente()
        v2 = crear_vehiculo(c, placa="BBB222"); v1 = crear_vehiculo(c, placa="AAA111")
        self.assertEqual(list(c.vehiculos.all()), [v2, v1])
        s1 = crear_sensor(v1, nivel=90); s2 = crear_sensor(v1, nivel=10)
        self.assertEqual(list(v1.sensores.all()), [s1, s2])
```

- [ ] **Step 2: Ejecutar y verificar que fallan**

Run: `.venv/Scripts/python manage.py test core.tests.test_modelos -v 2`
Expected: `ImportError`.

- [ ] **Step 3: Implementar `core/models.py` según la tabla §5, y `fabricas.py`**

- Cada campo lleva `db_column` con el nombre MySQL exacto.
- Longitudes, nulos y valores por defecto: según §5.
- FKs:
  - `Cliente.usuario` → `PROTECT`, `null=True`.
  - `Vehiculo.cliente` → `PROTECT`.
  - `Sensor.vehiculo` → `CASCADE`, `null=True`.
- `Lectura.id_vehiculo` y `Alerta.id_vehiculo`: `IntegerField(db_index=True)`.
- `Meta.ordering = ["id_<entidad>"]` y `db_table` en cada modelo.
- `__str__` sencillo en cada modelo.

Run: `.venv/Scripts/python manage.py makemigrations core` y luego `migrate`.

- [ ] **Step 4: Ejecutar y verificar que pasan**

Run: el mismo comando del Step 2. Expected: 8 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Modelos de las seis tablas y migración inicial"`.

---

### Task 4: Importador del dump de phpMyAdmin

**Files:**
- Create: `core/importador.py`, `core/management/__init__.py`, `core/management/commands/__init__.py`, `core/management/commands/importar_mysql.py`, `core/tests/datos/dump_prueba.sql`
- Test: `core/tests/test_importador.py`

**Interfaces:**
- Consumes: modelos (Task 3).
- Produces:
  - `parsear_valores(texto: str) -> list[list]`: tuplas `(...)` separadas por comas. Tipos posibles: `int`, `float`, `str` y `None`.
  - `extraer_inserts(sql: str) -> list[tuple[str, list[str], list[list]]]`: devuelve `(tabla, columnas, filas)` en el orden en que aparecen.
  - `importar(sql: str, limpiar: bool) -> dict[str, int]`: filas importadas por tabla.
  - Comando: `importar_mysql <archivo> [--limpiar]`.

- [ ] **Step 1: Crear el dump de prueba (texto exacto)**

```sql
-- phpMyAdmin SQL Dump (datos de prueba inventados)
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
CREATE TABLE `usuario` (`Id_usuario` int(11) NOT NULL) ENGINE=InnoDB;
INSERT INTO `usuario` (`Id_usuario`, `Nombre`, `Correo`, `Contrasena`, `Rol`) VALUES
(1, 'Admin', 'admin@autosen.com', '$2y$12$hashDePruebaNoReal', 'admin');
INSERT INTO `cliente` (`Id_cliente`, `Nombre_cliente`, `Apellido_cliente`, `Contrasena`, `Correo`, `Id_usuario`, `Estado`) VALUES
(1, 'Joel', 'O\'Neil', 'h1', 'joel@test.com', 1, 'activo'),
(2, 'Juan', 'Ro''cio', 'h2', 'juan@test.com', NULL, 'bloqueado');
INSERT INTO `vehiculo` (`Id_vehiculo`, `Id_cliente`, `Nombre_vehiculo`, `Color`, `Marca`, `Modelo`, `Placa`, `Tipo_placa`) VALUES
(4, 1, 'Onix, el rojo', 'rojo', 'chevrolet', '2026-01-01', 'emt262', 'Público');
INSERT INTO `sensores` (`Id_sensor`, `Nombre_sensor`, `Tipo_sensor`, `Tipo_daño`, `Nivel`, `Id_vehiculo`) VALUES
(21, 'Sensor de Oxígeno', 'O2', 'Falla en mezcla\ncombustible', 79, 4),
(22, 'Prueba', 'TEST', 'Ninguno', NULL, 4);
INSERT INTO `lecturas` (`Id_lectura`, `Id_vehiculo`, `Nombre_sensor`, `Tipo_sensor`, `Valor`, `Unidad`, `Nivel`, `Estado`, `Fecha_lectura`) VALUES
(7, 4, 'RPM del motor', 'RPM', 2345.5, 'rpm', 73, 'FALLA', '2026-09-14 20:04:25');
INSERT INTO `alertas` (`Id_alerta`, `Id_vehiculo`, `Nombre_sensor`, `Tipo_sensor`, `Valor`, `Nivel`, `Tipo`, `Mensaje`, `Leida`, `Fecha_alerta`) VALUES
(3, 4, 'RPM del motor', 'RPM', 2345.5, 73, 'falla', 'Falla crítica; revisar (motor)', 0, '2026-09-14 20:04:25');
COMMIT;
```

(`\n` en `Tipo_daño` son los dos caracteres barra invertida + n, que es como phpMyAdmin escribe un salto de línea).

- [ ] **Step 2: Escribir las pruebas**

```python
# core/tests/test_importador.py
from datetime import datetime
from io import StringIO
from pathlib import Path
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from core.importador import parsear_valores, extraer_inserts
from core.models import Usuario, Cliente, Vehiculo, Sensor, Lectura, Alerta
from core.tests.fabricas import crear_cliente

DUMP = Path(__file__).parent / "datos" / "dump_prueba.sql"

class ParserTests(SimpleTestCase):
    def test_tipos_y_escapes(self):
        texto = "(1, 'O\\'Neil', NULL, 2.5, 'a''b', 'x\\ny'),\n(2, 'c,d;(e)', -3, '', 'z\\\\', 't\\tu')"
        self.assertEqual(parsear_valores(texto),
                         [[1, "O'Neil", None, 2.5, "a'b", "x\ny"], [2, "c,d;(e)", -3, "", "z\\", "t\tu"]])

    def test_extraer_inserts_en_orden(self):
        inserts = extraer_inserts(DUMP.read_text(encoding="utf-8"))
        self.assertEqual([t for t, _, _ in inserts], ["usuario", "cliente", "vehiculo", "sensores", "lecturas", "alertas"])
        self.assertEqual(inserts[3][1][3], "Tipo_daño")

class ImportarMysqlTests(TestCase):
    def importar(self, **opciones):
        salida = StringIO()
        call_command("importar_mysql", str(DUMP), stdout=salida, **opciones)
        return salida.getvalue()

    def test_importa_conservando_ids_y_valores(self):
        salida = self.importar()
        for linea in ("usuario: 1", "cliente: 2", "vehiculo: 1", "sensores: 2", "lecturas: 1", "alertas: 1"):
            self.assertIn(linea, salida)
        self.assertEqual(Usuario.objects.get(pk=1).contrasena, "$2y$12$hashDePruebaNoReal")
        self.assertEqual(Cliente.objects.get(pk=1).apellido_cliente, "O'Neil")
        juan = Cliente.objects.get(pk=2)
        self.assertEqual((juan.apellido_cliente, juan.usuario, juan.estado), ("Ro'cio", None, "bloqueado"))
        v = Vehiculo.objects.get(pk=4)
        self.assertEqual((v.nombre_vehiculo, v.placa, v.tipo_placa, v.elm_mac), ("Onix, el rojo", "emt262", "Público", None))
        s = Sensor.objects.get(pk=21)
        self.assertEqual((s.tipo_dano, s.estado), ("Falla en mezcla\ncombustible", None))
        self.assertIsNone(Sensor.objects.get(pk=22).nivel)
        l = Lectura.objects.get(pk=7)
        self.assertEqual((l.valor, l.fecha_lectura), (2345.5, datetime(2026, 9, 14, 20, 4, 25)))
        self.assertEqual(Alerta.objects.get(pk=3).mensaje, "Falla crítica; revisar (motor)")

    def test_secuencias_continuan_despues_de_los_ids_importados(self):
        self.importar()
        self.assertEqual(crear_cliente(correo="nuevo@test.com").pk, 3)

    def test_aborta_si_hay_datos_y_no_se_pide_limpiar(self):
        crear_cliente(correo="otro@test.com")
        with self.assertRaisesMessage(CommandError, "La tabla cliente ya tiene datos; usa --limpiar para reemplazarlos."):
            self.importar()

    def test_limpiar_reemplaza_los_datos(self):
        crear_cliente(correo="otro@test.com")
        self.importar(limpiar=True)
        self.assertEqual(Cliente.objects.count(), 2)
        self.assertFalse(Cliente.objects.filter(correo="otro@test.com").exists())
```

- [ ] **Step 3: Ejecutar y verificar que fallan**

Run: `.venv/Scripts/python manage.py test core.tests.test_importador -v 2`
Expected: `ImportError`.

- [ ] **Step 4: Implementar según §11**

Solo hay que escribir a mano el parser de valores, porque la firma no lo determina:

```python
ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "\\": "\\", "'": "'", '"': '"', "Z": "\x1a"}
# Recorrido carácter a carácter:
#   fuera de comillas: "(" abre fila, "," separa valores, ")" cierra fila; se ignoran espacios y saltos.
#   el token sin comillas "NULL" → None; si tiene "." o "e" → float; si no → int.
#   dentro de comillas: "\\X" → ESCAPES.get(X, X); "''" → "'"; "'" cierra la cadena.
```

- `extraer_inserts` localiza con una regex no voraz cada `INSERT INTO \`(\w+)\` \(([^)]*)\) VALUES` y pasa el resto, hasta el `;` que esté fuera de comillas, a `parsear_valores`. El ancla del final de la sentencia la decide el propio recorrido del parser.
- Las fechas `AAAA-MM-DD HH:MM:SS` se convierten con `datetime.strptime` cuando el campo destino es `DateTimeField`.
- `importar` aplica §11 completo: mapeo por `db_column`, orden de tablas, `transaction.atomic()` y reinicio de secuencias con `connection.ops.sequence_reset_sql(no_style(), modelos)`.
- `--limpiar` borra en orden inverso. Sin `--limpiar`, comprueba las tablas en orden y lanza `CommandError` con el mensaje de la prueba para la primera que tenga datos.

- [ ] **Step 5: Ejecutar y verificar que pasan**

Run: el mismo comando del Step 3. Expected: 6 pruebas OK.

- [ ] **Step 6: Importar el dump real en la base de desarrollo**

Run: `.venv/Scripts/python manage.py importar_mysql "datos/vehiculos (10).sql"`
Expected: `usuario: 1`, `cliente: 2`, `vehiculo: 3`, `sensores: 9`, `lecturas: 0`, `alertas: 0`.

- [ ] **Step 7: Commit** — mensaje `"Comando importar_mysql para dumps de phpMyAdmin"` (sin `datos/`, que está ignorada).

---

### Task 5: Patrones GoF

**Files:**
- Create: `core/patrones/__init__.py`, `core/patrones/estrategia/__init__.py`, `core/patrones/fabrica/__init__.py`, `core/patrones/singleton/__init__.py`, `core/patrones/observador/__init__.py`
- Modify: `core/apps.py` (conecta el receptor en `ready()`)
- Create: `PATRONES_GOF.md`, reescrito a partir de `referencia/proyecto-java/PATRONES_GOF.md` con rutas y nombres de Python, la misma estructura y la sección de patrones nativos adaptada a Django (señales, middleware, ORM, decoradores)
- Test: `core/tests/test_patrones.py`

**Interfaces:**
- Produces:
  - `UmbralesReporte.INSTANCIA` con `es_optimo(n: int) -> bool`, `es_advertencia(n)` y `es_falla(n)`. Las constantes `UmbralesReporte.MINIMO_ADVERTENCIA == 40` y `MINIMO_FALLA == 70` se declaran con `enum.nonmember`.
  - `EstadoSensorStrategy` (ABC, `clasificar(nivel: int | None) -> str`).
  - `EstadoSensorReporteStrategy.get_instancia()` y `EstadoSensorFiltroStrategy.get_instancia()`.
  - `ClasificadorEstadoSensor(strategy)` con `.set_strategy()`, `.get_strategy()` y `.clasificar()`.
  - `TipoEstado.REPORTE` / `TipoEstado.FILTRO` y `EstadoSensorStrategyFactory.crear(tipo) -> EstadoSensorStrategy`.
  - `alerta_critica` (`Signal`), cuyo receptor `atender_alerta_critica(sender, alerta, **kwargs)` registra el mensaje con el logger `autosen.observador`.

- [ ] **Step 1: Escribir las pruebas**

```python
# core/tests/test_patrones.py
from django.test import SimpleTestCase
from core.models import Alerta
from core.patrones.estrategia import ClasificadorEstadoSensor, EstadoSensorFiltroStrategy, EstadoSensorReporteStrategy
from core.patrones.fabrica import EstadoSensorStrategyFactory, TipoEstado
from core.patrones.observador import alerta_critica
from core.patrones.singleton import UmbralesReporte

NIVELES = (None, 0, 39, 40, 69, 70, 100)

class PatronesTests(SimpleTestCase):
    def test_estrategia_reporte(self):
        s = EstadoSensorReporteStrategy.get_instancia()
        self.assertEqual([s.clasificar(n) for n in NIVELES], ["OK", "OK", "OK", "ADVERTENCIA", "ADVERTENCIA", "FALLA", "FALLA"])

    def test_estrategia_filtro(self):
        s = EstadoSensorFiltroStrategy.get_instancia()
        self.assertEqual([s.clasificar(n) for n in NIVELES], ["optimo", "optimo", "optimo", "advertencia", "advertencia", "falla", "falla"])

    def test_fabrica_devuelve_instancias_unicas(self):
        self.assertIs(EstadoSensorStrategyFactory.crear(TipoEstado.REPORTE), EstadoSensorReporteStrategy.get_instancia())
        self.assertIs(EstadoSensorStrategyFactory.crear(TipoEstado.FILTRO), EstadoSensorFiltroStrategy.get_instancia())

    def test_contexto_cambia_de_estrategia(self):
        c = ClasificadorEstadoSensor(EstadoSensorStrategyFactory.crear(TipoEstado.REPORTE))
        self.assertEqual(c.clasificar(50), "ADVERTENCIA")
        c.set_strategy(EstadoSensorStrategyFactory.crear(TipoEstado.FILTRO))
        self.assertEqual(c.clasificar(50), "advertencia")
        with self.assertRaises(RuntimeError):
            ClasificadorEstadoSensor(None).clasificar(10)

    def test_singleton(self):
        self.assertEqual(len(UmbralesReporte), 1)
        self.assertEqual((UmbralesReporte.MINIMO_ADVERTENCIA, UmbralesReporte.MINIMO_FALLA), (40, 70))
        u = UmbralesReporte.INSTANCIA
        self.assertEqual([u.es_optimo(39), u.es_optimo(40), u.es_advertencia(69), u.es_advertencia(70), u.es_falla(70)],
                         [True, False, True, False, True])

    def test_observador_registra_la_alerta(self):
        alerta = Alerta(id_vehiculo=4, nombre_sensor="RPM del motor", nivel=73, mensaje="Falla crítica en RPM del motor: nivel 73% (2345.0 rpm).")
        with self.assertLogs("autosen.observador", level="WARNING") as registro:
            alerta_critica.send(sender=None, alerta=alerta)
        self.assertEqual(registro.output, ["WARNING:autosen.observador:[OBSERVER] Alerta registrada -> Sensor 'RPM del motor' "
                                          "(vehículo 4) nivel 73% | Falla crítica en RPM del motor: nivel 73% (2345.0 rpm)."])
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test core.tests.test_patrones -v 2`. Expected: `ImportError`.

- [ ] **Step 3: Implementar** según §8, traduciendo las clases de `J/java/.../patrones/`. El receptor formatea cada argumento con `texto_java` y se conecta en `CoreConfig.ready()`.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 6 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Patrones GoF en Python y PATRONES_GOF.md"`.

---

### Task 6: Infraestructura web (parámetros, errores, tema, estáticos y filtros)

**Files:**
- Create: `core/http.py`, `core/errores.py`, `core/middleware.py`, `core/templatetags/__init__.py`, `core/templatetags/autosen.py`
- Create: `templates/error.html`, convertido de `J/resources/templates/error.html`
- Create: `static/css/light-mode.css` y `static/js/theme-toggle.js`, copiados byte a byte de `J/resources/static/`
- Modify: `autosen/settings.py` (añade `core.middleware.TemaMiddleware` a `MIDDLEWARE` justo después de WhiteNoise); `autosen/urls.py` (`handler400`, `handler403`, `handler404` y `handler500`); `web/urls.py` (`path("error", errores.pagina_error, name="error")`)
- Test: `core/tests/test_http.py`, `core/tests/test_errores.py`, `core/tests/test_tema.py`, `core/tests/test_filtros_plantilla.py`

**Interfaces:**
- Produces:
  - `parametro(request, nombre: str, tipo: type = str, requerido: bool = True)`:
    - Lee `request.POST` y luego `request.GET`. Devuelve el texto tal cual, sin `strip`.
    - Para `int` usa `entero_java`; para `float`, `float()`.
    - Un parámetro obligatorio ausente lanza `django.core.exceptions.BadRequest`. Un número vacío da `None` si es opcional, y `BadRequest` si es obligatorio. Un número inválido siempre lanza `BadRequest`.
  - `metodos(*permitidos: str)`: decorador. Si el método no está permitido, devuelve `error.html` con status 405. `"GET"` implica también `"HEAD"`.
  - `render_error(request, status: int, http_status: int | None = None) -> HttpResponse`
  - `error_400`, `error_403`, `error_404` y `error_500` (handlers); `pagina_error(request)`, que es la vista `/error`.
  - `TemaMiddleware` y la constante `SNIPPET`.
  - Filtros de plantilla:
    - `estado_nivel(nivel, "falla,advertencia,ok")`: devuelve la etiqueta 0 si `nivel >= 70`, la 1 si `>= 40` y, si no, la 2. `None` cuenta como la 2.
    - `estado_informe(obj, "falla,advertencia,ok")`: igual, pero usando `obj.nivel` y `obj.estado`. Es falla si `nivel >= 70` o `estado` es `'falla'` (sin distinguir mayúsculas); advertencia si `nivel >= 40` o `estado` es `'advertencia'`.

- [ ] **Step 1: Escribir las pruebas**

```python
# core/tests/test_http.py
from django.core.exceptions import BadRequest
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from core.http import parametro, metodos

rf = RequestFactory()

class ParametroTests(SimpleTestCase):
    def test_lee_formulario_y_query(self):
        req = rf.post("/x?b=2", {"a": " 1 "})
        self.assertEqual((parametro(req, "a"), parametro(req, "b")), (" 1 ", "2"))

    def test_texto_vacio_es_valido(self):
        self.assertEqual(parametro(rf.post("/x", {"a": ""}), "a"), "")

    def test_ausente(self):
        with self.assertRaises(BadRequest):
            parametro(rf.post("/x"), "a")
        self.assertIsNone(parametro(rf.get("/x"), "a", requerido=False))

    def test_numeros(self):
        self.assertEqual(parametro(rf.get("/x?n=12"), "n", int), 12)
        self.assertEqual(parametro(rf.get("/x?n=2.5"), "n", float), 2.5)
        self.assertIsNone(parametro(rf.get("/x?n="), "n", int, requerido=False))
        for url, tipo in (("/x?n=", int), ("/x?n=abc", int), ("/x?n=abc", float)):
            with self.assertRaises(BadRequest):
                parametro(rf.get(url), "n", tipo)

class MetodosTests(SimpleTestCase):
    def test_rechaza_metodo_no_permitido_con_405(self):
        vista = metodos("GET")(lambda request: HttpResponse("ok"))
        self.assertEqual(vista(rf.head("/x")).status_code, 200)
        r = vista(rf.post("/x"))
        self.assertEqual(r.status_code, 405)
        self.assertContains(r, "Código: 405", status_code=405)
```

```python
# core/tests/test_errores.py
from django.test import Client, RequestFactory, TestCase
from core import errores

class PaginasDeErrorTests(TestCase):
    def test_404_en_ruta_publica(self):
        r = Client().get("/api/no-existe")
        self.assertContains(r, "NO ENCONTRADA", status_code=404)
        self.assertContains(r, "Not Found", status_code=404)

    def test_get_error_muestra_500_con_estado_200(self):
        r = Client().get("/error")
        self.assertContains(r, "DEL SERVIDOR")
        self.assertContains(r, "Código: 500")

    def test_handlers_400_y_500(self):
        req = RequestFactory().get("/x")
        self.assertContains(errores.error_400(req, Exception()), "Bad Request", status_code=400)
        self.assertContains(errores.error_500(req), "Internal Server Error", status_code=500)
```

```python
# core/tests/test_tema.py
from django.http import HttpResponse, JsonResponse
from django.test import Client, RequestFactory, SimpleTestCase
from core.middleware import TemaMiddleware, SNIPPET

def procesar(respuesta):
    return TemaMiddleware(lambda request: respuesta)(RequestFactory().get("/"))

class TemaMiddlewareTests(SimpleTestCase):
    def test_inyecta_antes_de_body(self):
        r = procesar(HttpResponse("<html><body>Hola</body></html>"))
        self.assertEqual(r.content.decode(), "<html><body>Hola" + SNIPPET + "</html>")
        self.assertIn('href="/static/css/light-mode.css"', SNIPPET)
        self.assertIn('src="/static/js/theme-toggle.js"', SNIPPET)
        self.assertEqual(r["Content-Length"], str(len(r.content)))

    def test_reemplaza_todas_las_apariciones(self):
        r = procesar(HttpResponse("<body>a</body><body>b</body>"))
        self.assertEqual(r.content.decode().count("theme-toggle.js"), 2)

    def test_no_toca_lo_que_no_corresponde(self):
        for respuesta in (HttpResponse("<p>sin cierre</p>"),
                          HttpResponse('<body><script src="/static/js/theme-toggle.js"></script></body>'),
                          JsonResponse({"html": "</body>"})):
            antes = respuesta.content
            self.assertEqual(procesar(respuesta).content, antes)

    def test_estaticos_servidos(self):
        self.assertEqual(Client().get("/static/js/theme-toggle.js").status_code, 200)
```

```python
# core/tests/test_filtros_plantilla.py
from types import SimpleNamespace as O
from django.test import SimpleTestCase
from core.templatetags.autosen import estado_nivel, estado_informe

class FiltrosPlantillaTests(SimpleTestCase):
    def test_estado_nivel(self):
        self.assertEqual([estado_nivel(n, "F,A,O") for n in (100, 70, 69, 40, 39, None)], ["F", "F", "A", "A", "O", "O"])

    def test_estado_informe(self):
        casos = [(O(nivel=10, estado="FALLA"), "F"), (O(nivel=10, estado="advertencia"), "A"),
                 (O(nivel=None, estado=None), "O"), (O(nivel=75, estado=None), "F"), (O(nivel=45, estado="OK"), "A")]
        for obj, esperado in casos:
            self.assertEqual(estado_informe(obj, "F,A,O"), esperado)
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test core.tests.test_http core.tests.test_errores core.tests.test_tema core.tests.test_filtros_plantilla -v 2`. Expected: `ImportError`.

- [ ] **Step 3: Implementar**

- `SNIPPET`: es el texto de `J/java/.../config/TemaFilter.java:24-33` copiado literalmente, cambiando solo `/css/light-mode.css` → `/static/css/light-mode.css` y `/js/theme-toggle.js` → `/static/js/theme-toggle.js`.
- `TemaMiddleware` aplica §9.
- `render_error`:
  - Usa como `error` la frase de `HTTPStatus(status).phrase`.
  - Toma `message` del `switch` de `CustomErrorController` (404, 403 y 500; cualquier otro, "Ocurrió un error inesperado.").
  - `http_status` vale por defecto `status`. `pagina_error` lo llama con `status=500, http_status=200`.
- `error.html`: se convierte según §10. Los `th:switch` pasan a `{% if status == 404 %}…{% elif %}`, y los enlaces `href="/"` y `href="/dashboard"` se quedan literales.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 14 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Parámetros, páginas de error, middleware de tema y filtros de plantilla"`.

---

### Task 7: Sesiones y login de clientes y administradores

**Files:**
- Modify: `core/auth.py` (añade sesiones y decoradores), `core/errores.py` (`error_404` redirige al login correspondiente), `autosen/settings.py` (context processor `core.context_processors.admin_correo`)
- Create: `core/context_processors.py`, `web/views.py`, `panel/views.py`
- Modify: `web/urls.py`, `panel/urls.py`
- Create: plantillas convertidas de `J/resources/templates/` (§10): `templates/paginas/index.html`, `nosotros.html`, `login.html`, `register.html` y `templates/admin/login.html`
- Modify: `core/tests/fabricas.py` (añade `login_cliente(client, cliente)` y `login_admin(client, usuario)`. Cada una hace primero GET a `/login` o `/admin/login`, para obtener la cookie `csrftoken`, y después el POST con `CLAVE` y `csrfmiddlewaretoken`. Así funcionan también con `Client(enforce_csrf_checks=True)`.)
- Test: `core/tests/test_sesiones.py`, `web/tests/test_autenticacion.py`

**Interfaces:**
- Consumes: `verificar_contrasena` y `cifrar_contrasena` (Task 2); `render_error` (Task 6).
- Produces (`core/auth.py`):
  - `iniciar_sesion_cliente(request, cliente)`, `cerrar_sesion_cliente(request)` y `cliente_actual(request) -> Cliente | None`
  - `iniciar_sesion_admin(request, usuario)`, `cerrar_sesion_admin(request)` y `admin_actual(request) -> Usuario | None`
  - Las claves de sesión son `"cliente_id"` y `"admin_id"`. Iniciar sesión llama a `cycle_key()`.
  - `@cliente_requerido`: pone `request.cliente` y `request.cliente_correo`; sin sesión, redirige a `/login`.
  - `@admin_requerido`: pone `request.admin` y `request.admin_correo`; sin sesión, redirige a `/admin/login`.
  - `ruta_publica(path: str) -> bool`, con la lista de §6.
- Produces (rutas y nombres de URL):
  - `inicio` (`""`), `nosotros`, `login`, `logout` y `register` en `web`.
  - `admin_login` y `admin_logout` en `panel`.
  - Context processor: `{"admin_correo": <correo del admin en sesión o "">}`. Tolera peticiones sin `session`, como las de `RequestFactory` en las pruebas de errores.

- [ ] **Step 1: Escribir las pruebas**

```python
# core/tests/test_sesiones.py
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from core.auth import admin_requerido, cliente_requerido
from core.tests.fabricas import crear_cliente, crear_usuario

def peticion(**sesion):
    req = RequestFactory().get("/x")
    req.session = SessionStore()
    req.session.update(sesion)
    return req

ok = lambda request: HttpResponse("ok")

class DecoradoresTests(TestCase):
    def test_admin_requerido_rechaza_sesion_de_cliente(self):  # F2
        r = admin_requerido(ok)(peticion(cliente_id=crear_cliente().pk))
        self.assertEqual((r.status_code, r["Location"]), (302, "/admin/login"))

    def test_admin_requerido_acepta_admin(self):
        u = crear_usuario()
        req = peticion(admin_id=u.pk)
        self.assertEqual(admin_requerido(ok)(req).status_code, 200)
        self.assertEqual(req.admin_correo, "admin@autosen.com")

    def test_cliente_requerido(self):
        c = crear_cliente()
        self.assertEqual(cliente_requerido(ok)(peticion(admin_id=crear_usuario().pk))["Location"], "/login")
        req = peticion(cliente_id=c.pk)
        self.assertEqual(cliente_requerido(ok)(req).status_code, 200)
        self.assertEqual((req.cliente, req.cliente_correo), (c, "joel@test.com"))

    def test_id_de_sesion_inexistente_redirige(self):
        self.assertEqual(cliente_requerido(ok)(peticion(cliente_id=9999))["Location"], "/login")
```

```python
# web/tests/test_autenticacion.py
from django.test import Client, TestCase
from core.models import Cliente
from core.tests.fabricas import CLAVE, crear_cliente, crear_usuario, login_admin, login_cliente

class LoginClienteTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()

    def post_login(self, correo, contrasena=CLAVE):
        return self.client.post("/login", {"correo": correo, "contrasena": contrasena})

    def test_login_correcto(self):
        self.assertRedirects(self.post_login("joel@test.com"), "/dashboard", fetch_redirect_response=False)
        self.assertEqual(self.client.session["cliente_id"], self.cliente.pk)

    def test_correo_con_otras_mayusculas(self):
        self.assertRedirects(self.post_login("JOEL@Test.com"), "/dashboard", fetch_redirect_response=False)

    def test_fallos_redirigen_con_error(self):
        Cliente.objects.create(nombre_cliente="B", apellido_cliente="B", correo="b@test.com",
                               contrasena=self.cliente.contrasena, estado="bloqueado")
        for correo, clave in (("joel@test.com", "mala"), ("nadie@test.com", CLAVE), ("b@test.com", CLAVE)):
            self.assertRedirects(self.post_login(correo, clave), "/login?error", fetch_redirect_response=False)

    def test_pagina_login_muestra_error(self):
        self.assertContains(self.client.get("/login?error"), "Correo o contraseña incorrectos.")

    def test_logout_por_get_y_post(self):
        for metodo in ("get", "post"):
            login_cliente(self.client, self.cliente)
            self.assertRedirects(getattr(self.client, metodo)("/logout"), "/login", fetch_redirect_response=False)
            self.assertNotIn("cliente_id", self.client.session)

    def test_paginas_publicas(self):
        for url in ("/", "/nosotros", "/login", "/register", "/admin/login"):
            self.assertEqual(Client().get(url).status_code, 200, url)

class RegistroTests(TestCase):
    def test_registro_sin_recortar_espacios(self):
        r = self.client.post("/register", {"nombre": " Ana ", "apellido": "Paz", "correo": "ana@test.com", "contrasena": "secreto"})
        self.assertRedirects(r, "/login", fetch_redirect_response=False)
        ana = Cliente.objects.get(correo="ana@test.com")
        self.assertEqual((ana.nombre_cliente, ana.estado), (" Ana ", "activo"))
        self.assertTrue(ana.contrasena.startswith("$2a$10$"))

    def test_registro_correo_duplicado(self):
        crear_cliente()
        r = self.client.post("/register", {"nombre": "J", "apellido": "M", "correo": "JOEL@TEST.COM", "contrasena": "x"})
        self.assertContains(r, "El correo ya está registrado.")

class LoginAdminTests(TestCase):
    def test_login_y_logout_admin(self):
        u = crear_usuario()
        r = self.client.post("/admin/login", {"correo": "admin@autosen.com", "contrasena": CLAVE})
        self.assertRedirects(r, "/admin", fetch_redirect_response=False)
        self.assertEqual(self.client.session["admin_id"], u.pk)
        self.assertRedirects(self.client.post("/admin/logout"), "/admin/login", fetch_redirect_response=False)

    def test_login_admin_fallido(self):
        crear_usuario()
        r = self.client.post("/admin/login", {"correo": "admin@autosen.com", "contrasena": "mala"})
        self.assertRedirects(r, "/admin/login?error", fetch_redirect_response=False)
        self.assertContains(self.client.get("/admin/login?error"), "Credenciales incorrectas.")

    def test_sesiones_independientes(self):  # F2
        login_admin(self.client, crear_usuario())
        login_cliente(self.client, crear_cliente())
        self.client.post("/logout")
        self.assertIn("admin_id", self.client.session)

class RutasDesconocidasTests(TestCase):
    def test_sin_sesion_redirigen_al_login_que_corresponde(self):
        c = Client(raise_request_exception=False)
        self.assertRedirects(c.get("/no-existe"), "/login", fetch_redirect_response=False)
        self.assertRedirects(c.get("/admin/no-existe"), "/admin/login", fetch_redirect_response=False)
        self.assertEqual(c.get("/api/no-existe").status_code, 404)

    def test_con_sesion_dan_404(self):
        login_cliente(self.client, crear_cliente())
        self.assertEqual(self.client.get("/no-existe").status_code, 404)
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test core.tests.test_sesiones web.tests.test_autenticacion -v 2`. Expected: `ImportError`.

- [ ] **Step 3: Implementar**

- **Login de cliente:** la vista `/login` (`metodos("GET", "POST")`) muestra `paginas/login.html` en GET. En POST:
  - Busca el cliente con `Cliente.objects.filter(correo__iexact=correo).first()`.
  - Comprueba la contraseña con `verificar_contrasena` y que `estado != "bloqueado"`.
  - Si todo cuadra, redirige a `/dashboard`; si no, a `/login?error`.
- **`/register`:** equivale a `AuthController.register` (`J/java/.../controller/AuthController.java:30-51`).
- **Login de admin:** `/admin/login` funciona igual contra `Usuario`.
- **Plantillas:**
  - `th:if="${param.error}"` → `{% if "error" in request.GET %}`.
  - Los formularios llevan `{% csrf_token %}`.
  - Los enlaces usan `{% url %}`. `@{/admin}` se queda como `href="/admin"` hasta que exista la vista en la Task 12.
- **`error_404`:** si la ruta no es pública y no hay sesión, redirige a `/admin/login` (si la ruta es `/admin` o empieza por `/admin/`) o a `/login` (cualquier otra). En el resto de casos responde 404.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 17 pruebas OK. Run también `.venv/Scripts/python manage.py test` (toda la suite). Expected: OK.

- [ ] **Step 5: Commit** — mensaje `"Sesiones separadas de cliente y admin, login, registro y páginas públicas"`.

---

### Task 8: Web del cliente (dashboard, vehículos y sensores)

**Files:**
- Modify: `web/views.py`, `web/urls.py`
- Create: plantillas convertidas: `templates/paginas/dashboard.html`, `mis-vehiculos.html`, `sensores.html`, `crear-vehiculo.html` y `editar-vehiculo.html`
- Create: `core/sensores_defecto.py` con `SENSORES_POR_DEFECTO` (las 4 tuplas de `J/java/.../controller/ApiController.java:36-41`) y `crear_sensores_por_defecto(vehiculo) -> None`
- Test: `web/tests/test_vehiculos.py`

**Interfaces:**
- Consumes: `cliente_requerido`, `metodos`, `parametro`, `entero_java`, `estado_nivel`.
- Produces:
  - Rutas `dashboard`, `vehiculos`, `sensores`, `vehiculo_crear`, `vehiculo_editar` (`<int:id>`) y `vehiculo_eliminar` (`<int:id>`).
  - `crear_sensores_por_defecto(vehiculo)`, que reutiliza la API en la Task 10.

Vistas que se reproducen:

- `DashboardController.dashboard`, `.misVehiculos` y `.sensores` (`J/java/.../controller/DashboardController.java:30-74`).
- `VehiculoController.showCrear`, `.crear`, `.showEditar`, `.editar` y `.eliminar` (`J/java/.../controller/VehiculoController.java:24-168`).
- En `eliminar`, el borrado usa `vehiculo.delete()`, con cascada de sensores (F3).

- [ ] **Step 1: Escribir las pruebas**

```python
# web/tests/test_vehiculos.py
import re
from django.test import TestCase
from core.models import Lectura, Sensor, Vehiculo
from core.tests.fabricas import crear_alerta, crear_cliente, crear_lectura, crear_sensor, crear_vehiculo, login_cliente

DATOS = {"nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": "2020", "color": "Negro", "placa": "abc-123", "tipoPlaca": "particular"}

class Base(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()
        login_cliente(self.client, self.cliente)

class DashboardTests(Base):
    def test_kpis(self):
        v = crear_vehiculo(self.cliente)
        for n in (10, 39, 40, 69, 70):
            crear_sensor(v, nivel=n)
        crear_sensor(crear_vehiculo(crear_cliente(correo="otro@test.com"), placa="ZZZ999"), nivel=90)
        r = self.client.get("/dashboard")
        self.assertTemplateUsed(r, "paginas/dashboard.html")
        self.assertEqual([r.context[k] for k in ("totalSensores", "sensoresOk", "advertencias", "fallas")], [5, 2, 2, 1])
        self.assertRegex(r.content.decode(), r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo), \d{2} \w+ \d{4}")

    def test_sin_sesion(self):
        self.client.post("/logout")
        for url in ("/dashboard", "/vehiculos", "/sensores", "/vehiculos/crear"):
            self.assertRedirects(self.client.get(url), "/login", fetch_redirect_response=False)

class CrearVehiculoTests(Base):
    def test_crea_con_los_cuatro_sensores(self):
        self.assertRedirects(self.client.post("/vehiculos/crear", DATOS), "/vehiculos", fetch_redirect_response=False)
        v = Vehiculo.objects.get()
        self.assertEqual((v.placa, v.modelo, v.cliente), ("ABC-123", "2020-01-01", self.cliente))
        self.assertEqual([(s.tipo_sensor, s.nombre_sensor, s.tipo_dano, s.nivel) for s in v.sensores.all()], [
            ("MAF", "Sensor de Flujo de Masa de Aire (MAF)", "Falla en flujo de aire", 0),
            ("O2", "Sensor de Oxígeno (O2)", "Falla en mezcla", 0),
            ("ECT", "Sensor de Temperatura del Refrigerante (ECT)", "Sobrecalentamiento", 0),
            ("MAP", "Sensor de Presión Absoluta del Colector (MAP)", "Falla en presión", 0)])

    def test_validaciones_en_el_orden_de_java(self):
        crear_vehiculo(self.cliente, placa="xyz")  # placa no válida, como las importadas
        casos = [({"marca": "  "}, "Todos los campos son obligatorios."),
                 ({"modelo": "1989"}, "El año debe estar entre 1990 y 2030."),
                 ({"modelo": " 2020"}, "El año debe ser un número válido."),
                 ({"placa": "XYZ"}, "Ya existe un vehículo registrado con esa placa."),  # duplicado antes que formato
                 ({"placa": "AB1234"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")]
        for cambio, mensaje in casos:
            with self.subTest(cambio):
                self.assertContains(self.client.post("/vehiculos/crear", {**DATOS, **cambio}), mensaje)
        self.assertEqual(Vehiculo.objects.count(), 1)

class EditarEliminarTests(Base):
    def setUp(self):
        super().setUp()
        self.v = crear_vehiculo(self.cliente, placa="ABC123")
        self.ajeno = crear_vehiculo(crear_cliente(correo="otro@test.com"), placa="OTR111")

    def test_vehiculo_ajeno_redirige_sin_cambios(self):
        url = f"/vehiculos/{self.ajeno.pk}"
        self.assertRedirects(self.client.get(url + "/editar"), "/vehiculos", fetch_redirect_response=False)
        self.client.post(url + "/editar", {**DATOS, "placa": "NEW111"})
        self.client.post(url + "/eliminar")
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.placa, "OTR111")

    def test_editar(self):
        datos = {"nombreVehiculo": "Nuevo", "marca": "Kia", "color": "Azul", "placa": "xyz999", "tipoPlaca": "publico"}
        self.assertRedirects(self.client.post(f"/vehiculos/{self.v.pk}/editar", datos), "/vehiculos", fetch_redirect_response=False)
        self.v.refresh_from_db()
        self.assertEqual((self.v.placa, self.v.marca, self.v.tipo_placa), ("XYZ999", "Kia", "publico"))

    def test_editar_errores(self):
        base = {"nombreVehiculo": "N", "marca": "K", "color": "A", "tipoPlaca": "publico"}
        self.assertContains(self.client.post(f"/vehiculos/{self.v.pk}/editar", {**base, "placa": "otr111"}), "Ya existe un vehículo con esa placa.")
        self.assertContains(self.client.post(f"/vehiculos/{self.v.pk}/editar", {**base, "placa": " "}), "Todos los campos son obligatorios.")
        r = self.client.post(f"/vehiculos/{self.v.pk}/editar", {**base, "placa": "abc123"})  # su propia placa en minúsculas
        self.assertEqual(r.status_code, 302)

    def test_eliminar_conserva_historial(self):  # F3
        crear_sensor(self.v); crear_lectura(self.v.pk); crear_alerta(self.v.pk)
        self.assertRedirects(self.client.post(f"/vehiculos/{self.v.pk}/eliminar"), "/vehiculos", fetch_redirect_response=False)
        self.assertFalse(Vehiculo.objects.filter(pk=self.v.pk).exists())
        self.assertEqual((Sensor.objects.count(), Lectura.objects.count()), (0, 1))

    def test_paginas_con_datos_importados(self):  # Review Focus 1
        importado = crear_vehiculo(self.cliente, placa="emt262", tipo_placa="Público", modelo="2026-01-01")
        crear_sensor(importado, nivel=50)
        self.assertContains(self.client.get("/vehiculos"), "emt262")
        r = self.client.get("/sensores")
        self.assertContains(r, "ADVERTENCIA")
        self.assertContains(self.client.get(f"/vehiculos/{importado.pk}/editar"), 'value="emt262"')
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test web.tests.test_vehiculos -v 2`. Expected: FAIL (404 o redirección al login).

- [ ] **Step 3: Implementar las vistas y convertir las plantillas**

- El JS de `paginas/dashboard.html` se copia tal cual. `fetch('/api/obd2/conectar', {method: 'POST'})` funciona sin token, porque la API está exenta de CSRF.
- `paginas/crear-vehiculo.html` no recibe el cliente; conserva el texto fijo "Mi cuenta", como en Java.
- Validaciones:
  - El año se valida con `entero_java(modelo)` sobre el valor sin recortar.
  - La placa duplicada se busca con `Vehiculo.objects.filter(placa__iexact=placa.upper()).exists()`.
  - El formato se comprueba con `re.fullmatch(r"[A-Z]{3}-?[0-9]{3}", placa.upper())`.
- Un vehículo inexistente se obtiene con `Vehiculo.objects.get(pk=id)`, que da 500 igual que `orElseThrow`.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 9 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Web del cliente: dashboard, vehículos y sensores"`.

---

### Task 9: Lógica OBD2 y alertas

**Files:**
- Create: `api/obd2.py`
- Test: `api/tests/test_obd2_logica.py`

**Interfaces:**
- Consumes: `redondear_java`, `double_java`, `ahora`, `alerta_critica` y `Alerta`.
- Produces (`api/obd2.py`; se importa `random` como módulo y se llama a `random.random()`):
  - `calcular_nivel(tipo_sensor: str, valor: float) -> int`
  - `valor_simulado(tipo: str | None) -> float`
  - `unidad_de(tipo: str | None) -> str`
  - `redondear(d: float) -> float`, `redondear_dos(d: float) -> float`
  - `estado_por_nivel(nivel: int) -> str`: `"OK"` / `"ADVERTENCIA"` / `"FALLA"`.
  - `crear_alerta_si_corresponde(id_vehiculo: int, nombre_sensor: str, tipo_sensor: str, valor: float, nivel: int, sufijo_unidad: str) -> Alerta | None`
    - Con nivel ≥ 40, crea la `Alerta` con `leida=0` y `fecha_alerta=ahora()`, emite `alerta_critica` y la devuelve.
    - Tipo `"falla"` si nivel ≥ 70; si no, `"advertencia"`.
    - Mensaje: `"Falla crítica en {nombre}: nivel {nivel}% ({double_java(valor)}{sufijo_unidad})."` o `"Advertencia en …"`.

Todas las constantes y fórmulas se copian de `J/java/.../controller/Obd2Controller.java:298-355`.

- [ ] **Step 1: Escribir las pruebas**

```python
# api/tests/test_obd2_logica.py
from unittest import mock
from django.test import SimpleTestCase, TestCase
from api.obd2 import (calcular_nivel, crear_alerta_si_corresponde, estado_por_nivel, redondear,
                      redondear_dos, unidad_de, valor_simulado)
from core.models import Alerta

class CalcularNivelTests(SimpleTestCase):
    def test_casos_calculados_a_mano(self):
        casos = [("TEMP", 95, 75), ("RPM", 600, 0), ("RPM", 599, 0), ("RPM", 3000, 100), ("RPM", 5000, 100),
                 ("RPM", 1800, 50), ("VELOCIDAD", 2.5, 3), ("O2", 0.5, 50), ("FUEL", 50, 50), ("OIL", 3, 50),
                 ("MAF", 5, 50), ("ECT", 90, 90), ("MAP", 1.0, 1), ("DESCONOCIDO", 42.4, 42)]
        for tipo, valor, esperado in casos:
            self.assertEqual(calcular_nivel(tipo, valor), esperado, (tipo, valor))

class SimulacionTests(SimpleTestCase):
    def test_limites_del_valor_simulado(self):
        minimos = {"MAF": 2.0, "O2": 0.1, "ECT": 75.0, "MAP": 0.5, "RPM": 650.0, "VELOCIDAD": 0.0, "TEMP": 75.0, "OIL": 1.0, "FUEL": 15.0, None: 0.0}
        maximos = {"MAF": 12.0, "O2": 1.2, "ECT": 130.0, "MAP": 1.2, "RPM": 4450.0, "VELOCIDAD": 120.0, "TEMP": 130.0, "OIL": 6.0, "FUEL": 95.0, None: 100.0}
        for azar, esperados in ((0.0, minimos), (0.9999999, maximos)):
            with mock.patch("api.obd2.random.random", return_value=azar):
                for tipo, esperado in esperados.items():
                    valor = valor_simulado(tipo)
                    self.assertIsInstance(valor, float)
                    self.assertEqual(valor, esperado, tipo)

    def test_unidades_y_redondeo(self):
        self.assertEqual([unidad_de(t) for t in ("RPM", "VELOCIDAD", "TEMP", "ECT", "MAF", "O2", "OIL", "FUEL", "MAP", None)],
                         ["rpm", "km/h", "°C", "°C", "g/s", "V", "bar", "%", "", ""])
        self.assertEqual((redondear(2.25), redondear_dos(0.125)), (2.3, 0.13))
        self.assertEqual([estado_por_nivel(n) for n in (39, 40, 69, 70)], ["OK", "ADVERTENCIA", "ADVERTENCIA", "FALLA"])

class AlertasTests(TestCase):
    def test_crea_alerta_de_falla_y_notifica(self):
        with self.assertLogs("autosen.observador", level="WARNING"):
            a = crear_alerta_si_corresponde(4, "RPM del motor", "RPM", 2345.0, 73, " rpm")
        self.assertEqual((a.tipo, a.mensaje, a.leida, a.fecha_alerta.microsecond),
                         ("falla", "Falla crítica en RPM del motor: nivel 73% (2345.0 rpm).", 0, 0))

    def test_advertencia_y_nivel_bajo(self):
        a = crear_alerta_si_corresponde(4, "O2", "O2", 0.5, 40, "")
        self.assertEqual((a.tipo, a.mensaje), ("advertencia", "Advertencia en O2: nivel 40% (0.5)."))
        self.assertIsNone(crear_alerta_si_corresponde(4, "O2", "O2", 0.1, 39, ""))
        self.assertEqual(Alerta.objects.count(), 1)
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test api.tests.test_obd2_logica -v 2`. Expected: `ImportError`.

- [ ] **Step 3: Implementar**

- `calcular_nivel`: `if valor <= min: 0`; `if valor >= max: 100`; si no, `redondear_java((valor - min) / (max - min) * 100)`.
- `valor_simulado`: los casos que en Java usan `Math.round` devuelven `float(redondear_java(...))`.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 5 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Lógica OBD2: nivel, simulación y alertas"`.

---

### Task 10: API de la app (ApiController)

**Files:**
- Create: `api/views.py` (se importa `random` como módulo), `api/urls.py`
- Test: `api/tests/test_api_cliente.py`

**Interfaces:**
- Consumes: `parametro`, `metodos`, `verificar_contrasena`, `cifrar_contrasena`, `crear_sensores_por_defecto` y `entero_java`.
- Produces:
  - Rutas `/api/auth/register`, `/api/auth/login`, `/api/cliente/<str:correo>`, `/api/vehiculos/crear` y `/api/bluetooth/simular`. Todas `@csrf_exempt`, públicas (F1), y ninguna inicia sesión.
  - Helpers `cliente_info(c) -> dict` y `sensor_info(s) -> dict`.
  - `datos_cliente_json(correo: str) -> dict`, que reutiliza `simular`.
  - `simular` usa `random.randint(-6, 25)`, el equivalente a `nextInt(-6, 26)`.

Métodos Java que se reproducen: `J/java/.../controller/ApiController.java:44-257`. En `datosCliente`, los vehículos y sensores van ordenados por PK.

- [ ] **Step 1: Escribir las pruebas**

```python
# api/tests/test_api_cliente.py
from unittest import mock
from django.test import Client, TestCase
from core.models import Cliente, Sensor, Vehiculo
from core.tests.fabricas import CLAVE, crear_cliente, crear_sensor, crear_vehiculo

def info(c):
    return {"idCliente": c.pk, "nombreCliente": c.nombre_cliente, "apellidoCliente": c.apellido_cliente, "correo": c.correo, "estado": c.estado}

class AuthApiTests(TestCase):
    def test_registro(self):
        r = self.client.post("/api/auth/register", {"nombre": " Ana ", "apellido": " Paz ", "correo": " ana@test.com ", "contrasena": "x1"})
        ana = Cliente.objects.get(correo="ana@test.com")
        self.assertEqual(r.json(), {"ok": True, "mensaje": "Cuenta creada correctamente.", "cliente": info(ana)})
        self.assertEqual(list(r.json()), ["ok", "mensaje", "cliente"])
        self.assertEqual(list(r.json()["cliente"]), ["idCliente", "nombreCliente", "apellidoCliente", "correo", "estado"])
        self.assertEqual(ana.nombre_cliente, "Ana")

    def test_registro_duplicado_y_parametro_faltante(self):
        crear_cliente()
        r = self.client.post("/api/auth/register", {"nombre": "a", "apellido": "b", "correo": "joel@test.com", "contrasena": "x"})
        self.assertEqual(r.json(), {"ok": False, "mensaje": "El correo ya está registrado."})
        sin_clave = Client(raise_request_exception=False).post("/api/auth/register", {"nombre": "a", "apellido": "b", "correo": "z@z.co"})
        self.assertEqual(sin_clave.status_code, 400)

    def test_login(self):
        c = crear_cliente()
        bloqueado = crear_cliente(correo="b@test.com", estado="bloqueado")
        ok = self.client.post("/api/auth/login", {"correo": "joel@test.com", "contrasena": CLAVE})
        self.assertEqual(ok.json(), {"ok": True, "mensaje": "Bienvenido.", "cliente": info(c)})
        self.assertNotIn("cliente_id", self.client.session)
        mal = self.client.post("/api/auth/login", {"correo": "joel@test.com", "contrasena": "mala"})
        self.assertEqual(mal.json(), {"ok": False, "mensaje": "Correo o contraseña incorrectos."})
        b = self.client.post("/api/auth/login", {"correo": bloqueado.correo, "contrasena": CLAVE})
        self.assertEqual(b.json(), {"ok": False, "mensaje": "Tu cuenta está bloqueada. Contacta al administrador."})

    def test_sin_csrf_y_json_utf8_sin_escapar(self):  # F1 + Review Focus 3
        r = Client(enforce_csrf_checks=True).post("/api/auth/login", {"correo": "x@x.co", "contrasena": "y"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("contraseña".encode(), r.content)

class DatosClienteTests(TestCase):
    def test_estructura_completa(self):
        c = crear_cliente()
        v = crear_vehiculo(c, modelo="2018-01-01")
        s = [crear_sensor(v, nivel=n, tipo=t) for n, t in ((10, "MAF"), (50, "O2"), (80, "ECT"))]
        r = self.client.get("/api/cliente/JOEL@test.com")
        self.assertEqual(r.json(), {"ok": True, "cliente": info(c), "vehiculos": [{
            "idVehiculo": v.pk, "nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": "2018", "color": "Negro",
            "placa": "ABC123", "tipoPlaca": "particular",
            "sensores": [{"idSensor": x.pk, "nombreSensor": x.nombre_sensor, "tipoSensor": x.tipo_sensor,
                          "tipoDano": x.tipo_dano, "nivel": x.nivel} for x in s]}],
            "estadisticas": {"totalVehiculos": 1, "totalSensores": 3, "sensoresOk": 1, "advertencias": 1, "fallas": 1}})

    def test_modelo_vacio_y_cliente_inexistente(self):
        crear_vehiculo(crear_cliente(), modelo=None)
        self.assertEqual(self.client.get("/api/cliente/joel@test.com").json()["vehiculos"][0]["modelo"], "")
        self.assertEqual(self.client.get("/api/cliente/nadie@test.com").json(), {"ok": False, "mensaje": "Cliente no encontrado."})

class CrearVehiculoApiTests(TestCase):
    BASE = {"correo": "joel@test.com", "nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": " 2020 ",
            "color": "Negro", "placa": " abc123 ", "tipoPlaca": "particular"}

    def setUp(self):
        crear_cliente()

    def test_crea_con_valores_recortados(self):
        r = self.client.post("/api/vehiculos/crear", self.BASE)
        self.assertEqual(r.json(), {"ok": True, "mensaje": "Vehículo registrado correctamente."})
        v = Vehiculo.objects.get()
        self.assertEqual((v.modelo, v.placa, v.sensores.count()), ("2020-01-01", "ABC123", 4))

    def test_mensajes_en_orden(self):
        crear_vehiculo(Cliente.objects.get(), placa="DUP111")
        casos = [({"correo": "nadie@test.com"}, "Cliente no encontrado."), ({"color": " "}, "Todos los campos son obligatorios."),
                 ({"modelo": "1989"}, "El año debe estar entre 1990 y 2030."), ({"modelo": "abc"}, "El año debe ser un número válido."),
                 ({"placa": "dup111"}, "Ya existe un vehículo registrado con esa placa."),
                 ({"placa": "AB1234"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")]
        for cambio, mensaje in casos:
            with self.subTest(cambio):
                self.assertEqual(self.client.post("/api/vehiculos/crear", {**self.BASE, **cambio}).json(), {"ok": False, "mensaje": mensaje})

class SimularApiTests(TestCase):
    def test_simular_suma_delta_con_limites(self):
        v = crear_vehiculo(crear_cliente())
        alto, bajo = crear_sensor(v, nivel=90), crear_sensor(v, nivel=3)
        with mock.patch("api.views.random.randint", side_effect=[25, -6]) as azar:
            r = self.client.post("/api/bluetooth/simular", {"correo": "joel@test.com"})
        azar.assert_called_with(-6, 25)
        self.assertEqual([s["nivel"] for s in r.json()["vehiculos"][0]["sensores"]], [100, 0])
        self.assertEqual(Sensor.objects.get(pk=alto.pk).nivel, 100)
        self.assertEqual(self.client.post("/api/bluetooth/simular", {"correo": "x@x.co"}).json(),
                         {"ok": False, "mensaje": "Cliente no encontrado."})
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test api.tests.test_api_cliente -v 2`. Expected: 404 / FAIL.

- [ ] **Step 3: Implementar**

- El registro comprueba el duplicado con `correo__iexact` sobre el correo **sin recortar** y guarda los valores recortados, como en Java.
- En `crearVehiculo`, el orden de comprobaciones es: cliente, vacíos, año (`entero_java(modelo.strip())`), duplicado y formato.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 9 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"API de la app: auth, datos del cliente, crear vehículo y simulación"`.

---

### Task 11: API OBD2 (Obd2Controller)

**Files:**
- Modify: `api/views.py`, `api/urls.py`
- Test: `api/tests/test_api_obd2.py`

**Interfaces:**
- Consumes: todo `api/obd2.py` (Task 9), `cliente_requerido`, `fecha_java`, `parametro` y `metodos`.
- Produces:
  - Rutas `/api/obd2/lecturas`, `/api/obd2/vehiculo/<int:id>/elm` (GET y POST en la misma vista), `/api/obd2/historial/<int:id_vehiculo>`, `/api/obd2/alertas/<int:id_vehiculo>`, `/api/obd2/ultima/<int:id_vehiculo>` y `/api/obd2/conectar`. La última exige `@cliente_requerido`, que deja `@csrf_exempt` por fuera.
  - En `guardar_lectura`, `sufijo_unidad = "" if unidad is None else " " + unidad`. En `conectar`, `sufijo_unidad = " " + unidad`.

Métodos Java que se reproducen: `J/java/.../controller/Obd2Controller.java:46-296`. Consultas:

- `historial`: todas las lecturas del vehículo, de la más reciente a la más antigua.
- `ultima`: las 30 más recientes.
- `alertas`: las 50 alertas más recientes de **todo el sistema**, filtradas después por vehículo.
- `conectar`: el primer vehículo del cliente por PK.

- [ ] **Step 1: Escribir las pruebas**

```python
# api/tests/test_api_obd2.py
from datetime import datetime
from unittest import mock
from django.test import Client, TestCase
from core.models import Alerta, Lectura
from core.tests.fabricas import crear_alerta, crear_cliente, crear_lectura, crear_sensor, crear_vehiculo, login_cliente

class LecturasTests(TestCase):
    def setUp(self):
        self.v = crear_vehiculo(crear_cliente())

    def enviar(self, **datos):
        base = {"idVehiculo": self.v.pk, "nombreSensor": "Temperatura refrigerante", "tipoSensor": "TEMP", "valor": "95"}
        return self.client.post("/api/obd2/lecturas", {**base, **datos})

    def test_guardar_lectura_con_falla(self):
        r = self.enviar(unidad="°C")
        l = Lectura.objects.get()
        self.assertEqual(r.json(), {"ok": True, "mensaje": "Lectura registrada.", "idLectura": l.pk, "nivel": 75, "estado": "FALLA"})
        self.assertEqual((l.valor, l.unidad, l.fecha_lectura.microsecond), (95.0, "°C", 0))
        self.assertEqual(Alerta.objects.get().mensaje, "Falla crítica en Temperatura refrigerante: nivel 75% (95.0 °C).")

    def test_sin_unidad(self):  # Review Focus 5
        self.enviar()
        self.assertEqual(Lectura.objects.get().unidad, "")
        self.assertEqual(Alerta.objects.get().mensaje, "Falla crítica en Temperatura refrigerante: nivel 75% (95.0).")

    def test_unidad_vacia(self):  # Review Focus 5
        self.enviar(unidad="")
        self.assertEqual(Alerta.objects.get().mensaje, "Falla crítica en Temperatura refrigerante: nivel 75% (95.0 ).")

    def test_advertencia_y_sin_alerta(self):
        self.assertEqual(self.enviar(tipoSensor="RPM", valor="1800").json()["estado"], "ADVERTENCIA")
        self.assertEqual(Alerta.objects.get().tipo, "advertencia")
        self.assertEqual(self.enviar(valor="80").json()["estado"], "OK")
        self.assertEqual(Alerta.objects.count(), 1)

    def test_errores(self):
        self.assertEqual(self.enviar(idVehiculo=9999).json(), {"ok": False, "mensaje": "Vehículo no encontrado."})
        self.assertEqual(Client(raise_request_exception=False).post("/api/obd2/lecturas", {"idVehiculo": self.v.pk,
                         "nombreSensor": "x", "tipoSensor": "TEMP", "valor": "abc"}).status_code, 400)

class ElmTests(TestCase):
    def test_guardar_y_consultar_elm(self):
        v = crear_vehiculo(crear_cliente())
        url = f"/api/obd2/vehiculo/{v.pk}/elm"
        self.assertEqual(self.client.get(url).json(), {"ok": True, "idVehiculo": v.pk, "elmMac": None, "conectado": False,
                                                       "mensaje": "No hay un ELM327 asociado a este vehículo."})
        r = self.client.post(url, {"elmMac": "00:1D:A5:68:98:8B"})
        self.assertEqual(r.json(), {"ok": True, "mensaje": "ELM327 guardado para reconexión futura.", "elmMac": "00:1D:A5:68:98:8B"})
        self.assertEqual(self.client.get(url).json()["mensaje"], "ELM327 registrado. La conexión Bluetooth debe realizarse desde Android.")
        for metodo in ("get", "post"):
            r = getattr(self.client, metodo)("/api/obd2/vehiculo/9999/elm", {"elmMac": "x"})
            self.assertEqual(r.json(), {"ok": False, "mensaje": "Vehículo no encontrado."})

class ConsultasTests(TestCase):
    def setUp(self):
        self.v = crear_vehiculo(crear_cliente())

    def test_historial_y_ultima(self):
        primera = crear_lectura(self.v.pk, fecha=datetime(2026, 10, 21, 19, 45, 0), nombre_sensor="A", tipo_sensor="RPM", valor=900.0, unidad="rpm", nivel=13)
        for i in range(30):
            crear_lectura(self.v.pk, nombre_sensor=f"S{i}")
        historial = self.client.get(f"/api/obd2/historial/{self.v.pk}").json()["lecturas"]
        self.assertEqual(len(historial), 31)
        self.assertEqual(historial[-1], {"idLectura": primera.pk, "nombreSensor": "A", "tipoSensor": "RPM", "valor": 900.0,
                                         "unidad": "rpm", "nivel": 13, "estado": "OK", "fechaLectura": "2026-10-21T19:45"})
        ultima = self.client.get(f"/api/obd2/ultima/{self.v.pk}").json()
        self.assertEqual((ultima["ok"], len(ultima["lecturas"]), ultima["lecturas"][0]["nombreSensor"]), (True, 30, "S29"))
        self.assertEqual(list(ultima["lecturas"][0]), ["nombreSensor", "tipoSensor", "valor", "unidad", "nivel", "estado", "fechaLectura"])

    def test_alertas_solo_miran_las_ultimas_50_globales(self):
        propia = crear_alerta(self.v.pk, leida=1)
        r = self.client.get(f"/api/obd2/alertas/{self.v.pk}").json()
        self.assertEqual(list(r["alertas"][0]), ["idAlerta", "nombreSensor", "tipoSensor", "valor", "nivel", "tipo", "mensaje", "leida", "fechaAlerta"])
        self.assertEqual((r["alertas"][0]["idAlerta"], r["alertas"][0]["leida"]), (propia.pk, True))
        for _ in range(50):
            crear_alerta(self.v.pk + 1000)
        self.assertEqual(self.client.get(f"/api/obd2/alertas/{self.v.pk}").json(), {"ok": True, "alertas": []})

class ConectarTests(TestCase):
    def test_requiere_sesion_de_cliente(self):
        self.assertRedirects(self.client.post("/api/obd2/conectar"), "/login", fetch_redirect_response=False)

    def test_sin_vehiculos(self):
        login_cliente(self.client, crear_cliente())
        self.assertEqual(self.client.post("/api/obd2/conectar").json(), {"ok": False, "conectado": False,
                         "mensaje": "Primero registra un vehículo para poder conectar el escáner ELM327."})

    def test_conecta_el_primer_vehiculo(self):
        c = crear_cliente()
        v1, v2 = crear_vehiculo(c, placa="ABC123"), crear_vehiculo(c, placa="DEF456")
        crear_sensor(v1, tipo="MAF", nombre="MAF"); crear_sensor(v1, tipo="ECT", nombre="ECT"); crear_sensor(v2, tipo="O2")
        cliente_http = Client(enforce_csrf_checks=True)
        login_cliente(cliente_http, c)
        with mock.patch("api.obd2.random.random", return_value=0.0):
            r = cliente_http.post("/api/obd2/conectar")
        self.assertEqual(r.json(), {"ok": True, "conectado": True, "idVehiculo": v1.pk, "vehiculo": "Onix ABC123",
            "elmMac": "ELM327-SIM-ABC123",
            "mensaje": "Escáner ELM327 conectado por Bluetooth. Recibiendo datos del vehículo en tiempo real.",
            "lecturas": [{"nombreSensor": "MAF", "tipoSensor": "MAF", "valor": 2.0, "unidad": "g/s", "nivel": 0, "estado": "OK"},
                         {"nombreSensor": "ECT", "tipoSensor": "ECT", "valor": 75.0, "unidad": "°C", "nivel": 75, "estado": "FALLA"}]})
        self.assertEqual(Lectura.objects.count(), 2)
        self.assertEqual(Alerta.objects.get().mensaje, "Falla crítica en ECT: nivel 75% (75.0 °C).")
```

Nota para la prueba: `crear_lectura` y `crear_alerta` aceptan `**campos`, entre ellos `leida`. `login_cliente` ya envía el token CSRF (Task 7).

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test api.tests.test_api_obd2 -v 2`. Expected: FAIL.

- [ ] **Step 3: Implementar** las vistas.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 11 pruebas OK. Run también `.venv/Scripts/python manage.py test`. Expected: OK.

- [ ] **Step 5: Commit** — mensaje `"API OBD2: lecturas, ELM, historial, alertas y conexión simulada"`.

---

### Task 12: Panel admin: dashboard, clientes y administradores

**Files:**
- Modify: `panel/views.py`, `panel/urls.py`
- Create: plantillas convertidas `templates/admin/dashboard.html`, `crear-cliente.html`, `editar-cliente.html`, `crear-usuario.html` y `editar-usuario.html`. `#authentication.name` pasa a `{{ admin_correo }}`.
- Test: `panel/tests/test_clientes_usuarios.py`

**Interfaces:**
- Consumes: `admin_requerido`, `parametro`, `metodos` y `cifrar_contrasena`.
- Produces: rutas `admin_index` (`"admin"`), `admin_nosotros`, `admin_cliente_estado`, `admin_cliente_nuevo`, `admin_cliente_crear`, `admin_cliente_editar`, `admin_cliente_eliminar`, `admin_usuario_nuevo`, `admin_usuario_crear`, `admin_usuario_editar` y `admin_usuario_eliminar`, más el helper `cargar_totales(contexto: dict) -> None`.

Métodos Java que se reproducen, de `AdminController.java`:

- `index` y `cargarTotales` (79-87, 840-854)
- `nosotrosPage` (94)
- `cambiarEstado` (105)
- clientes (129-177, 236-280)
- usuarios (744-838)

`eliminarCliente` borra cada vehículo con `vehiculo.delete()` (F3) y después el cliente.

- [ ] **Step 1: Escribir las pruebas**

```python
# panel/tests/test_clientes_usuarios.py
from django.test import Client, TestCase
from core.models import Cliente, Lectura, Usuario, Vehiculo
from core.tests.fabricas import CLAVE, crear_cliente, crear_lectura, crear_sensor, crear_usuario, crear_vehiculo, login_admin, login_cliente

class AccesoTests(TestCase):
    def test_sin_sesion_y_con_sesion_de_cliente(self):  # F2
        self.assertRedirects(self.client.get("/admin"), "/admin/login", fetch_redirect_response=False)
        login_cliente(self.client, crear_cliente())
        for url in ("/admin", "/admin/cliente/nuevo", "/admin/usuario/nuevo"):
            self.assertRedirects(self.client.get(url), "/admin/login", fetch_redirect_response=False)

class Base(TestCase):
    def setUp(self):
        self.admin = crear_usuario()
        login_admin(self.client, self.admin)

class DashboardAdminTests(Base):
    def test_totales_con_nivel_nulo(self):  # Review Focus 2
        v = crear_vehiculo(crear_cliente())
        for n in (10, 45, 75, None):
            crear_sensor(v, nivel=n)
        r = self.client.get("/admin")
        self.assertEqual([r.context[k] for k in ("totalSensores", "totalFallas", "totalAdvertencias", "sensoresOk", "totalClientes")], [4, 1, 1, 2, 1])
        self.assertContains(r, "admin@autosen.com")
        self.assertContains(r, "0%")

class ClientesTests(Base):
    def test_crear_cliente(self):
        r = self.client.post("/admin/cliente/crear", {"nombre": " Ana ", "apellido": "Paz", "correo": " ana@test.com ", "contrasena": "secreto"})
        self.assertRedirects(r, "/admin", fetch_redirect_response=False)
        ana = Cliente.objects.get(correo="ana@test.com")
        self.assertEqual((ana.nombre_cliente, ana.estado, ana.contrasena[:7]), ("Ana", "activo", "$2a$10$"))

    def test_validaciones_crear(self):
        crear_cliente()
        base = {"nombre": "A", "apellido": "B", "correo": "a@b.co", "contrasena": "secreto"}
        for cambio, mensaje in (({"nombre": " "}, "Todos los campos son obligatorios."), ({"correo": "abco"}, "El correo no tiene un formato válido."),
                                ({"contrasena": "12345"}, "La contraseña debe tener al menos 6 caracteres."),
                                ({"correo": "JOEL@test.com"}, "Ya existe un cliente con ese correo.")):
            self.assertContains(self.client.post("/admin/cliente/crear", {**base, **cambio}), mensaje)

    def test_editar_cliente(self):
        c, otro = crear_cliente(), crear_cliente(correo="otro@test.com")
        url = f"/admin/cliente/{c.pk}/editar"
        clave_antes = c.contrasena
        self.client.post(url, {"nombre": "J", "apellido": "M", "correo": "joel@test.com", "contrasena": ""})
        c.refresh_from_db()
        self.assertEqual(c.contrasena, clave_antes)
        self.assertContains(self.client.post(url, {"nombre": "J", "apellido": "M", "correo": "otro@test.com"}), "Ya existe un cliente con ese correo.")
        self.assertContains(self.client.post(url, {"nombre": "J", "apellido": "M", "correo": "joel@test.com", "contrasena": "123"}),
                            "La contraseña debe tener al menos 6 caracteres.")

    def test_cambiar_estado(self):
        c = crear_cliente()
        url = f"/admin/cliente/{c.pk}/estado"
        self.client.post(url); c.refresh_from_db(); self.assertEqual(c.estado, "bloqueado")
        self.client.post(url); c.refresh_from_db(); self.assertEqual(c.estado, "activo")
        Cliente.objects.filter(pk=c.pk).update(estado=None)
        self.client.post(url); c.refresh_from_db(); self.assertEqual(c.estado, "activo")

    def test_eliminar_cliente_con_vehiculos_y_lecturas(self):  # F3
        c = crear_cliente(); v = crear_vehiculo(c); crear_sensor(v); crear_lectura(v.pk)
        self.assertRedirects(self.client.post(f"/admin/cliente/{c.pk}/eliminar"), "/admin", fetch_redirect_response=False)
        self.assertEqual((Cliente.objects.count(), Vehiculo.objects.count(), Lectura.objects.count()), (0, 0, 1))

    def test_id_inexistente_da_500(self):
        c = Client(raise_request_exception=False)
        login_admin(c, self.admin)
        self.assertEqual(c.get("/admin/cliente/9999/editar").status_code, 500)

class UsuariosTests(Base):
    def test_crear_con_rol_libre_y_rol_vacio(self):  # S2
        base = {"nombre": "Ana", "contrasena": "secreto"}
        self.client.post("/admin/usuario/crear", {**base, "correo": "ana@autosen.com", "rol": "SUPERADMIN"})
        self.client.post("/admin/usuario/crear", {**base, "correo": "eva@autosen.com", "rol": " "})
        self.assertEqual([u.rol for u in Usuario.objects.exclude(pk=self.admin.pk)], ["SUPERADMIN", "ADMIN"])
        self.assertContains(self.client.post("/admin/usuario/crear", {**base, "correo": "ADMIN@autosen.com", "rol": "ADMIN"}),
                            "Ya existe un usuario con ese correo.")

    def test_editar_rol_vacio_conserva(self):
        self.client.post(f"/admin/usuario/{self.admin.pk}/editar", {"nombre": "Jefe", "correo": "admin@autosen.com", "rol": ""})
        self.admin.refresh_from_db()
        self.assertEqual((self.admin.nombre, self.admin.rol), ("Jefe", "admin"))

    def test_eliminar(self):
        self.client.post(f"/admin/usuario/{self.admin.pk}/eliminar")  # a sí mismo: no
        self.assertEqual(Usuario.objects.count(), 1)
        otro = crear_usuario(correo="otro@autosen.com")
        self.client.post(f"/admin/usuario/{otro.pk}/eliminar")
        self.assertFalse(Usuario.objects.filter(pk=otro.pk).exists())
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test panel.tests.test_clientes_usuarios -v 2`. Expected: FAIL.

- [ ] **Step 3: Implementar** las vistas y las plantillas. En `admin/dashboard.html`:

- La clase del sensor sale de `{{ s.nivel|estado_nivel:"falla,adv,ok" }}`.
- La etiqueta, de `{{ s.nivel|estado_nivel:"FALLA,ADVERTENCIA,ÓPTIMO" }}`.
- `c.vehiculos.size()` pasa a `c.vehiculos.count`.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 11 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Panel admin: dashboard, clientes y administradores"`.

---

### Task 13: Panel admin: vehículos y sensores

**Files:**
- Modify: `panel/views.py`, `panel/urls.py`
- Create: plantillas convertidas `templates/admin/crear-vehiculo.html`, `editar-vehiculo.html`, `crear-sensor.html` y `editar-sensor.html`
- Test: `panel/tests/test_vehiculos_sensores.py`

**Interfaces:**
- Consumes: igual que la Task 12.
- Produces: rutas `admin_vehiculo_nuevo`, `admin_vehiculo_crear`, `admin_vehiculo_editar`, `admin_vehiculo_eliminar`, `admin_sensor_nuevo`, `admin_sensor_crear`, `admin_sensor_editar` y `admin_sensor_eliminar`.

Métodos Java que se reproducen, de `AdminController.java`:

- `eliminarVehiculo` y `eliminarSensor` (113-124)
- vehículos (182-231, 285-337)
- sensores (342-430), incluido `estadoDesdeNivel`

Al crear un vehículo desde el panel **no** se crean los sensores por defecto, igual que en Java.

- [ ] **Step 1: Escribir las pruebas**

```python
# panel/tests/test_vehiculos_sensores.py
from django.test import Client, TestCase
from core.models import Lectura, Sensor, Vehiculo
from core.tests.fabricas import crear_cliente, crear_lectura, crear_sensor, crear_usuario, crear_vehiculo, login_admin

class Base(TestCase):
    def setUp(self):
        login_admin(self.client, crear_usuario())
        self.cliente = crear_cliente()

class VehiculosAdminTests(Base):
    def datos(self, **cambios):
        return {"clienteId": self.cliente.pk, "nombreVehiculo": " Onix ", "marca": "Chevrolet", "modelo": "", "color": "Negro",
                "placa": " abc-123 ", "tipoPlaca": "particular", "elmMac": "", **cambios}

    def test_crear_sin_sensores_por_defecto(self):
        self.assertRedirects(self.client.post("/admin/vehiculo/crear", self.datos()), "/admin", fetch_redirect_response=False)
        v = Vehiculo.objects.get()
        self.assertEqual((v.nombre_vehiculo, v.modelo, v.placa, v.elm_mac, v.sensores.count()), ("Onix", None, "ABC-123", None, 0))

    def test_validaciones_en_orden(self):
        crear_vehiculo(self.cliente, placa="DUP111")
        for cambio, mensaje in (({"marca": " "}, "Todos los campos obligatorios deben estar completos."),
                                ({"placa": "AB123"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."),
                                ({"placa": "dup111"}, "Ya existe un vehículo con esa placa."),
                                ({"clienteId": 9999}, "Selecciona un cliente válido.")):
            self.assertContains(self.client.post("/admin/vehiculo/crear", self.datos(**cambio)), mensaje)
        c = Client(raise_request_exception=False); login_admin(c, crear_usuario(correo="b@autosen.com"))
        self.assertEqual(c.post("/admin/vehiculo/crear", self.datos(clienteId="")).status_code, 400)

    def test_editar(self):
        v = crear_vehiculo(self.cliente, modelo="2019-01-01", elm_mac="AA:BB")
        otro = crear_cliente(correo="otro@test.com")
        self.client.post(f"/admin/vehiculo/{v.pk}/editar", self.datos(clienteId=otro.pk, modelo=""))
        v.refresh_from_db()
        self.assertEqual((v.modelo, v.elm_mac, v.cliente), ("2019-01-01", None, otro))
        self.client.post(f"/admin/vehiculo/{v.pk}/editar", self.datos(clienteId=""))
        v.refresh_from_db()
        self.assertEqual(v.cliente, otro)

    def test_eliminar_con_lecturas(self):  # F3
        v = crear_vehiculo(self.cliente); crear_sensor(v); crear_lectura(v.pk)
        self.client.post(f"/admin/vehiculo/{v.pk}/eliminar")
        self.assertEqual((Vehiculo.objects.count(), Sensor.objects.count(), Lectura.objects.count()), (0, 0, 1))

class SensoresAdminTests(Base):
    def setUp(self):
        super().setUp()
        self.v = crear_vehiculo(self.cliente)

    def datos(self, **cambios):
        return {"vehiculoId": self.v.pk, "nombreSensor": " Frenos ", "tipoSensor": "Pastillas", "nivel": "75", "tipoDano": "", **cambios}

    def test_crear_con_estado_y_sin_tipo_dano(self):  # F4
        for nivel, estado in (("75", "FALLA"), ("45", "ADVERTENCIA"), ("10", "OK")):
            self.client.post("/admin/sensor/crear", self.datos(nivel=nivel))
        self.assertEqual([(s.nombre_sensor, s.estado, s.tipo_dano) for s in Sensor.objects.all()],
                         [("Frenos", "FALLA", None), ("Frenos", "ADVERTENCIA", None), ("Frenos", "OK", None)])

    def test_validaciones(self):
        for cambio, mensaje in (({"nombreSensor": " "}, "Todos los campos obligatorios deben estar completos."),
                                ({"nivel": "101"}, "El nivel debe estar entre 0 y 100."),
                                ({"vehiculoId": 9999}, "Selecciona un vehículo válido.")):
            self.assertContains(self.client.post("/admin/sensor/crear", self.datos(**cambio)), mensaje)

    def test_editar_y_eliminar(self):
        s = crear_sensor(self.v, nivel=10)
        self.client.post(f"/admin/sensor/{s.pk}/editar", self.datos(nivel="70", tipoDano="Desgaste"))
        s.refresh_from_db()
        self.assertEqual((s.nivel, s.estado, s.tipo_dano), (70, "FALLA", "Desgaste"))
        self.client.post(f"/admin/sensor/{s.pk}/eliminar")
        self.assertEqual(Sensor.objects.count(), 0)
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test panel.tests.test_vehiculos_sensores -v 2`. Expected: FAIL.

- [ ] **Step 3: Implementar** las vistas y las plantillas. En `editarVehiculo`, `clienteId` es opcional (`parametro(..., int, requerido=False)`). El resto de identificadores numéricos son obligatorios.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 7 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Panel admin: vehículos y sensores"`.

---

### Task 14: Reportes: filtros y vistas

**Files:**
- Create: `reportes/filtros.py`, `reportes/views.py`, `reportes/urls.py`
- Create: plantillas convertidas `templates/admin/reportes.html`, `reportes-pdf.html` y `reporte-cliente-pdf.html`. En los badges de los informes imprimibles se usa `estado_informe`.
- Test: `reportes/tests/test_filtros.py`, `reportes/tests/test_vistas.py`

**Interfaces:**
- Consumes: `admin_requerido`, `parametro`, los patrones (Task 5) y `redondear_java`.
- Produces (`reportes/filtros.py`):
  - `normalizar_rango(nivel_min, nivel_max) -> tuple[int | None, int | None]`
  - `filtrar_sensores(sensores, estado_sensor, tipo_sensor, nivel_min, nivel_max) -> list[Sensor]`
  - `filtrar_clientes(clientes, q, estado_cliente, marca, tipo_placa) -> list[Cliente]` (F5)
  - `ordenar_sensores(sensores: list, ordenar_por: str | None) -> list`
  - `peso_estado(estado: str | None) -> int`
  - `sin_tildes(texto: str | None) -> str`: minúsculas y sin marcas diacríticas, vía NFKD.
  - `parametros_filtro(request) -> dict` con las claves `q`, `estadoCliente`, `estadoSensor`, `tipoSensor`, `marca`, `tipoPlaca`, `nivelMin`, `nivelMax` y `ordenarPor`; los números se leen como `int` opcional y el rango ya va normalizado.
- Produces (rutas): `admin_reportes`, `admin_reportes_filtrado`, `admin_reportes_pdf_vista` (`admin/reportes-pdf`) y `admin_reporte_cliente_vista` (`admin/reporte-cliente-pdf/<int:cliente_id>`).

Métodos Java que se reproducen:

- `AdminController.reportes` y `cargarDatosReportes` (99-103, 856-892).
- `ReporteController.listaReportes`, `reporteGeneral` y `reporteCliente`, con los helpers 284-379. `filtrar_clientes` añade el filtro `tipo_placa`, que compara con `sin_tildes(...) == sin_tildes(...)` contra los vehículos del cliente.

Cuidado con dos diferencias que hay que conservar:

- `cargarDatosReportes` ordena `tiposSensor` y `marcas` (distintos, sin vacíos).
- `listaReportes` usa el orden de inserción (`LinkedHashSet`, incluye vacíos que no sean null).

- [ ] **Step 1: Escribir las pruebas**

```python
# reportes/tests/test_filtros.py  (los datos también se usan en test_vistas y en la Task 15)
from django.test import TestCase
from core.tests.fabricas import crear_cliente, crear_sensor, crear_vehiculo
from reportes.filtros import filtrar_clientes, filtrar_sensores, normalizar_rango, ordenar_sensores

def datos_reportes():
    joel = crear_cliente(correo="joel@test.com", nombre="Joel", apellido="Moncaleano")
    ana = crear_cliente(correo="ana@test.com", nombre="Ana", apellido="Paz", estado="bloqueado")
    v1 = crear_vehiculo(joel, placa="EMT262", marca="Chevrolet", tipo_placa="Público")
    v2 = crear_vehiculo(ana, placa="KIA111", nombre="Rio", marca="Kia", tipo_placa="particular")
    s1 = crear_sensor(v1, nivel=10, tipo="MAF", nombre="Sensor MAF")
    s2 = crear_sensor(v1, nivel=50, tipo="O2", nombre="Sensor O2")
    s3 = crear_sensor(v2, nivel=80, tipo="ECT", nombre="Sensor ECT", tipo_dano=None)
    s4 = crear_sensor(v2, nivel=None, tipo="TEST", nombre="Prueba")
    return joel, ana, (s1, s2, s3, s4)

class FiltrosTests(TestCase):
    def setUp(self):
        self.joel, self.ana, (self.s1, self.s2, self.s3, self.s4) = datos_reportes()
        self.sensores = [self.s1, self.s2, self.s3, self.s4]
        self.clientes = [self.joel, self.ana]

    def test_filtrar_sensores(self):
        f = lambda *a: filtrar_sensores(self.sensores, *a)
        self.assertEqual(f("falla", None, None, None), [self.s3])
        self.assertEqual(f("OPTIMO", None, None, None), [self.s1, self.s4])
        self.assertEqual((f(None, "O2", None, None), f(None, "o2", None, None)), ([self.s2], []))
        self.assertEqual(f(None, None, 40, None), [self.s2, self.s3])
        self.assertEqual(f(None, None, None, 50), [self.s1, self.s2])

    def test_filtrar_clientes(self):
        f = lambda *a: filtrar_clientes(self.clientes, *a)
        self.assertEqual([f("emt", None, None, None), f("PAZ", None, None, None), f(None, "BLOQUEADO", None, None),
                          f(None, None, "kia", None)], [[self.joel], [self.ana], [self.ana], [self.ana]])

    def test_tipo_placa_sin_tildes(self):  # F5 + Review Focus 1
        self.assertEqual(filtrar_clientes(self.clientes, None, None, None, "publico"), [self.joel])
        self.assertEqual(filtrar_clientes(self.clientes, None, None, None, "PARTICULAR"), [self.ana])

    def test_ordenar_y_rango(self):
        self.assertEqual(ordenar_sensores(self.sensores, "nivel"), [self.s3, self.s2, self.s1, self.s4])
        self.assertEqual(ordenar_sensores(self.sensores, "estado"), [self.s1, self.s4, self.s2, self.s3])
        self.assertEqual(ordenar_sensores(self.sensores, None), [self.s3, self.s4, self.s1, self.s2])
        self.assertEqual(normalizar_rango(70, 10), (10, 70))
```

```python
# reportes/tests/test_vistas.py
from django.test import Client, TestCase
from core.tests.fabricas import crear_usuario, login_admin
from reportes.tests.test_filtros import datos_reportes

class VistasReportesTests(TestCase):
    def setUp(self):
        login_admin(self.client, crear_usuario())
        self.joel, self.ana, self.sensores = datos_reportes()

    def test_reportes(self):
        r = self.client.get("/admin/reportes")
        self.assertEqual((r.context["tiposSensor"], r.context["marcas"], r.context["tiposPlaca"]),
                         (["ECT", "MAF", "O2", "TEST"], ["Chevrolet", "Kia"], ["particular", "publico"]))
        self.assertEqual((r.context["totalFallas"], r.context["totalAdvertencias"]), (1, 1))
        self.assertEqual([v.placa for v in r.context["vehiculosConFallas"]], ["KIA111"])

    def test_numeros_vacios_son_sin_filtro(self):  # Review Focus 4 + F5
        r = self.client.get("/admin/reportes-filtrado?tipoPlaca=publico&nivelMin=&nivelMax=")
        self.assertEqual((r.status_code, r.context["clientes"], r.context["nivelMin"]), (200, [self.joel], None))
        self.assertEqual(r.context["tiposSensor"], ["MAF", "O2", "ECT", "TEST"])
        self.assertEqual(len(r.context["todosSensores"]), 4)

    def test_rango_invertido(self):
        r = self.client.get("/admin/reportes-filtrado?nivelMin=70&nivelMax=10")
        self.assertEqual((r.context["nivelMin"], r.context["nivelMax"]), (10, 70))

    def test_informes_imprimibles(self):
        r = self.client.get("/admin/reportes-pdf")
        self.assertEqual([r.context[k] for k in ("saludFlota", "sensoresOptimos", "sensoresAdvertencia", "sensoresFalla")], [50, 2, 1, 1])
        self.assertEqual(len(r.context["alertas"]), 2)
        self.assertTrue(r.context["reporteId"].startswith("RPT-"))
        self.assertContains(self.client.get(f"/admin/reporte-cliente-pdf/{self.joel.pk}"), "EMT262")
        c = Client(raise_request_exception=False); login_admin(c, crear_usuario(correo="b@autosen.com"))
        self.assertEqual(c.get("/admin/reporte-cliente-pdf/9999").status_code, 500)

    def test_requiere_admin(self):
        self.assertRedirects(Client().get("/admin/reportes"), "/admin/login", fetch_redirect_response=False)
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test reportes -v 2`. Expected: `ImportError`.

- [ ] **Step 3: Implementar.** En `reportes.html`, los `th:selected` del tipo `'activo'.equals(estadoCliente)` pasan a `{% if estadoCliente == "activo" %}selected{% endif %}`. Los botones "PDF filtrado" y "Excel filtrado" conservan `formaction` con `{% url %}`.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 9 pruebas OK.

- [ ] **Step 5: Commit** — mensaje `"Reportes: filtros (con tipo de placa), vistas e informes imprimibles"`.

---

### Task 15: Exportaciones CSV, Excel y PDF

**Files:**
- Create: `reportes/exportar.py`
- Modify: `reportes/views.py`, `reportes/urls.py`
- Test: `reportes/tests/test_exportar.py`

**Interfaces:**
- Consumes: `reportes/filtros.py` y `parametros_filtro` (Task 14), los patrones y `texto_java`.
- Produces:
  - `datos_pdf_general(params: dict) -> tuple[list[Cliente], list[Sensor]]` (F5): `filtrar_clientes` con `q`, `estadoCliente`, `marca` y `tipoPlaca`; `filtrar_sensores` con el estado, el tipo y el rango.
  - `csv_reporte(tipo: str) -> str`
  - `excel_reporte(clientes, sensores) -> bytes`
  - `pdf_general(clientes, sensores) -> bytes`
  - `pdf_cliente(cliente) -> bytes`
  - Rutas `admin_reportes_csv` (`admin/reportes/csv/<str:tipo>`), `admin_reportes_excel`, `admin_reportes_pdf` y `admin_reportes_cliente_pdf` (`admin/reportes/cliente/<int:id>/pdf`).

Métodos Java que se reproducen:

- `AdminController.exportarCsv` (523-577), con las líneas `printf` literales, `texto_java` para los null y separador `\r\n`.
- `ReporteController.exportarExcel` (195-279) más el filtro `tipoPlaca`.
- `AdminController.exportarPdfCompleto` y `exportarPdfCliente` (432-521), con los helpers de PDF 582-739, la paleta (69-75) y el logo `static/images/logo-autosen.png` si existe.

- [ ] **Step 1: Escribir las pruebas**

```python
# reportes/tests/test_exportar.py
from io import BytesIO
from openpyxl import load_workbook
from django.test import TestCase
from core.models import Cliente
from core.tests.fabricas import crear_cliente, crear_usuario, crear_vehiculo, login_admin
from reportes.exportar import datos_pdf_general
from reportes.tests.test_filtros import datos_reportes

class ExportarTests(TestCase):
    def setUp(self):
        login_admin(self.client, crear_usuario())
        self.joel, self.ana, (self.s1, self.s2, self.s3, self.s4) = datos_reportes()

    def test_csv_clientes(self):
        r = self.client.get("/admin/reportes/csv/clientes")
        self.assertEqual((r["Content-Type"], r["Content-Disposition"]), ("text/csv; charset=UTF-8", "attachment; filename=reporte-clientes.csv"))
        self.assertEqual(r.content.decode(), f"ID,Nombre,Correo,Estado,Vehiculos\r\n{self.joel.pk},Joel Moncaleano,joel@test.com,activo,1\r\n"
                                             f"{self.ana.pk},Ana Paz,ana@test.com,bloqueado,1\r\n")

    def test_csv_fallas_bloqueados_y_desconocido(self):
        self.s4.delete()  # con nivel NULL Java falla (PENDIENTES 18)
        self.assertEqual(self.client.get("/admin/reportes/csv/fallas").content.decode(),
                         "Vehiculo,Placa,Cliente,Sensor,Nivel,Tipo Dano\r\nRio,KIA111,Ana,Sensor ECT,80,-\r\n")
        self.assertEqual(self.client.get("/admin/reportes/csv/bloqueados").content.decode(), "Nombre,Correo,Vehiculos\r\nAna Paz,ana@test.com,1\r\n")
        r = self.client.get("/admin/reportes/csv/otro")
        self.assertEqual((r.status_code, r.content), (200, b""))

    def test_csv_sensores(self):
        self.s4.delete()  # con nivel NULL Java falla (PENDIENTES 18)
        self.assertEqual(self.client.get("/admin/reportes/csv/sensores").content.decode(),
                         "Sensor,Tipo,Nivel,Estado,Vehiculo,Cliente\r\nSensor MAF,MAF,10,OK,Onix,Joel\r\n"
                         "Sensor O2,O2,50,Advertencia,Onix,Joel\r\nSensor ECT,ECT,80,Falla,Rio,Ana\r\n")

    def test_csv_estado_null(self):  # Review Focus 1
        Cliente.objects.filter(pk=self.ana.pk).update(estado=None)
        self.assertIn(",ana@test.com,null,1\r\n", self.client.get("/admin/reportes/csv/clientes").content.decode())

    def test_excel(self):
        r = self.client.get("/admin/reportes/excel?tipoPlaca=publico&nivelMin=")
        self.assertEqual(r["Content-Disposition"], "attachment; filename=reporte-autosen.xlsx")
        wb = load_workbook(BytesIO(r.content))
        self.assertEqual(wb.sheetnames, ["Clientes", "Sensores", "Vehículos con fallas", "Clientes bloqueados"])
        filas = lambda hoja: [list(f) for f in wb[hoja].iter_rows(values_only=True)]
        self.assertEqual(filas("Clientes"), [["ID", "Nombre", "Correo", "Estado", "Vehículos"], [self.joel.pk, "Joel Moncaleano", "joel@test.com", "activo", 1]])
        self.assertEqual(filas("Sensores")[0], ["Sensor", "Tipo", "Vehículo", "Cliente", "Nivel", "Estado", "Diagnóstico"])
        self.assertEqual(filas("Sensores")[2], ["Sensor O2", "O2", "Onix", "Joel Moncaleano", 50, "ADVERTENCIA", "Falla en flujo de aire"])
        self.assertEqual(filas("Vehículos con fallas")[1], ["Rio", "KIA111", "Ana Paz"])
        self.assertEqual(filas("Clientes bloqueados")[1], ["Ana Paz", "ana@test.com", 1])

    def test_seleccion_del_pdf_respeta_todos_los_filtros(self):  # F5
        params = {"q": "paz", "estadoCliente": None, "marca": "Kia", "tipoPlaca": "particular", "estadoSensor": "falla",
                  "tipoSensor": None, "nivelMin": None, "nivelMax": None}
        self.assertEqual(datos_pdf_general(params), ([self.ana], [self.s3]))

    def test_pdfs(self):
        r = self.client.get("/admin/reportes/pdf?q=&nivelMin=")
        self.assertEqual((r["Content-Type"], r["Content-Disposition"]), ("application/pdf", "attachment; filename=reporte-autosen.pdf"))
        self.assertTrue(r.content.startswith(b"%PDF"))
        r = self.client.get(f"/admin/reportes/cliente/{self.joel.pk}/pdf")
        self.assertEqual(r["Content-Disposition"], "attachment; filename=reporte-joel.pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_pdf_con_texto_unicode(self):  # Review Focus 3
        c = crear_cliente(correo="inigo@test.com", nombre="Íñigo", apellido="Peña")
        crear_vehiculo(c, placa="ÑAN123", nombre="Camión — azul", tipo_placa="Público")
        self.assertTrue(self.client.get(f"/admin/reportes/cliente/{c.pk}/pdf").content.startswith(b"%PDF"))
        self.assertTrue(self.client.get("/admin/reportes/pdf").content.startswith(b"%PDF"))
```

- [ ] **Step 2: Ejecutar y verificar que fallan.** Run: `.venv/Scripts/python manage.py test reportes.tests.test_exportar -v 2`. Expected: `ImportError`.

- [ ] **Step 3: Implementar** con reportlab platypus:

- `SimpleDocTemplate` con `pagesize=landscape(A4)` (general) o `A4` (cliente) y márgenes de 30 pt.
- `Table` con `TableStyle` para la cabecera `AZUL_OSCURO` en Helvetica-Bold 9 blanco, filas alternas `GRIS_CLARO`/blanco y el color del estado según `agregarFila`/`agregarTablaSensores`.
- La paleta se pasa a `colors.Color(r/255, g/255, b/255)`.
- El Excel se arma con `openpyxl.Workbook()`; `crear_fila` escribe `""` cuando el valor es `None`.

- [ ] **Step 4: Ejecutar y verificar que pasan.** Expected: 8 pruebas OK. Run también la suite completa `.venv/Scripts/python manage.py test`. Expected: OK.

- [ ] **Step 5: Commit** — mensaje `"Exportaciones de reportes a CSV, Excel y PDF"`.

---

### Task 16: Documentación y verificación final

**Files:**
- Create: `README.md` (en español): qué es AutoSen y los pasos de §12 (PostgreSQL 18 con winget, `createdb`, `.env` desde `.env.example`, entorno virtual, `migrate`, `importar_mysql`, `runserver 0.0.0.0:8080`, pruebas y la nota del emulador Android).
- Create: `docs/PENDIENTES.md`: los 18 puntos de §13, cada uno con su ubicación en Python (`archivo:función`) y en Java (`Archivo.java:línea`).

- [ ] **Step 1: Escribir `README.md` y `docs/PENDIENTES.md`**

- [ ] **Step 2: Ejecutar la suite completa y el chequeo**

Run: `.venv/Scripts/python manage.py check` y `.venv/Scripts/python manage.py test`
Expected: `no issues` y 133 pruebas OK.

- [ ] **Step 3: Prueba de humo con los datos reales.** La base de desarrollo ya tiene el dump importado en la Task 4.

Arrancar `.venv/Scripts/python manage.py runserver 0.0.0.0:8080` en segundo plano y comprobar:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/
curl -s http://127.0.0.1:8080/api/cliente/millermoncaleano112@gmail.com
curl -s -X POST -d "correo=millermoncaleano112@gmail.com&contrasena=incorrecta" http://127.0.0.1:8080/api/auth/login
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8080/admin
```

Expected:

- `200`
- JSON con `"ok": true`, 3 vehículos y `"estadisticas": {"totalVehiculos": 3, "totalSensores": 9, "sensoresOk": 5, "advertencias": 2, "fallas": 2}`
- `{"ok": false, "mensaje": "Correo o contraseña incorrectos."}`
- `302 http://127.0.0.1:8080/admin/login`

Después, detener el servidor.

- [ ] **Step 4: Commit** — mensaje `"README de instalación y lista de pendientes"`.

---

### Task 17 (no ejecutar ahora): antes de subir a GitHub

Solo cuando el usuario pida subir el proyecto a GitHub:

- [ ] **Step 1:** Preguntar al usuario si basta un commit que borre `referencia/` o si prefiere reescribir el historial para que no aparezca en ningún commit. Ya está en el commit inicial `ebce1d5`.
- [ ] **Step 2:** Aplicar la opción elegida y comprobar con `git ls-files referencia` (no debe devolver nada). En el caso de reescritura, comprobar también con `git log --all -- referencia` (tampoco debe devolver nada).
- [ ] **Step 3:** Confirmar con el usuario antes de hacer `push`.
