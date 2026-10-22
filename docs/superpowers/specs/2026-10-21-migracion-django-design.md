# Migración de AutoSen de Spring Boot a Django — Diseño

Fecha: 2026-10-21
Estado: aprobado en conversación, pendiente de revisión escrita

## 1. Contexto y objetivo

AutoSen es un sistema de monitoreo vehicular (clientes, vehículos, sensores, lecturas OBD2 y alertas) hecho en Spring Boot 3.5 / Java 21 con Thymeleaf, Spring Security, JPA + MySQL, iText y Apache POI. Lo consume además una app Android (repo `jader-posso/AutoSen-AppMovil`, rama `conexion`).

Para la entrega del trimestre en el SENA, el proyecto debe migrarse a Python/Django, y el equipo seguirá desarrollándolo en Django.

**Objetivo:** reproducir en Django la misma lógica, pantallas, rutas y API del proyecto Java. Es una migración, no un rediseño. Solo se corrige la lista cerrada de defectos de la sección 3.

**Criterios de éxito**

1. Cada ruta web y cada endpoint de la API del proyecto Java existe en Django con la misma URL, el mismo método HTTP, los mismos parámetros y el mismo comportamiento, salvo las correcciones de la sección 3.
2. La app Android de la rama `conexion` funciona contra Django sin cambios: login, registro, datos del cliente, crear vehículo, simular, lecturas OBD2, ELM, historial, alertas y última lectura.
3. Los datos de `datos/vehiculos (10).sql` se importan a PostgreSQL, y los usuarios entran con sus contraseñas actuales.
4. Las pantallas se ven igual: mismo HTML y CSS.
5. Hay pruebas automáticas que cubren la lógica, el contrato de la API, los flujos web, los reportes y el importador, y todas pasan contra PostgreSQL.

**Material de referencia** (dentro del repo)

- `referencia/proyecto-java/`: código fuente Java original. Es la fuente de verdad del comportamiento.
- `referencia/app-android/`: `ApiService.kt`, `Models.kt`, `RetrofitClient.kt` y `ApiError.kt` de la app. Definen el contrato de la API.
- `datos/vehiculos (10).sql`: dump de phpMyAdmin con los datos reales. No se versiona.
- `datos/Vehiculos nuevo.sql`: esquema alternativo que el código Java no usa. Se ignora.

## 2. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Enfoque | Django "clásico" y fiel 1:1. Vistas con funciones, una por método de controlador Java. API con `JsonResponse`, sin DRF. Login propio, sin `django.contrib.auth` ni el admin de Django. |
| Versiones | Python 3.15 (el instalado; si Django falla, se pasa a 3.14) y Django 6.1.x |
| Base de datos | PostgreSQL 18, instalado por el usuario. Credenciales en `.env`. Esquema creado por las migraciones de Django. |
| Datos | El comando `importar_mysql` lee el dump de phpMyAdmin y conserva IDs y hashes de contraseñas |
| Errores del proyecto Java | Se conservan, salvo los que bloquean (sección 3). Lo conservado se documenta en `docs/PENDIENTES.md`. |
| Ubicación | `C:\Users\posso\AutoSen-Django`, con git local. No se sube a ningún remoto. |
| Puerto | 8080: la app Android usa `http://10.0.2.2:8080/` |

## 3. Desviaciones respecto al código Java (lista cerrada)

Regla general: **cuando el dump y el código Java no coinciden, manda el código Java**. Fuera de esta lista, cualquier diferencia de comportamiento es un error de la migración.

| ID | Cambio | Motivo |
|---|---|---|
| F1 | `/api/**` es público: no exige sesión ni CSRF. Excepción: `/api/obd2/conectar` exige sesión de cliente. | La app Android no maneja sesión. En Java, `/api/**` exige sesión y la app recibe un 302 a una página HTML. |
| F2 | Sesiones de admin y de cliente independientes. Todo `/admin/**` (salvo `/admin/login`) exige sesión de admin. | En Java ambas cadenas comparten el `SecurityContext` y la de admin solo pide `authenticated()`, así que un cliente logueado entra a `/admin`. |
| F3 | Borrar un vehículo (desde el panel, desde la web del cliente o en cascada al borrar un cliente) no falla. Los sensores se borran en cascada. `lecturas` y `alertas` guardan `Id_vehiculo` sin clave foránea, así que se conservan como historial. | En Java, el `deleteBy…` derivado se ejecuta sin `@Transactional`, y las claves foráneas de `lecturas`/`alertas` en MySQL impiden el borrado. El README pide conservar las lecturas históricas. |
| F4 | `sensores."Tipo_daño"` acepta NULL. | El panel permite dejarlo vacío, pero en MySQL la columna es NOT NULL, lo que da un 500. |
| F5 | El filtro `tipoPlaca` se aplica (clientes con al menos un vehículo de ese tipo; comparación sin distinguir mayúsculas ni tildes) en `/admin/reportes-filtrado`, `/admin/reportes/excel` y `/admin/reportes/pdf`. Además, el PDF general aplica `q` y `marca` con la misma función `filtrar_clientes` que el Excel. | Hoy el filtro solo se repinta en el formulario, y el PDF filtrado ignora parte de los filtros. |
| F6 | Existen las columnas `vehiculo.elm_mac` y `sensores."Estado"` (ambas aceptan NULL). | El código Java las usa y el dump no las tiene. |
| S1 | La protección CSRF de Django queda activa en los formularios web (`{% csrf_token %}`) y desactivada en `/api/**`. | Es el comportamiento por defecto de Django; desactivarla sería debilitar la seguridad a propósito. Para el usuario no cambia nada. |
| S2 | `usuario."Rol"` es texto libre (`max_length=20`). | El panel Java crea ADMIN, SUPERADMIN y SOPORTE, pero en MySQL la columna era `enum('admin')`. |
| S3 | Los estáticos se sirven en `/static/...` (antes `/css/...` y `/js/...`), con WhiteNoise. | Django usa un único prefijo de estáticos, y WhiteNoise los sirve también con `DEBUG=False`. Ningún cliente externo depende de esas URL. |

