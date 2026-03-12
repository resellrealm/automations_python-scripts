"""
CAPTCHA Handler
===============
Strategy (in order):
  1. Try 2captcha API (automated, ~$3/1000 solves)
  2. If no API key or solve fails → send noVNC link via Telegram
     User opens http://VPS_IP:6080 in their browser,
     sees the live browser, clicks the CAPTCHA, replies "done".

noVNC gives you full mouse+keyboard control of the real browser
running on the VPS — exactly like sitting in front of it.
"""

import time
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class CaptchaHandler:
    def __init__(self, page, notifier, twocaptcha_key: str = "", vps_ip: str = ""):
        self.page             = page
        self.notifier         = notifier
        self.twocaptcha_key   = twocaptcha_key
        self.vps_ip           = vps_ip
        self.novnc_port       = 6080

    def detect(self) -> str:
        """
        Returns: 'hcaptcha' | 'recaptcha' | 'cloudflare' | 'none'
        """
        try:
            content = self.page.content().lower()
            if "hcaptcha" in content:
                return "hcaptcha"
            if "recaptcha" in content or "g-recaptcha" in content:
                return "recaptcha"
            if "cf-challenge" in content or "cloudflare" in content:
                return "cloudflare"
        except Exception:
            pass
        return "none"

    def solve(self) -> bool:
        """
        Attempt to solve the CAPTCHA. Returns True if solved, False if failed.
        """
        captcha_type = self.detect()
        if captcha_type == "none":
            return True

        logger.warning(f"CAPTCHA detected: {captcha_type}")

        # Try 2captcha first
        if self.twocaptcha_key:
            solved = self._solve_2captcha(captcha_type)
            if solved:
                return True
            logger.warning("2captcha failed — falling back to noVNC manual solve.")

        # Fallback: noVNC manual
        return self._solve_novnc(captcha_type)

    def _solve_2captcha(self, captcha_type: str) -> bool:
        """Submit CAPTCHA to 2captcha and inject the token."""
        try:
            current_url = self.page.url

            if captcha_type == "hcaptcha":
                sitekey = self._extract_sitekey("data-sitekey", "h-captcha")
                if not sitekey:
                    return False
                token = self._submit_2captcha_hcaptcha(sitekey, current_url)

            elif captcha_type == "recaptcha":
                sitekey = self._extract_sitekey("data-sitekey", "g-recaptcha")
                if not sitekey:
                    return False
                token = self._submit_2captcha_recaptcha(sitekey, current_url)

            else:
                return False  # Cloudflare needs noVNC

            if not token:
                return False

            # Inject token into page
            self.page.evaluate(f"""
                () => {{
                    // hCaptcha
                    const hc = document.querySelector('[name="h-captcha-response"]');
                    if (hc) hc.value = "{token}";
                    // reCAPTCHA
                    const rc = document.querySelector('[name="g-recaptcha-response"]');
                    if (rc) rc.value = "{token}";
                    // Trigger callbacks
                    if (typeof hcaptcha !== 'undefined') hcaptcha.submit();
                    if (typeof grecaptcha !== 'undefined') grecaptcha.execute();
                }}
            """)

            time.sleep(1)
            logger.info("2captcha token injected successfully.")
            return True

        except Exception as e:
            logger.error(f"2captcha solve error: {e}")
            return False

    def _extract_sitekey(self, attr: str, widget_class: str) -> str:
        """Extract the CAPTCHA sitekey from the page HTML."""
        try:
            sitekey = self.page.evaluate(f"""
                () => {{
                    const el = document.querySelector('.{widget_class}, [{attr}]');
                    return el ? el.getAttribute('{attr}') : null;
                }}
            """)
            return sitekey or ""
        except Exception:
            return ""

    def _submit_2captcha_hcaptcha(self, sitekey: str, url: str) -> str:
        """Send hCaptcha to 2captcha and poll for result."""
        return self._submit_and_poll(
            submit_params={
                "key": self.twocaptcha_key,
                "method": "hcaptcha",
                "sitekey": sitekey,
                "pageurl": url,
                "json": 1,
            }
        )

    def _submit_2captcha_recaptcha(self, sitekey: str, url: str) -> str:
        """Send reCAPTCHA to 2captcha and poll for result."""
        return self._submit_and_poll(
            submit_params={
                "key": self.twocaptcha_key,
                "method": "userrecaptcha",
                "googlekey": sitekey,
                "pageurl": url,
                "json": 1,
            }
        )

    def _submit_and_poll(self, submit_params: dict) -> str:
        """Submit CAPTCHA task and poll until solved."""
        try:
            # Submit task
            r = requests.post(
                "https://2captcha.com/in.php",
                data=submit_params,
                timeout=15,
            )
            data = r.json()
            if data.get("status") != 1:
                logger.error(f"2captcha submit error: {data.get('request')}")
                return ""

            task_id = data["request"]
            logger.info(f"2captcha task submitted: {task_id} — waiting for solve...")

            # Poll every 5s, up to 3 minutes
            for _ in range(36):
                time.sleep(5)
                res = requests.get(
                    "https://2captcha.com/res.php",
                    params={"key": self.twocaptcha_key, "action": "get",
                            "id": task_id, "json": 1},
                    timeout=10,
                )
                result = res.json()
                if result.get("status") == 1:
                    logger.info("2captcha solved!")
                    return result["request"]
                if result.get("request") not in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
                    logger.error(f"2captcha error: {result.get('request')}")
                    return ""

        except Exception as e:
            logger.error(f"2captcha poll error: {e}")
        return ""

    def _solve_novnc(self, captcha_type: str) -> bool:
        """
        Send noVNC link via Telegram. User opens the browser, solves CAPTCHA,
        replies "done". Returns True when user confirms done.
        """
        # Take screenshot to show user what they're looking at
        ss_path = "/tmp/captcha_screenshot.png"
        try:
            self.page.screenshot(path=ss_path, full_page=False)
            self.notifier.send_photo(
                ss_path,
                caption=f"🤖 {captcha_type.upper()} CAPTCHA detected on {self.page.url}"
            )
        except Exception:
            pass

        if self.vps_ip:
            novnc_url = f"http://{self.vps_ip}:{self.novnc_port}/vnc.html?autoconnect=true"
            message = (
                f"🔒 <b>CAPTCHA needs solving!</b>\n\n"
                f"1. Open this link on your phone/laptop:\n"
                f"<code>{novnc_url}</code>\n\n"
                f"2. You'll see the live browser — solve the CAPTCHA\n"
                f"3. Reply <b>done</b> when finished\n\n"
                f"⏰ Timeout: 5 minutes"
            )
        else:
            message = (
                f"🔒 <b>CAPTCHA detected!</b> ({captcha_type})\n\n"
                f"VPS_IP not set — can't provide noVNC link.\n"
                f"Add VPS_IP to your .env file.\n\n"
                f"Reply <b>skip</b> to skip this job, or <b>retry</b> to try again."
            )

        reply = self.notifier.ask(message, timeout=300)

        if reply.lower() in ("done", "solved", "ok", "yes", "d"):
            logger.info("User confirmed CAPTCHA solved via Telegram.")
            return True

        logger.warning(f"CAPTCHA not solved — user replied: {reply}")
        return False
