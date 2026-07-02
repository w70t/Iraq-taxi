package com.taxione.iraq.ui

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AirportShuttle
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.LocalTaxi
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.taxione.core.location.LocationTracker
import com.taxione.core.map.MapPin
import com.taxione.core.map.PickupMap
import com.taxione.core.net.Geocoder
import com.taxione.core.ui.theme.Navy
import com.taxione.core.ui.theme.SafeGreen
import com.taxione.core.ui.theme.TaxiOrange
import com.taxione.iraq.R
import com.taxione.iraq.data.RideViewModel
import com.taxione.iraq.model.VehicleTier
import java.text.NumberFormat
import kotlinx.coroutines.delay

internal fun VehicleTier.icon(): ImageVector = when (this) {
    VehicleTier.ECONOMY -> Icons.Filled.DirectionsCar
    VehicleTier.FAMILY -> Icons.Filled.AirportShuttle
    VehicleTier.PREMIUM -> Icons.Filled.LocalTaxi
}

internal fun formatFare(fare: Int): String = NumberFormat.getIntegerInstance().format(fare)

// Baghdad — Tahrir Square, the fallback before the rider shares a location.
private const val DEFAULT_LAT = 33.3152
private const val DEFAULT_LNG = 44.3661

@Composable
fun RideScreen(rides: RideViewModel) {
    val context = LocalContext.current
    val tracker = remember { LocationTracker(context) }

    var pickupLat by rememberSaveable { mutableStateOf(DEFAULT_LAT) }
    var pickupLng by rememberSaveable { mutableStateOf(DEFAULT_LNG) }
    var pickupAddress by remember { mutableStateOf<String?>(null) }
    var recenter by remember { mutableStateOf<MapPin?>(null) }
    var awaitingFix by remember { mutableStateOf(false) }

    var destination by rememberSaveable { mutableStateOf("") }
    var selectedTier by rememberSaveable { mutableStateOf(VehicleTier.ECONOMY) }
    var showConfirmation by remember { mutableStateOf(false) }

    val lastLocation by tracker.lastLocation.collectAsStateWithLifecycle()

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        if (grants.values.any { it }) {
            awaitingFix = true
            tracker.start()
        }
    }

    // One GPS fix centres the map, then location stops — no continuous tracking.
    LaunchedEffect(lastLocation, awaitingFix) {
        val location = lastLocation
        if (awaitingFix && location != null) {
            awaitingFix = false
            recenter = MapPin(location.latitude, location.longitude)
            pickupLat = location.latitude
            pickupLng = location.longitude
            tracker.stop()
        }
    }
    DisposableEffect(Unit) { onDispose { tracker.stop() } }

    // Debounced Arabic address lookup for the point under the pin.
    LaunchedEffect(pickupLat, pickupLng) {
        pickupAddress = null
        delay(700)
        pickupAddress = Geocoder.reverse(context, pickupLat, pickupLng)
    }

    Box(Modifier.fillMaxSize().background(Navy)) {
        PickupMap(
            initial = MapPin(DEFAULT_LAT, DEFAULT_LNG),
            recenter = recenter,
            onCenterChanged = { lat, lng ->
                pickupLat = lat
                pickupLng = lng
            },
            modifier = Modifier.fillMaxSize(),
        )

        // Fixed pickup pin over the map centre.
        Icon(
            Icons.Filled.Place,
            contentDescription = stringResource(R.string.pickup_point),
            tint = TaxiOrange,
            modifier = Modifier
                .align(Alignment.Center)
                .size(46.dp)
                .offset(y = (-23).dp),
        )

        LanguageButton(
            Modifier
                .align(Alignment.TopEnd)
                .statusBarsPadding()
                .padding(12.dp)
        )

        Column(Modifier.align(Alignment.BottomCenter)) {
            FloatingActionButton(
                onClick = {
                    if (tracker.hasPermission()) {
                        awaitingFix = true
                        tracker.start()
                    } else {
                        permissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION,
                            )
                        )
                    }
                },
                containerColor = Navy,
                contentColor = SafeGreen,
                modifier = Modifier
                    .align(Alignment.End)
                    .padding(horizontal = 16.dp, vertical = 10.dp),
            ) {
                Icon(Icons.Filled.MyLocation, contentDescription = stringResource(R.string.my_location))
            }

            RequestSheet(
                pickupAddress = pickupAddress,
                destination = destination,
                onDestinationChange = { destination = it },
                selectedTier = selectedTier,
                onTierSelect = { selectedTier = it },
                onRequest = {
                    rides.requestRide(
                        destination = destination.trim(),
                        tier = selectedTier,
                        pickup = pickupAddress.orEmpty(),
                    )
                    showConfirmation = true
                },
            )
        }
    }

    if (showConfirmation) {
        AlertDialog(
            onDismissRequest = { showConfirmation = false },
            title = { Text(stringResource(R.string.request_received_title)) },
            text = { Text(stringResource(R.string.request_received_message)) },
            confirmButton = {
                TextButton(onClick = { showConfirmation = false }) {
                    Text(stringResource(R.string.ok), color = TaxiOrange)
                }
            },
        )
    }
}