Lo que **no** se corrige y se documenta en `PENDIENTES.md` (lista inicial en la sección 13).

## 4. Arquitectura y estructura

```
AutoSen-Django/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore                 .venv/, .env, __pycache__/, datos/, staticfiles/
├── README.md                  instalación y ejecución (en español)
├── PATRONES_GOF.md            equivalencias de los patrones en Python
├── autosen/                   settings.py, urls.py, wsgi.py, asgi.py
├── core/
│   ├── models.py              las 6 tablas (sección 5)
│   ├── auth.py                login/logout, decoradores, verificación bcrypt (sección 6)
│   ├── middleware.py          TemaMiddleware (equivale a TemaFilter)
│   ├── context_processors.py  admin_correo (sustituye a #authentication.name)
│   ├── errores.py             handlers 400/403/404/500 con error.html
│   ├── utilidades.py          fecha_java(), funciones de nivel compartidas
│   ├── templatetags/autosen.py filtros de plantilla (sección 10)
│   ├── patrones/              estrategia/, fabrica/, singleton/, observador/ (sección 8)
│   ├── management/commands/importar_mysql.py
│   └── tests/
├── web/      urls.py, views.py, tests/     ← AuthController, DashboardController, VehiculoController, CustomErrorController
├── panel/    urls.py, views.py, tests/     ← AdminController (todo menos reportes y exportaciones)
├── reportes/ urls.py, views.py, exportar.py, filtros.py, tests/  ← ReporteController + exportaciones de AdminController
├── api/      urls.py, views.py, obd2.py, tests/  ← ApiController + Obd2Controller
├── templates/                 paginas/, admin/, error.html (misma estructura que en Java)
├── static/                    css/light-mode.css, js/theme-toggle.js, images/ (vacío, para el logo)
├── referencia/                proyecto-java/, app-android/ (versionado)
├── datos/                     dumps SQL (no versionado)
└── docs/                      PENDIENTES.md, superpowers/specs, superpowers/plans
```

`INSTALLED_APPS`: `django.contrib.sessions`, `django.contrib.staticfiles`, `core`, `web`, `panel`, `reportes`, `api`. No se instalan `django.contrib.auth`, `contenttypes` ni `admin`.

Los repositorios de Spring Data se sustituyen por consultas del ORM dentro de las vistas, con los mismos filtros. Si una consulta se repite en varias vistas, va a una función en el módulo de la app.

## 5. Modelo de datos

Tablas y columnas con **los mismos nombres que en MySQL** (`db_table` y `db_column`; Django las cita en PostgreSQL). Los campos de Python van en `snake_case`.

