// Surve — AnimationSystem.swift
// All animation constants, modifiers, and reusable animated components

import SwiftUI

// ─── Animation Constants ──────────────────────────────────────────────────────

enum SurveAnim {
    static let snappy      = Animation.spring(response: 0.28, dampingFraction: 0.72)
    static let bouncy      = Animation.spring(response: 0.4,  dampingFraction: 0.58)
    static let soft        = Animation.spring(response: 0.5,  dampingFraction: 0.82)
    static let quick       = Animation.easeOut(duration: 0.14)
    static let smooth      = Animation.easeInOut(duration: 0.24)
    static let scoreFlip   = Animation.interpolatingSpring(stiffness: 380, damping: 22)
    static let celebration = Animation.spring(response: 0.45, dampingFraction: 0.48)
    static let luciSwoop   = Animation.spring(response: 0.6,  dampingFraction: 0.6)
    static let tabSwitch   = Animation.easeInOut(duration: 0.2)
}

// ─── Pressable Button Style ───────────────────────────────────────────────────

struct PressableButtonStyle: ButtonStyle {
    var scale: CGFloat = 0.94

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? scale : 1.0)
            .opacity(configuration.isPressed ? 0.88 : 1.0)
            .animation(SurveAnim.snappy, value: configuration.isPressed)
    }
}

struct LargePressableStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
            .animation(SurveAnim.snappy, value: configuration.isPressed)
    }
}

// ─── Animated Score Display ───────────────────────────────────────────────────

struct AnimatedScoreView: View {
    let score: Int
    let font: Font
    let color: Color

    @State private var displayedScore: Int = 0
    @State private var scale: CGFloat = 1.0
    @State private var flashColor: Color = .clear

    var body: some View {
        Text("\(displayedScore)")
            .font(font)
            .foregroundColor(color)
            .overlay(
                Text("\(displayedScore)")
                    .font(font)
                    .foregroundColor(flashColor)
                    .opacity(flashColor == .clear ? 0 : 0.6)
            )
            .scaleEffect(scale)
            .onChange(of: score) { newValue in
                let isIncrement = newValue > displayedScore
                animateScore(to: newValue, increment: isIncrement)
            }
            .onAppear { displayedScore = score }
    }

    private func animateScore(to value: Int, increment: Bool) {
        // Flash green on increment, red on decrement
        withAnimation(.easeOut(duration: 0.08)) {
            flashColor = increment ? Color(hex: "#10B981") : Color(hex: "#EF4444")
            scale = increment ? 1.3 : 0.8
        }
        withAnimation(SurveAnim.scoreFlip.delay(0.08)) {
            scale = 1.0
            displayedScore = value
        }
        withAnimation(.easeOut(duration: 0.3).delay(0.15)) {
            flashColor = .clear
        }

        if increment {
            SurveHaptics.shared.scoreIncrement()
        } else {
            SurveHaptics.shared.scoreDecrement()
        }
    }
}

// ─── Win Flash Overlay ────────────────────────────────────────────────────────

struct WinFlashModifier: ViewModifier {
    let trigger: Bool
    @State private var flash = false

    func body(content: Content) -> some View {
        content
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(hex: "#10B981"))
                    .opacity(flash ? 0.25 : 0)
            )
            .onChange(of: trigger) { fired in
                guard fired else { return }
                withAnimation(.easeOut(duration: 0.12)) { flash = true }
                withAnimation(.easeOut(duration: 0.4).delay(0.15)) { flash = false }
            }
    }
}

extension View {
    func winFlash(trigger: Bool) -> some View {
        modifier(WinFlashModifier(trigger: trigger))
    }
}

// ─── Sport Card Entrance Animation ───────────────────────────────────────────

struct StaggeredEntrance: ViewModifier {
    let index: Int
    @State private var visible = false

    func body(content: Content) -> some View {
        content
            .opacity(visible ? 1 : 0)
            .offset(y: visible ? 0 : 16)
            .onAppear {
                withAnimation(SurveAnim.bouncy.delay(Double(index) * 0.05)) {
                    visible = true
                }
            }
    }
}

extension View {
    func staggeredEntrance(index: Int) -> some View {
        modifier(StaggeredEntrance(index: index))
    }
}

// ─── Luci Eagle Animations ───────────────────────────────────────────────────

struct LuciEyeBlink: View {
    @State private var opacity: Double = 1.0

