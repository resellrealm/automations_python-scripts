# Park-it — Full Design System

## Mascot: The Panther

**Concept:**
The Park-it Panther is a sleek, ultra-minimal black panther silhouette — barely visible, like a shadow knowing exactly where it is. Low, coiled, ready. This isn't a cartoon cat; it's a precision predator. Still. Present. Always knows the location.

**Personality:** Confident, minimal, premium. Never lost.

**Style Direction:**
- Flat monochromatic silhouette — pure black shape, zero detail
- Crouched/coiled pose: low profile, body long and horizontal
- Single piercing accent-blue eye (`#3B82F6`) — the only color in the whole icon
- Works on pure white OR pure black background (two versions)
- Should feel like a luxury brand mark (think Puma, Jaguar cars)

**Where the Panther Appears:**
- App icon (panther crouched on white or black, blue eye)
- Splash screen (panther walks onto screen from left, pauses, blinks)
- Map pin (replace standard blue dot with a tiny panther silhouette)
- Empty state (panther looking up at blank screen with question mark)
- Success save (panther crouches into saved pin animation)
- Loading spinner (panther tail curling in a circle)
- Widget background (ghosted, ultra faint, behind the parking info)
- Find Car screen (panther faces direction arrow, walks)

**DIY Creation Guide:**
1. Go to Flaticon → search "black panther" → filter "Lineal" or "Flat" style
2. Or Vecteezy → search "black panther silhouette vector" → 7,100+ results
3. In Figma: import SVG, reduce to single flat shape, remove all gradients
4. Set body fill to `#000000` (or `#1F2937` for dark theme)
5. Add single eye: ellipse, `#3B82F6`, positioned precisely
6. Export: SVG master, 1024×1024 PNG (App Store), standard iOS sizes

**Search Terms:**
- Flaticon: "black panther", "panther silhouette"
- Vecteezy: "black panther logo vector", "panther minimal silhouette"
- Icons8: "black panther"
- IconScout: "panther flat icon"

---

## Typography

### Font Stack

| Role | Font | Weight | Source |
|------|------|--------|--------|
| **Brand / App Name** | Space Grotesk | 700 Bold | Google Fonts |
| **Timer / Display** | Bebas Neue | Regular | Google Fonts |
| **Headings** | Space Grotesk | 600 SemiBold | Google Fonts |
| **Body / Labels** | Space Grotesk | 400, 500 | Google Fonts |
| **Coordinates / Times** | SF Mono | — | iOS System |
| **Fallback** | SF Pro Display | — | iOS System |

### Why Space Grotesk + Bebas Neue (Panther Mood Match)

**Space Grotesk Bold** → This IS the panther. Space Grotesk has a slightly irregular, distinctive character that feels like precision tech — not a standard clean sans, but something with a personality. Sleek, modern, slightly futuristic. "Park-It" in Space Grotesk Bold feels like a stealth tech tool, not a generic utility app. The panther moves with intent — Space Grotesk types with intent.

**Bebas Neue** → Timer display only. "2h 34m" in Bebas Neue reads like a race clock from the other side of the car park. Pure functional display — no personality needed here, just clarity.

**Why not DM Sans?** It's clean but anonymous. Space Grotesk has the same minimalism with character — the slightly quirky letterforms give it a stealth/tech edge that DM Sans lacks.

### Type Scale

