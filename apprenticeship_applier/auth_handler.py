"""
Gov.uk Authentication Handler
==============================
Handles login to findapprenticeship.service.gov.uk via GOV.UK One Login.

GOV.UK One Login flow (post-2024 migration):
  1. Click "Sign in" → redirected to signin.account.gov.uk
  2. Enter email → continue
  3. Enter password → continue
  4. OTP sent to email inbox (6-digit code)
  5. Enter OTP → redirected back to findapprenticeship.service.gov.uk (logged in)

Session persistence: saves cookies to disk, restores on next run.
2FA / OTP: prompts user via Telegram to paste the code from their email.
"""

import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

GOVUK_LOGIN_URL  = "https://www.findapprenticeship.service.gov.uk/signin"
GOVUK_DASHBOARD  = "https://www.findapprenticeship.service.gov.uk/dashboard"
SESSION_FILE     = Path(__file__).parent / ".govuk_session.json"

# GOV.UK One Login domains — being ON these is part of the login flow, not failure
ONELOGIN_DOMAINS = ("signin.account.gov.uk", "oidc.account.gov.uk", "id.account.gov.uk")


class AuthHandler:
    def __init__(self, page, context, notifier, email: str, password: str):
        self.page     = page
        self.context  = context
        self.notifier = notifier
        self.email    = email
        self.password = password

    def login(self) -> bool:
        """
        Full login flow with GOV.UK One Login (email + password + email OTP).
        Returns True if logged in successfully.
        """
        if self._restore_session():
            logger.info("Session restored from saved cookies.")
            return True

        logger.info("Logging in via GOV.UK One Login...")

        try:
            self.page.goto(GOVUK_LOGIN_URL, timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1.5)

            # Step 1: Enter email on GOV.UK One Login
            self._fill("input[name='email'], #email, input[type='email']", self.email)
            time.sleep(0.4)
            self._submit()
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1.5)

            # Step 2: Enter password (if on password page)
            if self._is_password_page():
                self._fill("input[name='password'], #password, input[type='password']", self.password)
                time.sleep(0.3)
                self._submit()
                self.page.wait_for_load_state("domcontentloaded")
                time.sleep(1.5)

            # Step 3: OTP sent to email — ask user via Telegram
            if self._is_otp_page():
                success = self._handle_otp()
                if not success:
                    return False

            # Step 4: Legacy 2FA (authenticator app) — kept for compatibility
            elif self._is_2fa_page():
                success = self._handle_2fa()
                if not success:
                    return False

            # Verify we landed back on findapprenticeship
            if not self._is_logged_in():
                errors = self._get_errors()
                logger.error(f"Login failed. URL={self.page.url} Errors: {errors}")
                self.notifier.send(f"❌ Gov.uk login failed.\nURL: {self.page.url}\nErrors: {errors or 'unknown'}")
                return False

            self._save_session()
            logger.info("Logged in successfully.")
            self.notifier.send("✅ Logged in to gov.uk successfully.")
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            self.notifier.send(f"❌ Login error: {e}")
            return False

    # ── OTP (GOV.UK One Login email code) ─────────────────────────────────────

    def _is_otp_page(self) -> bool:
        """Detect GOV.UK One Login email OTP screen."""
        url     = self.page.url.lower()
        content = self.page.content().lower()
        return (
            "check-your-email" in url or
            "enter-code" in url or
            "security-code" in url or
            "check your email" in content or
            "we've sent you an email" in content or
            "enter the 6 digit security code" in content or
            "enter the code we sent" in content or
            "6-digit" in content
        )

    def _handle_otp(self) -> bool:
        """Ask user for email OTP via Telegram, submit it."""
        logger.info("Email OTP screen detected — asking user via Telegram.")

        code = self.notifier.ask(
            "📧 <b>Gov.uk sent you a 6-digit code</b>\n\n"
            "Check your email inbox (including spam) and reply with the 6-digit code:",
            timeout=600,   # 10 minutes
        )

        if not code or not code.strip().isdigit() or len(code.strip()) != 6:
            self.notifier.send("❌ Invalid or no code received — login aborted.")
            return False

        selectors = [
            "input[name='code']",
            "input[autocomplete='one-time-code']",
            "input[name*='otp']",
            "input[name*='token']",
            "input[inputmode='numeric']",
            "input[type='number']",
            "input[type='text'][maxlength='6']",
        ]
        filled = False
        for sel in selectors:
            try:
                field = self.page.locator(sel).first
                if field.count() > 0 and field.is_visible():
                    field.fill(code.strip())
                    filled = True
                    break
            except Exception:
                pass

        if not filled:
            logger.error("Could not find OTP input field.")
            self.notifier.send("❌ Could not find OTP input field. Check screenshots.")
            return False

        time.sleep(0.5)
        self._submit()
        self.page.wait_for_load_state("domcontentloaded")
        time.sleep(2.0)

        if self._is_logged_in():
            self.notifier.send("✅ OTP accepted!")
            return True

        self.notifier.send("❌ OTP rejected. Will retry on next run.")
        return False

    # ── Legacy 2FA (authenticator app) ────────────────────────────────────────

    def _is_2fa_page(self) -> bool:
        content = self.page.url.lower() + " " + self.page.content().lower()
        return (
            "two-factor" in content or
            "2fa" in content or
            "authenticator" in content or
            ("verification" in content and "code" in content)
        )

    def _handle_2fa(self) -> bool:
        """Ask user for authenticator 2FA code via Telegram."""
        logger.info("2FA screen detected — asking user via Telegram.")

        code = self.notifier.ask(
            "🔐 <b>Gov.uk needs your 2FA code</b>\n\n"
            "Open your authenticator app and reply with the 6-digit code:",
            timeout=300,
        )

        if not code or not code.strip().isdigit():
            self.notifier.send("❌ No valid code received — skipping login.")
            return False

        selectors = [
            "input[name*='Code']",
            "input[name*='code']",
            "input[autocomplete='one-time-code']",
            "input[inputmode='numeric']",
            "input[type='number']",
        ]
        filled = False
        for sel in selectors:
            try:
                field = self.page.locator(sel).first
                if field.count() > 0 and field.is_visible():
                    field.fill(code.strip())
                    filled = True
                    break
            except Exception:
                pass

        if not filled:
            logger.error("Could not find 2FA input field.")
            self.notifier.send("❌ Could not find 2FA input field.")
            return False

        time.sleep(0.5)
        self._submit()
        self.page.wait_for_load_state("domcontentloaded")
        time.sleep(1.5)

        if self._is_logged_in():
            self.notifier.send("✅ 2FA accepted!")
            return True

        self.notifier.send("❌ 2FA code was rejected. Try again on next run.")
        return False

    # ── State detection ────────────────────────────────────────────────────────

    def _is_password_page(self) -> bool:
        url     = self.page.url.lower()
        content = self.page.content().lower()
        return (
            "enter-password" in url or
            "password" in url or
            "input[type='password']" in content or
            "enter your password" in content or
            "your password" in content
        )

    def _is_logged_in(self) -> bool:
        """
        True when browser is on findapprenticeship.service.gov.uk (not on GOV.UK One Login).
        GOV.UK One Login domains are part of the login FLOW — being on them mid-login
        does NOT mean we're logged out; but if we end up there AFTER OTP, login failed.
        """
        url     = self.page.url.lower()
        content = self.page.content().lower()

        # We're on findapprenticeship — check for logged-in content
        if "findapprenticeship.service.gov.uk" in url:
            signed_out_indicators = ("sign-in" in url, "signin" in url, "/start" in url)
            if not any(signed_out_indicators):
                return True
            # Could still be logged in if page contains these
            return "sign out" in content or "my applications" in content or "dashboard" in content

        # Still on GOV.UK One Login — login not complete yet
        if any(domain in url for domain in ONELOGIN_DOMAINS):
            return False

        # Unknown domain — check content
        return "sign out" in content or "my applications" in content

    # ── Session persistence ────────────────────────────────────────────────────

    def _restore_session(self) -> bool:
        """Try loading saved cookies and verify still logged in."""
        if not SESSION_FILE.exists():
            return False
        try:
            cookies = json.loads(SESSION_FILE.read_text())
            self.context.add_cookies(cookies)
            self.page.goto(GOVUK_DASHBOARD, timeout=15000)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1)
            if self._is_logged_in():
                return True
            logger.debug("Saved session expired.")
            return False
        except Exception as e:
            logger.debug(f"Session restore failed: {e}")
            return False

    def _save_session(self):
        """Save cookies for next run."""
        try:
            cookies = self.context.cookies()
            SESSION_FILE.write_text(json.dumps(cookies))
            logger.debug("Session cookies saved.")
        except Exception as e:
            logger.debug(f"Could not save session: {e}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _submit(self):
        try:
            self.page.locator("button[type='submit'], input[type='submit']").first.click()
        except Exception as e:
            logger.debug(f"Submit click error: {e}")

    def _fill(self, selector: str, value: str):
        for sel in selector.split(", "):
            try:
                field = self.page.locator(sel.strip()).first
                if field.count() > 0 and field.is_visible():
                    field.fill(value)
                    return
            except Exception:
                pass

    def _get_errors(self) -> str:
        try:
            msgs = self.page.locator(".govuk-error-message, .error-message, .field-error").all_text_contents()
            return " | ".join(m.strip() for m in msgs if m.strip())
        except Exception:
            return ""
