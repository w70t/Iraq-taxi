package com.taxione.iraq.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Place
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.taxione.iraq.R
import com.taxione.iraq.data.RideViewModel
import com.taxione.iraq.model.Ride
import com.taxione.iraq.model.RideStatus
import com.taxione.core.ui.theme.TaxiOrange

private val CardShape = RoundedCornerShape(20.dp)
private val CardColor = Color.White.copy(alpha = 0.08f)

@Composable
fun TripsScreen(rides: RideViewModel) {
    val current by rides.currentRide.collectAsStateWithLifecycle()
    val history by rides.history.collectAsStateWithLifecycle()

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text(
                stringResource(R.string.tab_trips),
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
            )
        }

        current?.let { ride ->
            item { SectionTitle(stringResource(R.string.current_ride)) }
            item {
                RideCard(ride) {
                    RideActions(ride, rides)
                }
            }
        }

        item { SectionTitle(stringResource(R.string.previous_rides)) }

        if (history.isEmpty()) {
            item { EmptyHistory() }
        } else {
            items(history, key = { it.id }) { ride ->
                RideCard(ride)
            }
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text,
        style = MaterialTheme.typography.titleMedium,
        fontWeight = FontWeight.SemiBold,
        color = Color.White.copy(alpha = 0.8f),
        modifier = Modifier.padding(top = 8.dp),
    )
}

@Composable
private fun RideCard(ride: Ride, actions: (@Composable () -> Unit)? = null) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Filled.DirectionsCar,
                contentDescription = null,
                tint = TaxiOrange,
                modifier = Modifier.size(22.dp),
            )
            Spacer(Modifier.size(8.dp))
            Text(stringResource(ride.tier.label), fontWeight = FontWeight.Bold)
            Spacer(Modifier.weight(1f))
            Text(
                stringResource(R.string.fare_amount, formatFare(ride.fare)),
                fontWeight = FontWeight.SemiBold,
            )
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Filled.Place,
                contentDescription = null,
                tint = Color.White.copy(alpha = 0.7f),
                modifier = Modifier.size(18.dp),
            )
            Spacer(Modifier.size(8.dp))
            Text(
                ride.destination.ifBlank { stringResource(R.string.destination_unset) },
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        Text(
            stringResource(ride.status.label),
            style = MaterialTheme.typography.bodySmall,
            color = Color.White.copy(alpha = 0.6f),
        )
        actions?.invoke()
    }
}

@Composable
private fun RideActions(ride: Ride, rides: RideViewModel) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        when (ride.status) {
            RideStatus.SEARCHING -> {
                ActionButton(stringResource(R.string.simulate_acceptance)) {
                    rides.simulateDriverAccepted()
                }
                TextButton(onClick = { rides.cancelRide() }) {
                    Text(
                        stringResource(R.string.cancel_request),
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }

            RideStatus.DRIVER_ASSIGNED, RideStatus.DRIVER_ARRIVING -> {
                if (ride.driverName != null) {
                    DriverProfileRow(ride)
                }
                ActionButton(stringResource(R.string.start_ride)) { rides.startRide() }
            }

            RideStatus.IN_PROGRESS -> {
                ActionButton(stringResource(R.string.complete_ride)) { rides.completeRide() }
            }

            else -> Unit
        }
    }
}

/** The rider's view of who is coming: avatar, name, car with its real color, and plate. */
@Composable
private fun DriverProfileRow(ride: Ride) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White.copy(alpha = 0.06f))
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        // Photo placeholder: the driver's photo replaces this once the live
        // trip system is connected; until then a monogram keeps it personal.
        Box(
            Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(Color(0xFF1D2F4C))
                .border(2.dp, TaxiOrange.copy(alpha = 0.6f), CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                ride.driverName?.trim()?.firstOrNull()?.toString() ?: "؟",
                color = TaxiOrange,
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp,
            )
        }
        Column(Modifier.weight(1f)) {
            Text(ride.driverName.orEmpty(), fontWeight = FontWeight.Bold)
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                ride.driverColor?.let { hex ->
                    val carColor = runCatching {
                        Color(android.graphics.Color.parseColor(hex))
                    }.getOrDefault(Color.Gray)
                    Box(
                        Modifier
                            .size(13.dp)
                            .clip(RoundedCornerShape(4.dp))
                            .background(carColor)
                            .border(1.dp, Color.White.copy(alpha = 0.4f), RoundedCornerShape(4.dp))
                    )
                }
                Text(
                    ride.driverCar.orEmpty(),
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.7f),
                )
            }
        }
        ride.driverPlate?.let { PlateChip(it) }
    }
}

/** Iraqi-style licence plate chip: light body with a red side band. */
@Composable
private fun PlateChip(plate: String) {
    Row(
        Modifier.clip(RoundedCornerShape(6.dp)),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier
                .width(6.dp)
                .height(30.dp)
                .background(Color(0xFFD64545))
        )
        Text(
            plate,
            color = Color(0xFF111111),
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp,
            modifier = Modifier
                .background(Color(0xFFF4F4F4))
                .height(30.dp)
                .padding(horizontal = 9.dp, vertical = 4.dp),
        )
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

@Composable
private fun EmptyHistory() {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(
            Icons.Filled.DirectionsCar,
            contentDescription = null,
            tint = Color.White.copy(alpha = 0.4f),
            modifier = Modifier.size(44.dp),
        )
        Text(
            stringResource(R.string.no_rides_title),
            fontWeight = FontWeight.SemiBold,
        )
        Text(
            stringResource(R.string.no_rides_caption),
            style = MaterialTheme.typography.bodySmall,
            color = Color.White.copy(alpha = 0.6f),
        )
    }
}
