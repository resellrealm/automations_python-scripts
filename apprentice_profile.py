"""
====================================================
GEORGE BAILEY — APPRENTICESHIP BOT PROFILE & LOGIC
====================================================
This file defines:
1. George's CV data (used to auto-fill applications)
2. Job filtering criteria (what to apply for)
3. Cover letter templates (tailored per role type)
4. Application logic (scoring/matching system)
====================================================
"""

# ─────────────────────────────────────────────
# 1. CANDIDATE PROFILE (from CV)
# ─────────────────────────────────────────────

CANDIDATE = {
    "name": "George Bailey",
    "email": "georgeb9@protonmail.com",
    "phone": "07304 454654",
    "location": "Brighton & Hove",
    "postcode": "BN1",  # update with full postcode

    "education": [
        {
            "institution": "BHASVIC (Brighton Hove & Sussex Sixth Form College)",
            "dates": "Sept 2024 – Present",
            "qualifications": ["Maths A-Level", "Business & Law BTEC"],
        },
        {
            "institution": "Lewes Old Grammar School",
            "dates": "2019 – 2024",
            "qualifications": ["9 GCSEs including Maths & English"],
        },
    ],

    "work_experience": [
        {
            "title": "Private Maths Tutor",
            "employer": "Self-employed",
            "dates": "Nov 2023 – Jun 2024",
            "duties": [
                "Tutored 3 GCSE students in Mathematics",
                "Developed tailored lesson plans and materials",
                "Monitored student progress with regular assessments",
            ],
        },
        {
            "title": "General Labourer",
            "employer": "Wolfox",
            "dates": "Oct 2024 – Present",
            "duties": [
                "Assisted with painting, site clean-ups, and moving materials",
                "Followed safety instructions and used tools responsibly",
                "Demonstrated strong work ethic and reliability",
            ],
        },
    ],

    "skills": [
        "Strong numerical and analytical skills",
        "Problem-solving and logical thinking",
        "Reliable, organised, and detail-oriented",
        "Clear written and verbal communication",
        "Self-motivated, works well independently",
        "Experience with AI tools and app development",
        "Microsoft Office / Google Workspace",
    ],

    "interests": [
        "App development and technology",
        "AI and digital products",
        "Gym and fitness",
        "Business systems and finance",
    ],

    "cv_path": "/root/automation/cv/George_Bailey_CV.pdf",  # update after uploading
}


# ─────────────────────────────────────────────
# 2. JOB SEARCH CRITERIA (filters)
# ─────────────────────────────────────────────

JOB_CRITERIA = {

    # Target sectors
    "sectors": [
        "Finance",
        "Accounting",
        "Insurance",
        "Risk",
        "Financial Services",
        "Banking",
        "Actuarial",
        "Investment",
        "Audit",
        "Compliance",
        "Business Management",
    ],

    # Role types
    "role_types": [
        "School Leaver Apprenticeship",
        "Degree Apprenticeship",
        "Level 3 Apprenticeship",
        "Level 4 Apprenticeship",
        "Level 6 Apprenticeship",
        "Level 7 Apprenticeship",
    ],

    # Keywords to INCLUDE (job title/description must match at least one)
    "keywords_include": [
        "apprentice",
        "school leaver",
        "finance",
        "insurance",
        "risk",
        "accounting",
        "actuarial",
        "banking",
        "investment",
        "financial",
        "business",
        "audit",
        "compliance",
        "analyst",
    ],

    # Keywords to EXCLUDE (skip any listing with these)
    "keywords_exclude": [
        "engineer",
        "electrician",
        "plumber",
        "mechanic",
        "construction",
        "chef",
        "hairdresser",
        "care worker",
        "driver",
        "warehouse",
        "security guard",
        "degree required",
        "2:1 required",
    ],

    # Salary filters
    "min_salary": 20000,
    "max_salary": None,  # no cap

    # Location
    "locations": [
        "Brighton",
        "Hove",
        "Sussex",
        "London",  # willing to commute/relocate
        "Remote",
        "Hybrid",
        "South East",
    ],
    "max_commute_miles": 60,
    "remote_ok": True,

    # Sources to scrape
    "job_boards": [
        "https://www.gov.uk/apply-apprenticeship",
        "https://www.indeed.co.uk",
        "https://www.ratemyapprenticeship.co.uk",
        "https://www.allaboutschoolleavers.co.uk",
        "https://www.milkround.com",
        "https://www.notgoingtouni.co.uk",
    ],

    # Companies to target directly
    "target_companies": [
        "Lloyd's of London",
        "Aviva",
        "Zurich Insurance",
        "AXA",
        "KPMG",
        "PwC",
        "Deloitte",
        "EY",
        "Grant Thornton",
        "BDO",
        "Barclays",
        "HSBC",
        "NatWest",
        "Lloyds Bank",
        "Prudential",
        "Legal & General",
        "Willis Towers Watson",
        "Aon",
        "Marsh",
    ],
}


# ─────────────────────────────────────────────
# 3. COVER LETTER TEMPLATES
# ─────────────────────────────────────────────