| Modelo (`db_table`) | Campo Python → columna | Tipo | Nulo | Notas |
|---|---|---|---|---|
| `Usuario` (`usuario`) | `id_usuario` → `Id_usuario` | AutoField PK | | |
| | `nombre` → `Nombre` | Char(50) | no | |
| | `correo` → `Correo` | Char(100) | no | |
| | `contrasena` → `Contrasena` | Char(100) | no | hash bcrypt |
| | `rol` → `Rol` | Char(20) | no | S2 |
| `Cliente` (`cliente`) | `id_cliente` → `Id_cliente` | AutoField PK | | |
| | `nombre_cliente` → `Nombre_cliente` | Char(60) | no | |
| | `apellido_cliente` → `Apellido_cliente` | Char(60) | no | |
| | `contrasena` → `Contrasena` | Char(100) | no | |
| | `correo` → `Correo` | Char(70) | no | |
| | `usuario` → `Id_usuario` | FK Usuario, `PROTECT` | sí | Java no lo usa; se conserva por los datos |
| | `estado` → `Estado` | Char(10), default `'activo'` | sí | valores `activo` / `bloqueado` |
| `Vehiculo` (`vehiculo`) | `id_vehiculo` → `Id_vehiculo` | AutoField PK | | |
| | `cliente` → `Id_cliente` | FK Cliente, `PROTECT` | no | Java borra los vehículos antes que al cliente |
| | `nombre_vehiculo` → `Nombre_vehiculo` | Char(60) | no | |
| | `color` → `Color` | Char(25) | no | |
| | `marca` → `Marca` | Char(50) | no | |
| | `modelo` → `Modelo` | Char(20) | sí | guarda `"AAAA-01-01"` |
| | `placa` → `Placa` | Char(10) | sí | |
| | `tipo_placa` → `Tipo_placa` | Char(60) | no | |
| | `elm_mac` → `elm_mac` | Char(50) | sí | F6 |
| `Sensor` (`sensores`) | `id_sensor` → `Id_sensor` | AutoField PK | | |
| | `nombre_sensor` → `Nombre_sensor` | Char(200) | no | |
| | `tipo_sensor` → `Tipo_sensor` | Char(50) | no | |
| | `tipo_dano` → `Tipo_daño` | Char(90) | **sí** | F4 |
| | `nivel` → `Nivel` | Integer, default 0 | sí | |
| | `estado` → `Estado` | Char(20) | sí | F6 |
| | `vehiculo` → `Id_vehiculo` | FK Vehiculo, `CASCADE` | sí | como el `CascadeType.ALL` de JPA |
| `Lectura` (`lecturas`) | `id_lectura` → `Id_lectura` | AutoField PK | | |
| | `id_vehiculo` → `Id_vehiculo` | Integer **sin FK**, indexado | no | F3 |
| | `nombre_sensor` → `Nombre_sensor` | Char(120) | no | |
| | `tipo_sensor` → `Tipo_sensor` | Char(50) | no | |
| | `valor` → `Valor` | Float | no | |
| | `unidad` → `Unidad` | Char(20), default `''` | no | |
| | `nivel` → `Nivel` | Integer, default 0 | no | |
| | `estado` → `Estado` | Char(20), default `'OK'` | no | |
| | `fecha_lectura` → `Fecha_lectura` | DateTime | no | |
| `Alerta` (`alertas`) | `id_alerta` → `Id_alerta` | AutoField PK | | |
| | `id_vehiculo` → `Id_vehiculo` | Integer **sin FK**, indexado | no | F3 |
| | `nombre_sensor`, `tipo_sensor`, `valor`, `nivel` | como en `Lectura` | no | |
| | `tipo` → `Tipo` | Char(20) | no | `falla` / `advertencia` |
| | `mensaje` → `Mensaje` | Char(255) | no | |
| | `leida` → `Leida` | SmallInteger, default 0 | sí | 0/1 |
| | `fecha_alerta` → `Fecha_alerta` | DateTime | no | |

`related_name`: `Cliente.vehiculos`, `Vehiculo.sensores`. Así `cliente.vehiculos.all()` y `vehiculo.sensores.all()` equivalen a las colecciones JPA.

**Orden:** toda consulta que en Java era `findAll()`, `findBy…` o una colección lazy se ordena explícitamente por la clave primaria ascendente, que es el orden en que la devolvía MySQL. Las que en Java tienen `OrderBy…Desc` mantienen ese orden.

**Comparaciones de texto en la base de datos:** las tablas MySQL usan la intercalación `utf8mb4_general_ci`, que no distingue mayúsculas. Por eso, las búsquedas por igualdad que Java delegaba a la base de datos (`findByCorreo` en clientes y usuarios, `findByPlaca`) usan `__iexact` en Django. Así `Joel@…` sigue encontrando a `joel@…` y la detección de placas duplicadas se comporta igual. Las comparaciones que Java hace en memoria (`equals`, `equalsIgnoreCase`) se traducen literalmente.

**Fechas:** `TIME_ZONE = "America/Bogota"` y `USE_TZ = False`, que equivale a `LocalDateTime`. Las fechas nuevas se guardan sin microsegundos (`datetime.now().replace(microsecond=0)`), igual que el `timestamp` de MySQL.

## 6. Seguridad y sesiones

**Sesiones:** se guardan en base de datos (`django.contrib.sessions`). Hay dos claves independientes: `admin_id` (PK de `usuario`) y `cliente_id` (PK de `cliente`).

- `SESSION_COOKIE_AGE = 1800`, `SESSION_SAVE_EVERY_REQUEST = True` y `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`: 30 minutos de inactividad, igual que Tomcat.
- Al iniciar sesión se rota la clave de sesión (`request.session.cycle_key()`).

**Login de cliente** (`POST /login`, campos `correo` y `contrasena`):

