package com.autosen.app.data

import org.json.JSONObject
import retrofit2.Response

/**
 * Extrae un mensaje legible del cuerpo de error de la API (Spring Boot).
 * El backend de Java responde: {"ok":false,"mensaje":"..."} ó {"message":"..."}
 */
fun mensajeDeErrorApi(response: Response<*>?): String {
    val cuerpo = response?.errorBody()?.string().orEmpty()
    if (cuerpo.isBlank()) return ""

    return try {
        val json = JSONObject(cuerpo)
        val mensaje = json.optString("mensaje").ifBlank { json.optString("message") }
        if (mensaje.isNotBlank()) {
            mensaje
        } else {
            val errors = json.optJSONObject("errors") ?: return mensaje
            val primeraClave = errors.keys().asSequence().firstOrNull() ?: return mensaje
            errors.optJSONArray(primeraClave)?.optString(0) ?: mensaje
        }
    } catch (e: Exception) {
        ""
    }
}