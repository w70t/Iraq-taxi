package com.taxione.core.map

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import org.osmdroid.config.Configuration
import org.osmdroid.events.DelayedMapListener
import org.osmdroid.events.MapListener
import org.osmdroid.events.ScrollEvent
import org.osmdroid.events.ZoomEvent
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

/**
 * Pan-to-pick map: the rider moves the map under a fixed center pin (drawn by
 * the caller) and [onCenterChanged] reports the point under the pin, debounced.
 * Setting a new [recenter] object animates the camera there once.
 */
@Composable
fun PickupMap(
    initial: MapPin,
    recenter: MapPin?,
    onCenterChanged: (Double, Double) -> Unit,
    modifier: Modifier = Modifier,
    zoom: Double = 16.0,
) {
    val centerCallback by rememberUpdatedState(onCenterChanged)
    AndroidView(
        modifier = modifier,
        factory = { context ->
            Configuration.getInstance().userAgentValue = context.packageName
            MapView(context).apply {
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)
                controller.setZoom(zoom)
                controller.setCenter(GeoPoint(initial.lat, initial.lng))
                addMapListener(
                    DelayedMapListener(
                        object : MapListener {
                            override fun onScroll(event: ScrollEvent?): Boolean {
                                centerCallback(mapCenter.latitude, mapCenter.longitude)
                                return true
                            }

                            override fun onZoom(event: ZoomEvent?): Boolean {
                                centerCallback(mapCenter.latitude, mapCenter.longitude)
                                return true
                            }
                        },
                        300L,
                    )
                )
            }
        },
        update = { map ->
            if (recenter != null && map.tag !== recenter) {
                map.tag = recenter
                map.controller.animateTo(GeoPoint(recenter.lat, recenter.lng))
            }
        },
    )
}
