// Park-it — AnimationSystem.swift
// All animations, modifiers, and animated components
// Design rule: minimal motion — controlled and purposeful, like the panther

import SwiftUI

// ─── Animation Constants ──────────────────────────────────────────────────────

enum ParkItAnim {
    static let snappy   = Animation.spring(response: 0.28, dampingFraction: 0.76)
    static let smooth   = Animation.spring(response: 0.42, dampingFraction: 0.85)
    static let slow     = Animation.spring(response: 0.56, dampingFraction: 0.88)
    static let quick    = Animation.easeOut(duration: 0.16)
    static let fade     = Animation.easeInOut(duration: 0.22)
    static let panther  = Animation.spring(response: 0.5,  dampingFraction: 0.64)
    static let pinDrop  = Animation.spring(response: 0.35, dampingFraction: 0.52)
    static let pulse    = Animation.easeInOut(duration: 0.8).repeatForever(autoreverses: true)
}

// ─── Pressable Button Style ───────────────────────────────────────────────────

struct ParkPressableStyle: ButtonStyle {
    var scale: CGFloat = 0.95

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? scale : 1.0)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(ParkItAnim.snappy, value: configuration.isPressed)
    }
}

// ─── Panther Map Pin ──────────────────────────────────────────────────────────

struct PantherPinView: View {
    @State private var pinDropped = false
    @State private var shadowVisible = false
    @State private var tailOffset: CGFloat = 0

    var body: some View {
        VStack(spacing: 2) {
            Image("panther_pin")       // Your flat panther silhouette asset
                .resizable()
                .scaledToFit()
                .frame(width: 34, height: 34)
                .offset(y: pinDropped ? 0 : -50)
                .animation(ParkItAnim.pinDrop, value: pinDropped)
                .overlay(
                    // Blue eye detail
                    Circle()
                        .fill(Color(hex: "#3B82F6"))
                        .frame(width: 5, height: 5)
                        .offset(x: 6, y: -4)
                )

            // Drop shadow grows when pin lands
            Ellipse()
                .fill(Color.black.opacity(shadowVisible ? 0.2 : 0))
                .frame(width: 18, height: 5)
                .blur(radius: 2)
                .animation(ParkItAnim.quick, value: shadowVisible)
        }
        .onAppear {
            withAnimation(ParkItAnim.pinDrop) {
                pinDropped = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                shadowVisible = true
                ParkItHaptics.shared.saveLocation()
                // Tail bounce
                withAnimation(.spring(response: 0.2, dampingFraction: 0.35)) {
                    tailOffset = 5
                }
                withAnimation(.spring(response: 0.25, dampingFraction: 0.65).delay(0.12)) {
                    tailOffset = 0
                }
            }
        }
    }
}

// ─── Save Success Overlay ─────────────────────────────────────────────────────

struct ParkSaveSuccessView: View {
    @Binding var isShowing: Bool

    @State private var circleScale: CGFloat = 0.1
    @State private var circleOpacity: Double = 1
    @State private var checkScale: CGFloat = 0.3
    @State private var textOpacity: Double = 0
    @State private var textOffset: CGFloat = 12

    var body: some View {
        if isShowing {
            VStack(spacing: 20) {
                ZStack {
                    Circle()
                        .fill(Color(hex: "#000000"))
                        .frame(width: 80, height: 80)
                        .scaleEffect(circleScale)
                        .opacity(circleOpacity)

                    Image(systemName: "p.square.fill")
                        .font(.system(size: 32, weight: .black))
                        .foregroundColor(.white)
                        .scaleEffect(checkScale)
                }

                Text("Parked")
                    .font(Font.custom("BebasNeue-Regular", size: 36))
                    .foregroundColor(Color(hex: "#000000"))
                    .opacity(textOpacity)
                    .offset(y: textOffset)
            }
            .onAppear {
                withAnimation(ParkItAnim.pinDrop) {
                    circleScale = 1.0
                    checkScale = 1.0
                }
                withAnimation(ParkItAnim.smooth.delay(0.2)) {
                    textOpacity = 1
                    textOffset = 0
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    withAnimation(ParkItAnim.fade) {
                        circleOpacity = 0
                        textOpacity = 0
                        isShowing = false
                    }
                }
            }
        }
    }
}

// ─── Animated Timer Display ───────────────────────────────────────────────────

struct ParkTimerView: View {
    let hours: Int
    let minutes: Int
    let isWarning: Bool

    @State private var pulsing = false

    var body: some View {
        HStack(alignment: .bottom, spacing: 2) {
            if hours > 0 {
                Text("\(hours)h")
                    .font(Font.custom("BebasNeue-Regular", size: 52))
            }
            Text("\(String(format: "%02d", minutes))m")
                .font(Font.custom("BebasNeue-Regular", size: 52))
        }
        .foregroundColor(isWarning ? Color(hex: "#EF4444") : Color(hex: "#000000"))
        .scaleEffect(isWarning && pulsing ? 1.04 : 1.0)
        .onChange(of: isWarning) { warning in
            if warning {
                withAnimation(ParkItAnim.pulse) {
                    pulsing = true
                }
            } else {
                pulsing = false
            }
        }
    }
}

// ─── Compass Direction Arrow ──────────────────────────────────────────────────

