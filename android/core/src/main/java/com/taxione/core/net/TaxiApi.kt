package com.taxione.core.net

import com.taxione.core.model.TripDto
import org.json.JSONObject

/** Typed wrappers over the backend endpoints used by the mobile apps. */
class TaxiApi(val client: ApiClient) {

    suspend fun requestOtp(phone: String, role: String): String? {
        val response = client.request(
            "POST", "/auth/otp/request",
            JSONObject().put("phone", phone).put("role", role),
        )
        // Present only when the server runs with OTP_ECHO=true (dev builds).
        return response.optString("debug_code").ifEmpty { null }
    }

    suspend fun verifyOtp(phone: String, role: String, code: String, name: String): String {
        val response = client.request(
            "POST", "/auth/otp/verify",
            JSONObject().put("phone", phone).put("role", role)
                .put("code", code).put("name", name),
        )
        val token = response.getString("access_token")
        client.token = token
        return token
    }

    suspend fun setOnline(online: Boolean, carModel: String = "", plate: String = "") {
        client.request(
            "POST", "/drivers/status",
            JSONObject().put("online", online).put("car_model", carModel).put("plate", plate),
        )
    }

    suspend fun sendLocation(lat: Double, lng: Double) {
        client.request("POST", "/drivers/location", JSONObject().put("lat", lat).put("lng", lng))
    }

    suspend fun openTrips(): List<TripDto> {
        val response = client.request("GET", "/drivers/trips/open")
        val items = response.optJSONArray("items") ?: return emptyList()
        return (0 until items.length()).map { TripDto.fromJson(items.getJSONObject(it)) }
    }

    suspend fun currentTrip(): TripDto? = try {
        TripDto.fromJson(client.request("GET", "/trips/current"))
    } catch (e: ApiException) {
        if (e.code == 404) null else throw e
    }

    suspend fun tripAction(tripId: String, action: String): TripDto =
        TripDto.fromJson(client.request("POST", "/trips/$tripId/$action"))

    suspend fun earnings(): Pair<Int, Int> {
        val response = client.request("GET", "/drivers/earnings")
        return response.optInt("total") to response.optInt("count")
    }
}