1. Busca el `Cliente` por `correo` exacto. Si no existe, la contraseña no coincide o el estado es `bloqueado`, redirige a `/login?error`.
2. Si todo cuadra, guarda `cliente_id` y redirige a `/dashboard`. Siempre va ahí: se ignora la página que pidió antes, como `defaultSuccessUrl(..., true)`.

**Login de admin** (`POST /admin/login`): igual, contra `Usuario`, sin comprobar estado. Si falla, `/admin/login?error`; si funciona, `/admin`.

**Logout:**

- `/logout` (GET o POST) quita `cliente_id` y redirige a `/login`.
- `/admin/logout` (GET o POST) quita `admin_id` y redirige a `/admin/login`.

**Decoradores (`core/auth.py`):**

- `@cliente_requerido`: sin `cliente_id` válido, redirige a `/login`. Inyecta `request.cliente_correo`, el equivalente a `userDetails.getUsername()`.
- `@admin_requerido`: sin `admin_id` válido, redirige a `/admin/login`. Inyecta `request.admin_correo`.

**Rutas públicas:** `/`, `/nosotros`, `/login`, `/register`, `/error`, `/admin/login`, `/static/**` y `/api/**` excepto `/api/obd2/conectar`. Todo lo demás exige sesión de cliente (rutas web) o de admin (`/admin/**`).

**Contraseñas (`core/auth.py`):**

- `verificar(plano, hash)` usa `bcrypt.checkpw`. Acepta `$2a$`, `$2b$` y `$2y$`; si la librería rechaza `$2y$`, se normaliza a `$2b$` antes de comparar.
- `cifrar(plano)` usa `bcrypt.hashpw(plano, bcrypt.gensalt(rounds=10, prefix=b"2a"))`, idéntico a `BCryptPasswordEncoder()`.

**CSRF:** `CsrfViewMiddleware` activo. Todas las vistas de `api/` llevan `@csrf_exempt` (S1).

**URLs:** sin barra final, exactamente como en Java (`path("login", …)`). `APPEND_SLASH = False`.

**Errores (`core/errores.py`):**

- `handler400`, `handler403`, `handler404` y `handler500` renderizan `error.html` con `status`, `error` (frase HTTP, p. ej. "Not Found") y `message` (el mismo `switch` de `CustomErrorController`).
- `GET /error` renderiza la página con status 500, igual que acceder a `/error` en Java.
- Un parámetro obligatorio que falta, o un número que no se puede convertir, produce 400 con `error.html`. La API se comporta igual: la app ya trata un 400 sin JSON.
- Un `orElseThrow()` de Java sobre un ID inexistente produce 500, para conservar el comportamiento.

## 7. Rutas y comportamiento

Cada vista reproduce el método Java indicado: mismas validaciones, en el mismo orden, con los mismos mensajes, los mismos datos de contexto y las mismas redirecciones. El nombre del método Java va en el docstring de la vista.

### 7.1 `web` (cliente)

| Ruta | Método | Acceso | Java |
|---|---|---|---|
| `/` | GET | público | `AuthController.home` → `paginas/index.html` |
| `/nosotros` | GET | público | `AuthController.nosotros` |
| `/login` | GET, POST | público | `AuthController.showLogin` + formLogin de Spring (sección 6) |
| `/logout` | GET, POST | — | logout de Spring (sección 6) |
| `/register` | GET, POST | público | `AuthController.showRegister` / `register` (sin `trim`, como en Java) |
| `/error` | GET | público | `CustomErrorController.handleError` |
| `/dashboard` | GET | cliente | `DashboardController.dashboard` |
| `/vehiculos` | GET | cliente | `DashboardController.misVehiculos` |
| `/sensores` | GET | cliente | `DashboardController.sensores` |
| `/vehiculos/crear` | GET, POST | cliente | `VehiculoController.showCrear` / `crear` (4 sensores por defecto) |
| `/vehiculos/<id>/editar` | GET, POST | cliente | `VehiculoController.showEditar` / `editar` |
| `/vehiculos/<id>/eliminar` | POST | cliente | `VehiculoController.eliminar` (F3) |

### 7.2 `panel` (admin)

