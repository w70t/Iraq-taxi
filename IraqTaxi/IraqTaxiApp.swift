import SwiftUI

@main
struct IraqTaxiApp: App {
    @AppStorage("appLanguage") private var language = "ar"
    @StateObject private var rides = RideStore()

    var body: some Scene {
        WindowGroup {
            AppShell(language: language) { language = $0 }
                .environmentObject(rides)
                .environment(\.layoutDirection, language == "ar" ? .rightToLeft : .leftToRight)
        }
    }
}
