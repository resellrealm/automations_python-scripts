"""
Apprenticeship Applier
Uses Playwright (headless Chromium) to fill in and submit applications
on findapprenticeship.service.gov.uk.

The gov.uk service requires a registered account to apply.
Set GOVUK_EMAIL and GOVUK_PASSWORD in your .env file.

CAPTCHA HANDLING:
    If a CAPTCHA is detected, the browser pauses and alerts you.
    Run with HEADLESS=false in your .env to see the browser and solve it manually.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeoutError

from config import Config
from shared.logger import get_logger
import database

logger = get_logger("applier")

GOVUK_LOGIN_URL = "https://www.findapprenticeship.service.gov.uk/signin"


class ApprenticeshipApplier:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._logged_in = False

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self.page = context.new_page()
        return self

    def __exit__(self, *args):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self) -> bool:
        """Log in to the gov.uk apprenticeship service."""
        if self._logged_in:
            return True

        logger.info("Logging in to findapprenticeship.service.gov.uk...")
        try:
            self.page.goto(GOVUK_LOGIN_URL, timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")

            # Fill email
            email_field = self.page.locator("input[type='email'], #Email, input[name='Email']")
            email_field.fill(Config.GOVUK_EMAIL)

            # Fill password
            password_field = self.page.locator("input[type='password'], #Password, input[name='Password']")
            password_field.fill(Config.GOVUK_PASSWORD)

            # Submit
            self.page.locator("button[type='submit'], input[type='submit']").click()
            self.page.wait_for_load_state("domcontentloaded")

            # Check if login succeeded
            if "sign-in" in self.page.url.lower() or "login" in self.page.url.lower():
                logger.error("Login failed — check your GOVUK_EMAIL and GOVUK_PASSWORD in .env")
                return False

            self._logged_in = True
            logger.info("Logged in successfully.")
            return True

        except PWTimeoutError as e:
            logger.error(f"Login timed out: {e}")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def apply_to_job(self, job: dict, cover_letter: str, profile) -> str:
        """
        Navigate to a job listing and submit an application.

        Returns:
            Status: 'applied' | 'failed' | 'captcha_blocked' | 'skipped'
        """
        url = job["url"]
        logger.info(f"Applying to: {job['title']} at {job['company']}")

        try:
            self.page.goto(url, timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1)

            # Check for CAPTCHA
            if self._is_captcha_present():
                logger.warning("CAPTCHA detected — pausing. Solve it in the browser window.")
                if Config.HEADLESS:
                    logger.error("Cannot solve CAPTCHA in headless mode. Set HEADLESS=false in .env and retry.")
                    return "captcha_blocked"
                # Wait up to 3 minutes for user to solve
                input("  CAPTCHA detected — solve it in the browser, then press Enter to continue...")

            # Find and click the Apply button
            apply_button = self._find_apply_button()
            if not apply_button:
                logger.warning(f"No Apply button found for: {job['title']}")
                return "skipped"

            apply_button.click()
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1)

            # Work through the multi-step application form
            status = self._complete_application_form(cover_letter, profile)
            return status

        except PWTimeoutError as e:
            logger.error(f"Timeout applying to {job['title']}: {e}")
            return "failed"
        except Exception as e:
            logger.error(f"Error applying to {job['title']}: {e}", exc_info=True)
            return "failed"

    def _find_apply_button(self):
        """Find the Apply button on the job listing page."""
        selectors = [
            "a:text('Apply now')",
            "a:text('Apply for this apprenticeship')",
            "a:text('Start application')",
            "button:text('Apply')",
            "[data-automation='apply-button']",
            ".apply-button",
        ]
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible():
                    return btn
            except Exception:
                pass
        return None

    def _complete_application_form(self, cover_letter: str, profile) -> str:
        """
        Work through the multi-step gov.uk application form.
        Fills each section and advances to the next step.
        """
        max_steps = 15  # Safety limit on steps
        step = 0

        while step < max_steps:
            step += 1
            current_url = self.page.url
            logger.debug(f"Application step {step}: {current_url}")

            page_text = self.page.content().lower()

            # ── Personal details ──────────────────────────────
            if any(t in page_text for t in ["first name", "date of birth", "phone number"]):
                self._fill_personal_details(profile)

            # ── Education / qualifications ─────────────────────
            elif any(t in page_text for t in ["qualification", "gcse", "education", "school"]):
                self._fill_education(profile)

            # ── Work history ───────────────────────────────────
            elif any(t in page_text for t in ["work experience", "employment history", "previous job"]):
                self._fill_work_experience(profile)

            # ── Skills / competencies ──────────────────────────
            elif any(t in page_text for t in ["skills", "competencies", "strengths"]):
                self._fill_skills(profile)

            # ── Cover letter / personal statement ─────────────
            elif any(t in page_text for t in ["cover letter", "personal statement", "why do you want"]):
                self._fill_cover_letter(cover_letter)

            # ── CV upload ─────────────────────────────────────
            elif "upload" in page_text and "cv" in page_text:
                self._upload_cv(profile)

            # ── Disability / diversity questions ──────────────
            elif any(t in page_text for t in ["disability", "ethnicity", "diversity"]):
                self._fill_diversity_questions(profile)

            # ── Review / confirm page ─────────────────────────
            elif any(t in page_text for t in ["review", "check your answers", "confirm"]):
                screenshot = self._take_screenshot(f"review_{step}")
                logger.info(f"Review page reached — screenshot saved: {screenshot}")
                result = self._submit_application()
                return result

            # ── Confirmation page ─────────────────────────────
            elif any(t in page_text for t in ["application submitted", "you've applied", "thank you for applying"]):
                screenshot = self._take_screenshot("confirmation")
                logger.info(f"Application confirmed! Screenshot: {screenshot}")
                return "applied"

            # Advance to next step
            advanced = self._click_continue()
            if not advanced:
                logger.warning(f"Could not advance past step {step} — stopping.")
                break

            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(0.8)

            # Check if URL changed (still on same page = problem)
            if self.page.url == current_url and step > 1:
                logger.warning(f"URL didn't change after step {step} — possible form error.")
                errors = self._get_form_errors()
                if errors:
                    logger.warning(f"Form errors: {errors}")
                break

        logger.warning("Max steps reached without confirmation — application may be incomplete.")
        return "failed"

    def _fill_personal_details(self, profile):
        """Fill in personal information fields."""
        p = profile.personal
        self._fill_if_exists("input[name*='FirstName'], #FirstName", p.get("first_name", ""))
        self._fill_if_exists("input[name*='LastName'], #LastName", p.get("last_name", ""))
        self._fill_if_exists("input[name*='Phone'], #Phone, input[type='tel']", p.get("phone", ""))
        self._fill_if_exists("input[name*='AddressLine1'], #AddressLine1", p.get("address_line_1", ""))
        self._fill_if_exists("input[name*='AddressLine2'], #AddressLine2", p.get("address_line_2", ""))
        self._fill_if_exists("input[name*='Town'], #Town, input[name*='City']", p.get("city", ""))
        self._fill_if_exists("input[name*='Postcode'], #Postcode", p.get("postcode", ""))

        # Date of birth (day/month/year fields)
        dob = p.get("date_of_birth", "")
        if dob and "/" in dob:
            parts = dob.split("/")
            if len(parts) == 3:
                self._fill_if_exists("input[name*='Day'], #Day", parts[0])
                self._fill_if_exists("input[name*='Month'], #Month", parts[1])
                self._fill_if_exists("input[name*='Year'], #Year", parts[2])

    def _fill_education(self, profile):
        """Fill in the most recent qualification."""
        if not profile.education:
            return
        latest_edu = profile.education[-1]
        quals = latest_edu.get("qualifications", [])
        if quals:
            q = quals[0]
            self._fill_if_exists("input[name*='Subject'], #Subject", q.get("subject", ""))
            self._fill_if_exists("input[name*='Grade'], #Grade", q.get("grade", ""))

    def _fill_work_experience(self, profile):
        """Fill in work experience if any."""
        if not profile.work_experience:
            # Select "no work experience" if available
            self._click_if_exists("input[value*='no'], label:text('No')")
            return
        job = profile.work_experience[0]
        self._fill_if_exists("input[name*='Employer'], #Employer", job.get("employer", ""))
        self._fill_if_exists("input[name*='JobTitle'], #JobTitle", job.get("job_title", ""))
        self._fill_if_exists("textarea[name*='Description'], #Description", job.get("description", ""))

    def _fill_skills(self, profile):
        """Fill in skills text area."""
        skills_text = ", ".join(profile.skills[:10])
        self._fill_if_exists("textarea[name*='Skills'], #Skills, textarea", skills_text)

    def _fill_cover_letter(self, cover_letter: str):
        """Fill in cover letter or personal statement field."""
        selectors = [
            "textarea[name*='CoverLetter']",
            "textarea[name*='PersonalStatement']",
            "#CoverLetter",
            "#PersonalStatement",
            "textarea[name*='WhatAreYourStrengths']",
            "textarea",  # fallback
        ]
        for selector in selectors:
            try:
                field = self.page.locator(selector).first
                if field.is_visible():
                    field.fill(cover_letter[:4000])  # Most fields have character limits
                    logger.debug("Cover letter filled.")
                    return
            except Exception:
                pass

    def _upload_cv(self, profile):
        """Upload CV file if a file input is present."""
        cv_path = profile.cv_path
        if not cv_path or not Path(cv_path).exists():
            logger.warning(f"CV file not found at '{cv_path}' — skipping upload.")
            return
        try:
            file_input = self.page.locator("input[type='file']").first
            if file_input.is_visible() or file_input.count() > 0:
                file_input.set_input_files(cv_path)
                logger.info(f"CV uploaded: {cv_path}")
        except Exception as e:
            logger.warning(f"CV upload failed: {e}")

    def _fill_diversity_questions(self, profile):
        """Answer optional diversity / equal opportunities questions."""
        p = profile.personal
        # Gender
        if p.get("gender"):
            self._select_option_if_exists("select[name*='Gender'], #Gender", p["gender"])
        # Ethnicity
        if p.get("ethnicity"):
            self._select_option_if_exists("select[name*='Ethnicity'], #Ethnicity", p["ethnicity"])
        # Disability
        disability = "Yes" if p.get("disability_or_health_condition") else "No"
        self._click_if_exists(f"input[value='{disability}']")

    def _submit_application(self) -> str:
        """Click the final submit / confirm button."""
        submit_selectors = [
            "button:text('Submit application')",
            "button:text('Confirm and send')",
            "button:text('Submit')",
            "input[type='submit']",
            "button[type='submit']",
        ]
        for selector in submit_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible():
                    btn.click()
                    self.page.wait_for_load_state("domcontentloaded")
                    time.sleep(1)
                    # Check for confirmation
                    if any(
                        t in self.page.content().lower()
                        for t in ["application submitted", "you've applied", "thank you"]
                    ):
                        self._take_screenshot("confirmation")
                        return "applied"
            except Exception:
                pass
        return "failed"

    def _click_continue(self) -> bool:
        """Click the Continue / Next / Save and continue button."""
        selectors = [
            "button:text('Continue')",
            "button:text('Next')",
            "button:text('Save and continue')",
            "button:text('Save and next')",
            "input[value='Continue']",
            "button[type='submit']",
        ]
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible():
                    btn.click()
                    return True
            except Exception:
                pass
        return False

    def _fill_if_exists(self, selector: str, value: str):
        """Fill a field if it exists and value is non-empty."""
        if not value:
            return
        try:
            for sel in selector.split(", "):
                field = self.page.locator(sel.strip()).first
                if field.count() > 0 and field.is_visible():
                    field.fill(str(value))
                    return
        except Exception:
            pass

    def _click_if_exists(self, selector: str):
        """Click an element if it exists."""
        try:
            for sel in selector.split(", "):
                el = self.page.locator(sel.strip()).first
                if el.count() > 0 and el.is_visible():
                    el.click()
                    return
        except Exception:
            pass

    def _select_option_if_exists(self, selector: str, value: str):
        """Select an option in a <select> dropdown."""
        if not value:
            return
        try:
            for sel in selector.split(", "):
                el = self.page.locator(sel.strip()).first
                if el.count() > 0:
                    el.select_option(label=value)
                    return
        except Exception:
            pass

    def _get_form_errors(self) -> list:
        """Extract visible form error messages."""
        try:
            errors = self.page.locator(
                ".error, .govuk-error-message, [class*='error']"
            ).all_text_contents()
            return [e.strip() for e in errors if e.strip()]
        except Exception:
            return []

    def _is_captcha_present(self) -> bool:
        """Detect common CAPTCHA implementations."""
        try:
            content = self.page.content().lower()
            return any(t in content for t in ["recaptcha", "hcaptcha", "captcha", "cloudflare"])
        except Exception:
            return False

    def _take_screenshot(self, label: str) -> str:
        """Take a screenshot and save to screenshots/ folder."""
        Path(Config.SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{label}.png"
        filepath = os.path.join(Config.SCREENSHOTS_DIR, filename)
        try:
            self.page.screenshot(path=filepath, full_page=True)
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")
        return filepath