```swift
enum ParkItFont {
    // Brand — Space Grotesk Bold
    static let brand     = Font.custom("SpaceGrotesk-Bold", size: 28)  // "Park-It" wordmark

    // Timer / Display — Bebas Neue (race clock energy)
    static let displayXL = Font.custom("BebasNeue-Regular", size: 72)  // Main timer
    static let displayLG = Font.custom("BebasNeue-Regular", size: 52)  // Distance
    static let displayMD = Font.custom("BebasNeue-Regular", size: 36)  // Card labels
    static let displaySM = Font.custom("BebasNeue-Regular", size: 24)  // Button text

    // Headings — Space Grotesk SemiBold
    static let headingLG = Font.custom("SpaceGrotesk-SemiBold", size: 22)
    static let headingMD = Font.custom("SpaceGrotesk-SemiBold", size: 18)
    static let headingSM = Font.custom("SpaceGrotesk-Medium", size: 15)

    // Body — Space Grotesk Regular (consistent single family)
    static let bodyLG   = Font.custom("SpaceGrotesk-Medium", size: 17)
    static let bodyMD   = Font.custom("SpaceGrotesk-Regular", size: 15)
    static let bodySM   = Font.custom("SpaceGrotesk-Regular", size: 13)
    static let caption  = Font.custom("SpaceGrotesk-Regular", size: 11)

    // Monospace — SF Mono (coordinates, rates)
    static let mono     = Font.system(.body, design: .monospaced)
    static let monoSM   = Font.system(.caption2, design: .monospaced)
}
```

### Mood Pairing Logic
```
Panther Personality  → Sleek · Stealthy · Modern · Precision tech
Space Grotesk Bold   → Slightly irregular → feels distinctive, not generic
                       Geometric but with character → feels intentional
Bebas Neue           → Race clock energy for the timer → can't miss it
Result               → App feels like a stealth tracking tool. Premium, not basic.
```

---

## Color Palette — "Monochrome"

```swift
extension Color {
    // Backgrounds
    static let parkWhite     = Color(hex: "#FFFFFF")
    static let parkOffWhite  = Color(hex: "#F5F5F5")
    static let parkLightGray = Color(hex: "#E5E5E5")
    static let parkMidGray   = Color(hex: "#9CA3AF")
    static let parkDarkGray  = Color(hex: "#4B5563")
    static let parkCharcoal  = Color(hex: "#1F2937")
    static let parkBlack     = Color(hex: "#000000")

    // Accents (used sparingly — the only color in the app)
    static let parkBlue      = Color(hex: "#3B82F6")  // Panther eye, location dot, CTA
    static let parkSuccess   = Color(hex: "#10B981")  // Saved successfully
    static let parkWarning   = Color(hex: "#F59E0B")  // Time warnings
    static let parkDanger    = Color(hex: "#EF4444")  // Delete, expired
}
```

**Color Rule:** The entire app is black and white. `parkBlue` appears ONLY for:
- The active location dot on the map
- The "Park Here" and "Find Car" primary buttons
- The panther's eye
- Active navigation arrow
- Warning badges

Everything else = shades of black, white, and gray.

---

## Haptics — Full Map

```swift
import UIKit
import CoreHaptics

final class ParkItHaptics {
    static let shared = ParkItHaptics()

    func saveLocation() {
        // Success: satisfying confirmation
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    func findCar() {
        // Heavy + success: rewarding confirmation
        UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
    }

    func timeWarning() {
        // Warning: urgent but not alarming
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
    }

    func timeCritical() {
        // Double warning: very urgent
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.18) {
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
        }
    }

    func longPressMap() {
        // Light: drop a pin manually
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    func navigationArrow() {
        // Selection: tapping nav arrow
        UISelectionFeedbackGenerator().selectionChanged()
    }

    func delete() {
        // Rigid: definitive delete
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred()
    }

    func pullToRefresh() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    func buttonTap() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    func mapZoom() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    func toggle() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    func endParking() {
        // Confirmation: session ended
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
    }

    // Proximity haptics — gets stronger as you approach car
    func proximityPulse(distance: Double) {
        // < 50m: medium pulse every 3s
        // < 20m: heavy pulse every 1.5s
        // < 10m: rapid double pulse
        let intensity: UIImpactFeedbackGenerator.FeedbackStyle
        switch distance {
        case ..<10:
            intensity = .heavy
        case ..<20:
            intensity = .medium
        default:
            intensity = .light
        }
        UIImpactFeedbackGenerator(style: intensity).impactOccurred()
    }
}
```

---

## Animations

