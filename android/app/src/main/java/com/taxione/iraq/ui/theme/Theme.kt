package com.taxione.iraq.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val Navy = Color(0xFF0A1729)
val NavyCard = Color(0xFF16253E)
val NavyElevated = Color(0xFF1D2F4C)
val TaxiOrange = Color(0xFFFFA22B)
val SafeGreen = Color(0xFF34D077)

private val DarkColors = darkColorScheme(
    primary = TaxiOrange,
    onPrimary = Color(0xFF221400),
    secondary = SafeGreen,
    onSecondary = Color(0xFF00210E),
    background = Navy,
    onBackground = Color.White,
    surface = Navy,
    onSurface = Color.White,
    surfaceVariant = NavyCard,
    onSurfaceVariant = Color(0xB3FFFFFF),
    surfaceContainer = NavyCard,
    surfaceContainerHigh = NavyElevated,
    surfaceContainerHighest = NavyElevated,
    outline = Color(0x33FFFFFF),
    error = Color(0xFFFF6B6B),
    onError = Color(0xFF330606),
)

/** The app ships a single dark, road-at-night look in both light and dark system modes. */
@Composable
fun IraqTaxiTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = DarkColors, content = content)
}
