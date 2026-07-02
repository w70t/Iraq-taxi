package com.taxione.iraq.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Person
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
                if (ride.driverName != null && ride.driverCar != null) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Filled.Person,
                            contentDescription = null,
                            tint = TaxiOrange,
                            modifier = Modifier.size(18.dp),
                        )
                        Spacer(Modifier.size(8.dp))
                        Text(
                            "${ride.driverName} · ${ride.driverCar}",
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
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
