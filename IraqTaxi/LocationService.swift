import CoreLocation
import Foundation

/// Foreground-only location sharing for riders.
/// No background location permission is requested in this service.
final class LocationService: NSObject, ObservableObject {
    @Published private(set) var isSharing = false
    @Published private(set) var authorizationStatus: CLAuthorizationStatus
    @Published private(set) var lastLocation: CLLocation?

    private let manager = CLLocationManager()

    override init() {
        authorizationStatus = manager.authorizationStatus
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.distanceFilter = 15
    }

    func setSharing(_ enabled: Bool) {
        isSharing = enabled
        guard enabled else {
            manager.stopUpdatingLocation()
            return
        }

        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways:
            manager.startUpdatingLocation()
        default:
            isSharing = false
        }
    }

    func requestCurrentLocation() {
        guard isSharing else { return }
        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            manager.requestLocation()
        default:
            setSharing(true)
        }
    }
}

extension LocationService: CLLocationManagerDelegate {
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        if isSharing, authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways {
            manager.startUpdatingLocation()
        } else if authorizationStatus == .denied || authorizationStatus == .restricted {
            isSharing = false
            manager.stopUpdatingLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        lastLocation = locations.last
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // The UI keeps the sharing state visible; a production build logs this safely.
    }
}