| Ruta | Método | Java (`AdminController`) |
|---|---|---|
| `/admin` | GET | `index` + `cargarTotales` → `admin/dashboard.html` |
| `/admin/login` | GET, POST | `loginPage` + formLogin |
| `/admin/logout` | GET, POST | logout |
| `/admin/nosotros` | GET | `nosotrosPage` |
| `/admin/cliente/<id>/estado` | POST | `cambiarEstado` |
| `/admin/cliente/nuevo` · `/admin/cliente/crear` | GET · POST | `nuevoCliente` · `crearCliente` |
| `/admin/cliente/<id>/editar` | GET, POST | `showEditarCliente` / `editarCliente` |
| `/admin/cliente/<id>/eliminar` | POST | `eliminarCliente` (F3) |
| `/admin/vehiculo/nuevo` · `/admin/vehiculo/crear` | GET · POST | `nuevoVehiculo` · `crearVehiculo` |
| `/admin/vehiculo/<id>/editar` | GET, POST | `showEditarVehiculo` / `editarVehiculo` |
| `/admin/vehiculo/<id>/eliminar` | POST | `eliminarVehiculo` (F3) |
| `/admin/sensor/nuevo` · `/admin/sensor/crear` | GET · POST | `nuevoSensor` · `crearSensor` (F4) |
| `/admin/sensor/<id>/editar` | GET, POST | `showEditarSensor` / `editarSensor` |
| `/admin/sensor/<id>/eliminar` | POST | `eliminarSensor` |
| `/admin/usuario/nuevo` · `/admin/usuario/crear` | GET · POST | `nuevoUsuario` · `crearUsuario` |
| `/admin/usuario/<id>/editar` | GET, POST | `showEditarUsuario` / `editarUsuario` |
| `/admin/usuario/<id>/eliminar` | POST | `eliminarUsuario` (no se borra a sí mismo ni al último) |

### 7.3 `reportes` (admin)

| Ruta | Método | Java |
|---|---|---|
| `/admin/reportes` | GET | `AdminController.reportes` + `cargarDatosReportes` |
| `/admin/reportes-filtrado` | GET | `ReporteController.listaReportes` (F5) |
| `/admin/reportes-pdf` | GET | `ReporteController.reporteGeneral` (vista imprimible) |
| `/admin/reporte-cliente-pdf/<clienteId>` | GET | `ReporteController.reporteCliente` |
| `/admin/reportes/excel` | GET | `ReporteController.exportarExcel` (F5) |
| `/admin/reportes/pdf` | GET | `AdminController.exportarPdfCompleto` (F5) |
| `/admin/reportes/cliente/<id>/pdf` | GET | `AdminController.exportarPdfCliente` |
| `/admin/reportes/csv/<tipo>` | GET | `AdminController.exportarCsv` (`clientes`, `sensores`, `fallas`, `bloqueados`; otro tipo da un CSV vacío) |

`reportes/filtros.py` reúne `filtrar_sensores`, `filtrar_clientes` (con `tipo_placa`, F5), `comparador_sensores` y `peso_estado`. Las vistas de reportes y las exportaciones Excel y PDF usan las mismas funciones.

### 7.4 `api` (sin sesión, sin CSRF; la app Android)

| Ruta | Método | Parámetros (form o query) | Java |
|---|---|---|---|
| `/api/auth/register` | POST | `nombre`, `apellido`, `correo`, `contrasena` | `ApiController.registrar` |
| `/api/auth/login` | POST | `correo`, `contrasena` | `ApiController.login` |
| `/api/cliente/<correo>` | GET | — | `ApiController.datosCliente` |
| `/api/vehiculos/crear` | POST | `correo`, `nombreVehiculo`, `marca`, `modelo`, `color`, `placa`, `tipoPlaca` | `ApiController.crearVehiculo` |
| `/api/bluetooth/simular` | POST | `correo` | `ApiController.simularLecturas` |
| `/api/obd2/lecturas` | POST | `idVehiculo`, `nombreSensor`, `tipoSensor`, `valor`, `unidad`? | `Obd2Controller.guardarLectura` |
| `/api/obd2/vehiculo/<id>/elm` | POST | `elmMac` | `Obd2Controller.guardarElm` |
| `/api/obd2/vehiculo/<id>/elm` | GET | — | `Obd2Controller.obtenerElm` |
| `/api/obd2/historial/<idVehiculo>` | GET | — | `Obd2Controller.historial` |
| `/api/obd2/alertas/<idVehiculo>` | GET | — | `Obd2Controller.alertas` (últimas 50 globales, filtradas después) |
| `/api/obd2/ultima/<idVehiculo>` | GET | — | `Obd2Controller.ultima` (top 30 del vehículo) |
| `/api/obd2/conectar` | POST | — (sesión de cliente) | `Obd2Controller.conectar` (primer vehículo por PK) |

**Formato JSON (contrato con `referencia/app-android/Models.kt`):**

- Las respuestas son diccionarios en el **mismo orden de claves** que los `LinkedHashMap` de Java, con `JsonResponse(..., json_dumps_params={"ensure_ascii": False})`.
- Tipos:
  - `valor` siempre `float`, aunque el valor simulado sea entero (`Math.round` → `double` en Java).
  - `nivel` entero.
  - `ok` y `leida` booleanos.
  - IDs enteros.
- Las fechas pasan por `fecha_java(dt)`, que replica `String.valueOf(LocalDateTime)`:
  - formato `AAAA-MM-DDTHH:MM:SS`;
  - omite `:SS` si los segundos son 0 (regla de `LocalDateTime.toString`);
  - devuelve `"null"` si la fecha es `None`.
