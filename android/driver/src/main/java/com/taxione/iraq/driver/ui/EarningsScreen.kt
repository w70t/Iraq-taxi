package com.taxione.iraq.driver.ui

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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.taxione.core.model.IncentivePlan
import com.taxione.core.ui.theme.SafeGreen
import com.taxione.core.ui.theme.TaxiOrange
import com.taxione.iraq.driver.DriverViewModel
import com.taxione.iraq.driver.R

private val CardShape = RoundedCornerShape(20.dp)
private val CardColor = Color.White.copy(alpha = 0.08f)

@Composable
fun EarningsScreen(vm: DriverViewModel) {
    val ui by vm.ui.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) { vm.loadEarnings() }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Text(
                stringResource(R.string.earnings_title),
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = Color.White,
            )
        }

        item {
            Column(
                Modifier
                    .fillMaxWidth()
                    .clip(CardShape)
                    .background(CardColor)
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text(
                    stringResource(R.string.earnings_total),
                    color = Color.White.copy(alpha = 0.7f),
                )
                Text(
                    stringResource(R.string.fare_amount, formatFare(ui.earningsTotal)),
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = SafeGreen,
                )
                Text(
                    "${ui.earningsCount} ${stringResource(R.string.earnings_trips)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.6f),
                )
            }
        }

        if (ui.incentives.isNotEmpty()) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        Icons.Filled.EmojiEvents,
                        contentDescription = null,
                        tint = TaxiOrange,
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        stringResource(R.string.incentives_title),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                    )
                    Spacer(Modifier.weight(1f))
                    Text(
                        stringResource(R.string.trips_today, ui.tripsToday),
                        style = MaterialTheme.typography.bodySmall,
                        color = SafeGreen,
                    )
                }
            }
            items(ui.incentives, key = { it.id }) { plan ->
                IncentiveCard(plan, ui.tripsToday)
            }
        }
    }
}

@Composable
private fun IncentiveCard(plan: IncentivePlan, tripsToday: Int) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(plan.title, fontWeight = FontWeight.Bold, color = Color.White)
        Text(
            plan.description,
            style = MaterialTheme.typography.bodySmall,
            color = Color.White.copy(alpha = 0.65f),
        )

        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                Icons.Filled.Timer,
                contentDescription = null,
                tint = TaxiOrange,
                modifier = Modifier.size(16.dp),
            )
            Spacer(Modifier.width(6.dp))
            val hours = plan.secondsRemaining / 3600
            val minutes = (plan.secondsRemaining % 3600) / 60
            Text(
                stringResource(R.string.time_remaining, hours, minutes),
                style = MaterialTheme.typography.bodySmall,
                color = TaxiOrange,
            )
        }

        // Progress ladder: each circle is a trip target, filled once reached.
        Row(
            Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            plan.steps.forEachIndexed { index, step ->
                val achieved = tripsToday >= step.trips
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Column(
                        Modifier
                            .size(42.dp)
                            .clip(CircleShape)
                            .background(if (achieved) SafeGreen else Color.White.copy(alpha = 0.1f)),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                    ) {
                        Text(
                            step.trips.toString(),
                            fontWeight = FontWeight.Bold,
                            color = if (achieved) Color(0xFF00210E) else Color.White,
                        )
                    }
                    Spacer(Modifier.height(4.dp))
                    Text(
                        stringResource(R.string.fare_amount, formatFare(step.bonus)),
                        style = MaterialTheme.typography.labelSmall,
                        color = if (achieved) SafeGreen else Color.White.copy(alpha = 0.6f),
                    )
                }
                if (index != plan.steps.lastIndex) {
                    Spacer(
                        Modifier
                            .weight(1f)
                            .padding(horizontal = 6.dp)
                            .height(3.dp)
                            .clip(CircleShape)
                            .background(
                                if (tripsToday >= plan.steps[index + 1].trips) SafeGreen
                                else Color.White.copy(alpha = 0.15f)
                            )
                    )
                }
            }
        }
    }
}
