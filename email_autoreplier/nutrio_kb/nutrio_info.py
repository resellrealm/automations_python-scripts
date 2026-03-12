"""
Nutrio+ Knowledge Base
Full product context injected into the AI so it can answer support emails accurately.
Update this file whenever the app changes.
"""

NUTRIO_KB = """
=== NUTRIO+ APP — SUPPORT KNOWLEDGE BASE ===

APP OVERVIEW:
Nutrio+ is an AI-powered nutrition tracking and fitness management app.
It helps users monitor food intake, plan meals, track workouts, and achieve health goals
through gamification, AI meal analysis, and social features.
App ID: com.nutrioplus.app | Version: 11.0.0
Support email: support@nutrioplus.com

PRICING & PLANS:
- Free plan: 2 AI meal scans per day, core features
- Monthly Premium: £7.99/month
- 6-Month Premium: £39.99 (save vs monthly)
- Yearly Premium: £59.99/year (best value)
- Free Trial: 7 days on all premium plans
- Promo codes: Available via referral rewards

PREMIUM BENEFITS vs FREE:
- Unlimited daily AI meal scans (free = 2/day)
- Full access to meal planning calendar
- Advanced analytics and progress charts
- Priority support

CORE FEATURES:
1. AI Meal Analysis — Take a photo of food → AI identifies it and logs macros/calories
2. Barcode Scanner — Scan packaged food barcodes for instant nutrition info
3. Manual Food Entry — Log food manually with full nutrient breakdown
4. Meal Planning — AI-generated weekly meal plans with shopping list
5. Workout Tracking — Log exercises, sets, reps, weight
6. Weight Tracking — Daily weigh-in with trend chart
7. Personal Records — Track strength PRs per exercise
8. Gamification — XP system, levels, achievements, streak tracking
9. Social Features — Friends system, public profiles
10. Home Screen Widgets — Stats widget showing streak, calories, workouts
11. Allergen Detection — Flags allergens in scanned/logged foods
12. Recipe Creator — Build custom recipes, save to collections
13. Offline Mode — Logs food offline, syncs when back online

COMMON SUPPORT QUESTIONS & ANSWERS:

Q: My AI meal scan isn't working / camera won't open
A: Check camera permissions — go to phone Settings > Nutrio+ > allow Camera.
   If still not working, try restarting the app or reinstalling.

Q: I've used my 2 free scans for today
A: Free plan allows 2 AI meal scans per day. Upgrade to Premium for unlimited scans.
   Scans reset at midnight in your local timezone.

Q: How do I cancel my subscription?
A: Cancel via the App Store: iPhone Settings > Apple ID > Subscriptions > Nutrio+ > Cancel.
   Your premium access continues until the end of the paid period.

Q: I want a refund
A: Refunds are handled by Apple (iOS). Contact Apple Support or go to reportaproblem.apple.com.
   We cannot process refunds directly as payments go through the App Store.

Q: My data isn't syncing between devices
A: Ensure you're logged into the same account on both devices.
   Check internet connection. Force-close the app and reopen.
   If still an issue, email support@nutrioplus.com with your account email.

Q: I forgot my password
A: Use the "Forgot Password" link on the login screen — a reset link will be emailed to you.
   Check your spam folder if it doesn't arrive within 5 minutes.

Q: Can I use Nutrio+ on Android?
A: Currently Nutrio+ is iOS only. Android support is on the roadmap.

Q: How accurate is the AI meal scanning?
A: The AI uses Google Gemini and is highly accurate for common foods.
   For best results: good lighting, single dish visible, photo taken from above.
   You can always edit the AI's suggestion after it logs.

Q: What does the XP/levelling system do?
A: You earn XP for logging meals, completing workouts, maintaining streaks,
   and unlocking achievements. XP increases your level and unlocks rewards.

Q: My streak reset even though I logged food
A: Streaks require at least one food log before midnight in your timezone each day.
   Streak shields (earned via referrals/achievements) protect your streak from breaking.

Q: How do I delete my account?
A: Email support@nutrioplus.com with your account email and request account deletion.
   This permanently removes all your data in accordance with our Privacy Policy.

Q: The app crashes on launch
A: Try: 1) Force close and reopen. 2) Update to the latest version from the App Store.
   3) Restart your phone. 4) Reinstall. If still crashing, email support@nutrioplus.com.

Q: How does the referral programme work?
A: Share your referral code from the app. When a friend signs up using your code,
   you both get a reward (streak shield or ring unlock).

Q: Can I export my data?
A: Data export is being worked on. Email support@nutrioplus.com to request your data manually.

ESCALATE TO HUMAN WHEN:
- User requesting refund (Apple handles, but needs empathy + Apple link)
- Account deletion requests
- Billing disputes or charge issues
- App crashes that aren't fixed by standard troubleshooting
- Privacy/data requests (GDPR etc.)
- Angry or upset users needing a personal touch
- Anything involving account security or suspected unauthorised access

TONE GUIDELINES:
- Friendly, warm, encouraging (fitness app audience)
- Keep replies concise — users are busy
- Always end with an offer to help further
- Sign off as: "[Name], Nutrio+ Support Team"
"""


def get_kb() -> str:
    """Return the full knowledge base string for injection into AI prompts."""
    return NUTRIO_KB.strip()


def get_short_context() -> str:
    """Return a compact version for token-limited contexts."""
    return (
        "Nutrio+ is an AI nutrition & fitness tracking app (iOS). "
        "Plans: Free (2 scans/day), Monthly £7.99, 6-Month £39.99, Yearly £59.99, 7-day trial. "
        "Refunds via Apple (reportaproblem.apple.com). "
        "Support: support@nutrioplus.com. "
        "Key features: AI meal scan, barcode scanner, workout tracking, XP/streaks, meal planning."
    )
