import Foundation

struct Ride: Identifiable, Equatable {
    enum Status: String, CaseIterable {
        case searching, driverAssigned, driverArriving, inProgress, completed, cancelled

        var arabicTitle: String {
            switch self {
            case .searching: return "جارٍ البحث عن سائق"
            case .driverAssigned: return "تم قبول الرحلة"
            case .driverArriving: return "السائق في الطريق إليك"
            case .inProgress: return "الرحلة جارية"
            case .completed: return "رحلة مكتملة"
            case .cancelled: return "رحلة ملغاة"
            }
        }
    }

    let id: UUID
    let pickup: String
    let destination: String
    let vehicleName: String
    let fare: Int
    var status: Status
    var createdAt: Date
    var driverName: String?
    var driverCar: String?

    var fareLabel: String { "\(fare.formatted()) IQD" }
}

@MainActor
final class RideStore: ObservableObject {
    @Published private(set) var currentRide: Ride?
    @Published private(set) var history: [Ride] = []

    func requestRide(destination: String, vehicleName: String, fare: Int) {
        let ride = Ride(
            id: UUID(),
            pickup: "موقعي الحالي",
            destination: destination.isEmpty ? "وجهة لم تُحدد" : destination,
            vehicleName: vehicleName,
            fare: fare,
            status: .searching,
            createdAt: .now,
            driverName: nil,
            driverCar: nil
        )
        currentRide = ride
    }

    func simulateDriverAccepted() {
        guard var ride = currentRide, ride.status == .searching else { return }
        ride.status = .driverArriving
        ride.driverName = "علي كريم"
        ride.driverCar = "Toyota Corolla · 27 أ ب 1234"
        currentRide = ride
    }

    func startRide() {
        guard var ride = currentRide, ride.status == .driverArriving else { return }
        ride.status = .inProgress
        currentRide = ride
    }

    func completeRide() {
        guard var ride = currentRide else { return }
        var completed = ride
        completed.status = .completed
        history.insert(completed, at: 0)
        currentRide = nil
    }

    func cancelRide() {
        guard var ride = currentRide else { return }
        ride.status = .cancelled
        history.insert(ride, at: 0)
        currentRide = nil
    }
}