- `obd2.py` contiene `calcular_nivel`, `valor_simulado`, `unidad_de`, `redondear` y `redondear_dos`, copiados de `Obd2Controller` sin cambios, incluidos los rangos y el default 0–100.
- El aviso de observador (`alerta_critica.send(...)`) se emite en los mismos dos sitios que `publishEvent`.

## 8. Patrones GoF (`core/patrones/`)

Misma organización que en Java:

- `estrategia/`:
  - `EstadoSensorStrategy` (clase base abstracta, `clasificar(nivel)`).
  - `EstadoSensorReporteStrategy` (`OK`/`ADVERTENCIA`/`FALLA`) y `EstadoSensorFiltroStrategy` (`optimo`/`advertencia`/`falla`), ambas con `get_instancia()`.
  - `ClasificadorEstadoSensor` (contexto con `set_strategy`; lanza `RuntimeError` si no hay estrategia).
- `fabrica/`: `TipoEstado` (`Enum` con `REPORTE` y `FILTRO`) y `EstadoSensorStrategyFactory.crear(tipo)`.
- `singleton/`: `UmbralesReporte` (`Enum` con el único miembro `INSTANCIA`; constantes `MINIMO_ADVERTENCIA = 40` y `MINIMO_FALLA = 70`; métodos `es_optimo`, `es_advertencia` y `es_falla`).
- `observador/`:
  - Evento: una señal de Django, `alerta_critica = Signal()`. Equivale a `AlertaCriticaEvento`.
  - Observador: el receptor `atender_alerta_critica`, registrado en `CoreConfig.ready()`. Escribe en el logger `autosen.observador` a nivel WARNING el mismo texto: `[OBSERVER] Alerta registrada -> Sensor '…' (vehículo …) nivel …% | …`.

Los patrones se usan exactamente donde los usa Java: los reportes, el PDF y el Excel. Donde Java tiene los umbrales 40/70 escritos a mano, en Python también. `PATRONES_GOF.md` se reescribe con las equivalencias en Python, manteniendo la misma estructura.

## 9. Exportaciones y middleware

**PDF (`reportes/exportar.py`, reportlab platypus):**

- Reproduce el `AdminController` de Java:
  - Mismos tamaños: A4 horizontal para el general, A4 vertical para el de cliente, márgenes de 30 pt.
  - Misma paleta (`NEGRO`, `AZUL_OSCURO`, `AZUL_MEDIO`, `VERDE`, `GRIS_CLARO`, `GRIS_TEXTO`).
  - El mismo encabezado: título en Helvetica-Bold 20 y, a la derecha, el logo `static/images/logo-autosen.png` si existe; si no, se omite.
  - La línea verde de 3 pt, "Generado el dd/MM/yyyy HH:mm", y las mismas tablas, columnas, filas alternas y colores del estado.
- Encabezados HTTP: `Content-Type: application/pdf` y `Content-Disposition: attachment; filename=reporte-autosen.pdf` o `reporte-{nombre en minúsculas}.pdf`.
- Será visualmente equivalente, no idéntico píxel a píxel.

**Excel (openpyxl):** cuatro hojas: "Clientes", "Sensores", "Vehículos con fallas" y "Clientes bloqueados". Mismas cabeceras, los números como números y el texto `None` como `""`. Archivo `reporte-autosen.xlsx` con el content type de xlsx.

**CSV:** mismas cabeceras y mismo formato línea a línea (equivalentes a los `printf`), sin escapar comas. Usa `text/csv; charset=UTF-8` y separador de línea `\r\n`, el de `println` de Java en Windows. Las etiquetas del CSV de sensores (`OK`/`Advertencia`/`Falla`) se calculan con el ternario a mano, como en Java.

**`TemaMiddleware`:**

- Tras generar la respuesta, si el `Content-Type` contiene `text/html` y no es streaming, decodifica el cuerpo en UTF-8.
- Si contiene `</body>` y no contiene `theme-toggle.js`, reemplaza **todas** las apariciones de `</body>` por el mismo fragmento del `TemaFilter`, con las rutas de S3 (`/static/css/light-mode.css` y `/static/js/theme-toggle.js`).
- Recalcula `Content-Length`.

## 10. Plantillas

- Se copia el HTML y el CSS de `referencia/proyecto-java/src/main/resources/templates/` y solo se traduce la sintaxis:
  - `th:text` → `{{ }}`
  - `th:if` → `{% if %}`
  - `th:each` → `{% for %}`, con `forloop.counter0` en lugar de `iter.index`
  - `th:href`/`th:action` `@{…}` → `{% url %}`, que produce la misma ruta
  - `th:value` y `th:selected` → condicionales
  - `th:classappend` → la clase en el atributo `class`
  - `th:style` → `style`