    var body: some View {
        // Replace with your Luci eye asset
        Circle()
            .fill(Color(hex: "#3B82F6"))
            .frame(width: 12, height: 12)
            .opacity(opacity)
            .onAppear {
                withAnimation(
                    Animation.easeInOut(duration: 0.18)
                        .repeatForever(autoreverses: true)
                        .delay(1.2)
                ) {
                    opacity = 0.2
                }
            }
    }
}

struct LuciSwoopTransition: ViewModifier {
    let show: Bool

    func body(content: Content) -> some View {
        content
            .transition(
                .asymmetric(
                    insertion: .move(edge: .top).combined(with: .scale(scale: 0.3)).combined(with: .opacity),
                    removal: .scale(scale: 1.4).combined(with: .opacity)
                )
            )
    }
}

// ─── Match Win Celebration ────────────────────────────────────────────────────

struct CelebrationOverlay: View {
    @Binding var isShowing: Bool
    let winnerName: String

    @State private var luciVisible = false
    @State private var textVisible = false

    var body: some View {
        if isShowing {
            ZStack {
                // Dark overlay
                Color.black.opacity(0.6)
                    .ignoresSafeArea()
                    .onTapGesture {
                        withAnimation(SurveAnim.soft) {
                            isShowing = false
                        }
                    }

                VStack(spacing: 24) {
                    // Luci swoops in
                    if luciVisible {
                        Image("luci_celebrate")  // Your eagle asset
                            .resizable()
                            .scaledToFit()
                            .frame(width: 160)
                            .modifier(LuciSwoopTransition(show: luciVisible))
                    }

                    if textVisible {
                        VStack(spacing: 8) {
                            Text(winnerName)
                                .font(Font.custom("RussoOne-Regular", size: 28))
                                .foregroundColor(.white)
                            Text("WINS!")
                                .font(Font.custom("BebasNeue-Regular", size: 64))
                                .foregroundColor(Color(hex: "#3B82F6"))
                        }
                        .transition(.scale(scale: 0.6).combined(with: .opacity))
                    }

                    if textVisible {
                        Button("Continue") {
                            withAnimation(SurveAnim.soft) { isShowing = false }
                        }
                        .font(Font.custom("DMSans-Medium", size: 17))
                        .foregroundColor(Color(hex: "#0F172A"))
                        .padding(.horizontal, 32)
                        .padding(.vertical, 14)
                        .background(Color.white)
                        .clipShape(Capsule())
                        .buttonStyle(PressableButtonStyle())
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    }
                }
            }
            .onAppear {
                SurveHaptics.shared.matchWin()
                withAnimation(SurveAnim.luciSwoop) { luciVisible = true }
                withAnimation(SurveAnim.bouncy.delay(0.3)) { textVisible = true }
            }
        }
    }
}

// ─── Score Tap Ripple ─────────────────────────────────────────────────────────

struct TapRippleModifier: ViewModifier {
    @State private var rippleScale: CGFloat = 0.5
    @State private var rippleOpacity: Double = 0

    func body(content: Content) -> some View {
        content.overlay(
            Circle()
                .fill(Color(hex: "#3B82F6").opacity(0.3))
                .scaleEffect(rippleScale)
                .opacity(rippleOpacity)
                .allowsHitTesting(false)
        )
        .onTapGesture {
            rippleScale = 0.5
            rippleOpacity = 0.7
            withAnimation(.easeOut(duration: 0.5)) {
                rippleScale = 2.5
                rippleOpacity = 0
            }
        }
    }
}

extension View {
    func tapRipple() -> some View { modifier(TapRippleModifier()) }
}

// ─── Shake Effect (for undo) ──────────────────────────────────────────────────

struct ShakeModifier: ViewModifier, Animatable {
    var shakes: CGFloat = 0
    var animatableData: CGFloat {
        get { shakes }
        set { shakes = newValue }
    }

    func body(content: Content) -> some View {
        content.offset(x: sin(shakes * .pi * 2) * 8)
    }
}

struct ShakeView: ViewModifier {
    @Binding var trigger: Bool

    func body(content: Content) -> some View {
        content
            .modifier(ShakeModifier(shakes: trigger ? 1 : 0))
            .animation(
                trigger ? Animation.linear(duration: 0.4).repeatCount(3, autoreverses: true) : .default,
                value: trigger
            )
            .onChange(of: trigger) { if $0 { DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { trigger = false } } }
    }
}

extension View {
    func shake(trigger: Binding<Bool>) -> some View {
        modifier(ShakeView(trigger: trigger))
    }
}

// ─── Color Hex Helper ─────────────────────────────────────────────────────────

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
