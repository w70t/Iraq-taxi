package com.taxione.core.map

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

data class MapPin(val lat: Double, val lng: Double, val title: String = "")

/**
 * Free OpenStreetMap view (osmdroid) — no API key, no billing account.
 * Tiles come from openstreetmap.org over HTTPS.
 */
@Composable
fun OsmMap(
    center: MapPin,
    pins: List<MapPin>,
    modifier: Modifier = Modifier,
    zoom: Double = 15.0,
) {
    AndroidView(
        modifier = modifier,
        factory = { context ->
            Configuration.getInstance().userAgentValue = context.packageName
            MapView(context).apply {
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)
                controller.setZoom(zoom)
            }
        },
        update = { map ->
            map.controller.setCenter(GeoPoint(center.lat, center.lng))
            map.overlays.removeAll { it is Marker }
            pins.forEach { pin ->
                map.overlays.add(
                    Marker(map).apply {
                        position = GeoPoint(pin.lat, pin.lng)
                        title = pin.title
                        setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
                    }
                )
            }
            map.invalidate()
        },
    )
}
