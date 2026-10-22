package com.autosen.app.data

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {

    // 10.0.2.2 es la IP especial que usa el EMULADOR de Android
    // para referirse al localhost de la PC donde corre el backend en JAVA (Spring Boot, puerto 8080)
    private const val BASE_URL = "http://10.0.2.2:8080/"

    // Sesión del cliente (correo). Persistido en memoria mientras la app esté abierta.
    var correoCliente: String? = null
    var nombreCliente: String = ""

    // Conexión Bluetooth ELM327 activa + MAC guardada para reconexiones
    var elm327: Elm327Client? = null
    var elmMacVehiculo: String? = null
    var ultimoNivel: Int? = null

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .build()

    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}