struct CompassArrowView: View {
    let heading: Double  // Degrees, 0 = North
    let distanceMeters: Double

    var body: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(Color(hex: "#000000"))
                    .frame(width: 120, height: 120)

                Image(systemName: "arrow.up")
                    .font(.system(size: 44, weight: .bold))
                    .foregroundColor(.white)
                    .rotationEffect(.degrees(heading))
                    .animation(ParkItAnim.smooth, value: heading)
            }

            Text(formatDistance(distanceMeters))
                .font(Font.custom("BebasNeue-Regular", size: 48))
                .foregroundColor(Color(hex: "#000000"))
                .contentTransition(.numericText())
                .animation(ParkItAnim.smooth, value: distanceMeters)
        }
    }

    private func formatDistance(_ meters: Double) -> String {
        if meters >= 1000 {
            return String(format: "%.1f km", meters / 1000)
        }
        return "\(Int(meters))m"
    }
}

// ─── Bottom Sheet Parking Card ────────────────────────────────────────────────

struct ParkingStatusCard: View {
    let isParked: Bool
    let timeString: String
    let distanceString: String
    let onParkHere: () -> Void
    let onFindCar: () -> Void

    @State private var cardVisible = false

    var body: some View {
        VStack(spacing: 0) {
            // Pull handle
            Capsule()
                .fill(Color(hex: "#E5E5E5"))
                .frame(width: 40, height: 4)
                .padding(.top, 10)
                .padding(.bottom, 18)

            if isParked {
                HStack(alignment: .center) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(timeString)
                            .font(Font.custom("BebasNeue-Regular", size: 44))
                            .foregroundColor(Color(hex: "#000000"))
                            .contentTransition(.numericText())

                        Text(distanceString)
                            .font(Font.custom("DMSans-Regular", size: 14))
                            .foregroundColor(Color(hex: "#9CA3AF"))
                    }

                    Spacer()

                    Button(action: {
                        ParkItHaptics.shared.findCar()
                        onFindCar()
                    }) {
                        HStack(spacing: 6) {
                            Image(systemName: "location.fill")
                                .font(.system(size: 14, weight: .semibold))
                            Text("Find Car")
                                .font(Font.custom("BebasNeue-Regular", size: 22))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 22)
                        .padding(.vertical, 14)
                        .background(Color(hex: "#3B82F6"))
                        .clipShape(Capsule())
                    }
                    .buttonStyle(ParkPressableStyle())
                }
                .padding(.horizontal, 22)
                .padding(.bottom, 28)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            } else {
                Button(action: {
                    ParkItHaptics.shared.buttonTap()
                    onParkHere()
                }) {
                    Text("Park Here")
                        .font(Font.custom("BebasNeue-Regular", size: 26))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                        .background(Color(hex: "#000000"))
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }
                .buttonStyle(ParkPressableStyle())
                .padding(.horizontal, 20)
                .padding(.bottom, 28)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .offset(y: cardVisible ? 0 : 150)
        .onAppear {
            withAnimation(ParkItAnim.smooth.delay(0.1)) {
                cardVisible = true
            }
        }
    }
}

// ─── History Row Entrance ─────────────────────────────────────────────────────

struct SlideInRow: ViewModifier {
    let index: Int
    @State private var visible = false

    func body(content: Content) -> some View {
        content
            .opacity(visible ? 1 : 0)
            .offset(x: visible ? 0 : 30)
            .onAppear {
                withAnimation(ParkItAnim.smooth.delay(Double(index) * 0.06)) {
                    visible = true
                }
            }
    }
}

extension View {
    func slideInRow(index: Int) -> some View {
        modifier(SlideInRow(index: index))
    }
}

// ─── Warning Pulse ────────────────────────────────────────────────────────────

struct WarningPulseModifier: ViewModifier {
    let isActive: Bool
    @State private var scale: CGFloat = 1.0

    func body(content: Content) -> some View {
        content
            .scaleEffect(scale)
            .onChange(of: isActive) { active in
                if active {
                    withAnimation(
                        .easeInOut(duration: 0.6)
                        .repeatForever(autoreverses: true)
                    ) {
                        scale = 1.06
                    }
                } else {
                    withAnimation(ParkItAnim.snappy) {
                        scale = 1.0
                    }
                }
            }
    }
}

extension View {
    func warningPulse(isActive: Bool) -> some View {
        modifier(WarningPulseModifier(isActive: isActive))
    }
}

// ─── Panther Loading Spinner ──────────────────────────────────────────────────

struct PantherLoader: View {
    @State private var rotation: Double = 0
    @State private var opacity: Double = 1

    var body: some View {
        // Panther tail curls in a circle (use tail asset or simple arc)
        Circle()
            .trim(from: 0, to: 0.75)
            .stroke(Color(hex: "#000000"), style: StrokeStyle(lineWidth: 3, lineCap: .round))
            .frame(width: 32, height: 32)
            .rotationEffect(.degrees(rotation))
            .onAppear {
                withAnimation(.linear(duration: 0.9).repeatForever(autoreverses: false)) {
                    rotation = 360
                }
            }
    }
}

// ─── Color Helper ─────────────────────────────────────────────────────────────

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:  (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:  (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:  (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default: (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB, red: Double(r)/255, green: Double(g)/255, blue: Double(b)/255, opacity: Double(a)/255)
    }
}
