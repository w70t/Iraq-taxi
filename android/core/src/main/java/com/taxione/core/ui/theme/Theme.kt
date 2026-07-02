package com.taxione.core.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import com.taxione.core.R

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

/** Cairo: the brand typeface for every text in both apps, bundled offline. */
val Cairo = FontFamily(
    Font(R.font.cairo_regular, FontWeight.Normal),
    Font(R.font.cairo_semibold, FontWeight.SemiBold),
    Font(R.font.cairo_bold, FontWeight.Bold),
)

private val CairoTypography = Typography().run {
    copy(
        displayLarge = displayLarge.copy(fontFamily = Cairo),
        displayMedium = displayMedium.copy(fontFamily = Cairo),
        displaySmall = displaySmall.copy(fontFamily = Cairo),
        headlineLarge = headlineLarge.copy(fontFamily = Cairo),
        headlineMedium = headlineMedium.copy(fontFamily = Cairo),
        headlineSmall = headlineSmall.copy(fontFamily = Cairo),
        titleLarge = titleLarge.copy(fontFamily = Cairo),
        titleMedium = titleMedium.copy(fontFamily = Cairo),
        titleSmall = titleSmall.copy(fontFamily = Cairo),
        bodyLarge = bodyLarge.copy(fontFamily = Cairo),
        bodyMedium = bodyMedium.copy(fontFamily = Cairo),
        bodySmall = bodySmall.copy(fontFamily = Cairo),
        labelLarge = labelLarge.copy(fontFamily = Cairo),
        labelMedium = labelMedium.copy(fontFamily = Cairo),
        labelSmall = labelSmall.copy(fontFamily = Cairo),
    )
}

/** The app ships a single dark, road-at-night look in both light and dark system modes. */
@Composable
fun IraqTaxiTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = DarkColors, typography = CairoTypography, content = content)
}