COVER_LETTER_TEMPLATES = {

    "finance_accounting": """
Dear Hiring Manager,

I am writing to apply for the {role_title} at {company_name}. As a sixth form student 
at BHASVIC studying Maths A-Level and Business & Law BTEC, I am keen to begin my 
career in finance and believe this apprenticeship is the ideal opportunity.

I have a strong passion for numbers and financial systems. My Maths A-Level has given 
me a solid analytical foundation, and my Business & Law BTEC has given me an understanding 
of commercial and legal frameworks. Outside of college, I develop my own app, which has 
given me experience managing systems, tracking data, and solving problems — skills I 
believe are directly transferable to a finance environment.

In my role as a private maths tutor, I consistently delivered results for three GCSE 
students, demonstrating my ability to work accurately, communicate clearly, and take 
responsibility. I am reliable, detail-oriented, and committed to doing things right.

I am particularly drawn to {company_name} because of {company_reason}. I would welcome 
the opportunity to contribute to your team while developing my professional skills.

Thank you for considering my application. I look forward to hearing from you.

Yours sincerely,
George Bailey
""",

    "insurance_risk": """
Dear Hiring Manager,

I am writing to apply for the {role_title} at {company_name}. I am a sixth form student 
at BHASVIC, currently studying Maths A-Level and Business & Law BTEC, and I am eager 
to begin a career in insurance and risk management.

Risk management combines two of my strongest interests: analytical thinking and business 
systems. My Maths A-Level has developed my ability to assess data and identify patterns, 
while my Business & Law BTEC has given me an understanding of how organisations manage 
legal and commercial exposure. I also have a personal interest in financial markets and 
prediction, which I have explored through independent research and projects.

I am a reliable and organised individual — qualities that are essential in a risk 
environment. As a maths tutor, I developed the ability to explain complex ideas clearly 
and adapt my approach based on individual needs. I take pride in accuracy and always 
double-check my work.

{company_name}'s reputation for {company_reason} makes it an organisation I am 
particularly excited to join. I am confident I can make a positive contribution from 
day one.

Thank you for your time and consideration.

Yours sincerely,
George Bailey
""",

}


# ─────────────────────────────────────────────
# 4. SCORING / MATCHING LOGIC
# ─────────────────────────────────────────────

def score_job(job: dict) -> int:
    """
    Score a job listing 0-100 based on how well it matches George's criteria.
    job = {
        'title': str,
        'company': str,
        'description': str,
        'salary': int or None,
        'location': str,
        'type': str,
    }
    """
    score = 0
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()
    salary = job.get("salary")
    location = job.get("location", "").lower()
    combined = title + " " + description

    # Must-have: apprenticeship type
    for role_type in ["apprentice", "school leaver", "level 3", "level 4", "level 6", "level 7"]:
        if role_type in combined:
            score += 20
            break

    # Sector match
    for keyword in JOB_CRITERIA["keywords_include"]:
        if keyword in combined:
            score += 5
            break

    # Target company bonus
    for company in JOB_CRITERIA["target_companies"]:
        if company.lower() in job.get("company", "").lower():
            score += 15
            break

    # Salary check
    if salary:
        if salary >= JOB_CRITERIA["min_salary"]:
            score += 15
        else:
            score -= 20  # penalise below minimum

    # Location match
    for loc in JOB_CRITERIA["locations"]:
        if loc.lower() in location:
            score += 10
            break

    # Exclude keywords — disqualify
    for kw in JOB_CRITERIA["keywords_exclude"]:
        if kw in combined:
            return 0  # instant reject

    return min(score, 100)


def should_apply(job: dict, min_score: int = 40) -> bool:
    """Returns True if George should apply to this job."""
    return score_job(job) >= min_score


# ─────────────────────────────────────────────
# 5. AUTO-FILL ANSWERS (common application questions)
# ─────────────────────────────────────────────

COMMON_ANSWERS = {
    "why_this_role": (
        "I am drawn to this role because it combines analytical thinking with real business impact. "
        "My Maths A-Level and Business & Law BTEC have prepared me well for a career in finance and risk, "
        "and I am eager to develop my skills in a professional environment."
    ),
    "why_this_company": (
        "I admire {company_name}'s reputation for developing young talent and its strong position in the industry. "
        "I believe the values and culture here align with my own work ethic and ambitions."
    ),
    "strengths": (
        "My key strengths are numerical reasoning, reliability, and attention to detail. "
        "I consistently double-check my work and take pride in accuracy."
    ),
    "weaknesses": (
        "I sometimes spend too long perfecting work before moving on. "
        "I am actively working on balancing quality with efficiency."
    ),
    "where_in_5_years": (
        "In five years, I aim to have completed my apprenticeship qualifications and be working "
        "as a qualified professional in finance or risk, ideally taking on more responsibility within my team."
    ),
    "work_under_pressure": (
        "During my A-Levels I balance college, part-time work, and personal projects simultaneously. "
        "I manage this by planning ahead, prioritising tasks, and staying organised."
    ),
    "teamwork_example": (
        "As a maths tutor, I worked closely with students and their parents to agree on goals and track progress. "
        "Clear communication and consistency were key to achieving results together."
    ),
}
