package com.taxione.iraq.model

import androidx.annotation.StringRes
import com.taxione.iraq.R
import org.json.JSONObject
import java.util.UUID

enum class RideStatus(@StringRes val label: Int) {
    SEARCHING(R.string.status_searching),
    DRIVER_ASSIGNED(R.string.status_driver_assigned),
    DRIVER_ARRIVING(R.string.status_driver_arriving),
    IN_PROGRESS(R.string.status_in_progress),
    COMPLETED(R.string.status_completed),
    CANCELLED(R.string.status_cancelled),
}

enum class VehicleTier(
    @StringRes val label: Int,
    @StringRes val caption: Int,
    val fare: Int,
) {
    ECONOMY(R.string.tier_economy, R.string.tier_economy_caption, 5_000),
    FAMILY(R.string.tier_family, R.string.tier_family_caption, 8_000),
    PREMIUM(R.string.tier_premium, R.string.tier_premium_caption, 12_000),
}

data class Ride(
    val id: String = UUID.randomUUID().toString(),
    val pickup: String = "",
    val destination: String,
    val tier: VehicleTier,
    val fare: Int,
    val status: RideStatus,
    val createdAt: Long = System.currentTimeMillis(),
    val driverName: String? = null,
    val driverCar: String? = null,
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("id", id)
        put("pickup", pickup)
        put("destination", destination)
        put("tier", tier.name)
        put("fare", fare)
        put("status", status.name)
        put("createdAt", createdAt)
        driverName?.let { put("driverName", it) }
        driverCar?.let { put("driverCar", it) }
    }

    companion object {
        fun fromJson(json: JSONObject): Ride = Ride(
            id = json.optString("id", UUID.randomUUID().toString()),
            pickup = json.optString("pickup"),
            destination = json.optString("destination"),
            tier = runCatching { VehicleTier.valueOf(json.optString("tier")) }
                .getOrDefault(VehicleTier.ECONOMY),
            fare = json.optInt("fare"),
            status = runCatching { RideStatus.valueOf(json.optString("status")) }
                .getOrDefault(RideStatus.COMPLETED),
            createdAt = json.optLong("createdAt", System.currentTimeMillis()),
            driverName = json.optString("driverName").ifEmpty { null },
            driverCar = json.optString("driverCar").ifEmpty { null },
        )
    }
}
