"""
AI Cover Letter Generator
Uses Kimi AI to write a tailored cover letter for each apprenticeship.
Each cover letter is saved to the cover_letters/ folder.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import re
from pathlib import Path
from datetime import datetime

from shared.kimi_client import KimiClient
from shared.logger import get_logger
from config import Config

logger = get_logger("ai_cover_letter")

# Compact prompt — same output quality, fewer tokens
SYSTEM_PROMPT = """UK apprenticeship cover letter writer. 3 paragraphs, 250-300 words.
P1: why this role+company. P2: relevant skills/quals from profile. P3: why apprenticeship+closing.
No "I am writing to apply". No headers. UK English. End: "Yours sincerely,\\n{name}". Letter text only."""


def generate_cover_letter(job: dict, profile_summary: str, full_name: str) -> str:
    """
    Generate a tailored cover letter for a job.

    Args:
        job:            Job dict with title, company, description_snippet, location
        profile_summary: Text summary of the applicant's profile
        full_name:       Applicant's full name for sign-off

    Returns:
        Cover letter as plain text string
    """
    client = KimiClient()

    # Compress profile to essential info only — big token saving
    compressed_profile = _compress_profile(profile_summary)
    job_desc = job.get('description_snippet', '')[:700]

    user_message = (
        f"APPLICANT: {full_name}\n{compressed_profile}\n\n"
        f"JOB: {job['title']} @ {job['company']}, {job['location']} | "
        f"Level: {job.get('apprenticeship_level','?')} | Wage: {job.get('wage','?')}\n"
        f"DESCRIPTION: {job_desc}"
    )

    logger.info(f"Generating cover letter for: {job['title']} at {job['company']}")

    try:
        letter = client.chat(
            user_message,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.75,
            max_tokens=550,  # 250-300 words ≈ 400 tokens, buffer of 150
        )
        logger.info(f"Cover letter generated ({len(letter)} chars)")
        return letter

    except Exception as e:
        logger.error(f"Failed to generate cover letter: {e}")
        return _fallback_cover_letter(job, profile_summary, full_name)


def save_cover_letter(job: dict, letter_text: str) -> str:
    """
    Save cover letter to the cover_letters/ folder.

    Returns:
        Path to the saved file
    """
    Path(Config.COVER_LETTERS_DIR).mkdir(parents=True, exist_ok=True)

    # Create a safe filename
    company_slug = re.sub(r"[^\w\s-]", "", job["company"])[:30].strip().replace(" ", "_")
    title_slug = re.sub(r"[^\w\s-]", "", job["title"])[:30].strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{company_slug}_{title_slug}.txt"
    filepath = os.path.join(Config.COVER_LETTERS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Cover Letter\n")
        f.write(f"Role: {job['title']}\n")
        f.write(f"Company: {job['company']}\n")
        f.write(f"URL: {job['url']}\n")
        f.write(f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"{'─' * 60}\n\n")
        f.write(letter_text)

    logger.info(f"Cover letter saved to: {filepath}")
    return filepath


def _compress_profile(profile_summary: str) -> str:
    """
    Extract only the key lines from the profile summary to reduce token usage.
    Keeps: skills, most recent education, most recent job.
    """
    lines = profile_summary.splitlines()
    keep = []
    capture = False
    for line in lines:
        stripped = line.strip()
        # Always keep skills and personal statement
        if any(k in stripped.upper() for k in ("SKILL", "INTEREST", "PERSONAL STATEMENT")):
            capture = True
        if stripped.startswith("EDUCATION") or stripped.startswith("WORK"):
            capture = True
        if capture and stripped:
            keep.append(stripped)
        if len(keep) > 20:  # cap at 20 lines
            break
    return "\n".join(keep)[:900]


def _fallback_cover_letter(job: dict, profile_summary: str, full_name: str) -> str:
    """Basic fallback if AI call fails."""
    return (
        f"I am very interested in the {job['title']} apprenticeship at {job['company']}. "
        f"I believe my skills and enthusiasm make me an excellent candidate for this opportunity. "
        f"I look forward to hearing from you.\n\n"
        f"Yours sincerely,\n{full_name}"
    )
