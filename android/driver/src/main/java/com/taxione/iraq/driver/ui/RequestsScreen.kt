package com.taxione.iraq.driver.ui

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Navigation
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.TripOrigin
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.repeatOnLifecycle
import com.taxione.core.location.LocationTracker
import com.taxione.core.map.MapPin
import com.taxione.core.map.OsmMap
import com.taxione.core.model.TripDto
import com.taxione.core.nav.navigateWithWaze
import com.taxione.core.ui.theme.SafeGreen
import com.taxione.core.ui.theme.TaxiOrange
import com.taxione.iraq.driver.DriverViewModel
import com.taxione.iraq.driver.R
import java.text.NumberFormat
import kotlinx.coroutines.delay

private val CardShape = RoundedCornerShape(20.dp)
private val CardColor = Color.White.copy(alpha = 0.08f)

internal fun formatFare(fare: Int): String = NumberFormat.getIntegerInstance().format(fare)

@Composable
fun RequestsScreen(vm: DriverViewModel) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val tracker = remember { LocationTracker(context) }
    var permissionDenied by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        if (grants.values.any { it }) {
            permissionDenied = false
            tracker.start()
            vm.setOnline(true)
        } else {
            permissionDenied = true
        }
    }

    // Poll the server while the screen is in the foreground; the loop pauses
    // automatically in the background, which also stops location sharing.
    val lifecycleOwner = LocalLifecycleOwner.current
    LaunchedEffect(Unit) {
        lifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            while (true) {
                vm.refresh()
                val location = tracker.lastLocation.value
                if (location != null) {
                    vm.sendLocation(location.latitude, location.longitude)
                }
                delay(4_000)
            }
        }
    }
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_STOP) tracker.stop()
            if (event == Lifecycle.Event.ON_START && vm.ui.value.online) tracker.start()
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            tracker.stop()
        }
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            OnlineCard(
                online = ui.online,
                permissionDenied = permissionDenied,
                onToggle = { enabled ->
                    when {
                        !enabled -> {
                            tracker.stop()
                            vm.setOnline(false)
                        }
                        tracker.hasPermission() -> {
                            tracker.start()
                            vm.setOnline(true)
                        }
                        else -> permissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION,
                            )
                        )
                    }
                },
            )
        }

        ui.error?.let { error ->
            item {
                Text(
                    stringResource(R.string.error_generic, error),
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        val active = ui.activeTrip
        if (active != null) {
            item { SectionTitle(stringResource(R.string.active_trip)) }
            item { ActiveTripCard(active, vm) }
        } else {
            item { SectionTitle(stringResource(R.string.open_requests)) }
            if (!ui.online) {
                item { HintCard(stringResource(R.string.go_online_hint)) }
            } else if (ui.openTrips.isEmpty()) {
                item { HintCard(stringResource(R.string.no_requests)) }
            } else {
                items(ui.openTrips, key = { it.id }) { trip ->
                    OpenTripCard(trip) { vm.accept(trip.id) }
                }
            }
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text,
        style = MaterialTheme.typography.titleMedium,
        fontWeight = FontWeight.Bold,
        color = Color.White,
    )
}

@Composable
private fun OnlineCard(online: Boolean, permissionDenied: Boolean, onToggle: (Boolean) -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(
                    stringResource(R.string.online_title),
                    fontWeight = FontWeight.SemiBold,
                    color = Color.White,
                )
                Text(
                    stringResource(R.string.online_caption),
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.62f),
                )
            }
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = online,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedTrackColor = SafeGreen,
                    checkedThumbColor = Color.White,
                ),
            )
        }
        if (permissionDenied) {
            Text(
                stringResource(R.string.location_permission_needed),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
}

@Composable
private fun HintCard(text: String) {
    Text(
        text,
        color = Color.White.copy(alpha = 0.6f),
        style = MaterialTheme.typography.bodyMedium,
        modifier = Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(20.dp),
    )
}

@Composable
private fun TripRoute(trip: TripDto) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            Icons.Filled.TripOrigin,
            contentDescription = null,
            tint = SafeGreen,
            modifier = Modifier.size(16.dp),
        )
        Spacer(Modifier.width(8.dp))
        Text(
            trip.pickupLabel.ifBlank { stringResource(R.string.pickup_label) },
            color = Color.White,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            Icons.Filled.Place,
            contentDescription = null,
            tint = TaxiOrange,
            modifier = Modifier.size(16.dp),
        )
        Spacer(Modifier.width(8.dp))
        Text(
            trip.destLabel.ifBlank { stringResource(R.string.no_destination) },
            color = Color.White,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun OpenTripCard(trip: TripDto, onAccept: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                TripRoute(trip)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    stringResource(R.string.fare_amount, formatFare(trip.fareEstimate)),
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                )
                trip.distanceKm?.let {
                    Text(
                        stringResource(R.string.distance_away, it.toString()),
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.6f),
                    )
                }
            }
        }
        ActionButton(stringResource(R.string.accept), onAccept)
    }
}

@Composable
private fun ActiveTripCard(trip: TripDto, vm: DriverViewModel) {
    val context = LocalContext.current
    val statusRes = when (trip.status) {
        "accepted" -> R.string.status_accepted
        "arrived" -> R.string.status_arrived
        else -> R.string.status_in_progress
    }

    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(
            stringResource(statusRes),
            fontWeight = FontWeight.Bold,
            color = TaxiOrange,
        )
        TripRoute(trip)
        Text(
            stringResource(R.string.fare_amount, formatFare(trip.fareEstimate)),
            fontWeight = FontWeight.SemiBold,
            color = Color.White,
        )

        OsmMap(
            center = MapPin(trip.pickupLat, trip.pickupLng),
            pins = buildList {
                add(MapPin(trip.pickupLat, trip.pickupLng, trip.pickupLabel))
                if (trip.destLat != null && trip.destLng != null) {
                    add(MapPin(trip.destLat, trip.destLng, trip.destLabel))
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(180.dp)
                .clip(RoundedCornerShape(14.dp)),
        )

        // Waze gets the pickup point before the ride starts, then the destination.
        val navTarget = if (trip.status == "in_progress" && trip.destLat != null && trip.destLng != null) {
            trip.destLat to trip.destLng
        } else {
            trip.pickupLat to trip.pickupLng
        }
        Button(
            onClick = { navigateWithWaze(context, navTarget.first, navTarget.second) },
            shape = RoundedCornerShape(14.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF33CCFF),
                contentColor = Color(0xFF00222E),
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(Icons.Filled.Navigation, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text(stringResource(R.string.navigate_waze), fontWeight = FontWeight.Bold)
        }

        when (trip.status) {
            "accepted" -> ActionButton(stringResource(R.string.btn_arrived)) { vm.tripAction("arrived") }
            "arrived" -> ActionButton(stringResource(R.string.btn_start)) { vm.tripAction("start") }
            "in_progress" -> ActionButton(stringResource(R.string.btn_complete)) { vm.tripAction("complete") }
        }
        if (trip.status in listOf("accepted", "arrived")) {
            TextButton(onClick = { vm.tripAction("cancel") }) {
                Text(stringResource(R.string.btn_cancel), color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun ActionButton(label: String, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        shape = RoundedCornerShape(14.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = TaxiOrange,
            contentColor = Color(0xFF221400),
        ),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(label, fontWeight = FontWeight.Bold)
    }
}
