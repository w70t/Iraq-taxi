package com.taxione.iraq.ui

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AirportShuttle
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.LocalTaxi
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.geometry.CornerRadius
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.taxione.iraq.R
import com.taxione.iraq.data.LocationTracker
import com.taxione.iraq.data.RideViewModel
import com.taxione.iraq.model.VehicleTier
import com.taxione.iraq.ui.theme.Navy
import com.taxione.iraq.ui.theme.SafeGreen
import com.taxione.iraq.ui.theme.TaxiOrange
import java.text.NumberFormat

private val CardShape = RoundedCornerShape(22.dp)
private val CardColor = Color.White.copy(alpha = 0.08f)

internal fun VehicleTier.icon(): ImageVector = when (this) {
    VehicleTier.ECONOMY -> Icons.Filled.DirectionsCar
    VehicleTier.FAMILY -> Icons.Filled.AirportShuttle
    VehicleTier.PREMIUM -> Icons.Filled.LocalTaxi
}

internal fun formatFare(fare: Int): String = NumberFormat.getIntegerInstance().format(fare)

@Composable
fun RideScreen(rides: RideViewModel) {
    val context = LocalContext.current
    val tracker = remember { LocationTracker(context) }
    val isSharing by tracker.isSharing.collectAsStateWithLifecycle()

    var destination by rememberSaveable { mutableStateOf("") }
    var selectedTier by rememberSaveable { mutableStateOf(VehicleTier.ECONOMY) }
    var showConfirmation by remember { mutableStateOf(false) }
    var permissionDenied by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        if (grants.values.any { it }) {
            permissionDenied = false
            tracker.start()
        } else {
            permissionDenied = true
        }
    }

    // Privacy guard: location updates stop whenever the app leaves the foreground.
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_STOP) tracker.stop()
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            tracker.stop()
        }
    }

    Box(Modifier.fillMaxSize().background(Navy)) {
        MovingRoad()

        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Header()
            PickupCard()
            LocationCard(
                isSharing = isSharing,
                permissionDenied = permissionDenied,
                onToggle = { enabled ->
                    when {
                        !enabled -> tracker.stop()
                        tracker.hasPermission() -> tracker.start()
                        else -> permissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION,
                            )
                        )
                    }
                },
            )
            DestinationField(destination) { destination = it }
            TierChooser(selectedTier) { selectedTier = it }
            RequestButton(selectedTier) {
                rides.requestRide(destination.trim(), selectedTier)
                showConfirmation = true
            }
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
private fun Header() {
    var menuOpen by remember { mutableStateOf(false) }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(
                stringResource(R.string.welcome_title),
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
            )
            Text(
                stringResource(R.string.welcome_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.65f),
            )
        }
        Box {
            IconButton(
                onClick = { menuOpen = true },
                modifier = Modifier
                    .clip(CircleShape)
                    .background(Color.White.copy(alpha = 0.12f)),
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
}

@Composable
private fun PickupCard() {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Box(contentAlignment = Alignment.Center) {
            Box(
                Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(SafeGreen.copy(alpha = 0.2f))
            )
            Box(
                Modifier
                    .size(12.dp)
                    .clip(CircleShape)
                    .background(SafeGreen)
            )
        }
        Column(Modifier.weight(1f)) {
            Text(
                stringResource(R.string.pickup_label),
                style = MaterialTheme.typography.labelSmall,
                color = Color.White.copy(alpha = 0.6f),
            )
            Text(
                stringResource(R.string.pickup_current),
                fontWeight = FontWeight.SemiBold,
            )
        }
        Icon(Icons.Filled.MyLocation, contentDescription = null, tint = SafeGreen)
    }
}

@Composable
private fun LocationCard(
    isSharing: Boolean,
    permissionDenied: Boolean,
    onToggle: (Boolean) -> Unit,
) {
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
                    stringResource(R.string.share_location_title),
                    fontWeight = FontWeight.SemiBold,
                )
                Text(
                    stringResource(R.string.share_location_caption),
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.62f),
                )
            }
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = isSharing,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedTrackColor = SafeGreen,
                    checkedThumbColor = Color.White,
                ),
            )
        }
        if (permissionDenied) {
            Text(
                stringResource(R.string.location_permission_denied),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
}

@Composable
private fun DestinationField(value: String, onValueChange: (String) -> Unit) {
    TextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        placeholder = { Text(stringResource(R.string.search_destination)) },
        leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null, tint = TaxiOrange) },
        trailingIcon = {
            if (value.isNotEmpty()) {
                IconButton(onClick = { onValueChange("") }) {
                    Icon(
                        Icons.Filled.Cancel,
                        contentDescription = stringResource(R.string.clear_destination),
                        tint = Color.White.copy(alpha = 0.45f),
                    )
                }
            }
        },
        shape = CardShape,
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
}

@Composable
private fun TierChooser(selected: VehicleTier, onSelect: (VehicleTier) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            stringResource(R.string.choose_ride),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
        )
        VehicleTier.entries.forEach { tier ->
            val isSelected = tier == selected
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(20.dp))
                    .background(if (isSelected) TaxiOrange.copy(alpha = 0.2f) else CardColor)
                    .clickable { onSelect(tier) }
                    .padding(15.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                Icon(
                    tier.icon(),
                    contentDescription = null,
                    tint = if (isSelected) TaxiOrange else Color.White.copy(alpha = 0.75f),
                    modifier = Modifier.size(32.dp),
                )
                Column(Modifier.weight(1f)) {
                    Text(stringResource(tier.label), fontWeight = FontWeight.Bold)
                    Text(
                        stringResource(tier.caption),
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.62f),
                    )
                }
                Text(
                    stringResource(R.string.fare_amount, formatFare(tier.fare)),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@Composable
private fun RequestButton(tier: VehicleTier, onRequest: () -> Unit) {
    Button(
        onClick = onRequest,
        shape = RoundedCornerShape(20.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = TaxiOrange,
            contentColor = Color(0xFF221400),
        ),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(19.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Icon(Icons.Filled.Bolt, contentDescription = null)
        Spacer(Modifier.width(8.dp))
        Text(
            stringResource(R.string.request_now, stringResource(tier.label)),
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun MovingRoad() {
    val transition = rememberInfiniteTransition(label = "road")
    val shift by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1400, easing = LinearEasing)),
        label = "shift",
    )
    Canvas(Modifier.fillMaxSize()) {
        val dashHeight = 30.dp.toPx()
        val gap = 46.dp.toPx()
        val step = dashHeight + gap
        val dashWidth = 8.dp.toPx()
        val corner = CornerRadius(dashWidth / 2)
        rotate(32f) {
            listOf(size.width * 0.3f, size.width * 0.72f).forEach { x ->
                var y = -step + shift * step
                while (y < size.height + step) {
                    drawRoundRect(
                        color = Color.White.copy(alpha = 0.09f),
                        topLeft = Offset(x, y),
                        size = Size(dashWidth, dashHeight),
                        cornerRadius = corner,
                    )
                    y += step
                }
            }
        }
    }
}
