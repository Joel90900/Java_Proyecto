# AutoSen (Django)

AutoSen es un sistema de monitoreo vehicular. Permite:

- Registrar clientes, vehículos y sensores.
- Recibir lecturas OBD2 (desde la app Android o con la simulación del dashboard web).
- Generar alertas cuando un sensor pasa a advertencia (nivel ≥ 40) o a falla (nivel ≥ 70).
- Consultar y exportar reportes en PDF, Excel y CSV.

Esta es la migración a **Python/Django + PostgreSQL** del proyecto original en Spring Boot.
Conserva las mismas pantallas, rutas, reglas de negocio y la API que usa la app Android.

| Documento | Contenido |
|---|---|
| `docs/superpowers/specs/2026-10-21-migracion-django-design.md` | Diseño de la migración y lista de cambios respecto a Java |
| `docs/PENDIENTES.md` | Lo que queda por corregir (lotes B, C y D) y diferencias conocidas con Java |
| `PATRONES_GOF.md` | Patrones de diseño (Strategy, Factory, Singleton, Observer) |

## Requisitos

- Python 3.12 o superior. Se probó con Python 3.15 y Django 6.1.2.
- PostgreSQL 18.

## Instalación

1. **Instalar PostgreSQL 18.** Guarda la contraseña del usuario `postgres`.

   ```bash
   winget install -e --id PostgreSQL.PostgreSQL.18
   ```

2. **Crear la base de datos `vehiculos`.** Pide la contraseña de `postgres`.

   ```bash
   "C:/Program Files/PostgreSQL/18/bin/createdb.exe" -h 127.0.0.1 -U postgres -E UTF8 -T template0 vehiculos
   ```

3. **Configurar el archivo `.env`.** Copia `.env.example` como `.env` y completa:
   - `SECRET_KEY`: una cadena larga y aleatoria.
   - `DB_PASSWORD`: la contraseña de PostgreSQL.

   `.env` no se sube a git.

4. **Crear el entorno virtual e instalar las dependencias.**

   ```bash
   python -m venv .venv
   .venv/Scripts/pip install --only-binary=:all: -r requirements.txt
   ```

5. **Crear las tablas.**

   ```bash
   .venv/Scripts/python manage.py migrate
   ```

6. **Importar los datos de MySQL.** Exporta la base `vehiculos` con phpMyAdmin (formato SQL) y guarda el archivo en `datos/`. Esa carpeta no se sube a git, porque el dump trae datos personales. Las contraseñas existentes siguen funcionando.

   ```bash
   .venv/Scripts/python manage.py importar_mysql "datos/vehiculos (10).sql"
   ```

   Para volver a importar un dump más reciente sobre una base con datos, añade `--limpiar` (borra los datos actuales antes de importar).

7. **Arrancar el servidor en el puerto 8080**, el que usa la app Android.

   ```bash
   .venv/Scripts/python manage.py runserver 0.0.0.0:8080
   ```

   - Web del cliente: http://localhost:8080/
   - Panel de administración: http://localhost:8080/admin

## App Android

La app apunta a `http://10.0.2.2:8080/`, que es la IP con la que el emulador de Android
ve tu PC. `10.0.2.2` ya está en `ALLOWED_HOSTS`, así que solo hay que arrancar el
servidor como en el paso 7.

Con un teléfono físico en la misma red:

1. Añade la IP de tu PC en `ALLOWED_HOSTS_EXTRA` dentro de `.env`.
2. Cambia `BASE_URL` en la app.

La API (`/api/**`) no usa sesión ni CSRF, igual que la espera la app.

## Pruebas

```bash
.venv/Scripts/python manage.py test
```

Las pruebas crean una base temporal `test_vehiculos`, así que el usuario de PostgreSQL
necesita permiso para crear bases de datos (el usuario `postgres` lo tiene).

## Estructura

| Carpeta | Contenido | Equivale en Java a |
|---|---|---|
| `autosen/` | configuración del proyecto (`settings.py`, `urls.py`) | `application.properties`, `SecurityConfig` |
| `core/` | modelos, login de cliente y admin, utilidades, middleware de tema, patrones GoF, importador | `model/`, `service/`, `config/`, `patrones/` |
| `web/` | web del cliente | `AuthController`, `DashboardController`, `VehiculoController` |
| `panel/` | panel de administración | `AdminController` |
| `reportes/` | reportes, filtros y exportaciones | `ReporteController`, exportaciones de `AdminController` |
| `api/` | API JSON de la app Android | `ApiController`, `Obd2Controller` |
| `templates/` | plantillas HTML | plantillas Thymeleaf |
| `static/` | CSS y JS del botón de tema | `static/` |
