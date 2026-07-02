package com.taxione.core.net

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Free reverse geocoding via OpenStreetMap Nominatim: turns the point under
 * the pickup pin into an Arabic street/neighbourhood label, Baly-style.
 * Fair-use service — calls are debounced by the UI and carry the app's UA.
 */
object Geocoder {

    private val http = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(8, TimeUnit.SECONDS)
        .build()

    suspend fun reverse(context: Context, lat: Double, lng: Double): String? =
        withContext(Dispatchers.IO) {
            runCatching {
                val url = "https://nominatim.openstreetmap.org/reverse" +
                    "?format=jsonv2&lat=$lat&lon=$lng&zoom=17&accept-language=ar"
                val request = Request.Builder()
                    .url(url)
                    .header("User-Agent", "TaxiOneIraq/${context.packageName}")
                    .build()
                http.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) return@runCatching null
                    val body = JSONObject(response.body?.string().orEmpty())
                    body.optString("display_name")
                        .split(",")
                        .take(3)
                        .joinToString("، ") { it.trim() }
                        .ifBlank { null }
                }
            }.getOrNull()
        }
}
