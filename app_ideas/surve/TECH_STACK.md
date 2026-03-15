# Surve - Technical Specification

## Frontend (iOS)

### Framework
- **SwiftUI** (primary UI)
- **UIKit** (where needed for complex interactions)
- **WatchKit** (Apple Watch)

### Architecture
- **MVVM** pattern
- **Combine** for reactive programming
- **SwiftData** (iOS 17+) or **Core Data** for local storage

### Key Dependencies
```swift
// Package.swift or SPM
dependencies: [
    .package(url: "https://github.com/Alamofire/Alamofire", from: "5.8.0"),
    .package(url: "https://github.com/apple/swift-protobuf", from: "1.0.0"),
    .package(url: "https://github.com/daltoniam/Starscream", from: "4.0.0"), // WebSockets
    .package(url: "https://github.com/kean/Nuke", from: "12.0.0"), // Image loading
    .package(url: "https://github.com/simibac/ConfettiSwiftUI", from: "1.0.0"),
]
```

### Haptics
```swift
import CoreHaptics

class HapticManager {
    static let shared = HapticManager()
    
    func scoreIncrement() {
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
    }
    
    func gameWin() {
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.success)
    }
    
    func matchWin() {
        // Heavy impact + success notification
        let heavy = UIImpactFeedbackGenerator(style: .heavy)
        heavy.impactOccurred()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            let success = UINotificationFeedbackGenerator()
            success.notificationOccurred(.success)
        }
    }
}
```

---

## Backend

### Option A: Swift + Vapor (Recommended)
```swift
// Package.swift
// Vapor 4.x
// PostgreSQL with Fluent
// WebSockets for real-time
```

### Option B: Node.js + Express
```javascript
// Express.js
// PostgreSQL with Sequelize/Prisma
// Socket.io for real-time
// JWT auth
```

### Real-time Updates
```swift
// WebSocket for live score updates
class MatchWebSocketManager {
    func connect(to matchId: UUID) {
        // Connect to WebSocket
        // Subscribe to match updates
    }
    
    func sendScoreUpdate(_ update: ScoreUpdate) {
        // Broadcast to connected clients
    }
}
```

---

## Database

### PostgreSQL with PostGIS
- Stores match data, player stats
- Spatial queries for location-based features

### CloudKit
- Primary sync mechanism
- Offline support with local caching

---

## Third-Party Services

| Service | Purpose |
|---------|---------|
| RevenueCat | In-app purchases |
| Firebase Crashlytics | Crash reporting |
| Amplitude | Analytics |
| OneSignal | Push notifications |

---

## Project Structure

```
Surve/
├── App/
│   ├── SurveApp.swift
│   ├── AppDelegate.swift
│   └── Info.plist
├── Core/
│   ├── Models/
│   ├── ViewModels/
│   ├── Services/
│   └── Utilities/
├── Features/
│   ├── Home/
│   ├── LiveMatch/
│   ├── Sports/
│   ├── Statistics/
│   └── Settings/
├── DesignSystem/
│   ├── Colors.swift
│   ├── Fonts.swift
│   ├── Haptics.swift
│   └── Components/
├── WatchApp/
│   └── SurveWatchApp.swift
├── Shared/
│   └── Models/ (shared with watch)
└── Resources/
    ├── Assets.xcassets
    └── Localizations/
```

---

## Build Configuration

```
Development:
- Debug symbols enabled
- Local API: http://localhost:8080
- TestFlight for QA

Production:
- Release optimization
- Production API: https://api.surve.app
- App Store distribution
```
