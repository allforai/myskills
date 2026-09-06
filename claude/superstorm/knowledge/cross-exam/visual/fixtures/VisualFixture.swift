import SwiftUI

@main
struct VisualFixture: App {
    var body: some Scene { WindowGroup { FixtureScreen() } }
}

struct FixtureScreen: View {
    @State private var sheet = false
    private let mode = ProcessInfo.processInfo.environment["FIXTURE_STATE"] ?? "normal"
    var body: some View {
        TabView {
            NavigationStack {
                VStack(spacing: 16) {
                    if mode == "loading" { ProgressView("Loading") }
                    else if mode == "empty" { ContentUnavailableView("No items", systemImage: "tray") }
                    else if mode == "error" { Text("Could not load. Try again.").foregroundStyle(.red) }
                    else { Text("Visual acceptance fixture").font(.title) }
                    Button("Open details") { sheet = true }
                        .accessibilityIdentifier("details")
                }
                .padding()
                .navigationTitle("Home")
                .sheet(isPresented: $sheet) {
                    NavigationStack {
                        Text("Details").toolbar {
                            Button("Close") { sheet = false }
                        }
                    }
                }
            }.tabItem { Label("Home", systemImage: "house") }
            NavigationStack { Text("Settings").navigationTitle("Settings") }
                .tabItem { Label("Settings", systemImage: "gear") }
        }
    }
}
