import SwiftUI

struct AppShell: View {
    let language: String
    let setLanguage: (String) -> Void
    @EnvironmentObject private var rides: RideStore

    private var arabic: Bool { language == "ar" }

    var body: some View {
        TabView {
            ContentView(language: language, setLanguage: setLanguage)
                .tabItem { Label(arabic ? "اطلب" : "Ride", systemImage: "map.fill") }

            TripsView(language: language)
                .tabItem { Label(arabic ? "رحلاتي" : "Trips", systemImage: "clock.arrow.circlepath") }

            AccountView(language: language, setLanguage: setLanguage)
                .tabItem { Label(arabic ? "حسابي" : "Account", systemImage: "person.crop.circle") }
        }
        .tint(.orange)
    }
}

private struct TripsView: View {
    let language: String
    @EnvironmentObject private var rides: RideStore

    private var arabic: Bool { language == "ar" }

    var body: some View {
        NavigationStack {
            List {
                if let ride = rides.currentRide {
                    Section(arabic ? "الرحلة الحالية" : "Current ride") {
                        RideRow(ride: ride)
                        RideActions(ride: ride, language: language)
                    }
                }

                Section(arabic ? "الرحلات السابقة" : "Previous rides") {
                    if rides.history.isEmpty {
                        ContentUnavailableView(
                            arabic ? "لا توجد رحلات بعد" : "No rides yet",
                            systemImage: "car",
                            description: Text(arabic ? "ستظهر رحلاتك المكتملة أو الملغاة هنا." : "Completed and cancelled rides will appear here.")
                        )
                    } else {
                        ForEach(rides.history) { RideRow(ride: $0) }
                    }
                }
            }
            .navigationTitle(arabic ? "رحلاتي" : "My trips")
        }
    }
}

private struct RideRow: View {
    let ride: Ride

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Image(systemName: "car.fill").foregroundStyle(.orange)
                Text(ride.vehicleName).fontWeight(.bold)
                Spacer()
                Text(ride.fareLabel).fontWeight(.semibold)
            }
            Label(ride.destination, systemImage: "mappin.and.ellipse")
                .font(.subheadline)
            Text(ride.status.arabicTitle).font(.caption).foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

private struct RideActions: View {
    let ride: Ride
    let language: String
    @EnvironmentObject private var rides: RideStore

    var body: some View {
        switch ride.status {
        case .searching:
            Button(language == "ar" ? "محاكاة قبول السائق" : "Simulate driver acceptance") {
                rides.simulateDriverAccepted()
            }
            Button(language == "ar" ? "إلغاء الطلب" : "Cancel request", role: .destructive) {
                rides.cancelRide()
            }
        case .driverArriving:
            if let driver = ride.driverName, let car = ride.driverCar {
                Label("\(driver) · \(car)", systemImage: "person.fill")
            }
            Button(language == "ar" ? "بدء الرحلة" : "Start ride") { rides.startRide() }
        case .inProgress:
            Button(language == "ar" ? "إنهاء الرحلة" : "Complete ride") { rides.completeRide() }
        default:
            EmptyView()
        }
    }
}

private struct AccountView: View {
    let language: String
    let setLanguage: (String) -> Void

    private var arabic: Bool { language == "ar" }

    var body: some View {
        NavigationStack {
            Form {
                Section(arabic ? "الحساب" : "Account") {
                    LabeledContent(arabic ? "الاسم" : "Name", value: arabic ? "مستخدم تكسي واحد" : "Taxi One user")
                    LabeledContent(arabic ? "الدفع" : "Payment", value: arabic ? "نقداً عند الوصول" : "Cash on arrival")
                }
                Section(arabic ? "اللغة" : "Language") {
                    Picker(arabic ? "لغة التطبيق" : "App language", selection: Binding(get: { language }, set: setLanguage)) {
                        Text("العربية").tag("ar")
                        Text("English").tag("en")
                    }
                }
                Section(arabic ? "الأمان والخصوصية" : "Safety & privacy") {
                    Label(arabic ? "مشاركة الموقع للرحلة فقط" : "Location sharing for rides only", systemImage: "location.shield")
                    Label(arabic ? "زر طوارئ سيضاف قبل الإطلاق" : "Emergency support before launch", systemImage: "shield")
                }
            }
            .navigationTitle(arabic ? "حسابي" : "My account")
        }
    }
}
