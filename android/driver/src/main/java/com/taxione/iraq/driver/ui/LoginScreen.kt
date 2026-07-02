package com.taxione.iraq.driver.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.taxione.core.ui.theme.Navy
import com.taxione.core.ui.theme.SafeGreen
import com.taxione.core.ui.theme.TaxiOrange
import com.taxione.iraq.driver.DriverViewModel
import com.taxione.iraq.driver.R

@Composable
fun LoginScreen(vm: DriverViewModel) {
    val ui by vm.ui.collectAsStateWithLifecycle()

    var phone by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var car by rememberSaveable { mutableStateOf("") }
    var plate by rememberSaveable { mutableStateOf("") }
    var code by rememberSaveable { mutableStateOf("") }
    var codeSent by rememberSaveable { mutableStateOf(false) }
    var server by rememberSaveable { mutableStateOf(ui.serverUrl) }

    Column(
        Modifier
            .fillMaxSize()
            .background(Navy)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            stringResource(R.string.login_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = Color.White,
        )
        Text(
            stringResource(R.string.login_caption),
            style = MaterialTheme.typography.bodyMedium,
            color = Color.White.copy(alpha = 0.65f),
        )

        LoginField(phone, { phone = it }, stringResource(R.string.phone_label), KeyboardType.Phone)
        LoginField(name, { name = it }, stringResource(R.string.name_label))
        LoginField(car, { car = it }, stringResource(R.string.car_model_label))
        LoginField(plate, { plate = it }, stringResource(R.string.plate_label))

        if (codeSent) {
            LoginField(code, { code = it }, stringResource(R.string.code_label), KeyboardType.Number)
            ui.debugCode?.let {
                Text(
                    stringResource(R.string.debug_code_hint, it),
                    color = SafeGreen,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        if (ui.busy) {
            CircularProgressIndicator(color = TaxiOrange)
        } else {
            Button(
                onClick = {
                    if (!codeSent) {
                        vm.requestOtp(phone)
                        codeSent = true
                    } else {
                        vm.verify(phone, code, name, car, plate)
                    }
                },
                enabled = phone.isNotBlank() && (!codeSent || code.isNotBlank()),
                shape = RoundedCornerShape(18.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = TaxiOrange,
                    contentColor = Color(0xFF221400),
                ),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    stringResource(if (codeSent) R.string.verify else R.string.send_code),
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(6.dp),
                )
            }
        }

        ui.error?.let {
            Text(
                stringResource(R.string.error_generic, it),
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
            )
        }

        LoginField(server, { server = it; vm.setServer(it) }, stringResource(R.string.server_label))
    }
}

@Composable
private fun LoginField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    keyboardType: KeyboardType = KeyboardType.Text,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
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
}
