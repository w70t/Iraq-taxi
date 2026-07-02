package com.taxione.iraq.data

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import com.taxione.core.security.SecureStorage
import com.taxione.iraq.model.Ride
import com.taxione.iraq.model.RideStatus
import com.taxione.iraq.model.VehicleTier
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONArray
import org.json.JSONObject

class RideViewModel(application: Application) : AndroidViewModel(application) {

    private val storage = SecureStorage(application)

    private val _currentRide = MutableStateFlow<Ride?>(null)
    val currentRide: StateFlow<Ride?> = _currentRide.asStateFlow()

    private val _history = MutableStateFlow<List<Ride>>(emptyList())
    val history: StateFlow<List<Ride>> = _history.asStateFlow()

    init {
        restore()
    }

    fun requestRide(destination: String, tier: VehicleTier) {
        _currentRide.value = Ride(
            destination = destination,
            tier = tier,
            fare = tier.fare,
            status = RideStatus.SEARCHING,
        )
        persist()
    }

    fun simulateDriverAccepted() {
        val ride = _currentRide.value ?: return
        if (ride.status != RideStatus.SEARCHING) return
        _currentRide.value = ride.copy(
            status = RideStatus.DRIVER_ARRIVING,
            driverName = DEMO_DRIVER_NAME,
            driverCar = DEMO_DRIVER_CAR,
        )
        persist()
    }

    fun startRide() {
        val ride = _currentRide.value ?: return
        if (ride.status != RideStatus.DRIVER_ARRIVING) return
        _currentRide.value = ride.copy(status = RideStatus.IN_PROGRESS)
        persist()
    }

    fun completeRide() {
        val ride = _currentRide.value ?: return
        _history.value = listOf(ride.copy(status = RideStatus.COMPLETED)) + _history.value
        _currentRide.value = null
        persist()
    }

    fun cancelRide() {
        val ride = _currentRide.value ?: return
        _history.value = listOf(ride.copy(status = RideStatus.CANCELLED)) + _history.value
        _currentRide.value = null
        persist()
    }

    /** Erases everything this app stored on the device. */
    fun clearAllData() {
        _currentRide.value = null
        _history.value = emptyList()
        storage.clear()
    }

    private fun persist() {
        val root = JSONObject()
        _currentRide.value?.let { root.put("current", it.toJson()) }
        root.put("history", JSONArray().apply { _history.value.forEach { put(it.toJson()) } })
        storage.putString(KEY_RIDES, root.toString())
    }

    private fun restore() {
        val raw = storage.getString(KEY_RIDES) ?: return
        runCatching {
            val root = JSONObject(raw)
            _currentRide.value = root.optJSONObject("current")?.let(Ride::fromJson)
            val entries = root.optJSONArray("history") ?: JSONArray()
            _history.value = (0 until entries.length()).mapNotNull { index ->
                runCatching { Ride.fromJson(entries.getJSONObject(index)) }.getOrNull()
            }
        }
    }

    private companion object {
        const val KEY_RIDES = "rides"
        const val DEMO_DRIVER_NAME = "علي كريم"
        const val DEMO_DRIVER_CAR = "Toyota Corolla · 27 أ ب 1234"
    }
}
