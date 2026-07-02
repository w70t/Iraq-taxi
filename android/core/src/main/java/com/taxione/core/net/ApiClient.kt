package com.taxione.core.net

import com.taxione.core.security.SecureStorage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class ApiException(val code: Int, message: String) : Exception(message)

/**
 * Minimal HTTP client for the Taxi One backend. The auth token and server
 * URL live in Keystore-encrypted storage, never in plain preferences.
 */
class ApiClient(private val storage: SecureStorage) {

    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    var baseUrl: String
        get() = storage.getString(KEY_SERVER) ?: DEFAULT_SERVER
        set(value) = storage.putString(KEY_SERVER, value.trim().trimEnd('/'))

    var token: String?
        get() = storage.getString(KEY_TOKEN)
        set(value) {
            if (value == null) storage.remove(KEY_TOKEN) else storage.putString(KEY_TOKEN, value)
        }

    val loggedIn: Boolean get() = token != null

    suspend fun request(method: String, path: String, body: JSONObject? = null): JSONObject =
        withContext(Dispatchers.IO) {
            val builder = Request.Builder().url(baseUrl + path)
            token?.let { builder.header("Authorization", "Bearer $it") }
            if (method == "GET") {
                builder.get()
            } else {
                val payload = (body ?: JSONObject()).toString()
                    .toRequestBody("application/json".toMediaType())
                builder.method(method, payload)
            }
            http.newCall(builder.build()).execute().use { response ->
                val text = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    val detail = runCatching { JSONObject(text).optString("detail") }
                        .getOrNull().orEmpty()
                    throw ApiException(response.code, detail.ifEmpty { "HTTP ${response.code}" })
                }
                // Arrays are wrapped so callers always get a JSONObject.
                if (text.trimStart().startsWith("[")) JSONObject("""{"items":$text}""")
                else if (text.isBlank()) JSONObject()
                else JSONObject(text)
            }
        }

    private companion object {
        const val KEY_SERVER = "server_url"
        const val KEY_TOKEN = "auth_token"
        // Android emulator loopback to a backend on the host machine.
        const val DEFAULT_SERVER = "http://10.0.2.2:8000"
    }
}
