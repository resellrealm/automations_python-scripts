# Surve — Full Design System

## Mascot: Luci the Eagle

**Concept:**
Luci is a geometric, minimalist eagle built from sharp angular shapes — no curves, all precision. She represents accuracy, dominance, and tracking every point of every game. One eye always locked forward. Wings mid-spread, sharp like blades.

**Style Direction:**
- Geometric/abstract — not photorealistic, not cartoon
- Angular symmetrical wings extending outward
- Bold silhouette readable at all sizes (16px app icon → billboard)
- Steel blue + white on dark background version
- White + steel outline on light background version

**Where Luci Appears:**
- App icon (centered, wings spread, glowing steel-blue eye)
- Onboarding splash (large hero illustration, animated wing flap on entry)
- Empty states (Luci perching, looking curious, no matches yet)
- Win celebration (Luci diving/swooping, triggered with confetti)
- Loading indicators (Luci's eye blinking, wing feathers cycling)
- Settings avatar placeholder
- Widget background (very faint, ghosted behind data)

**DIY Creation Guide:**
1. Go to Flaticon → search "eagle" → filter by "Lineal Color" or "Flat" style
2. Best starting point: Freepik's geometric eagle vectors (SVG)
3. In Figma/Illustrator: simplify to 3-4 angular shapes for wings + sharp head
4. Eye = solid steel-blue circle (`#3B82F6`)
5. Body = dark charcoal (`#0F172A`) or steel-white
6. Export: SVG, 1024×1024 PNG (App Store), 60×60 @2x, @3x

**Search Terms:**
- Flaticon: "eagle", "symbol eagle", "geometric eagle"
- Vecteezy: "eagle minimal vector", "geometric eagle logo"
- Freepik: "eagle line art logo"

---

## Typography

### Font Stack

| Role | Font | Weight | Source |
|------|------|--------|--------|
| **Brand / App Name** | Montserrat | 800 ExtraBold | Google Fonts |
| **Score Display** | Bebas Neue | Regular | Google Fonts |
| **Headings** | Montserrat | 700 Bold | Google Fonts |
| **Body / Labels** | Montserrat | 400, 500 | Google Fonts |
| **Stats / Data** | SF Mono | — | iOS System |
| **Fallback** | SF Pro Display | — | iOS System |

### Why Montserrat + Bebas Neue (Eagle Mood Match)

**Montserrat Bold** → This is Luci. Strong, geometric, confident. The uppercase "SURVE" in Montserrat ExtraBold looks like a brand athletes trust. It's used in sports logos, leadership brands, premium apps — exactly the energy an eagle projects. Powerful, not aggressive.

**Bebas Neue** → Scores only. When "6" appears at 96pt Bebas Neue it looks like a real scoreboard — Wimbledon, ATP, NBA. Pure display role. Montserrat and Bebas Neue sit well together because one is round-geometric (brand) and the other is tall-condensed (data).

**Why not Russo One?** It's powerful but anonymous. Montserrat has the same strength with far more personality — better for a named brand with a mascot.

### Type Scale

```swift
// Surve Typography Scale
enum SurveFont {
    // Brand / App name — Montserrat ExtraBold
    static let brand       = Font.custom("Montserrat-ExtraBold", size: 32)  // "SURVE" wordmark

    // Score display — Bebas Neue (scoreboard role only)
    static let scoreHuge   = Font.custom("BebasNeue-Regular", size: 96)  // Live score
    static let scoreLarge  = Font.custom("BebasNeue-Regular", size: 64)  // Main scoreboard
    static let scoreMedium = Font.custom("BebasNeue-Regular", size: 48)  // History cells
    static let scoreSmall  = Font.custom("BebasNeue-Regular", size: 32)  // Watch / compact

    // Headings — Montserrat Bold
    static let headingXL   = Font.custom("Montserrat-Bold", size: 28)
    static let headingLG   = Font.custom("Montserrat-Bold", size: 22)
    static let headingMD   = Font.custom("Montserrat-SemiBold", size: 18)
    static let headingSM   = Font.custom("Montserrat-SemiBold", size: 15)

    // Body — Montserrat Regular/Medium (consistent single family)
    static let bodyLG      = Font.custom("Montserrat-Medium", size: 17)
    static let bodyMD      = Font.custom("Montserrat-Regular", size: 15)
    static let bodySM      = Font.custom("Montserrat-Regular", size: 13)
    static let caption     = Font.custom("Montserrat-Regular", size: 11)

    // Stats — SF Mono
    static let mono        = Font.system(.body, design: .monospaced)
    static let monoSM      = Font.system(.caption, design: .monospaced)
}
```

### Mood Pairing Logic
```
Eagle Personality → Strong · Confident · Premium · Leadership
Montserrat Bold   → Strong geometric shapes · Sports logos · Brand authority
Bebas Neue        → Scoreboard energy · Athletic data display
Result            → Brand feels like a sports network. Scores feel like a real court.
```

---

## Color Palette — "Modern Steel"

```swift
extension Color {
    // Backgrounds
    static let steel50  = Color(hex: "#F8FAFC")
    static let steel100 = Color(hex: "#F1F5F9")
    static let steel200 = Color(hex: "#E2E8F0")
    static let steel300 = Color(hex: "#CBD5E1")
    static let steel400 = Color(hex: "#94A3B8")
    static let steel500 = Color(hex: "#64748B")
    static let steel600 = Color(hex: "#475569")
    static let steel700 = Color(hex: "#334155")
    static let steel800 = Color(hex: "#1E293B")
    static let steel900 = Color(hex: "#0F172A")

    // Accent
    static let accentBlue = Color(hex: "#3B82F6")   // Primary actions, Luci's eye
    static let accentCyan = Color(hex: "#06B6D4")   // Highlights, serve indicators

    // Match states
    static let winGreen  = Color(hex: "#10B981")
    static let lossRed   = Color(hex: "#EF4444")
    static let drawGray  = Color(hex: "#94A3B8")

    // Dark mode overrides
    static let surfaceDark    = Color(hex: "#0F172A")
    static let surfaceElevated = Color(hex: "#1E293B")
}
```

---

## Haptics — Full Map

```swift
import UIKit
import CoreHaptics

class SurveHaptics {
    static let shared = SurveHaptics()
    private var engine: CHHapticEngine?

    // MARK: - Simple UIKit haptics
    func scoreIncrement() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    func scoreDecrement() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    func buttonTap() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    func longPress() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }

    func deleteAction() {
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred()
    }

    func gameWin() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    func error() {
        UINotificationFeedbackGenerator().notificationOccurred(.error)
    }

    func pullToRefresh() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    // MARK: - Match win (heavy + success)
    func matchWin() {
        let impact = UIImpactFeedbackGenerator(style: .heavy)
        impact.impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        }
    }

    // MARK: - Set win (medium + success)
    func setWin() {
        let impact = UIImpactFeedbackGenerator(style: .medium)
        impact.impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
    }

    // MARK: - Deuce / tie point
    func deuce() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        }
    }

    // MARK: - Sport card select
    func sportSelect() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    // MARK: - Undo swipe
    func undoSwipe() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    // MARK: - Shake to undo
    func shakeUndo() {
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
    }

    // MARK: - Confetti / celebration burst (CoreHaptics)
    func celebrationBurst() {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else {
            matchWin()
            return
        }
        // Pattern: three sharp taps ascending
        let intensities: [Float] = [0.4, 0.65, 1.0]
        let times: [TimeInterval] = [0, 0.1, 0.22]
        var events = [CHHapticEvent]()
        for (i, intensity) in intensities.enumerated() {
            events.append(CHHapticEvent(
                eventType: .hapticTransient,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: intensity),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.8)
                ],
                relativeTime: times[i]
            ))
        }
        try? engine?.start()
        if let pattern = try? CHHapticPattern(events: events, parameters: []) {
            try? engine?.makePlayer(with: pattern).start(atTime: 0)
        }
    }
}
```

---

## Animations

### Core Principles
- **Spring-first**: All interactive elements use spring animations, never linear
- **Scale-on-tap**: Every tappable element scales down 0.95 on press, springs back
- **Score count-up**: Scores animate with a brief number counter effect
- **Match state transitions**: Full-screen transitions between states (SwiftUI `.transition`)

### Animation Constants

```swift
enum SurveAnimation {
    // Springs
    static let snappy = Animation.spring(response: 0.3, dampingFraction: 0.7)
    static let bouncy = Animation.spring(response: 0.4, dampingFraction: 0.6)
    static let soft   = Animation.spring(response: 0.5, dampingFraction: 0.8)

    // Standard
    static let quick  = Animation.easeOut(duration: 0.15)
    static let smooth = Animation.easeInOut(duration: 0.25)

    // Celebration
    static let celebration = Animation.spring(response: 0.5, dampingFraction: 0.5)

    // Score flip
    static let scoreFlip = Animation.interpolatingSpring(stiffness: 300, damping: 20)
}
```

### Key Animated Interactions

| Interaction | Animation | Haptic |
|-------------|-----------|--------|
| Score tap `+` | Score scales 1.3 → 1.0 (bouncy spring), number increments with counter | Light impact |
| Score tap `-` | Score scales 0.8 → 1.0 (soft spring), number decrements | Soft impact |
| Game win | Score flashes green, Luci dives down from top (slide + scale) | gameWin() |
| Match win | Confetti explosion (ConfettiSwiftUI), Luci swoops full screen, score glows | matchWin() + celebrationBurst() |
| Sport card tap | Card scales 0.95, releases with snappy spring | sportSelect() |
| Match history swipe | iOS standard swipe with rubber-band at edges | — |
| New match sheet | Spring slide from bottom | buttonTap() |
| Tab switch | SF symbol morphs (iOS 18+) or cross-fade | — |
| Onboarding | Luci wings animate open on launch (stagger delay) | — |
| Pull to refresh | Luci's eye animates (rotation) | pullToRefresh() |
| Shake to undo | Score shakes side-to-side, fades to previous | shakeUndo() |

### Score Counter Effect (SwiftUI)
```swift
struct AnimatedScore: View {
    let score: Int
    @State private var displayed: Int = 0
    @State private var scale: CGFloat = 1.0

    var body: some View {
        Text("\(displayed)")
            .font(SurveFont.scoreLarge)
            .scaleEffect(scale)
            .onChange(of: score) { newValue in
                withAnimation(SurveAnimation.scoreFlip) {
                    scale = 1.25
                }
                withAnimation(SurveAnimation.scoreFlip.delay(0.05)) {
                    scale = 1.0
                    displayed = newValue
                }
                SurveHaptics.shared.scoreIncrement()
            }
    }
}
```

### Pressable Button Modifier
```swift
struct PressableStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.94 : 1.0)
            .animation(SurveAnimation.snappy, value: configuration.isPressed)
    }
}
```

### Luci Win Animation
```swift
struct LuciWinOverlay: View {
    @Binding var isShowing: Bool

    var body: some View {
        if isShowing {
            ZStack {
                ConfettiView()

                Image("luci_swoop")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 200)
                    .transition(.asymmetric(
                        insertion: .move(edge: .top).combined(with: .opacity),
                        removal: .scale.combined(with: .opacity)
                    ))
            }
            .onTapGesture { withAnimation { isShowing = false } }
        }
    }
}
```

---

## App Icon Spec

**Canvas:** 1024×1024px, no rounded corners (App Store adds them)
**Background:** Deep navy `#0F172A` or steel gradient (`#0F172A` → `#1E293B`)
**Luci:** Centered, white geometric eagle, wings spread to 70% canvas width
**Eye:** Solid `#3B82F6` circle, slightly oversized for visual pop
**Optional:** Subtle `#3B82F6` glow behind eagle
**Shadow:** None (flat design reads better at small sizes)

**Variations needed:**
- `AppIcon.png` — 1024×1024 (App Store)
- `Icon-60@2x.png` — 120×120
- `Icon-60@3x.png` — 180×180
- `Icon-76@2x.png` — 152×152 (iPad)
- `Icon-Watch-44@2x.png` — 88×88 (Watch)

---

## Loading & Empty States

| State | Luci Behavior | Copy |
|-------|--------------|------|
| No matches | Luci perched, head tilted | "Ready to track your first game?" |
| Loading | Luci's eye blinks (opacity 0→1 loop) | — |
| First launch | Luci flies in from right | "Every sport. Every score." |
| Search no results | Luci shrugs (wing animation) | "No matches found" |
| Error state | Luci looks down | "Couldn't load. Tap to retry." |