### Core Principles
- **Minimal motion** — animations should feel like the panther: controlled, purposeful, not flashy
- **Map-first** — the map is the hero; UI elements slide over it, never obscure it
- **B&W contrast transitions** — fades and slides in black/white look cinematic
- **The panther moves fluidly** — any panther animation must feel liquid, never jerky

### Animation Constants

```swift
enum ParkItAnim {
    static let snappy   = Animation.spring(response: 0.28, dampingFraction: 0.75)
    static let smooth   = Animation.spring(response: 0.4,  dampingFraction: 0.85)
    static let slow     = Animation.spring(response: 0.55, dampingFraction: 0.88)
    static let quick    = Animation.easeOut(duration: 0.16)
    static let fade     = Animation.easeInOut(duration: 0.22)
    static let panther  = Animation.spring(response: 0.5,  dampingFraction: 0.65)  // Panther walks
    static let mapPin   = Animation.spring(response: 0.35, dampingFraction: 0.55)  // Pin drops
}
```

### Key Animated Interactions

| Interaction | Animation | Haptic |
|-------------|-----------|--------|
| Park Here button tap | Button scales 0.95 → 1.0, ripple expands | buttonTap() |
| Location saved | Pin drops onto map with bounce, success card slides up | saveLocation() |
| Find Car tap | Button flashes blue, compass animates in | findCar() |
| Parking card expand | Sheet slides up with spring, blurs map behind | smooth spring |
| Time warning | Timer text pulses red, badge bounces | timeWarning() |
| Delete swipe | Red background slides in, cell scales 0.95 | delete() |
| Panther map pin | Pin is panther silhouette, drops with tail bounce | mapPin spring |
| Compass rotation | Smooth continuous rotation following heading | — |
| Distance counter | Number counts down smoothly as you walk | proximityPulse |
| End parking | Card slides down and fades, map zooms to current loc | endParking() |
| History row appear | Rows slide in from right, staggered | — |
| Long press map | Pin hovers above finger, drops on release | longPressMap() |

### Panther Pin Drop Animation
```swift
struct PantherPinView: View {
    @State private var dropped = false
    @State private var tailBounce: CGFloat = 0

    var body: some View {
        VStack(spacing: 0) {
            Image("panther_pin")  // Your panther silhouette asset
                .resizable()
                .scaledToFit()
                .frame(width: 32, height: 32)
                .offset(y: dropped ? 0 : -40)
                .animation(ParkItAnim.mapPin, value: dropped)
                .onAppear {
                    withAnimation(ParkItAnim.mapPin) { dropped = true }
                    // Tail bounce after drop
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        withAnimation(.spring(response: 0.25, dampingFraction: 0.4)) {
                            tailBounce = 4
                        }
                        withAnimation(.spring(response: 0.25, dampingFraction: 0.6).delay(0.15)) {
                            tailBounce = 0
                        }
                    }
                }

            // Shadow that appears when pin drops
            Ellipse()
                .fill(.black.opacity(dropped ? 0.25 : 0))
                .frame(width: 16, height: 6)
                .animation(ParkItAnim.quick, value: dropped)
        }
    }
}
```

### Save Location Confirmation Animation
```swift
struct SaveConfirmationOverlay: View {
    @Binding var isShowing: Bool
    @State private var circleScale: CGFloat = 0
    @State private var checkVisible = false
    @State private var textVisible = false

    var body: some View {
        if isShowing {
            VStack(spacing: 16) {
                ZStack {
                    Circle()
                        .fill(Color(hex: "#10B981"))
                        .frame(width: 72, height: 72)
                        .scaleEffect(circleScale)

                    Image(systemName: "checkmark")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(.white)
                        .opacity(checkVisible ? 1 : 0)
                        .scaleEffect(checkVisible ? 1 : 0.5)
                }

                if textVisible {
                    Text("Location Saved")
                        .font(Font.custom("BebasNeue-Regular", size: 28))
                        .foregroundColor(Color(hex: "#1F2937"))
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
            .onAppear {
                ParkItHaptics.shared.saveLocation()
                withAnimation(ParkItAnim.mapPin) { circleScale = 1.0 }
                withAnimation(ParkItAnim.snappy.delay(0.15)) {
                    checkVisible = true
                }
                withAnimation(ParkItAnim.smooth.delay(0.25)) {
                    textVisible = true
                }
                // Auto-dismiss
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.8) {
                    withAnimation(ParkItAnim.fade) { isShowing = false }
                }
            }
        }
    }
}
```

