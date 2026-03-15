// Surve — HapticManager.swift
// Full haptic system for all in-app interactions
// Import this anywhere: SurveHaptics.shared.scoreIncrement()

import UIKit
import CoreHaptics

final class SurveHaptics {
    static let shared = SurveHaptics()

    private var engine: CHHapticEngine?
    private var supportsCustomHaptics: Bool

    private init() {
        supportsCustomHaptics = CHHapticEngine.capabilitiesForHardware().supportsHaptics
        if supportsCustomHaptics {
            setupEngine()
        }
    }

    private func setupEngine() {
        do {
            engine = try CHHapticEngine()
            engine?.playsHapticsOnly = true
            try engine?.start()

            engine?.stoppedHandler = { [weak self] reason in
                self?.setupEngine()
            }
            engine?.resetHandler = { [weak self] in
                try? self?.engine?.start()
            }
        } catch {
            supportsCustomHaptics = false
        }
    }

    // ─── Score Actions ───────────────────────────────────────────────

    /// Tap score to add a point
    func scoreIncrement() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    /// Tap score to remove a point / undo
    func scoreDecrement() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    /// Score reaches deuce / tie
    func deuce() {
        let gen = UIImpactFeedbackGenerator(style: .medium)
        gen.impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            gen.impactOccurred()
        }
    }

    // ─── Win States ──────────────────────────────────────────────────

    /// Win a game within a set
    func gameWin() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    /// Win a set
    func setWin() {
        let impact = UIImpactFeedbackGenerator(style: .medium)
        impact.impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
    }

    /// Win the whole match — heavy impact + success + celebration
    func matchWin() {
        guard supportsCustomHaptics else {
            let heavy = UIImpactFeedbackGenerator(style: .heavy)
            heavy.impactOccurred()
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                UINotificationFeedbackGenerator().notificationOccurred(.success)
            }
            return
        }

        // Custom: three ascending thumps
        let events: [CHHapticEvent] = [
            CHHapticEvent(
                eventType: .hapticTransient,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: 0.5),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.7)
                ],
                relativeTime: 0
            ),
            CHHapticEvent(
                eventType: .hapticTransient,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: 0.75),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.8)
                ],
                relativeTime: 0.12
            ),
            CHHapticEvent(
                eventType: .hapticTransient,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: 1.0),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 1.0)
                ],
                relativeTime: 0.26
            ),
            CHHapticEvent(
                eventType: .hapticContinuous,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: 0.6),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.3)
                ],
                relativeTime: 0.32,
                duration: 0.25
            )
        ]
        playCustomPattern(events)
    }

    // ─── UI Actions ──────────────────────────────────────────────────

    /// Any button tap (nav, CTA)
    func buttonTap() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    /// Sport card selected
    func sportSelect() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    /// Long press (manual score edit, pin drop)
    func longPress() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }

    /// Delete / destructive action
    func deleteAction() {
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred()
    }

    /// Pull to refresh start
    func pullToRefresh() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    /// Shake to undo detected
    func shakeUndo() {
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
    }

    /// Toggle switch
    func toggle() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    /// Error / invalid action
    func error() {
        UINotificationFeedbackGenerator().notificationOccurred(.error)
    }

    /// Tab bar switch
    func tabSwitch() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    /// Sheet presented
    func sheetPresent() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    // ─── Watch Haptics ───────────────────────────────────────────────
    // WKInterfaceDevice.current().play(.click) on watchOS
    // Use WKHapticType: .success, .notification, .directionUp, .directionDown

    // ─── Private ─────────────────────────────────────────────────────

    private func playCustomPattern(_ events: [CHHapticEvent]) {
        guard let engine = engine else { return }
        do {
            let pattern = try CHHapticPattern(events: events, parameters: [])
            let player = try engine.makePlayer(with: pattern)
            try engine.start()
            try player.start(atTime: 0)
        } catch {
            // Fallback
            UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        }
    }
}
