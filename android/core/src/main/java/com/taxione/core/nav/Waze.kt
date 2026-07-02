package com.taxione.core.nav

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri

/**
 * Opens turn-by-turn navigation to the given point in the Waze app —
 * the tool Iraqi drivers already trust for live traffic and checkpoints.
 * Falls back to the Waze web/store page when the app is not installed.
 */
fun navigateWithWaze(context: Context, lat: Double, lng: Double) {
    val appUri = Uri.parse("waze://?ll=$lat,$lng&navigate=yes")
    try {
        context.startActivity(Intent(Intent.ACTION_VIEW, appUri))
    } catch (_: ActivityNotFoundException) {
        val webUri = Uri.parse("https://waze.com/ul?ll=$lat,$lng&navigate=yes")
        context.startActivity(Intent(Intent.ACTION_VIEW, webUri))
    }
}
