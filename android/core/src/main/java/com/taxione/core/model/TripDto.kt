package com.taxione.core.model

import org.json.JSONObject

data class DriverInfo(
    val name: String,
    val carModel: String,
    val plate: String,
    val lat: Double?,
    val lng: Double?,
)

data class TripDto(
    val id: String,
    val status: String,
    val pickupLat: Double,
    val pickupLng: Double,
    val pickupLabel: String,
    val destLat: Double?,
    val destLng: Double?,
    val destLabel: String,
    val tier: String,
    val fareEstimate: Int,
    val paymentMethod: String,
    val paid: Boolean,
    val distanceKm: Double?,
    val driver: DriverInfo?,
) {
    companion object {
        fun fromJson(json: JSONObject): TripDto {
            val pickup = json.optJSONObject("pickup") ?: JSONObject()
            val dest = json.optJSONObject("destination") ?: JSONObject()
            val driverJson = json.optJSONObject("driver")
            return TripDto(
                id = json.optString("id"),
                status = json.optString("status"),
                pickupLat = pickup.optDouble("lat", 0.0),
                pickupLng = pickup.optDouble("lng", 0.0),
                pickupLabel = pickup.optString("label"),
                destLat = dest.optDouble("lat").takeIf { !it.isNaN() },
                destLng = dest.optDouble("lng").takeIf { !it.isNaN() },
                destLabel = dest.optString("label"),
                tier = json.optString("tier", "economy"),
                fareEstimate = json.optInt("fare_estimate"),
                paymentMethod = json.optString("payment_method", "cash"),
                paid = json.optBoolean("paid"),
                distanceKm = json.optDouble("distance_km").takeIf { !it.isNaN() },
                driver = driverJson?.let {
                    DriverInfo(
                        name = it.optString("name"),
                        carModel = it.optString("car_model"),
                        plate = it.optString("plate"),
                        lat = it.optDouble("lat").takeIf { v -> !v.isNaN() },
                        lng = it.optDouble("lng").takeIf { v -> !v.isNaN() },
                    )
                },
            )
        }
    }
}
