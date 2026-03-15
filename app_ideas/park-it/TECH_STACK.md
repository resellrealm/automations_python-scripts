# Park-it - Technical Specification

## Frontend (iOS)

### Framework
- **SwiftUI** for all UI
- **MapKit** or **Mapbox** for maps
- **ARKit** for AR navigation (optional v2)
- **WidgetKit** for home/lock screen widgets
- **Live Activities** for Dynamic Island

### Architecture
- **MVVM** pattern
- **Combine** for reactive state
- **SwiftData** for local persistence
- **CloudKit** for sync

### Key Dependencies
```swift
dependencies: [
    // Maps
    .package(url: "https://github.com/mapbox/mapbox-maps-ios", from: "11.0.0"),
    
    // Geocoding
    .package(url: "https://github.com/geocodeorg/geocode", from: "1.0.0"),
    
    // Location
    .package(url: "https://github.com/malcommac/SwiftLocation", from: "6.0.0"),
    
    // AR (v2)
    .package(url: "https://github.com/ProjectDent/ARKit-CoreLocation", from: "1.0.0"),
    
    // Photos
    .package(url: "https://github.com/kean/Nuke", from: "12.0.0"),
]
```

### Location Services
```swift
import CoreLocation

class LocationManager: NSObject, ObservableObject {
    private let manager = CLLocationManager()
    
    @Published var currentLocation: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus?
    
    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.allowsBackgroundLocationUpdates = true
        manager.pausesLocationUpdatesAutomatically = false
    }
    
    func requestPermission() {
        manager.requestAlwaysAuthorization()
    }
    
    func startUpdating() {
        manager.startUpdatingLocation()
    }
}
```

### Motion Detection (Auto-Parking)
```swift
import CoreMotion

class MotionDetector: ObservableObject {
    private let motionManager = CMMotionActivityManager()
    private let pedometer = CMPedometer()
    
    @Published var isDriving = false
    @Published var isWalking = false
    @Published var isStationary = false
    
    func startDetection() {
        guard CMMotionActivityManager.isActivityAvailable() else { return }
        
        motionManager.startActivityUpdates(to: .main) { [weak self] activity in
            guard let activity = activity else { return }
            
            self?.isDriving = activity.automotive == true
            self?.isWalking = activity.walking == true
            self?.isStationary = activity.stationary == true
            
            // Detect parking transition
            if activity.stationary == true && self?.previousActivity?.automotive == true {
                self?.potentialParkingDetected()
            }
        }
    }
}
```

---

## Map Implementation

### CartoDB Dark Matter (Free, simple)
```swift
import MapKit

class DarkMapView: MKMapView {
    func setupDarkStyle() {
        // Use CartoDB Dark Matter tile overlay
        let template = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        let overlay = MKTileOverlay(urlTemplate: template)
        overlay.canReplaceMapContent = true
        addOverlay(overlay, level: .aboveLabels)
    }
}
```

### Mapbox Custom Style (More control)
```swift
import MapboxMaps

class ParkitMapView: UIView {
    private var mapView: MapView!
    
    func setup() {
        let resourceOptions = ResourceOptions(accessToken: "YOUR_TOKEN")
        let mapInitOptions = MapInitOptions(
            resourceOptions: resourceOptions,
            styleURI: StyleURI(rawValue: "mapbox://styles/YOUR_STYLE") // Black & white
        )
        
        mapView = MapView(frame: bounds, mapInitOptions: mapInitOptions)
        addSubview(mapView)
    }
}
```

---

## Backend

### Minimal Backend (CloudKit First)
Most features work offline/CloudKit only.
Backend only needed for:
- Reverse geocoding (can use Mapbox)
- Shared parking locations (optional)

### If Building Backend
```javascript
// Node.js + Express + PostgreSQL + PostGIS

// Key endpoints:
POST /api/parkings
GET  /api/parkings/active
POST /api/parkings/:id/end
GET  /api/parkings/nearby?lat=...&lng=...
```

