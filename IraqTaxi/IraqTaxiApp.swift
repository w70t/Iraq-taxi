import SwiftUI

@main
struct IraqTaxiApp: App {
    @AppStorage("appLanguage") private var language = "ar"

    var body: some Scene {
        WindowGroup {
            ContentView(language: language) { language = $0 }
                .environment(\.layoutDirection, language == "ar" ? .rightToLeft : .leftToRight)
        }
    }
}