### Bottom Sheet Parking Card
```swift
struct ParkingBottomCard: View {
    @Binding var isParked: Bool
    let timeParked: String   // "2h 34m"
    let distance: String     // "450m"

    var body: some View {
        VStack(spacing: 0) {
            // Drag handle
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(hex: "#E5E5E5"))
                .frame(width: 36, height: 4)
                .padding(.top, 8)
                .padding(.bottom, 16)

            if isParked {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(timeParked)
                            .font(ParkItFont.displayLG)
                            .foregroundColor(Color(hex: "#000000"))
                        Text(distance + " away")
                            .font(ParkItFont.bodyMD)
                            .foregroundColor(Color(hex: "#9CA3AF"))
                    }

                    Spacer()

                    Button(action: {}) {
                        Label("Find Car", systemImage: "location.fill")
                            .font(Font.custom("BebasNeue-Regular", size: 20))
                            .padding(.horizontal, 20)
                            .padding(.vertical, 12)
                            .background(Color(hex: "#3B82F6"))
                            .foregroundColor(.white)
                            .clipShape(Capsule())
                    }
                    .buttonStyle(PressableCard())
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            } else {
                Button(action: {}) {
                    Text("Park Here")
                        .font(Font.custom("BebasNeue-Regular", size: 24))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                        .background(Color(hex: "#000000"))
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                }
                .buttonStyle(PressableCard())
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
    }
}

struct PressableCard: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(ParkItAnim.snappy, value: configuration.isPressed)
    }
}
```

---

## App Icon Spec

**Canvas:** 1024×1024px
**Background:** Pure black `#000000` OR pure white `#FFFFFF` (make both, A/B test)

**Black version (recommended):**
- Background: `#000000`
- Panther silhouette: `#1F2937` (very dark gray — not pure black so it's visible)
- OR use negative space: panther = transparent cutout from white background
- Eye: `#3B82F6` solid ellipse
- Optional: subtle `P` letterform built into silhouette

**White version:**
- Background: `#FFFFFF`
- Panther: `#000000` flat silhouette
- Eye: `#3B82F6`

**Do NOT add:**
- Gradients
- Shadows
- Multiple colors
- Rounded elements (keep everything geometric)

---

## Map Customization

Apply this to Mapbox/MapKit for the B&W map look:

```swift
// For Apple Maps (MapKit) — tinted grayscale
let config = MKStandardMapConfiguration(emphasisStyle: .muted)
config.pointOfInterestFilter = .excludingAll
mapView.preferredConfiguration = config

// For Mapbox — CartoDB Dark Matter tiles
// URL: https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png
```

Custom location annotation (Panther pin):
```swift
class PantherAnnotationView: MKAnnotationView {
    override init(annotation: MKAnnotation?, reuseIdentifier: String?) {
        super.init(annotation: annotation, reuseIdentifier: reuseIdentifier)
        image = UIImage(named: "panther_pin")?.withTintColor(.black)
        frame = CGRect(x: 0, y: 0, width: 32, height: 32)
        centerOffset = CGPoint(x: 0, y: -16)
    }
}
```

---

## Live Activity (Dynamic Island) Design

```
┌────────────────────────────────────────┐
│  🐆  [panther icon]  2h 14m • 320m    │
│                       [Find Car →]     │
└────────────────────────────────────────┘
```

Background: `#000000`
Text: `#FFFFFF` (time) + `#3B82F6` (Find Car button)
Font: Bebas Neue for timer, DM Sans for labels
