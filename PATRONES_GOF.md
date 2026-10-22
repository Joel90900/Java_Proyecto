# Patrones de diseño GoF — Proyecto AutoSen (Django)

Este documento resume cómo se aplican los **patrones clásicos (Gang of Four)** en la
versión Django de AutoSen. Los patrones **integrados explícitamente** están en
`core/patrones/`, con la misma organización que tenía el proyecto Java
(`patrones/comportamiento` y `patrones/creacional`).

## Patrones integrados en el código propio

### 1. Strategy (comportamiento)
- **Intención:** una familia de algoritmos intercambiables; el cliente delega en el algoritmo activo.
- **Archivos:** `core/patrones/estrategia/__init__.py`
  - `EstadoSensorStrategy`: clase base abstracta (el contrato): `clasificar(nivel) -> str`.
  - `EstadoSensorReporteStrategy`: devuelve "OK / ADVERTENCIA / FALLA" (PDF y Excel).
  - `EstadoSensorFiltroStrategy`: devuelve "optimo / advertencia / falla" (filtros y vista web).
  - `ClasificadorEstadoSensor`: el contexto, que delega en la estrategia configurada (`set_strategy` la cambia en ejecución).
- **Uso real:**
  - `reportes/views.py`: filtros, KPIs, informe imprimible y hoja "Sensores" del Excel.
  - `reportes/exportar.py`: PDF general y PDF por cliente.
  - El estado se **deriva del nivel** según los umbrales, porque la columna `Estado` de la BD casi siempre está vacía.

### 2. Factory Method / Simple Factory (creacional)
- **Intención:** encapsular la creación de objetos; el cliente pide por tipo.
- **Archivos:** `core/patrones/fabrica/__init__.py`: `TipoEstado` (Enum) y `EstadoSensorStrategyFactory.crear(TipoEstado)`.
- **Beneficio:** agregar una nueva estrategia (p. ej., etiquetas en inglés) solo toca la fábrica.

### 3. Singleton (creacional)
- **Intención:** una única instancia global.
- **Archivos:** `core/patrones/singleton/__init__.py`: `UmbralesReporte`, un `Enum` con el único miembro `INSTANCIA`.
- **Detalle:** las constantes `MINIMO_ADVERTENCIA = 40` y `MINIMO_FALLA = 70` se declaran con `enum.nonmember`, para que no sean miembros adicionales del Enum.
- **Uso real:** las estrategias y los reportes la consultan para centralizar los umbrales de nivel.

### 4. Observer (comportamiento)
- **Intención:** notificar a observadores sin acoplarlos al sujeto.
- **Archivos:** `core/patrones/observador/__init__.py`
  - `alerta_critica`: el evento, una señal de Django que se emite al registrar una alerta (equivale a `AlertaCriticaEvento`).
  - `atender_alerta_critica`: el observador, que escribe la alerta en el log `autosen.observador` (equivale a `AlertaCriticaListener`). Se suscribe en `CoreConfig.ready()`.
- **Uso real:** `api/obd2.py` emite `alerta_critica` al guardar una lectura que genera una alerta, tanto en `/api/obd2/lecturas` como en `/api/obd2/conectar`.

## Patrones nativos del framework (Django)

- **Adapter:** `core/auth.py` adapta las tablas `usuario` y `cliente` a dos sesiones de login independientes, en lugar del modelo de usuario de Django.
- **Decorator:**
  - `cliente_requerido`, `admin_requerido` y `metodos` envuelven las vistas para añadir control de acceso y de método HTTP.
  - `TemaMiddleware` envuelve la respuesta para inyectar el botón de tema (en Java era un `HttpServletResponseWrapper`).
- **Chain of Responsibility:** la lista `MIDDLEWARE` de `settings.py`; cada middleware procesa la petición y la pasa al siguiente.
- **Observer:** las señales de Django (`django.dispatch.Signal`), usadas por el patrón 4.
- **Template Method:** las plantillas de Django y `BaseCommand.handle` en el comando `importar_mysql`.
- **Proxy:** carga perezosa del ORM (`cliente.vehiculos.all()` no consulta hasta que se recorre).
- **Iterator:** QuerySets, `for` y comprensiones de listas.
- **Factory:** el ORM crea los objetos de modelo; `bcrypt.gensalt` y `cifrar_contrasena` encapsulan la creación de hashes.

## Notas
- **Filtros de reportes:**
  - La página `/admin/reportes-filtrado` permite buscar por texto (`q`) y filtrar por estado de cliente o de sensor, tipo de sensor, marca, tipo de placa y rango de nivel, además de ordenar.
  - Los botones **PDF** y **Excel** del formulario respetan los filtros aplicados.
- **Exportaciones:**
  - PDF (reportlab) en `/admin/reportes/pdf`.
  - Excel (openpyxl) en `/admin/reportes/excel`.
  - CSV en `/admin/reportes/csv/<tipo>`.
