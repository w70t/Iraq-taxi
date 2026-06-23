import SwiftUI

struct ContentView: View {
    let language: String
    let setLanguage: (String) -> Void
    @EnvironmentObject private var rides: RideStore
    @State private var destination = ""
    @State private var selectedCar = 0
    @State private var isRequesting = false
    @State private var roadOffset: CGFloat = -80
    @StateObject private var locationService = LocationService()

    private var arabic: Bool { language == "ar" }
    private var cars: [CarType] {
        [
            .init(name: arabic ? "اقتصادي" : "Economy", subtitle: arabic ? "سيارة يومية مريحة" : "Comfortable everyday ride", price: "5,000 IQD", icon: "car.fill"),
            .init(name: arabic ? "عائلي" : "Family", subtitle: arabic ? "مساحة أكبر للجميع" : "More room for everyone", price: "8,000 IQD", icon: "car.side.fill"),
            .init(name: arabic ? "بريميوم" : "Premium", subtitle: arabic ? "تجربة أكثر راحة" : "A more refined ride", price: "12,000 IQD", icon: "car.rear.fill")
        ]
    }

    var body: some View {
        ZStack {
            Color(red: 0.04, green: 0.09, blue: 0.16).ignoresSafeArea()
            movingRoad.ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(spacing: 20) {
                    header
                    pickupCard
                    locationSharingCard
                    destinationCard
                    carChooser
                    requestButton
                }
                .padding(20)
            }
        }
        .foregroundStyle(.white)
        .onAppear {
            withAnimation(.linear(duration: 1.2).repeatForever(autoreverses: false)) {
                roadOffset = 80
            }
        }
        .alert(arabic ? "تم استلام طلبك" : "Request received", isPresented: $isRequesting) {
            Button(arabic ? "حسناً" : "OK", role: .cancel) { }
        } message: {
            Text(arabic ? "هذه نسخة تجريبية. سيظهر السائق هنا بعد ربط نظام الرحلات الحقيقي." : "This is a prototype. A driver will appear here after the live trip system is connected.")
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: arabic ? .trailing : .leading, spacing: 5) {
                Text(arabic ? "أهلاً بك في تكسي واحد عراق" : "Welcome to Taxi One Iraq")
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                Text(arabic ? "رحلة آمنة في جميع محافظات العراق" : "Safe rides across every Iraqi governorate")
                    .foregroundStyle(.white.opacity(0.65))
            }
            Spacer()
            Menu {
                Button("العربية") { setLanguage("ar") }
                Button("English") { setLanguage("en") }
            } label: {
                Image(systemName: "globe")
                    .font(.title3.weight(.bold))
                    .frame(width: 44, height: 44)
                    .background(.white.opacity(0.12), in: Circle())
            }
        }
    }

    private var pickupCard: some View {
        HStack(spacing: 14) {
            ZStack {
                Circle().fill(.green.opacity(0.2)).frame(width: 44, height: 44)
                Circle().fill(.green).frame(width: 12, height: 12)
                    .shadow(color: .green, radius: 12)
            }
            VStack(alignment: arabic ? .trailing : .leading, spacing: 4) {
                Text(arabic ? "موقع الاستلام" : "Pickup location").font(.caption).foregroundStyle(.white.opacity(0.6))
                Text(arabic ? "موقعي الحالي" : "My current location").fontWeight(.semibold)
            }
            Spacer()
            Image(systemName: "location.fill").foregroundStyle(.green)
        }
        .padding(16).background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 22))
    }

    private var locationSharingCard: some View {
        Toggle(isOn: Binding(
            get: { locationService.isSharing },
            set: { locationService.setSharing($0) }
        )) {
            VStack(alignment: arabic ? .trailing : .leading, spacing: 3) {
                Text(arabic ? "مشاركة موقعي للرحلة" : "Share my location for this ride")
                    .fontWeight(.semibold)
                Text(arabic ? "يتوقف التحديث عند إلغاء الطلب أو إيقاف الزر." : "Updates stop when you cancel or turn this off.")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.62))
            }
        }
        .tint(.green)
        .padding(16)
        .background(Color.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 20))
    }

    private var destinationCard: some View {
        HStack(spacing: 14) {
            Image(systemName: "magnifyingglass").foregroundStyle(.orange)
            TextField(arabic ? "ابحث عن وجهة" : "Search destination", text: $destination)
                .textInputAutocapitalization(.words)
                .foregroundStyle(.white)
            if !destination.isEmpty {
                Button { destination = "" } label: { Image(systemName: "xmark.circle.fill").foregroundStyle(.white.opacity(0.45)) }
            }
        }
        .padding(18)
        .background(Color.white.opacity(0.13), in: RoundedRectangle(cornerRadius: 22))
    }

    private var carChooser: some View {
        VStack(alignment: arabic ? .trailing : .leading, spacing: 12) {
            Text(arabic ? "اختر رحلتك" : "Choose your ride").font(.headline)
            ForEach(cars.indices, id: \.self) { index in
                Button { withAnimation(.spring(response: 0.35, dampingFraction: 0.75)) { selectedCar = index } } label: {
                    HStack(spacing: 14) {
                        Image(systemName: cars[index].icon)
                            .font(.title2).foregroundStyle(index == selectedCar ? .orange : .white.opacity(0.75))
                            .frame(width: 44)
                        VStack(alignment: arabic ? .trailing : .leading, spacing: 3) {
                            Text(cars[index].name).fontWeight(.bold)
                            Text(cars[index].subtitle).font(.caption).foregroundStyle(.white.opacity(0.62))
                        }
                        Spacer()
                        Text(cars[index].price).font(.subheadline.weight(.bold))
                    }
                    .padding(15)
                    .background(index == selectedCar ? Color.orange.opacity(0.2) : Color.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 20))
                    .overlay(RoundedRectangle(cornerRadius: 20).stroke(index == selectedCar ? .orange : .clear, lineWidth: 1))
                }
                .buttonStyle(.plain)
            }
        }
    }

    private var requestButton: some View {
        Button {
            locationService.requestCurrentLocation()
            rides.requestRide(
                destination: destination,
                vehicleName: cars[selectedCar].name,
                fare: [5_000, 8_000, 12_000][selectedCar]
            )
            isRequesting = true
        } label: {
            HStack {
                Image(systemName: "bolt.fill")
                Text(arabic ? "اطلب \(cars[selectedCar].name) الآن" : "Request \(cars[selectedCar].name) now")
                Spacer()
                Image(systemName: "arrow.left")
            }
            .fontWeight(.bold).padding(19)
            .background(.orange, in: RoundedRectangle(cornerRadius: 20))
        }
        .buttonStyle(.plain)
        .padding(.top, 4)
    }

    private var movingRoad: some View {
        GeometryReader { proxy in
            ZStack {
                LinearGradient(colors: [.clear, .black.opacity(0.28), .clear], startPoint: .top, endPoint: .bottom)
                VStack(spacing: 46) {
                    ForEach(0..<12, id: \.self) { _ in
                        Capsule().fill(.white.opacity(0.09)).frame(width: 8, height: 28)
                    }
                }
                .offset(x: roadOffset, y: 100)
                .rotationEffect(.degrees(32))
                .frame(width: proxy.size.width * 1.5)
            }
        }
    }
}

private struct CarType {
    let name: String
    let subtitle: String
    let price: String
    let icon: String
}

#Preview {
    ContentView(language: "ar", setLanguage: { _ in })
        .environment(\.layoutDirection, .rightToLeft)
}