### Database Schema (Core Data/SwiftData)
```swift
@Model
class ParkingSession {
    var id: UUID
    var latitude: Double
    var longitude: Double
    var parkedAt: Date
    var endedAt: Date?
    var note: String?
    var photoPath: String?
    var hourlyRate: Double?
    var isActive: Bool
    var isFavorite: Bool
    
    // Computed
    var duration: TimeInterval? {
        guard let endedAt = endedAt else { return nil }
        return endedAt.timeIntervalSince(parkedAt)
    }
}
```

---

## Widgets

### Home Screen Widget
```swift
import WidgetKit
import SwiftUI

struct ParkitWidget: Widget {
    let kind: String = "ParkitWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: Provider()) { entry in
            ParkitWidgetView(entry: entry)
        }
        .configurationDisplayName("Park-it")
        .description("Quick access to your parked car")
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryCircular])
    }
}
```

### Live Activity
```swift
import ActivityKit

struct ParkitAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var parkedAt: Date
        var duration: TimeInterval
        var distance: Double?
    }
    
    var locationName: String
}

// Start activity when parking
func startLiveActivity() {
    let attributes = ParkitAttributes(locationName: "Current Location")
    let state = ParkitAttributes.ContentState(
        parkedAt: Date(),
        duration: 0,
        distance: nil
    )
    
    let activity = try? Activity.request(
        attributes: attributes,
        contentState: state,
        pushType: nil
    )
}
```

---

## Watch App

```swift
import WatchKit
import SwiftUI

@main
struct ParkitWatchApp: App {
    var body: some Scene {
        WindowGroup {
            NavigationView {
                WatchMainView()
            }
        }
    }
}

struct WatchMainView: View {
    @StateObject private var viewModel = WatchViewModel()
    
    var body: some View {
        VStack {
            if let session = viewModel.activeSession {
                Text("Parked \(session.durationText)")
                    .font(.headline)
                
                Button("Find Car") {
                    viewModel.startNavigation()
                }
                .tint(.blue)
            } else {
                Button("Park Here") {
                    viewModel.saveParking()
                }
                .tint(.green)
            }
        }
    }
}
```

---

## Project Structure

```
ParkIt/
├── App/
│   ├── ParkItApp.swift
│   ├── AppDelegate.swift
│   └── Info.plist
├── Core/
│   ├── Models/
│   │   ├── ParkingSession.swift
│   │   ├── FavoriteLocation.swift
│   │   └── Statistics.swift
│   ├── Services/
│   │   ├── LocationManager.swift
│   │   ├── MotionDetector.swift
│   │   ├── HapticManager.swift
│   │   └── NotificationManager.swift
│   └── Utilities/
├── Features/
│   ├── Map/
│   │   ├── MapView.swift
│   │   └── MapViewModel.swift
│   ├── Park/
│   │   ├── ParkConfirmationView.swift
│   │   └── ParkDetailsView.swift
│   ├── FindCar/
│   │   ├── NavigationView.swift
│   │   └── ARNavigationView.swift
│   ├── History/
│   │   ├── HistoryListView.swift
│   │   └── StatisticsView.swift
│   └── Settings/
│       └── SettingsView.swift
├── DesignSystem/
│   ├── Colors.swift
│   ├── Haptics.swift
│   └── Components/
├── Widgets/
│   ├── ParkitWidget.swift
│   └── ParkitLiveActivity.swift
├── WatchApp/
│   └── ParkitWatchApp.swift
└── Resources/
    └── Assets.xcassets
```

---

## Monetization (RevenueCat)

```swift
import RevenueCat

class PurchaseManager: ObservableObject {
    static let shared = PurchaseManager()
    
    @Published var isPremium = false
    
    func configure() {
        Purchases.configure(withAPIKey: "your_api_key")
        Purchases.shared.delegate = self
    }
    
    func purchase() async throws {
        let package = try await Purchases.shared.offerings()
            .current?.availablePackages.first
        
        guard let package = package else { return }
        
        let result = try await Purchases.shared.purchase(package: package)
        self.isPremium = !result.userCancelled
    }
}
```
