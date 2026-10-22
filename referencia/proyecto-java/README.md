Auto Sen

Auto Sen es un sistema de monitoreo y gestión de sensores vehiculares desarrollado para registrar vehículos, administrar sensores, almacenar lecturas y generar alertas a partir de los datos obtenidos.

El sistema centraliza la información de usuarios, clientes, vehículos, sensores, lecturas y alertas mediante una base de datos relacional, permitiendo consultar el estado y comportamiento de los sensores de forma organizada.

Desarrollar Auto Sen, un sistema de monitoreo vehicular que permita gestionar sensores, registrar sus lecturas y generar alertas para facilitar el seguimiento del estado del vehículo.

Objetivos específicos Registrar y administrar vehículos. Asociar sensores a los vehículos. Registrar las mediciones obtenidas por los sensores. Consultar el historial de lecturas.

📖 Descripción del proyecto

Auto Sen permite centralizar la información relacionada con el monitoreo de vehículos mediante sensores.

El sistema utiliza una estructura relacional donde un cliente puede tener vehículos, y cada vehículo puede contar con diferentes sensores. Los sensores generan lecturas que son almacenadas para su posterior consulta.

Cuando una lectura presenta una condición que requiere atención, el sistema puede registrar una alerta asociada al vehículo y al sensor correspondiente.

El flujo general es:

Flujo de información El cliente tiene un vehículo registrado. El vehículo tiene sensores asociados. Los sensores generan datos. Los datos se almacenan como lecturas. El sistema valida la información. Si se detecta una condición anormal, se registra una alerta. El usuario puede consultar la información desde el sistema. ⚙️ Arquitectura

Auto Sen utiliza una arquitectura dividida en componentes para separar la interfaz, el procesamiento y la persistencia de los datos.

Componentes

Interfaz Web

Es la capa con la que interactúa el usuario. Permite consultar vehículos, sensores, lecturas y alertas.

Backend PHP

Procesa las solicitudes realizadas desde la interfaz y administra la comunicación con la base de datos.

Validaciones y lógica de negocio

Comprueba que los datos recibidos sean válidos y determina las acciones que debe realizar el sistema.

MySQL / MariaDB

Almacena permanentemente la información del sistema.

Sensores

Representan los dispositivos encargados de generar los datos que posteriormente son almacenados como lecturas.

🛠️ Tecnologías Tecnología Uso PHP Backend y lógica del sistema HTML5 Estructura de la interfaz CSS3 Diseño visual JavaScript Interactividad Bootstrap Componentes de interfaz MySQL / MariaDB Base de datos XAMPP Servidor local Apache Ejecución del proyecto Git Control de versiones GitHub Repositorio y colaboración

🔗 Modelo entidad-relación

El diagrama representa la estructura de la base de datos de Auto Sen y cómo se relacionan sus principales entidades.

Usuario: controla el acceso al sistema. Cliente: almacena los datos del propietario. Vehículo: contiene la información de cada vehículo. Sensores: registra los sensores asociados a un vehículo. Lecturas: almacena los valores obtenidos por los sensores. Alertas: registra las situaciones que requieren atención.

USUARIO ↓ CLIENTE ↓ VEHÍCULO ├── SENSORES ├── LECTURAS └── ALERTAS usuario

🔗 Relaciones principales Cliente → Vehículo CLIENTE 1 ───────── N VEHICULO

Un cliente puede tener uno o varios vehículos.

Vehículo → Sensores VEHICULO 1 ───────── N SENSORES

Un vehículo puede tener diferentes sensores.

Vehículo → Lecturas VEHICULO 1 ───────── N LECTURAS

Un vehículo puede acumular múltiples lecturas generadas por sus sensores.

Vehículo → Alertas VEHICULO 1 ───────── N ALERTAS

Un vehículo puede generar múltiples alertas durante su monitoreo.

📊 Flujo de una lectura Explicación Sensor: obtiene una medición. Captura: se obtiene el valor y los datos asociados. Backend: PHP recibe la información. Validación: se verifica que los datos sean correctos. Lectura: se almacena el resultado. Evaluación: se determina si existe una condición que requiera atención. Alerta: si corresponde, se registra una alerta. Visualización: el usuario puede consultar el resultado. 🔔 Sistema de alertas

Las alertas permiten identificar lecturas que necesitan atención.

Ejemplo:

Sensor: Temperatura Valor: 115 °C Tipo: Temperatura alta Mensaje: Valor fuera del rango permitido Leída: No

El campo Leida permite controlar el estado de visualización:

0 → No leída 1 → Leída

El campo Nivel puede utilizarse para clasificar la importancia de la lectura o alerta.

👥 Casos de uso Administrador

Puede realizar operaciones de gestión como:

Administrar vehículos. Gestionar sensores. Consultar lecturas. Revisar alertas.

Cliente

Puede acceder a la información relacionada con sus vehículos y consultar:

Sensores. Lecturas. Alertas.

Su función es proporcionar las mediciones utilizadas por el sistema.

📌 Reglas de negocio Cada vehículo debe tener un identificador único. La placa identifica al vehículo y debe evitar duplicados. Un sensor debe estar asociado a un vehículo. Las lecturas deben estar relacionadas con un vehículo. Los valores recibidos deben tener un formato válido. Las alertas deben estar asociadas al vehículo correspondiente. Solo los usuarios autorizados pueden realizar operaciones administrativas. Las lecturas históricas deben conservarse para futuras consultas. Las alertas deben registrar la fecha en la que fueron generadas. Las contraseñas no deben almacenarse en texto plano. 🔐 Seguridad

Una organización recomendada para el proyecto es:

AutoSen/ │ ├── config/ │ └── conexion.php │ ├── controllers/ │ ├── AuthController.php │ ├── VehiculoController.php │ ├── SensorController.php │ ├── LecturaController.php │ └── AlertaController.php │ ├── models/ │ ├── Usuario.php │ ├── Cliente.php │ ├── Vehiculo.php │ ├── Sensor.php │ ├── Lectura.php │ └── Alerta.php │ ├── views/ │ ├── login/ │ ├── vehiculos/ │ ├── sensores/ │ ├── lecturas/ │ └── alertas/ │ ├── css/ ├── js/ ├── img/ │ ├── database/ │ └── vehiculos.sql │ ├── index.php └── README.md

La estructura puede variar dependiendo de la organización actual del proyecto.