@Composable
private fun LanguageButton(modifier: Modifier = Modifier) {
    var menuOpen by remember { mutableStateOf(false) }
    Box(modifier) {
        IconButton(
            onClick = { menuOpen = true },
            modifier = Modifier
                .clip(CircleShape)
                .background(Navy.copy(alpha = 0.9f)),
        ) {
            Icon(
                Icons.Filled.Language,
                contentDescription = stringResource(R.string.change_language),
                tint = Color.White,
            )
        }
        DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
            DropdownMenuItem(
                text = { Text(stringResource(R.string.language_arabic)) },
                onClick = { menuOpen = false; setAppLanguage("ar") },
            )
            DropdownMenuItem(
                text = { Text(stringResource(R.string.language_english)) },
                onClick = { menuOpen = false; setAppLanguage("en") },
            )
        }
    }
}

@Composable
private fun RequestSheet(
    pickupAddress: String?,
    destination: String,
    onDestinationChange: (String) -> Unit,
    selectedTier: VehicleTier,
    onTierSelect: (VehicleTier) -> Unit,
    onRequest: () -> Unit,
) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(topStart = 26.dp, topEnd = 26.dp))
            .background(Navy)
            .padding(start = 16.dp, end = 16.dp, top = 16.dp, bottom = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        // Pickup address detected from the pin — the Baly-style label.
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(contentAlignment = Alignment.Center) {
                Box(
                    Modifier
                        .size(26.dp)
                        .clip(CircleShape)
                        .background(SafeGreen.copy(alpha = 0.2f))
                )
                Box(
                    Modifier
                        .size(9.dp)
                        .clip(CircleShape)
                        .background(SafeGreen)
                )
            }
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    stringResource(R.string.pickup_point),
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.6f),
                )
                Text(
                    pickupAddress ?: stringResource(R.string.locating_address),
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    color = Color.White,
                )
            }
        }

        TextField(
            value = destination,
            onValueChange = onDestinationChange,
            singleLine = true,
            placeholder = { Text(stringResource(R.string.search_destination)) },
            leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null, tint = TaxiOrange) },
            trailingIcon = {
                if (destination.isNotEmpty()) {
                    IconButton(onClick = { onDestinationChange("") }) {
                        Icon(
                            Icons.Filled.Cancel,
                            contentDescription = stringResource(R.string.clear_destination),
                            tint = Color.White.copy(alpha = 0.45f),
                        )
                    }
                }
            },
            shape = RoundedCornerShape(18.dp),
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Color.White.copy(alpha = 0.13f),
                unfocusedContainerColor = Color.White.copy(alpha = 0.10f),
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent,
                cursorColor = TaxiOrange,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedPlaceholderColor = Color.White.copy(alpha = 0.5f),
                unfocusedPlaceholderColor = Color.White.copy(alpha = 0.5f),
            ),
            modifier = Modifier.fillMaxWidth(),
        )

        // Upfront prices per tier — visible before requesting, unlike Baly.
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            VehicleTier.entries.forEach { tier ->
                val isSelected = tier == selectedTier
                Column(
                    Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(16.dp))
                        .background(if (isSelected) TaxiOrange.copy(alpha = 0.22f) else Color.White.copy(alpha = 0.08f))
                        .clickable { onTierSelect(tier) }
                        .padding(vertical = 10.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(3.dp),
                ) {
                    Icon(
                        tier.icon(),
                        contentDescription = null,
                        tint = if (isSelected) TaxiOrange else Color.White.copy(alpha = 0.75f),
                        modifier = Modifier.size(26.dp),
                    )
                    Text(
                        stringResource(tier.label),
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                    )
                    Text(
                        stringResource(R.string.fare_amount, formatFare(tier.fare)),
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isSelected) TaxiOrange else Color.White.copy(alpha = 0.6f),
                    )
                }
            }
        }

        Button(
            onClick = onRequest,
            shape = RoundedCornerShape(18.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = TaxiOrange,
                contentColor = Color(0xFF221400),
            ),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(Icons.Filled.Bolt, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text(
                stringResource(R.string.request_now, stringResource(selectedTier.label)),
                fontWeight = FontWeight.Bold,
            )
        }
    }
}
