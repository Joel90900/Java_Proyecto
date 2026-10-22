package com.autosen.app.data

import retrofit2.Response
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {

    // ── AUTENTICACIÓN (backend Spring Boot / Java) ───────────
    @FormUrlEncoded
    @POST("api/auth/login")
    suspend fun login(
        @Field("correo") correo: String,
        @Field("contrasena") contrasena: String
    ): Response<ApiRespuesta>

    @FormUrlEncoded
    @POST("api/auth/register")
    suspend fun registrar(
        @Field("nombre") nombre: String,
        @Field("apellido") apellido: String,
        @Field("correo") correo: String,
        @Field("contrasena") contrasena: String
    ): Response<ApiRespuesta>

    // ── DATOS DEL CLIENTE (dashboard, vehículos y sensores) ─────
    @GET("api/cliente/{correo}")
    suspend fun datosCliente(@Path("correo") correo: String): Response<ApiRespuesta>

    // ── VEHÍCULOS ───────────────────────────────────────────────
    @FormUrlEncoded
    @POST("api/vehiculos/crear")
    suspend fun crearVehiculo(
        @Field("correo") correo: String,
        @Field("nombreVehiculo") nombreVehiculo: String,
        @Field("marca") marca: String,
        @Field("modelo") modelo: String,
        @Field("color") color: String,
        @Field("placa") placa: String,
        @Field("tipoPlaca") tipoPlaca: String
    ): Response<ApiRespuesta>

    // ── SIMULACIÓN DE LECTURAS OBD2 (botón Bluetooth) ──────────
    @FormUrlEncoded
    @POST("api/bluetooth/simular")
    suspend fun simularBluetooth(@Field("correo") correo: String): Response<ApiRespuesta>

    // ── OBD2 REAL (ELM327) ─────────────────────────────────────
    @FormUrlEncoded
    @POST("api/obd2/lecturas")
    suspend fun guardarLecturaObd(
        @Field("idVehiculo") idVehiculo: Long,
        @Field("nombreSensor") nombreSensor: String,
        @Field("tipoSensor") tipoSensor: String,
        @Field("valor") valor: Double,
        @Field("unidad") unidad: String
    ): Response<ApiRespuesta>

    @FormUrlEncoded
    @POST("api/obd2/vehiculo/{id}/elm")
    suspend fun guardarElm(
        @Path("id") idVehiculo: Long,
        @Field("elmMac") elmMac: String
    ): Response<ApiRespuesta>

    @GET("api/obd2/historial/{idVehiculo}")
    suspend fun historialObd(@Path("idVehiculo") idVehiculo: Long): Response<ApiRespuesta>

    @GET("api/obd2/alertas/{idVehiculo}")
    suspend fun alertasObd(@Path("idVehiculo") idVehiculo: Long): Response<ApiRespuesta>

    @GET("api/obd2/ultima/{idVehiculo}")
    suspend fun ultimaObd(@Path("idVehiculo") idVehiculo: Long): Response<ApiRespuesta>
}