- Cada `<form method="post">` lleva `{% csrf_token %}` (S1).
- Las expresiones con lógica se convierten en filtros de `core/templatetags/autosen.py`, con la misma regla de la plantilla original:
  - estado por nivel (`>= 70` → falla, `>= 40` → advertencia, si no ok/óptimo; `None` cuenta como ok);
  - la variante de los informes imprimibles, que además consulta `estado` (`'falla'`/`'advertencia'` sin distinguir mayúsculas);
  - la inicial en mayúscula para el avatar.
- Fechas:
  - `#temporals.format(createNow, 'EEEE, dd MMMM yyyy')` → `{% now "l, d F Y" %}` con `LANGUAGE_CODE = "es"`;
  - `'dd/MM/yyyy HH:mm'` → `|date:"d/m/Y H:i"`.
- `#authentication.name` → `{{ admin_correo }}`, que pone el context processor.
- `static/css/light-mode.css` y `static/js/theme-toggle.js` se copian tal cual.
- No se migran `src/main/resources/js/` (los restos de Laravel/axios y `Java/script.js`), porque Spring nunca los servía.

## 11. Importador (`core/management/commands/importar_mysql.py`)

`python manage.py importar_mysql <archivo.sql> [--limpiar]`

- Lee el archivo en UTF-8 y extrae cada `INSERT INTO \`tabla\` (\`col\`, …) VALUES (…), (…);`.
- **Parser de valores:**
  - números (enteros y decimales);
  - `NULL`;
  - cadenas entre comillas simples con los escapes de MySQL: `\'`, `\\`, `\n`, `\r`, `\t`, `\0` y `''`.
- **Mapeo:** usa los nombres de columna MySQL → campos del modelo según `db_column`. Las columnas desconocidas se ignoran con un aviso. Las que faltan (`elm_mac`, `Estado` de sensores) quedan NULL. Las fechas `'AAAA-MM-DD HH:MM:SS'` pasan a `datetime`.
- **Orden de inserción:** `usuario` → `cliente` → `vehiculo` → `sensores` → `lecturas` → `alertas`, conservando las PK, todo dentro de `transaction.atomic()`.
- **Al final:** reinicia las secuencias de PostgreSQL (`connection.ops.sequence_reset_sql`) e imprime cuántas filas importó por tabla.
- **`--limpiar`:** borra antes todas las filas en orden inverso. Sin `--limpiar`, si alguna tabla destino tiene datos, aborta con un mensaje.
- **Sin transformaciones:** los datos se copian tal cual, incluidos los hashes, placas en minúsculas, `Público`, etc.

## 12. Configuración y ejecución

- **`.env`** (copiado de `.env.example`, cargado con python-dotenv):
  - `SECRET_KEY`, `DEBUG` (por defecto `False`);
  - `DB_NAME` (por defecto `vehiculos`), `DB_USER` (por defecto `postgres`), `DB_PASSWORD`;
  - `DB_HOST` (por defecto `127.0.0.1`), `DB_PORT` (por defecto `5432`).
- **`ALLOWED_HOSTS`:** `localhost`, `127.0.0.1`, `10.0.2.2`, más la variable opcional `ALLOWED_HOSTS_EXTRA` separada por comas.
- **`requirements.txt`** con versiones fijadas: Django 6.1.x, `psycopg[binary]` 3.3.x, bcrypt 5.0.x, reportlab 5.0.x, openpyxl 3.1.x, python-dotenv 1.2.x y whitenoise. El plan fija las versiones exactas.
- **Logging:** a consola, nivel INFO para `autosen.*`.
- **README**, con estos pasos:
  1. Instalar PostgreSQL 18 (`winget install -e --id PostgreSQL.PostgreSQL.18`).
  2. Crear la base `vehiculos`.
  3. Crear el `.env`.
  4. Crear el entorno virtual e instalar dependencias.
  5. `migrate`.
  6. `importar_mysql "datos/vehiculos (10).sql"`.
  7. `runserver 0.0.0.0:8080`.
  8. Ejecutar las pruebas con `python manage.py test`.
  9. Nota para la app Android: emulador → `10.0.2.2:8080`.

## 13. Pruebas

Django `TestCase` contra PostgreSQL (el usuario de `.env` necesita permiso para crear la base de pruebas). Se escribe cada prueba antes del código que prueba (TDD).

- **`core`:**
  - modelos y nombres de tablas y columnas;
  - bcrypt con hashes `$2a$`, `$2b$` y `$2y$` (generados en la prueba) y que `cifrar` produce `$2a$10$`;
  - `fecha_java`;
  - estrategias, fábrica y singleton;
  - el receptor del observador registra el mensaje;
  - `TemaMiddleware` (inyecta una vez, respeta lo que no es HTML y lo que ya tiene `theme-toggle.js`);
  - importador con un dump de prueba inventado en `core/tests/datos/dump_prueba.sql` (escapes, NULL, `--limpiar`, abortar si hay datos, secuencias reiniciadas: el siguiente ID continúa).
