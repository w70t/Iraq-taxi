package com.taxione.iraq.driver.ui

import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.core.os.LocaleListCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.taxione.core.ui.theme.Navy
import com.taxione.core.ui.theme.TaxiOrange
import com.taxione.iraq.driver.DriverViewModel
import com.taxione.iraq.driver.R

fun setAppLanguage(tag: String) {
    AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag))
}

fun isArabic(): Boolean =
    AppCompatDelegate.getApplicationLocales().toLanguageTags().startsWith("ar")

private data class TabSpec(val labelRes: Int, val icon: ImageVector)

@Composable
fun DriverShell(vm: DriverViewModel = viewModel()) {
    val ui by vm.ui.collectAsStateWithLifecycle()

    if (!ui.loggedIn) {
        LoginScreen(vm)
        return
    }

    var selectedTab by rememberSaveable { mutableIntStateOf(0) }
    val tabs = listOf(
        TabSpec(R.string.tab_requests, Icons.Filled.DirectionsCar),
        TabSpec(R.string.tab_earnings, Icons.Filled.Payments),
        TabSpec(R.string.tab_account, Icons.Filled.Person),
    )

    Scaffold(
        containerColor = Navy,
        bottomBar = {
            NavigationBar {
                tabs.forEachIndexed { index, tab ->
                    NavigationBarItem(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        icon = { Icon(tab.icon, contentDescription = null) },
                        label = { Text(stringResource(tab.labelRes)) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = TaxiOrange,
                            selectedTextColor = TaxiOrange,
                            indicatorColor = TaxiOrange.copy(alpha = 0.18f),
                            unselectedIconColor = Color.White.copy(alpha = 0.6f),
                            unselectedTextColor = Color.White.copy(alpha = 0.6f),
                        ),
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (selectedTab) {
                0 -> RequestsScreen(vm)
                1 -> EarningsScreen(vm)
                else -> DriverAccountScreen(vm)
            }
        }
    }
}
