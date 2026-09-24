# Patrones de Diseño GoF — Proyecto AutoSen

Este documento resume cómo se aplican los **patrones clásicos (Gang of Four)** en el
proyecto `autosen`. Los patrones **integrados explícitamente** viven en
`src/main/java/com/example/sensores_vsc/patrones/`, organizados por categoría
(creacional / comportamiento / estructural).

## Patrones integrados en el código propio

### 1. Strategy (Comportamental)
- **Intención:** familia de algoritmos intercambiables; el cliente delega en el algoritmo activo.
- **Archivos:**
  - `EstadoSensorStrategy` — interfaz (contrato): `String clasificar(Integer nivel)`
  - `EstadoSensorReporteStrategy` — "OK / ADVERTENCIA / FALLA" (PDF y Excel)
  - `EstadoSensorFiltroStrategy` — "optimo / advertencia / falla" (filtros y vista web)
  - `ClasificadorEstadoSensor` — contexto que delega en la estrategia configurada
- **Uso real:** `AdminController` (PDF general y PDF por cliente) y `ReporteController`
  (filtros, KPIs, hoja "Sensores" del Excel). Esto eliminó los ternarios de umbrales
  repetidos y el bug de "Estado vacío" (el campo `estado` de la BD casi siempre es nulo;
  ahora el estado se **deriva del nivel** según umbrales).

### 2. Factory Method / Simple Factory (Creacional)
- **Intención:** encapsular la creación de objetos; el cliente pide por tipo.
- **Archivos:** `TipoEstado` (enum) y `EstadoSensorStrategyFactory.crear(TipoEstado)`.
- **Beneficio:** agregar una nueva estrategia (p. ej. inglés) solo toca la fábrica.

### 3. Singleton (Creacional)
- **Intención:** una única instancia global.
- **Archivos:** `UmbralesReporte` (enum con `INSTANCIA`), usado por `ReporteController`
  y `AdminController` para centralizar los umbrales de nivel (40 = advertencia, 70 = falla).

### 4. Observer (Comportamental)
- **Intención:** notificar a observadores sin acoplarlos al sujeto.
- **Archivos:**
  - `AlertaCriticaEvento` — evento publicado cuando se registra una alerta
  - `AlertaCriticaListener` — observador `@EventListener` que reacciona (log de la alerta)
- **Uso real:** `Obd2Controller` publica `AlertaCriticaEvento` al guardar una lectura/alerta.

## Patrones nativos del framework (Spring/JPA)

- **Adapter:** `AdminUserDetailsService` y `ClienteUserDetailsService` adaptan `Usuario`/`Cliente`
  al modelo `UserDetails` de Spring Security.
- **Builder:** `User.builder()...build()` en los dos `UserDetailsService`.
- **Proxy:** lazy loading de JPA y AOP de `@Transactional`.
- **Chain of Responsibility:** cadena de filtros de `SecurityConfig` (admin y cliente).
- **Strategy:** `PasswordEncoder` ↔ `BCryptPasswordEncoder`.
- **Decorator:** uso de `HttpServletResponseWrapper` para capturar respuestas.
- **Iterator:** `List`, `for-each`, `Stream`.
- **Factory / Abstract Factory:** `@Bean passwordEncoder()` y factorías de Spring Data JPA.

## Notas
- **Filtros de reportes:** página `/admin/reportes-filtrado` con búsqueda (`q`), estado de
  cliente/sensor, tipo de sensor, marca, tipo de placa, rango de nivel y orden. Los botones
  **PDF** y **Excel** del formulario respetan los filtros aplicados.
- **Exportaciones:** PDF (iText) en `/admin/reportes/pdf` y Excel (Apache POI) en
  `/admin/reportes/excel`. El CSV existente se conserva sin cambios.