- **`api`:**
  - `calcular_nivel`, con casos calculados a mano a partir de la fórmula Java (p. ej. TEMP 95 → 75, RPM 600 → 0, RPM 3000 → 100, ECT con el rango 0–100);
  - rangos de `valor_simulado`;
  - cada endpoint: claves y orden, tipos, mensajes de `ok:false`, 400 si falta un parámetro, funcionamiento sin sesión, y `/conectar` que exige sesión;
  - creación de alertas desde nivel 40 y el tipo `falla` desde 70.
- **`web`:**
  - login (correcto, contraseña errónea, cliente bloqueado, correo con otras mayúsculas) y redirecciones;
  - registro;
  - el orden de las validaciones al crear un vehículo y los 4 sensores por defecto;
  - que nadie edite ni borre vehículos ajenos;
  - que borrar un vehículo con lecturas funcione y las lecturas sigan ahí (F3);
  - KPIs del dashboard.
- **`panel`:**
  - acceso: sin sesión → login; con sesión de cliente → login de admin (F2);
  - CRUD de cada entidad con sus validaciones;
  - crear un sensor sin tipo de daño (F4);
  - eliminar usuario: ni a sí mismo ni al último.
- **`reportes`:**
  - cada filtro, incluido `tipoPlaca` sin distinguir tildes (F5);
  - el orden;
  - el texto exacto del CSV;
  - del Excel: nombres de hoja, cabeceras y filas;
  - del PDF: `application/pdf`, que empiece por `%PDF` y que respete los filtros (F5);
  - las vistas imprimibles.

**Límite conocido:** la equivalencia se verifica con pruebas escritas a partir del código Java. No se ejecuta el backend Java para comparar respuestas, porque no hay MySQL disponible. La prueba manual con el emulador de Android queda a cargo del equipo.

**`docs/PENDIENTES.md`** (lista inicial, comportamientos conservados a propósito):

1. `calcularNivel` trata los valores dentro del rango normal como desgaste (TEMP 95 °C → 75 % → FALLA). ECT y MAP caen en el rango genérico 0–100.
2. Hay dos fuentes de nivel: `sensores.Nivel` y `lecturas.Nivel`. "Conectar Bluetooth" no actualiza los sensores.
3. La API no comprueba que el correo o el ID pertenezcan a quien llama: no hay token.
4. `/api/obd2/alertas/{id}` solo mira las 50 alertas más recientes de todo el sistema.
5. "Conectar" usa siempre el primer vehículo del cliente. La telemetría web no se actualiza sola: el sondeo de 3 s devuelve las mismas lecturas.
6. Un ID inexistente da 500 (`orElseThrow`).
7. El registro web no recorta espacios ni valida el formato del correo; el registro de la API sí recorta.
8. Al crear un vehículo se busca la placa duplicada antes de validar el formato, y sin recortar espacios. Editar un vehículo desde la web del cliente no valida el formato de la placa.
9. El CSV no escapa las comas.
10. Los umbrales 40/70 están escritos a mano fuera de los patrones.
11. Valores de `tipo_placa` inconsistentes (`Particular`/`Público` en los datos frente a `particular`/`publico` en los formularios).
12. No se puede borrar un admin si algún cliente lo referencia en `Id_usuario` (500).
13. El cliente no tiene botón para eliminar vehículos, aunque la ruta existe.
14. `/admin/reportes-pdf` y `/admin/reporte-cliente-pdf/{id}` no tienen enlaces en ninguna página.
15. `reportes-filtrado`: los totales de vehículos, vehículos con fallas y clientes bloqueados no se filtran.
16. `obtenerElm` siempre responde `conectado: false`.
17. `@EnableScheduling` no tenía tareas; no se migra.
18. Un `nivel` NULL en un sensor provoca un 500 en el dashboard del cliente, en `/api/cliente/{correo}`, en `/api/bluetooth/simular` y en los CSV de sensores y fallas.

## 14. Fuera de alcance

- Cambios en la app Android.
- Despliegue en un servidor (gunicorn, nginx, etc.).
- Corregir lo que está en `PENDIENTES.md`.
- El admin de Django y `django.contrib.auth`.
- Funciones nuevas.
- Ejecutar el backend Java.

## 15. Riesgos

| Riesgo | Mitigación |
|---|---|
| Django 6.1 no declara soporte para Python 3.15 | Si la instalación o las pruebas fallan por la versión, se usa Python 3.14 (`py install 3.14`) |
| bcrypt 5 rechaza el prefijo `$2y$` | Normalizar `$2y$` → `$2b$` antes de `checkpw` (equivalentes); hay una prueba que lo cubre |
| bcrypt 5 lanza un error con contraseñas de más de 72 bytes | Igual que Spring Security 6.5 (también falla); se conserva |
| El PDF de reportlab no es idéntico al de iText | Se acepta: equivalencia visual de contenido, tablas y colores |
| PostgreSQL todavía no está instalado | Las tareas que no necesitan base de datos van primero; las pruebas corren cuando el `.env` esté listo |
