package com.taxione.iraq.driver.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.SupportAgent
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.taxione.core.ui.theme.SafeGreen
import com.taxione.core.ui.theme.TaxiOrange
import com.taxione.iraq.driver.DriverViewModel
import com.taxione.iraq.driver.R

private val CardShape = RoundedCornerShape(20.dp)
private val CardColor = Color.White.copy(alpha = 0.08f)

@Composable
fun DriverAccountScreen(vm: DriverViewModel) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    var server by rememberSaveable { mutableStateOf(ui.serverUrl) }
    var complaintText by rememberSaveable { mutableStateOf("") }

    LaunchedEffect(Unit) { vm.loadComplaints() }
    LaunchedEffect(ui.complaintSent) {
        if (ui.complaintSent) {
            complaintText = ""
            vm.clearComplaintSent()
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            stringResource(R.string.account_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = Color.White,
        )

        SectionCard(stringResource(R.string.language_section)) {
            LanguageRow(stringResource(R.string.language_arabic), selected = isArabic()) {
                setAppLanguage("ar")
            }
            LanguageRow(stringResource(R.string.language_english), selected = !isArabic()) {
                setAppLanguage("en")
            }
        }

        SectionCard(stringResource(R.string.server_section)) {
            OutlinedTextField(
                value = server,
                onValueChange = { server = it },
                label = { Text(stringResource(R.string.server_label)) },
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = TaxiOrange,
                    unfocusedBorderColor = Color.White.copy(alpha = 0.3f),
                    focusedLabelColor = TaxiOrange,
                    unfocusedLabelColor = Color.White.copy(alpha = 0.5f),
                    cursorColor = TaxiOrange,
                ),
                modifier = Modifier.fillMaxWidth(),
            )
            TextButton(onClick = { vm.setServer(server) }) {
                Text(stringResource(R.string.save), color = TaxiOrange)
            }
        }

        SectionCard(stringResource(R.string.support_section)) {
            OutlinedTextField(
                value = complaintText,
                onValueChange = { complaintText = it },
                label = { Text(stringResource(R.string.complaint_hint)) },
                minLines = 2,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = TaxiOrange,
                    unfocusedBorderColor = Color.White.copy(alpha = 0.3f),
                    focusedLabelColor = TaxiOrange,
                    unfocusedLabelColor = Color.White.copy(alpha = 0.5f),
                    cursorColor = TaxiOrange,
                ),
                modifier = Modifier.fillMaxWidth(),
            )
            TextButton(
                onClick = { vm.submitComplaint(complaintText) },
                enabled = complaintText.trim().length >= 3 && !ui.busy,
            ) {
                Icon(
                    Icons.Filled.SupportAgent,
                    contentDescription = null,
                    tint = TaxiOrange,
                    modifier = Modifier.size(18.dp),
                )
                Text("  " + stringResource(R.string.send_complaint), color = TaxiOrange)
            }
            ui.complaints.forEach { complaint ->
                Column {
                    Text(
                        complaint.text,
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White,
                    )
                    Text(
                        stringResource(
                            if (complaint.status == "resolved") R.string.complaint_resolved
                            else R.string.complaint_open
                        ),
                        style = MaterialTheme.typography.labelSmall,
                        color = if (complaint.status == "resolved") SafeGreen else TaxiOrange,
                    )
                }
            }
        }

        SectionCard(stringResource(R.string.privacy_section)) {
            IconRow(Icons.Filled.MyLocation, stringResource(R.string.privacy_location))
            IconRow(Icons.Filled.Lock, stringResource(R.string.privacy_storage))
        }

        SectionCard(null) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .clickable { vm.logout() }
                    .padding(vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Icon(
                    Icons.Filled.Logout,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error,
                )
                Text(
                    stringResource(R.string.logout),
                    color = MaterialTheme.colorScheme.error,
                    fontWeight = FontWeight.SemiBold,
                )
            }
        }
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
        Text(label, color = Color.White)
    }
}

@Composable
private fun IconRow(icon: ImageVector, text: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Icon(icon, contentDescription = null, tint = SafeGreen, modifier = Modifier.size(20.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium, color = Color.White)
    }
}
