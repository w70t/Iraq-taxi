package com.taxione.iraq.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.DeleteForever
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.taxione.iraq.R
import com.taxione.iraq.data.RideViewModel
import com.taxione.iraq.ui.theme.SafeGreen
import com.taxione.iraq.ui.theme.TaxiOrange

private val CardShape = RoundedCornerShape(20.dp)
private val CardColor = Color.White.copy(alpha = 0.08f)

@Composable
fun AccountScreen(rides: RideViewModel) {
    var showDeleteConfirm by remember { mutableStateOf(false) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            stringResource(R.string.tab_account),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )

        SectionCard(stringResource(R.string.account_section)) {
            InfoRow(stringResource(R.string.name_label), stringResource(R.string.default_user_name))
            InfoRow(stringResource(R.string.payment_label), stringResource(R.string.payment_cash))
        }

        SectionCard(stringResource(R.string.language_section)) {
            LanguageRow(stringResource(R.string.language_arabic), selected = isArabic()) {
                setAppLanguage("ar")
            }
            LanguageRow(stringResource(R.string.language_english), selected = !isArabic()) {
                setAppLanguage("en")
            }
        }

        SectionCard(stringResource(R.string.privacy_section)) {
            IconRow(Icons.Filled.MyLocation, stringResource(R.string.privacy_location))
            IconRow(Icons.Filled.Lock, stringResource(R.string.privacy_storage))
            IconRow(Icons.Filled.CloudOff, stringResource(R.string.privacy_no_network))
        }

        SectionCard(null) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .clickable { showDeleteConfirm = true }
                    .padding(vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Icon(
                    Icons.Filled.DeleteForever,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error,
                )
                Text(
                    stringResource(R.string.delete_data),
                    color = MaterialTheme.colorScheme.error,
                    fontWeight = FontWeight.SemiBold,
                )
            }
            Text(
                stringResource(R.string.delete_data_caption),
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.6f),
            )
        }
    }

    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text(stringResource(R.string.delete_data_confirm_title)) },
            text = { Text(stringResource(R.string.delete_data_confirm_message)) },
            confirmButton = {
                TextButton(onClick = {
                    rides.clearAllData()
                    showDeleteConfirm = false
                }) {
                    Text(stringResource(R.string.delete), color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) {
                    Text(stringResource(R.string.cancel), color = TaxiOrange)
                }
            },
        )
    }
}

@Composable
private fun SectionCard(title: String?, content: @Composable () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(CardShape)
            .background(CardColor)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (title != null) {
            Text(
                title,
                style = MaterialTheme.typography.titleSmall,
                color = Color.White.copy(alpha = 0.7f),
            )
        }
        content()
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = Color.White.copy(alpha = 0.7f))
        Spacer(Modifier.weight(1f))
        Text(value, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun LanguageRow(label: String, selected: Boolean, onSelect: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .clickable(onClick = onSelect),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(
            selected = selected,
            onClick = onSelect,
            colors = RadioButtonDefaults.colors(
                selectedColor = TaxiOrange,
                unselectedColor = Color.White.copy(alpha = 0.5f),
            ),
        )
        Text(label)
    }
}

@Composable
private fun IconRow(icon: ImageVector, text: String) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Icon(icon, contentDescription = null, tint = SafeGreen, modifier = Modifier.size(20.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}
