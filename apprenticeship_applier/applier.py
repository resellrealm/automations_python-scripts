"""
Apprenticeship Applier
======================
Uses Camoufox (stealth Firefox) to fill and submit applications on
findapprenticeship.service.gov.uk.

CAPTCHA handling:
  1. Camoufox bypasses most Cloudflare bot checks silently
  2. If hCaptcha appears → try 2captcha API
  3. If 2captcha fails → send noVNC link via Telegram (you solve in browser)

2FA handling:
  - Bot detects 2FA screen, asks you for the code via Telegram
  - You reply with the 6-digit code → bot continues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import Config
from notifier import get_notifier
from auth_handler import AuthHandler
from captcha_handler import CaptchaHandler
import database

logger = logging.getLogger(__name__)

GOVUK_LOGIN_URL = "https://www.findapprenticeship.service.gov.uk/signin"


def _human_delay(min_s=0.5, max_s=1.8):
    time.sleep(random.uniform(min_s, max_s))


def _human_type(page, selector: str, text: str):
    """Type text with randomised keystroke delays to appear human."""
    try:
        page.click(selector)
        for char in text:
            page.keyboard.type(char)
            time.sleep(random.uniform(0.04, 0.16))
    except Exception as e:
        logger.debug(f"human_type fallback: {e}")
        page.fill(selector, text)


class ApprenticeshipApplier:
    def __init__(self):
        self.browser   = None
        self.context   = None
        self.page      = None
        self.notifier  = get_notifier()
        self._playwright_cm = None

    def __enter__(self):
        self._start_browser()
        return self

    def __exit__(self, *args):
        self._stop_browser()

    def _start_browser(self):
        """Launch Camoufox (stealth Firefox). Falls back to Playwright Chromium."""
        try:
            from camoufox.sync_api import Firefox
            logger.info("Launching Camoufox (stealth Firefox)...")
            self._camoufox_cm = Firefox(
                headless=Config.HEADLESS,
                humanize=True,
            )
            self.browser = self._camoufox_cm.__enter__()
            self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
            self.page    = self.context.new_page()
            logger.info("Camoufox launched.")

        except ImportError:
            logger.warning("camoufox not installed — falling back to Playwright Chromium with stealth.")
            self._start_playwright_fallback()
        except Exception as e:
            logger.warning(f"Camoufox failed ({e}) — falling back to Playwright.")
            self._start_playwright_fallback()

    def _start_playwright_fallback(self):
        """Fallback: Playwright Chromium + playwright-stealth patches."""
        from playwright.sync_api import sync_playwright
        self._playwright_cm = sync_playwright().start()
        browser = self._playwright_cm.chromium.launch(
            headless=Config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self.context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-GB",
            timezone_id="Europe/London",
        )
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(self.context.new_page())
        except ImportError:
            pass
        self.browser = browser
        self.page    = self.context.new_page()

    def _stop_browser(self):
        try:
            if hasattr(self, "_camoufox_cm") and self._camoufox_cm:
                self._camoufox_cm.__exit__(None, None, None)
            elif self.browser:
                self.browser.close()
            if self._playwright_cm:
                self._playwright_cm.stop()
        except Exception:
            pass

    def login(self) -> bool:
        auth = AuthHandler(
            page     = self.page,
            context  = self.context,
            notifier = self.notifier,
            email    = Config.GOVUK_EMAIL,
            password = Config.GOVUK_PASSWORD,
        )
        return auth.login()

    def apply_to_job(self, job: dict, cover_letter: str, profile) -> str:
        """
        Navigate to job and submit application.
        Returns: 'applied' | 'failed' | 'captcha_blocked' | 'skipped'
        """
        url = job["url"]
        logger.info(f"Applying: {job['title']} @ {job['company']}")

        try:
            self.page.goto(url, timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")
            _human_delay()

            # Handle CAPTCHA on listing page
            captcha = CaptchaHandler(
                page           = self.page,
                notifier       = self.notifier,
                twocaptcha_key = Config.TWOCAPTCHA_API_KEY,
                vps_ip         = Config.VPS_IP,
            )
            if not captcha.solve():
                return "captcha_blocked"

            # Find Apply button
            apply_btn = self._find_apply_button()
            if not apply_btn:
                logger.warning(f"No Apply button: {job['title']}")
                return "skipped"

            apply_btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            _human_delay(1, 2)

            # Complete multi-step form
            status = self._complete_form(cover_letter, profile)

            if status == "applied":
                self.notifier.send(
                    f"✅ <b>Application submitted!</b>\n"
                    f"Role: {job['title']}\n"
                    f"Company: {job['company']}\n"
                    f"Location: {job.get('location', '')}"
                )
            elif status == "failed":
                self.notifier.send(
                    f"❌ Application failed\n"
                    f"Role: {job['title']} @ {job['company']}"
                )

            return status

        except Exception as e:
            logger.error(f"apply_to_job error: {e}", exc_info=True)
            return "failed"

    def _find_apply_button(self):
        selectors = [
            "a:text('Apply now')",
            "a:text('Apply for this apprenticeship')",
            "a:text('Start application')",
            "button:text('Apply')",
            "[data-automation='apply-button']",
            ".apply-button",
        ]
        for sel in selectors:
            try:
                btn = self.page.locator(sel).first
                if btn.is_visible():
                    return btn
            except Exception:
                pass
        return None

    def _complete_form(self, cover_letter: str, profile) -> str:
        """Walk through the multi-step gov.uk application form."""
        max_steps = 20
        step = 0

        while step < max_steps:
            step += 1
            url  = self.page.url
            html = self.page.content().lower()

            # CAPTCHA mid-form
            captcha = CaptchaHandler(
                page=self.page, notifier=self.notifier,
                twocaptcha_key=Config.TWOCAPTCHA_API_KEY, vps_ip=Config.VPS_IP,
            )
            if not captcha.solve():
                return "captcha_blocked"

            # Detect form section and fill
            if any(t in html for t in ["first name", "date of birth", "phone"]):
                self._fill_personal(profile)

            elif any(t in html for t in ["qualification", "gcse", "education", "school"]):
                self._fill_education(profile)

            elif any(t in html for t in ["work experience", "employment", "previous job"]):
                self._fill_work(profile)

            elif any(t in html for t in ["skills", "competencies", "strengths"]):
                self._fill_skills(profile)

            elif any(t in html for t in ["cover letter", "personal statement", "why do you want", "why are you"]):
                self._fill_cover_letter(cover_letter)

            elif "upload" in html and "cv" in html:
                self._upload_cv(profile)

            elif any(t in html for t in ["disability", "ethnicity", "diversity"]):
                self._fill_diversity(profile)

            elif any(t in html for t in ["application submitted", "you've applied", "thank you for applying"]):
                self._screenshot("confirmation")
                return "applied"

            elif any(t in html for t in ["review", "check your answers", "confirm your"]):
                self._screenshot(f"review_step{step}")
                return self._submit()

            # Click Continue / Next
            if not self._click_continue():
                logger.warning(f"Could not advance at step {step}")
                break

            self.page.wait_for_load_state("domcontentloaded")
            _human_delay(0.6, 1.4)

            # Stall detection
            if self.page.url == url and step > 2:
                errors = self._get_errors()
                if errors:
                    logger.warning(f"Form errors at step {step}: {errors}")
                    self.notifier.send(f"⚠️ Form error:\n{errors}")
                break

        return "failed"

    def _fill_personal(self, profile):
        p = profile.personal
        self._fill("input[name*='FirstName'], #FirstName", p.get("first_name", ""))
        self._fill("input[name*='LastName'], #LastName",  p.get("last_name", ""))
        self._fill("input[type='tel'], input[name*='Phone'], #Phone", p.get("phone", ""))
        self._fill("input[name*='AddressLine1'], #AddressLine1", p.get("address_line_1", ""))
        self._fill("input[name*='Town'], input[name*='City']",   p.get("city", ""))
        self._fill("input[name*='Postcode'], #Postcode",         p.get("postcode", ""))
        dob = p.get("date_of_birth", "")
        if dob and "/" in dob:
            d, m, y = dob.split("/")
            self._fill("input[name*='Day'], #Day",   d)
            self._fill("input[name*='Month'], #Month", m)
            self._fill("input[name*='Year'], #Year",   y)

    def _fill_education(self, profile):
        if not profile.education:
            return
        latest = profile.education[-1]
        quals  = latest.get("qualifications", [])
        if quals:
            q = quals[0] if isinstance(quals[0], dict) else {"subject": quals[0], "grade": ""}
            self._fill("input[name*='Subject'], #Subject", q.get("subject", ""))
            self._fill("input[name*='Grade'], #Grade",     q.get("grade", ""))

    def _fill_work(self, profile):
        if not profile.work_experience:
            self._click("input[value*='no'], label:text('No')")
            return
        job = profile.work_experience[0]
        self._fill("input[name*='Employer'], #Employer",     job.get("employer", ""))
        self._fill("input[name*='JobTitle'], #JobTitle",     job.get("job_title", "") or job.get("title", ""))
        self._fill("textarea[name*='Description'], #Description", " ".join(job.get("duties", job.get("description", [])) if isinstance(job.get("duties", ""), list) else [job.get("description", "")]))

    def _fill_skills(self, profile):
        text = ", ".join(profile.skills[:10])
        self._fill("textarea[name*='Skills'], #Skills, textarea", text)

    def _fill_cover_letter(self, cover_letter: str):
        selectors = [
            "textarea[name*='CoverLetter']",
            "textarea[name*='PersonalStatement']",
            "#CoverLetter", "#PersonalStatement",
            "textarea[name*='WhatAreYourStrengths']",
            "textarea",
        ]
        for sel in selectors:
            try:
                field = self.page.locator(sel).first
                if field.is_visible():
                    field.fill(cover_letter[:4000])
                    return
            except Exception:
                pass

    def _upload_cv(self, profile):
        cv_path = getattr(profile, "cv_path", None) or profile.personal.get("cv_path", "")
        if not cv_path or not Path(cv_path).exists():
            logger.warning(f"CV not found at '{cv_path}'")
            return
        try:
            self.page.locator("input[type='file']").first.set_input_files(cv_path)
            logger.info(f"CV uploaded: {cv_path}")
        except Exception as e:
            logger.warning(f"CV upload failed: {e}")

    def _fill_diversity(self, profile):
        p = profile.personal
        if p.get("gender"):
            self._select("select[name*='Gender'], #Gender", p["gender"])
        if p.get("ethnicity"):
            self._select("select[name*='Ethnicity'], #Ethnicity", p["ethnicity"])
        val = "Yes" if p.get("disability_or_health_condition") else "No"
        self._click(f"input[value='{val}']")

    def _submit(self) -> str:
        for sel in [
            "button:text('Submit application')",
            "button:text('Confirm and send')",
            "button:text('Submit')",
            "input[type='submit']",
            "button[type='submit']",
        ]:
            try:
                btn = self.page.locator(sel).first
                if btn.is_visible():
                    btn.click()
                    self.page.wait_for_load_state("domcontentloaded")
                    time.sleep(1)
                    if any(t in self.page.content().lower() for t in ["submitted", "you've applied", "thank you"]):
                        self._screenshot("confirmation")
                        return "applied"
            except Exception:
                pass
        return "failed"

    def _click_continue(self) -> bool:
        for sel in [
            "button:text('Continue')", "button:text('Next')",
            "button:text('Save and continue')", "button:text('Save and next')",
            "input[value='Continue']", "button[type='submit']",
        ]:
            try:
                btn = self.page.locator(sel).first
                if btn.is_visible():
                    _human_delay(0.3, 0.8)
                    btn.click()
                    return True
            except Exception:
                pass
        return False

    def _fill(self, selector: str, value: str):
        if not value:
            return
        for sel in selector.split(", "):
            try:
                f = self.page.locator(sel.strip()).first
                if f.count() > 0 and f.is_visible():
                    f.fill(str(value))
                    return
            except Exception:
                pass

    def _click(self, selector: str):
        for sel in selector.split(", "):
            try:
                el = self.page.locator(sel.strip()).first
                if el.count() > 0 and el.is_visible():
                    el.click()
                    return
            except Exception:
                pass

    def _select(self, selector: str, value: str):
        if not value:
            return
        for sel in selector.split(", "):
            try:
                el = self.page.locator(sel.strip()).first
                if el.count() > 0:
                    el.select_option(label=value)
                    return
            except Exception:
                pass

    def _get_errors(self) -> str:
        try:
            msgs = self.page.locator(".govuk-error-message, .error-message").all_text_contents()
            return " | ".join(m.strip() for m in msgs if m.strip())
        except Exception:
            return ""

    def _screenshot(self, label: str) -> str:
        Path(Config.SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(Config.SCREENSHOTS_DIR, f"{ts}_{label}.png")
        try:
            self.page.screenshot(path=path, full_page=True)
            # Send confirmation screenshots to Telegram
            if "confirm" in label:
                self.notifier.send_photo(path, caption="📸 Application confirmation page")
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")
        return path
