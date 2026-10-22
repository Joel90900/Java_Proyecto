package com.autosen.app.data

import com.google.gson.annotations.SerializedName

// ── RESPUESTA GENÉRICA DE LA API (Spring Boot / Java) ─────────
// El backend responde siempre: { ok, mensaje, cliente, vehiculos, estadisticas }

data class ApiRespuesta(
    val ok: Boolean? = null,
    val mensaje: String? = null,
    val cliente: Cliente? = null,
    val vehiculos: List<Vehiculo>? = null,
    val estadisticas: Estadisticas? = null,
    val lecturas: List<LecturaObd>? = null,
    val alertas: List<AlertaObd>? = null,
    val nivel: Int? = null,
    val estado: String? = null
)

// ── LECTURA OBD2 (ELM327) ───────────────────────────────────────

data class LecturaObd(
    @SerializedName("idLectura") val idLectura: Long = 0,
    @SerializedName("nombreSensor") val nombreSensor: String = "",
    @SerializedName("tipoSensor") val tipoSensor: String = "",
    val valor: Double = 0.0,
    val unidad: String = "",
    val nivel: Int = 0,
    val estado: String = "OK",
    @SerializedName("fechaLectura") val fechaLectura: String = ""
)

// ── ALERTA OBD2 ─────────────────────────────────────────────────

data class AlertaObd(
    @SerializedName("idAlerta") val idAlerta: Long = 0,
    @SerializedName("nombreSensor") val nombreSensor: String = "",
    @SerializedName("tipoSensor") val tipoSensor: String = "",
    val valor: Double = 0.0,
    val nivel: Int = 0,
    val tipo: String = "",
    val mensaje: String = "",
    val leida: Boolean = false,
    @SerializedName("fechaAlerta") val fechaAlerta: String = ""
)

// ── AUTH ───────────────────────────────────────────────────────

data class LoginRequest(
    val correo: String,
    val contrasena: String
)

data class RegisterRequest(
    val nombre: String,
    val apellido: String,
    val correo: String,
    val contrasena: String
)

data class Cliente(
    @SerializedName("idCliente") val idCliente: Long = 0,
    @SerializedName("nombreCliente") val nombreCliente: String = "",
    @SerializedName("apellidoCliente") val apellidoCliente: String = "",
    val correo: String = "",
    val estado: String = ""
)

// ── VEHÍCULOS (con sus sensores incluidos) ─────────────────────

data class Vehiculo(
    @SerializedName("idVehiculo") val idVehiculo: Long = 0,
    @SerializedName("nombreVehiculo") val nombreVehiculo: String = "",
    val marca: String = "",
    val modelo: String = "",
    val color: String = "",
    val placa: String = "",
    @SerializedName("tipoPlaca") val tipoPlaca: String = "",
    val sensores: List<Sensor> = emptyList()
)

data class VehiculoRequest(
    val nombreVehiculo: String,
    val marca: String,
    val modelo: String,
    val color: String,
    val placa: String,
    val tipoPlaca: String
)

// ── SENSORES ────────────────────────────────────────────────────

data class Sensor(
    @SerializedName("idSensor") val idSensor: Long = 0,
    @SerializedName("nombreSensor") val nombreSensor: String = "",
    @SerializedName("tipoSensor") val tipoSensor: String = "",
    @SerializedName("tipoDano") val tipoDano: String = "",
    val nivel: Int = 0
)

// ── ESTADÍSTICAS DEL DASHBOARD ──────────────────────────────────

data class Estadisticas(
    @SerializedName("totalVehiculos") val totalVehiculos: Int = 0,
    @SerializedName("totalSensores") val totalSensores: Int = 0,
    @SerializedName("sensoresOk") val sensoresOk: Int = 0,
    val advertencias: Int = 0,
    val fallas: Int = 0
)