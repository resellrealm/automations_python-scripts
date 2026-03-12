"""
Profile Manager
Loads and validates the user's personal profile from user_profile.json.
All application data comes from this file.
"""

import json
from pathlib import Path
from typing import Any
from config import Config
from shared.logger import get_logger

logger = get_logger("profile_manager")


class Profile:
    def __init__(self, data: dict):
        self._data = data
        self.personal = data.get("personal", {})
        self.education = data.get("education", [])
        self.work_experience = data.get("work_experience", [])
        self.skills = data.get("skills", [])
        self.interests = data.get("interests_and_hobbies", [])
        self.personal_statement = data.get("personal_statement", "")
        self.preferences = data.get("preferences", {})
        self.cv = data.get("cv", {})
        self.references = data.get("references", [])

    @property
    def full_name(self) -> str:
        return f"{self.personal.get('first_name', '')} {self.personal.get('last_name', '')}".strip()

    @property
    def email(self) -> str:
        return self.personal.get("email", "")

    @property
    def phone(self) -> str:
        return self.personal.get("phone", "")

    @property
    def cv_path(self) -> str:
        # Support both {"cv": {"file_path": ...}} and top-level "cv_path"
        if isinstance(self.cv, dict):
            return self.cv.get("file_path", "")
        return self._data.get("cv_path", "")

    def to_summary_text(self) -> str:
        """
        Return a readable summary of the profile for AI context.
        Used when generating cover letters.
        """
        lines = [
            f"Name: {self.full_name}",
            f"Email: {self.email}",
            f"Phone: {self.phone}",
            f"Location: {self.personal.get('city', '')}, {self.personal.get('postcode', '')}",
            "",
            "EDUCATION:",
        ]
        for edu in self.education:
            qualifications = ", ".join(
                f"{q['subject']} ({q['grade']})" for q in edu.get("qualifications", [])
            )
            lines.append(f"  {edu.get('institution')} — {edu.get('type')} ({edu.get('start_date')} to {edu.get('end_date')})")
            if qualifications:
                lines.append(f"  Qualifications: {qualifications}")

        lines.append("")
        lines.append("WORK EXPERIENCE:")
        for job in self.work_experience:
            end = "Present" if job.get("current") else job.get("end_date", "")
            lines.append(f"  {job.get('job_title')} at {job.get('employer')} ({job.get('start_date')} – {end})")
            if job.get("description"):
                lines.append(f"  {job['description']}")

        lines.append("")
        lines.append(f"SKILLS: {', '.join(self.skills)}")
        lines.append(f"INTERESTS: {', '.join(self.interests)}")
        lines.append("")
        lines.append(f"PERSONAL STATEMENT:\n{self.personal_statement}")

        return "\n".join(lines)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


def load_profile() -> Profile:
    """Load and return the user profile from user_profile.json."""
    profile_path = Path(Config.PROFILE_FILE)

    if not profile_path.exists():
        raise FileNotFoundError(
            f"user_profile.json not found at {Config.PROFILE_FILE}\n"
            f"Copy and fill in the template provided."
        )

    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Remove instruction key if still present
    data.pop("_instructions", None)

    # Basic validation
    personal = data.get("personal", {})
    name = f"{personal.get('first_name', '')} {personal.get('last_name', '')}".strip()
    if not name or name == "Your First Name Your Last Name":
        logger.warning("user_profile.json still has placeholder values — please fill it in!")

    logger.info(f"Profile loaded for: {name}")
    return Profile(data)
