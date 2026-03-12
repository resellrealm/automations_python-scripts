"""
Gov.uk Authentication Handler
==============================
Handles login to findapprenticeship.service.gov.uk including:
  - Email + password
  - 2FA / authenticator code (asks via Telegram)
  - Session persistence (saves cookies to disk)
"""

import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

GOVUK_LOGIN_URL = "https://www.findapprenticeship.service.gov.uk/signin"
SESSION_FILE    = Path(__file__).parent / ".govuk_session.json"


class AuthHandler:
    def __init__(self, page, context, notifier, email: str, password: str):
        self.page     = page
        self.context  = context
        self.notifier = notifier
        self.email    = email
        self.password = password

    def login(self) -> bool:
        """
        Full login flow with 2FA support.
        Returns True if logged in successfully.
        """
        # Try restoring saved session first
        if self._restore_session():
            logger.info("Session restored from saved cookies.")
            return True

        logger.info("Logging in to gov.uk apprenticeship service...")

        try:
            self.page.goto(GOVUK_LOGIN_URL, timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1)

            # Fill email
            self._fill("input[type='email'], #Email, input[name='Email']", self.email)
            time.sleep(0.4)

            # Fill password
            self._fill("input[type='password'], #Password, input[name='Password']", self.password)
            time.sleep(0.3)

            # Submit
            self.page.locator("button[type='submit'], input[type='submit']").first.click()
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1.5)

            # Check for 2FA screen
            if self._is_2fa_page():
                success = self._handle_2fa()
                if not success:
                    return False

            # Verify login
            if not self._is_logged_in():
                errors = self._get_errors()
                logger.error(f"Login failed. Errors: {errors}")
                self.notifier.send(f"❌ Gov.uk login failed.\nErrors: {errors or 'unknown'}")
                return False

            # Save session
            self._save_session()
            logger.info("Logged in successfully.")
            self.notifier.send("✅ Logged in to gov.uk successfully.")
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            self.notifier.send(f"❌ Login error: {e}")
            return False

    def _handle_2fa(self) -> bool:
        """Ask user for 2FA code via Telegram and submit it."""
        logger.info("2FA screen detected — asking user via Telegram.")

        code = self.notifier.ask(
            "🔐 <b>Gov.uk needs your 2FA code</b>\n\n"
            "Open your authenticator app and reply with the 6-digit code:",
            timeout=300,
        )

        if not code or not code.strip().isdigit():
            self.notifier.send("❌ No valid code received — skipping login.")
            return False

        # Find the 2FA input field
        selectors = [
            "input[name*='Code']",
            "input[name*='code']",
            "input[name*='token']",
            "input[name*='otp']",
            "input[autocomplete='one-time-code']",
            "input[type='number']",
            "input[inputmode='numeric']",
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
            self.notifier.send("❌ Could not find 2FA input field on the page.")
            return False

        time.sleep(0.5)
        self.page.locator("button[type='submit'], input[type='submit']").first.click()
        self.page.wait_for_load_state("domcontentloaded")
        time.sleep(1.5)

        if self._is_logged_in():
            self.notifier.send("✅ 2FA accepted!")
            return True

        self.notifier.send("❌ 2FA code was rejected. Try again on next run.")
        return False

    def _is_2fa_page(self) -> bool:
        content = self.page.content().lower()
        url     = self.page.url.lower()
        return (
            "verification" in url or
            "two-factor" in url or
            "2fa" in url or
            "authentication code" in content or
            "enter the code" in content or
            "one-time" in content or
            "authenticator" in content
        )

    def _is_logged_in(self) -> bool:
        url     = self.page.url.lower()
        content = self.page.content().lower()
        signed_out = (
            "sign-in" in url or
            "login" in url or
            "signin" in url or
            "id.account.gov.uk" in url
        )
        return not signed_out or "sign out" in content or "my applications" in content

    def _restore_session(self) -> bool:
        """Try loading saved cookies and check if still logged in."""
        if not SESSION_FILE.exists():
            return False
        try:
            cookies = json.loads(SESSION_FILE.read_text())
            self.context.add_cookies(cookies)
            self.page.goto("https://www.findapprenticeship.service.gov.uk/dashboard", timeout=15000)
            self.page.wait_for_load_state("domcontentloaded")
            return self._is_logged_in()
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
