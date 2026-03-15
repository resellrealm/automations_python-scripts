// Park-it — HapticManager.swift
// Full haptic system — call ParkItHaptics.shared.saveLocation() anywhere

import UIKit
import CoreHaptics

final class ParkItHaptics {
    static let shared = ParkItHaptics()

    private var engine: CHHapticEngine?
    private var supportsCustomHaptics: Bool

    private init() {
        supportsCustomHaptics = CHHapticEngine.capabilitiesForHardware().supportsHaptics
        if supportsCustomHaptics { setupEngine() }
    }

    private func setupEngine() {
        do {
            engine = try CHHapticEngine()
            engine?.playsHapticsOnly = true
            try engine?.start()
            engine?.stoppedHandler = { [weak self] _ in self?.setupEngine() }
            engine?.resetHandler = { [weak self] in try? self?.engine?.start() }
        } catch {
            supportsCustomHaptics = false
        }
    }

    // ─── Core Parking Actions ─────────────────────────────────────────

    /// Car location saved — satisfying success pop
    func saveLocation() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    /// "Find Car" tapped — rewarding confirmation
    func findCar() {
        UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
    }

    /// Parking session ended
    func endParking() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }
    }

    // ─── Time Warnings ────────────────────────────────────────────────

    /// 30 min before expiry
    func timeWarning30min() {
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
    }

    /// 5 min before expiry — more urgent
    func timeWarning5min() {
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
        }
    }

    /// Expired — alarming triple tap
    func timeExpired() {
        guard supportsCustomHaptics else {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            return
        }
        let events: [CHHapticEvent] = [0, 0.15, 0.30].map { time in
            CHHapticEvent(
                eventType: .hapticTransient,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: 1.0),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 0.9)
                ],
                relativeTime: time
            )
        }
        playPattern(events)
    }

    // ─── Map Interactions ─────────────────────────────────────────────

    /// Long press to drop a pin manually
    func longPressMap() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    /// Compass/navigation arrow tapped
    func navigationArrowTap() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    /// Map zoom gesture
    func mapZoom() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    // ─── Proximity Guidance ───────────────────────────────────────────

    /// Haptic pulse that intensifies as you get closer to your car
    func proximityPulse(distanceMeters: Double) {
        switch distanceMeters {
        case ..<10:
            // Very close — rapid double pulse
            UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
            }
        case ..<25:
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        case ..<50:
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
        default:
            UIImpactFeedbackGenerator(style: .soft).impactOccurred()
        }
    }

    // ─── UI Actions ───────────────────────────────────────────────────

    /// Delete a parking record
    func delete() {
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred()
    }

    /// Any button tap
    func buttonTap() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    /// Pull to refresh
    func pullToRefresh() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    /// Toggle switch
    func toggle() {
        UIImpactFeedbackGenerator(style: .soft).impactOccurred()
    }

    /// Error
    func error() {
        UINotificationFeedbackGenerator().notificationOccurred(.error)
    }

    // ─── Private ─────────────────────────────────────────────────────

    private func playPattern(_ events: [CHHapticEvent]) {
        guard let engine = engine else {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            return
        }
        do {
            let pattern = try CHHapticPattern(events: events, parameters: [])
            let player = try engine.makePlayer(with: pattern)
            try engine.start()
            try player.start(atTime: 0)
        } catch {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
    }
}
