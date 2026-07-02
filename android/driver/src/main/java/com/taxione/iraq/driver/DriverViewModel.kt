package com.taxione.iraq.driver

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.taxione.core.model.TripDto
import com.taxione.core.net.ApiClient
import com.taxione.core.net.TaxiApi
import com.taxione.core.security.SecureStorage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class DriverUi(
    val loggedIn: Boolean = false,
    val busy: Boolean = false,
    val error: String? = null,
    val debugCode: String? = null,
    val online: Boolean = false,
    val openTrips: List<TripDto> = emptyList(),
    val activeTrip: TripDto? = null,
    val earningsTotal: Int = 0,
    val earningsCount: Int = 0,
    val serverUrl: String = "",
    val carModel: String = "",
    val plate: String = "",
)

class DriverViewModel(application: Application) : AndroidViewModel(application) {

    private val storage = SecureStorage(application)
    private val api = TaxiApi(ApiClient(storage))

    private val _ui = MutableStateFlow(
        DriverUi(
            loggedIn = api.client.loggedIn,
            serverUrl = api.client.baseUrl,
            carModel = storage.getString(KEY_CAR).orEmpty(),
            plate = storage.getString(KEY_PLATE).orEmpty(),
        )
    )
    val ui: StateFlow<DriverUi> = _ui.asStateFlow()

    private fun launchBusy(block: suspend () -> Unit) {
        viewModelScope.launch {
            _ui.update { it.copy(busy = true, error = null) }
            try {
                block()
            } catch (e: Exception) {
                _ui.update { it.copy(error = e.message ?: e.javaClass.simpleName) }
            } finally {
                _ui.update { it.copy(busy = false) }
            }
        }
    }

    fun requestOtp(phone: String) = launchBusy {
        val code = api.requestOtp(phone.trim(), "driver")
        _ui.update { it.copy(debugCode = code) }
    }

    fun verify(phone: String, code: String, name: String, car: String, plate: String) = launchBusy {
        api.verifyOtp(phone.trim(), "driver", code.trim(), name.trim())
        storage.putString(KEY_CAR, car.trim())
        storage.putString(KEY_PLATE, plate.trim())
        _ui.update {
            it.copy(loggedIn = true, debugCode = null, carModel = car.trim(), plate = plate.trim())
        }
    }

    fun setServer(url: String) {
        api.client.baseUrl = url
        _ui.update { it.copy(serverUrl = api.client.baseUrl) }
    }

    fun setOnline(online: Boolean) = launchBusy {
        api.setOnline(online, _ui.value.carModel, _ui.value.plate)
        _ui.update { it.copy(online = online, openTrips = if (online) it.openTrips else emptyList()) }
    }

    fun sendLocation(lat: Double, lng: Double) {
        viewModelScope.launch { runCatching { api.sendLocation(lat, lng) } }
    }

    suspend fun refresh() {
        try {
            val active = api.currentTrip()
            val open = if (active == null && _ui.value.online) api.openTrips() else emptyList()
            _ui.update { it.copy(activeTrip = active, openTrips = open, error = null) }
        } catch (e: Exception) {
            _ui.update { it.copy(error = e.message ?: e.javaClass.simpleName) }
        }
    }

    fun accept(tripId: String) = launchBusy {
        val trip = api.tripAction(tripId, "accept")
        _ui.update { it.copy(activeTrip = trip, openTrips = emptyList()) }
    }

    fun tripAction(action: String) = launchBusy {
        val trip = _ui.value.activeTrip ?: return@launchBusy
        val updated = api.tripAction(trip.id, action)
        val stillActive = updated.status !in listOf("completed", "cancelled")
        _ui.update { it.copy(activeTrip = if (stillActive) updated else null) }
    }

    fun loadEarnings() = launchBusy {
        val (total, count) = api.earnings()
        _ui.update { it.copy(earningsTotal = total, earningsCount = count) }
    }

    fun logout() {
        api.client.token = null
        _ui.value = DriverUi(loggedIn = false, serverUrl = api.client.baseUrl)
    }

    private companion object {
        const val KEY_CAR = "car_model"
        const val KEY_PLATE = "plate"
    }
}
