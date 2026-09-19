import os
import re
import time
from datetime import datetime
from typing import List

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OpportunityLens AI",
    page_icon="🔎",
    layout="wide",
)


# ============================================================
# GEMINI SETUP
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        API_KEY = None

if not API_KEY:
    st.error(
        "GEMINI_API_KEY was not found. "
        "Please add it to your .env file."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# USER PROFILE
# ============================================================

USER_PROFILE = {
    "education_level": "Final-year Computer Science student",
    "skills": [
        "Python",
        "Java",
        "C",
        "AI",
        "Web Development",
    ],
    "max_fee": 500,
    "certificate_preferred": True,
    "goodies_preferred": True,
    "online_preferred": True,
    "preferred_city": "Hyderabad",
    "outside_city_requires_support": True,
}


# ============================================================
# DATA MODELS
# ============================================================

class Deadline(BaseModel):
    date: str = "not_mentioned"
    time: str = "not_mentioned"
    timezone: str = "not_mentioned"
    status: str = "not_mentioned"


class Eligibility(BaseModel):
    summary: str = "not_mentioned"
    status: str = "unclear"
    requirements: List[str] = Field(default_factory=list)


class Fee(BaseModel):
    amount: str = "not_mentioned"
    currency: str = "INR"
    status: str = "not_mentioned"


class Certificate(BaseModel):
    available: bool = False
    status: str = "not_mentioned"


class Location(BaseModel):
    type: str = "not_mentioned"
    details: str = "not_mentioned"


class SupportInfo(BaseModel):
    provided: bool = False
    status: str = "not_mentioned"
    details: str = "not_mentioned"


class OpportunityAnalysis(BaseModel):
    title: str = "Unknown opportunity"
    organization: str = "Unknown organization"
    type: str = "Unknown"

    deadline: Deadline = Field(default_factory=Deadline)
    eligibility: Eligibility = Field(default_factory=Eligibility)
    fee: Fee = Field(default_factory=Fee)
    certificate: Certificate = Field(default_factory=Certificate)

    prizes: List[str] = Field(default_factory=list)
    goodies: List[str] = Field(default_factory=list)

    location: Location = Field(default_factory=Location)
    travel: SupportInfo = Field(default_factory=SupportInfo)
    accommodation: SupportInfo = Field(default_factory=SupportInfo)

    required_skills: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)

    red_flags: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    application_steps: List[str] = Field(default_factory=list)


# ============================================================
# GEMINI ANALYSIS
# ============================================================

def analyze_opportunity(opportunity_text: str):

    system_instruction = """
You are OpportunityLens AI.

Analyze opportunity descriptions such as:
internships, jobs, hackathons, scholarships,
competitions, fellowships, conferences and programs.

IMPORTANT RULES:

1. Extract only information supported by the supplied text.
2. Never invent information.
3. If information is absent, use "not_mentioned".
4. Distinguish between:
   - confirmed
   - unclear
   - not_mentioned
   - ineligible
5. Never treat "not_mentioned" as "not_available".
6. Identify explicit eligibility restrictions.
7. Pay special attention to:
   - student status
   - professional status
   - minimum experience
   - maximum experience
   - graduation status
   - graduation year
   - age
   - degree
   - branch
   - citizenship
   - location restrictions
8. If the opportunity explicitly excludes the user's profile,
   eligibility.status should be "ineligible".
9. If the opportunity clearly accepts the user's profile,
   eligibility.status should be "confirmed".
10. If there is insufficient information,
    eligibility.status should be "unclear".
11. Red flags must be factual and supported by the text.
12. Do not speculate.
13. Do not calculate a fit score.
14. Python calculates the final score separately.
15. Clearly extract explicit fees.
16. Clearly extract certificate information.
17. Clearly extract travel and accommodation support.
18. Clearly extract deadlines.
19. Clearly extract required skills.
20. If something is missing, explicitly leave it as
    "not_mentioned".
"""

    prompt = f"""
Analyze the following opportunity.

USER PROFILE:

Education:
{USER_PROFILE["education_level"]}

Skills:
{", ".join(USER_PROFILE["skills"])}

Maximum acceptable fee:
₹{USER_PROFILE["max_fee"]}

Preferred city:
{USER_PROFILE["preferred_city"]}

Online preferred:
{USER_PROFILE["online_preferred"]}

The user is a final-year Computer Science student.

OPPORTUNITY TEXT:

{opportunity_text}

Return the structured analysis according to the provided schema.
"""

    # Gemini can temporarily return 503/429 errors during periods of high demand.
    # Keep the required model and retry temporary failures with increasing delays.
    last_error = None
    retry_delays = [4, 8, 15, 25]

    for attempt in range(len(retry_delays) + 1):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=OpportunityAnalysis,
                    temperature=0.1,
                ),
            )

            return OpportunityAnalysis.model_validate_json(
                response.text
            )

        except Exception as error:

            last_error = error
            error_text = str(error).lower()

            quota_error = (
                "429" in error_text
                or "resource_exhausted" in error_text
                or "resource exhausted" in error_text
                or "quota exceeded" in error_text
                or "quotaexceeded" in error_text
            )

            if quota_error:
                raise RuntimeError(
                    "Gemini daily/free-tier quota has been reached. "
                    "Please wait for the quota to reset or use a Gemini API key "
                    "with available quota. No additional retries were made."
                ) from error

            temporary_error = (
                "503" in error_text
                or "unavailable" in error_text
                or "timeout" in error_text
            )

            if temporary_error and attempt < len(retry_delays):
                wait_seconds = retry_delays[attempt]
                time.sleep(wait_seconds)
                continue

            break

    raise RuntimeError(
        "Gemini is temporarily unavailable after multiple retries. "
        "Please wait a little and click Analyze again. "
        f"Last error: {last_error}"
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_value(value):
    """Return a safe display value for optional/empty fields."""
    if value is None:
        return "not_mentioned"
    if isinstance(value, str):
        value = value.strip()
        return value if value else "not_mentioned"
    return value


def normalize(text: str) -> str:

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9+# ]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# HARD ELIGIBILITY DETECTION
# ============================================================

def detect_hard_eligibility_conflict(
    analysis: OpportunityAnalysis,
    original_text: str,
):

    text = normalize(original_text)

    reasons = []

    # --------------------------------------------------------
    # STUDENT EXCLUSION
    # --------------------------------------------------------

    student_exclusion_phrases = [
        "not open to students",
        "students are not eligible",
        "students and fresh graduates are not eligible",
        "students are ineligible",
        "non students only",
        "non students are not eligible",
        "working professionals only",
        "experienced professionals only",
        "industry professionals only",
        "professionals only",
    ]

    for phrase in student_exclusion_phrases:

        if phrase in text:

            reasons.append(
                "The opportunity excludes or restricts students."
            )

            break

    # --------------------------------------------------------
    # EXPERIENCE REQUIREMENTS
    # --------------------------------------------------------

    experience_patterns = [
        r"must have at least (\d+) years? of experience",
        r"must have (\d+) years? of experience",
        r"minimum of (\d+) years? of experience",
        r"at least (\d+) years? of experience",
        r"(\d+)\+ years? of experience",
        r"(\d+) years? of industry experience",
    ]

    experience_found = False

    for pattern in experience_patterns:

        matches = re.findall(
            pattern,
            text,
        )

        for match in matches:

            try:

                years = int(match)

                if years >= 1:

                    reasons.append(
                        f"Requires at least {years} year(s) of experience."
                    )

                    experience_found = True
                    break

            except ValueError:
                continue

        if experience_found:
            break

    # --------------------------------------------------------
    # DEGREE RESTRICTIONS
    # --------------------------------------------------------

    restricted_degree_phrases = [
        (
            "mba students only",
            "The opportunity is restricted to MBA students."
        ),
        (
            "law students only",
            "The opportunity is restricted to law students."
        ),
        (
            "medical students only",
            "The opportunity is restricted to medical students."
        ),
        (
            "pharmacy students only",
            "The opportunity is restricted to pharmacy students."
        ),
        (
            "mba graduates only",
            "The opportunity is restricted to MBA graduates."
        ),
        (
            "law graduates only",
            "The opportunity is restricted to law graduates."
        ),
        (
            "medical graduates only",
            "The opportunity is restricted to medical graduates."
        ),
    ]

    for phrase, reason in restricted_degree_phrases:

        if phrase in text:
            reasons.append(reason)

    # --------------------------------------------------------
    # NON-CSE BRANCH RESTRICTIONS
    # --------------------------------------------------------

    branch_restrictions = [
        "mechanical engineering students only",
        "civil engineering students only",
        "electrical engineering students only",
        "electronics engineering students only",
        "chemical engineering students only",
    ]

    for phrase in branch_restrictions:

        if phrase in text:

            reasons.append(
                f"Branch restriction detected: {phrase}."
            )

    # --------------------------------------------------------
    # GEMINI ELIGIBILITY RESULT
    # --------------------------------------------------------

    eligibility_status = (
        analysis.eligibility.status.lower().strip()
    )

    if eligibility_status == "ineligible":

        summary = analysis.eligibility.summary.strip()

        if summary and summary != "not_mentioned":

            reasons.append(
                f"Eligibility analysis indicates a conflict: {summary}"
            )

        else:

            reasons.append(
                "The extracted eligibility criteria do not match the user profile."
            )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_reasons = []

    for reason in reasons:

        if reason not in unique_reasons:
            unique_reasons.append(reason)

    conflict = len(unique_reasons) > 0

    return conflict, unique_reasons


# ============================================================
# SKILL MATCHING
# ============================================================

def skill_matches(required_skill: str) -> bool:

    required = normalize(required_skill)

    user_skills = []

    for skill in USER_PROFILE["skills"]:

        user_skills.append(
            normalize(skill)
        )

    for skill in user_skills:

        if required == skill:
            return True

        if required in skill:
            return True

        if skill in required:
            return True

    skill_groups = {

        "machine learning": [
            "ai",
            "python",
        ],

        "artificial intelligence": [
            "ai",
            "python",
        ],

        "ml": [
            "ai",
            "python",
        ],

        "frontend": [
            "web development",
        ],

        "front end": [
            "web development",
        ],

        "backend": [
            "python",
            "java",
        ],

        "back end": [
            "python",
            "java",
        ],

        "software development": [
            "python",
            "java",
            "c",
        ],
    }

    for group, related_skills in skill_groups.items():

        if group in required:

            for related_skill in related_skills:

                if normalize(related_skill) in user_skills:
                    return True

    return False


# ============================================================
# FEE
# ============================================================

def extract_fee_amount(fee: Fee):

    status = fee.status.lower().strip()

    if status == "free":
        return 0

    amount_text = str(
        fee.amount
    )

    if amount_text.lower().strip() in {
        "not_mentioned",
        "unknown",
        "none",
        "n/a",
    }:

        return None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        amount_text,
    )

    if not numbers:
        return None

    try:

        return float(numbers[0])

    except ValueError:

        return None


# ============================================================
# DATE
# ============================================================

def parse_date(date_text: str):

    if not date_text:
        return None

    text = date_text.strip()

    if text.lower() in {
        "not_mentioned",
        "unknown",
        "none",
        "n/a",
    }:

        return None

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                text,
                fmt,
            )

        except ValueError:
            continue

    return None


# ============================================================
# LOCATION SCORE
# ============================================================

def calculate_location_score(
    analysis: OpportunityAnalysis
):

    location_type = normalize(
        analysis.location.type
    )

    details = normalize(
        analysis.location.details
    )

    combined = (
        f"{location_type} {details}"
    )

    if any(
        word in combined
        for word in [
            "online",
            "remote",
            "virtual",
        ]
    ):

        return (
            10,
            "Online participation matches your preference."
        )

    if "hyderabad" in combined:

        return (
            10,
            "The opportunity is located in Hyderabad."
        )

    if (
        location_type == "not mentioned"
        or location_type == "not_mentioned"
    ):

        return (
            5,
            "Location is not clearly mentioned."
        )

    travel_confirmed = (
        analysis.travel.status.lower() == "confirmed"
        and analysis.travel.provided
    )

    accommodation_confirmed = (
        analysis.accommodation.status.lower() == "confirmed"
        and analysis.accommodation.provided
    )

    if (
        travel_confirmed
        and accommodation_confirmed
    ):

        return (
            7,
            "Travel and accommodation support are confirmed."
        )

    return (
        2,
        "The opportunity is outside Hyderabad without "
        "confirmed full travel and accommodation support."
    )


# ============================================================
# DEADLINE SCORE
# ============================================================

def calculate_deadline_score(
    analysis: OpportunityAnalysis
):

    deadline = parse_date(
        analysis.deadline.date
    )

    if deadline is None:

        return (
            2,
            "The deadline could not be confirmed."
        )

    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if deadline < today:

        return (
            0,
            "The stated deadline appears to have passed."
        )

    days_left = (
        deadline.date()
        - today.date()
    ).days

    if days_left <= 2:

        return (
            5,
            f"The deadline is very close: "
            f"{days_left} day(s) remaining."
        )

    if days_left <= 7:

        return (
            4,
            f"The deadline is approaching: "
            f"{days_left} day(s) remaining."
        )

    return (
        5,
        f"The deadline is open with "
        f"{days_left} days remaining."
    )


# ============================================================
# SCORE CALCULATION
# ============================================================

def calculate_score(
    analysis: OpportunityAnalysis,
    original_text: str,
):

    score = 0

    reasons = []
    warnings = []

    breakdown = {}

    # --------------------------------------------------------
    # ELIGIBILITY - 30
    # --------------------------------------------------------

    hard_conflict, conflict_reasons = (
        detect_hard_eligibility_conflict(
            analysis,
            original_text,
        )
    )

    eligibility_status = (
        analysis.eligibility.status.lower().strip()
    )

    if hard_conflict:

        eligibility_points = 0

        for reason in conflict_reasons:

            warnings.append(
                f"Eligibility conflict: {reason}"
            )

    elif eligibility_status == "confirmed":

        eligibility_points = 30

        reasons.append(
            "Your profile appears eligible."
        )

    elif eligibility_status == "unclear":

        eligibility_points = 15

        warnings.append(
            "Eligibility is unclear and should be verified."
        )

    elif eligibility_status == "ineligible":

        eligibility_points = 0

        warnings.append(
            "The opportunity is marked as ineligible for your profile."
        )

    else:

        eligibility_points = 5

        warnings.append(
            "Your eligibility could not be fully established."
        )

    breakdown["Eligibility"] = (
        eligibility_points,
        30,
    )

    score += eligibility_points

    # --------------------------------------------------------
    # SKILLS - 20
    # --------------------------------------------------------

    if not analysis.required_skills:

        skill_points = 10

        reasons.append(
            "Required skills were not clearly specified."
        )

    else:

        matched_skills = []
        unmatched_skills = []

        for skill in analysis.required_skills:

            if skill_matches(skill):

                matched_skills.append(skill)

            else:

                unmatched_skills.append(skill)

        total_skills = len(
            analysis.required_skills
        )

        match_ratio = (
            len(matched_skills) / total_skills
        )

        skill_points = round(
            20 * match_ratio
        )

        if matched_skills:

            reasons.append(
                "Matching skills: "
                + ", ".join(matched_skills)
            )

        if unmatched_skills:

            warnings.append(
                "Skills to verify or learn: "
                + ", ".join(unmatched_skills)
            )

    breakdown["Skills"] = (
        skill_points,
        20,
    )

    score += skill_points

    # --------------------------------------------------------
    # COST - 15
    # --------------------------------------------------------

    fee_amount = extract_fee_amount(
        analysis.fee
    )

    fee_status = analysis.fee.status.lower().strip()

    if fee_status == "free" or fee_amount == 0:

        cost_points = 15

        reasons.append(
            "The opportunity is free."
        )

    elif fee_amount is not None:

        if fee_amount <= USER_PROFILE["max_fee"]:

            cost_points = 15

            reasons.append(
                f"The fee of ₹{fee_amount:g} is within your "
                f"₹{USER_PROFILE['max_fee']} limit."
            )

        else:

            cost_points = 0

            warnings.append(
                f"The fee of ₹{fee_amount:g} exceeds your "
                f"₹{USER_PROFILE['max_fee']} limit."
            )

    else:

        cost_points = 7

        warnings.append(
            "The participation fee is not clearly mentioned."
        )

    breakdown["Cost"] = (
        cost_points,
        15,
    )

    score += cost_points

    # --------------------------------------------------------
    # CERTIFICATE - 10
    # --------------------------------------------------------

    certificate_status = (
        analysis.certificate.status.lower().strip()
    )

    if (
        analysis.certificate.available
        or certificate_status == "confirmed"
    ):

        certificate_points = 10

        reasons.append(
            "A certificate is confirmed."
        )

    elif certificate_status == "unclear":

        certificate_points = 5

        warnings.append(
                       "Certificate availability is unclear."
        )

    else:

        certificate_points = 5

        warnings.append(
            "Certificate information is not clearly mentioned."
        )

    breakdown["Certificate"] = (
        certificate_points,
        10,
    )

    score += certificate_points

    # --------------------------------------------------------
    # LOCATION - 10
    # --------------------------------------------------------

    location_points, location_reason = calculate_location_score(
        analysis
    )

    breakdown["Location"] = (
        location_points,
        10,
    )

    score += location_points

    if location_points >= 7:
        reasons.append(location_reason)
    else:
        warnings.append(location_reason)

    # --------------------------------------------------------
    # BENEFITS - 10
    # --------------------------------------------------------

    benefits_points = 0

    if analysis.prizes:
        benefits_points += 5

    if analysis.goodies:
        benefits_points += 5

    if benefits_points > 0:
        reasons.append(
            "The opportunity provides additional benefits such as prizes or goodies."
        )
    else:
        benefits_points = 5
        warnings.append(
            "No prizes or goodies were clearly mentioned."
        )

    breakdown["Benefits"] = (
        benefits_points,
        10,
    )

    score += benefits_points

    # --------------------------------------------------------
    # DEADLINE - 5
    # --------------------------------------------------------

    deadline_points, deadline_reason = calculate_deadline_score(
        analysis
    )

    breakdown["Deadline"] = (
        deadline_points,
        5,
    )

    score += deadline_points

    if deadline_points >= 4:
        reasons.append(deadline_reason)
    else:
        warnings.append(deadline_reason)

    score = max(0, min(100, score))

    # --------------------------------------------------------
    # HARD ELIGIBILITY CAP
    # --------------------------------------------------------
    # An opportunity that explicitly excludes the user's profile
    # should never appear as a high-fit opportunity just because
    # it has a free fee, certificate, good location, etc.
    if hard_conflict or eligibility_status == "ineligible":
        original_score = score
        score = min(score, 20)

        if original_score > score:
            warnings.append(
                "Final score capped at 20 because the opportunity "
                "has an explicit eligibility conflict."
            )

    return score, breakdown, reasons, warnings


# ============================================================
# SCORE LABEL
# ============================================================

def score_label(score: int):

    if score >= 80:
        return "Strong Match"

    if score >= 60:
        return "Good Match"

    if score >= 40:
        return "Partial Match"

    return "Low Match"


# ============================================================
# CHECKLIST
# ============================================================

def build_checklist(analysis: OpportunityAnalysis):

    checklist = []

    eligibility_status = normalize(
        analysis.eligibility.status
    )

    if eligibility_status != "confirmed":
        checklist.append(
            "Verify eligibility requirements."
        )

    fee_status = normalize(analysis.fee.status)

    if fee_status in {
        "not mentioned",
        "not_mentioned",
        "unclear",
    }:
        checklist.append(
            "Verify the participation fee on the official page."
        )

    certificate_status = normalize(
        analysis.certificate.status
    )

    if certificate_status in {
        "not mentioned",
        "not_mentioned",
        "unclear",
    }:
        checklist.append(
            "Verify whether a certificate is provided."
        )

    location_type = normalize(analysis.location.type)
    location_details = normalize(analysis.location.details)

    if (
        location_type not in {"online", "remote", "virtual"}
        and location_details not in {
            "",
            "not mentioned",
            "not_mentioned",
        }
    ):
        checklist.append(
            "Verify travel support before attending an offline event."
        )

    if normalize(analysis.accommodation.status) != "confirmed":
        checklist.append(
            "Verify accommodation arrangements if physical attendance is required."
        )

    if normalize(analysis.deadline.date) in {
        "not mentioned",
        "not_mentioned",
        "unknown",
        "",
    }:
        checklist.append(
            "Confirm the application deadline."
        )

    if analysis.required_skills:
        unmatched = [
            skill
            for skill in analysis.required_skills
            if not skill_matches(skill)
        ]

        if unmatched:
            checklist.append(
                "Review required skills: "
                + ", ".join(unmatched)
            )

    if not checklist:
        checklist.append(
            "Review the official opportunity page before applying."
        )

    return checklist


# ============================================================
# SESSION STATE
# ============================================================

if "opportunity_results" not in st.session_state:
    st.session_state.opportunity_results = []
if "local_test_ran" not in st.session_state:
    st.session_state.local_test_ran = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("👤 Your Profile")

    st.write(
        f"**Education:** {USER_PROFILE['education_level']}"
    )

    st.write(
        "**Skills:** "
        + ", ".join(USER_PROFILE["skills"])
    )

    st.write(
        f"**Maximum Fee:** ₹{USER_PROFILE['max_fee']}"
    )

    st.write(
        f"**Preferred City:** {USER_PROFILE['preferred_city']}"
    )

    st.write(
        "**Online Preferred:** "
        + ("Yes" if USER_PROFILE["online_preferred"] else "No")
    )

    st.divider()

    st.caption(
        "Gemini extracts opportunity information. "
        "Python calculates the personalized Fit Score."
    )


# ============================================================
# HEADER
# ============================================================

st.title("🔎 OpportunityLens AI")

st.subheader(
    "AI-powered opportunity analysis and comparison"
)

st.write(
    "Analyze one opportunity or compare up to three opportunities "
    "using the same personalized scoring engine."
)

st.info(
    "💡 Paste opportunity descriptions below. OpportunityLens extracts "
    "eligibility, fees, deadlines, certificates, benefits, location "
    "and other important details."
)


# ============================================================
# INPUT TABS
# ============================================================

st.header("📥 Analyze Opportunities")

tab1, tab2, tab3 = st.tabs(
    [
        "Opportunity 1",
        "Opportunity 2",
        "Opportunity 3",
    ]
)

with tab1:
    opportunity_1 = st.text_area(
        "Opportunity 1 Description",
        height=250,
        placeholder="Paste the first opportunity description here...",
        key="opportunity_1",
    )

with tab2:
    opportunity_2 = st.text_area(
        "Opportunity 2 Description",
        height=250,
        placeholder="Paste the second opportunity description here...",
        key="opportunity_2",
    )

with tab3:
    opportunity_3 = st.text_area(
        "Opportunity 3 Description",
        height=250,
        placeholder="Paste the third opportunity description here...",
        key="opportunity_3",
    )


# ============================================================
# LOCAL SCORING TEST MODE
# ============================================================
def build_local_test_opportunities():
    return [
        (1, OpportunityAnalysis(
            title="TechSkills Online AI Challenge",
            organization="TechSkills", type="Hackathon",
            deadline=Deadline(date="2026-10-05", status="confirmed"),
            eligibility=Eligibility(summary="Open to current college students.", status="confirmed", requirements=["Current college student"]),
            fee=Fee(amount="0", currency="INR", status="free"),
            certificate=Certificate(available=True, status="confirmed"),
            prizes=["₹50,000 prize pool"], goodies=["Digital goodies"],
            location=Location(type="online", details="Online / Virtual"),
            required_skills=["Python", "AI", "Web Development"],
            requirements=["College student"],
            application_steps=["Register online", "Submit the project"]
        ), "Free online opportunity for students."),
        (2, OpportunityAnalysis(
            title="TechFuture National Innovation Summit 2026",
            organization="TechFuture", type="Technology Summit",
            deadline=Deadline(date="2026-09-30", status="confirmed"),
            eligibility=Eligibility(summary="Open to college students and recent graduates.", status="confirmed", requirements=["College student or recent graduate"]),
            fee=Fee(amount="1500", currency="INR", status="paid"),
            certificate=Certificate(available=True, status="confirmed"),
            location=Location(type="offline", details="Bengaluru, Karnataka"),
            travel=SupportInfo(provided=False, status="not_provided", details="Participants arrange and pay for their own travel."),
            accommodation=SupportInfo(provided=False, status="not_provided", details="Accommodation is not provided."),
            required_skills=["Python"],
            requirements=["College student or recent graduate"],
            red_flags=["Registration fee exceeds the user's ₹500 limit."],
            application_steps=["Register before the deadline"]
        ), "Paid offline opportunity outside Hyderabad without travel/accommodation support."),
        (3, OpportunityAnalysis(
            title="Senior Software Engineering Fellowship 2026",
            organization="Senior Engineering Fellowship", type="Fellowship",
            deadline=Deadline(date="2026-10-15", status="confirmed"),
            eligibility=Eligibility(summary="Students and fresh graduates are not eligible. Applicants must have at least 3 years of full-time software engineering experience.", status="ineligible", requirements=["Working professional", "At least 3 years of full-time software engineering experience"]),
            fee=Fee(amount="0", currency="INR", status="free"),
            certificate=Certificate(available=True, status="confirmed"),
            location=Location(type="online", details="Online"),
            required_skills=["Python", "Java", "Backend Development", "System Design"],
            requirements=["Working professional", "3+ years experience"],
            red_flags=["Students and fresh graduates are explicitly excluded."],
            application_steps=["Submit application"]
        ), "Students and fresh graduates are not eligible. Applicants must have at least 3 years of full-time software engineering experience."),
    ]


# ============================================================
# ANALYZE
# ============================================================

local_test_mode = st.checkbox(
    "🧪 Local Scoring Test (No Gemini API calls)",
    help="Tests the Python scoring engine without consuming Gemini quota."
)

if local_test_mode:
    st.info("Local test mode uses built-in sample data. No Gemini API request is made.")
    local_test_button = st.button("🧪 Run Local Scoring Test", use_container_width=True)
else:
    local_test_button = False

analyze_button = st.button(
    "🔍 Analyze Opportunities",
    type="primary",
    use_container_width=True,
)

if local_test_button:
    local_results = []
    for index, analysis, description in build_local_test_opportunities():
        score, breakdown, reasons, warnings = calculate_score(analysis, description)
        local_results.append({
            "slot": index, "analysis": analysis, "score": score,
            "breakdown": breakdown, "reasons": reasons,
            "warnings": warnings, "checklist": build_checklist(analysis),
        })
    st.session_state.opportunity_results = local_results
    st.session_state.local_test_ran = True
    st.success("Local scoring test completed. No Gemini API request was used.")

if analyze_button:
    st.session_state.local_test_ran = False

    opportunities = [
        opportunity_1,
        opportunity_2,
        opportunity_3,
    ]

    valid_opportunities = [
        (index, text.strip())
        for index, text in enumerate(opportunities, start=1)
        if text and text.strip()
    ]

    if not valid_opportunities:
        st.warning(
            "Please paste at least one opportunity description."
        )
        st.stop()

    results = []
    progress = st.progress(0)

    total = len(valid_opportunities)

    for position, (index, text) in enumerate(
        valid_opportunities,
        start=1,
    ):

        try:

            with st.spinner(
                f"Analyzing Opportunity {index}..."
            ):
                analysis = analyze_opportunity(text)

                (
                    score,
                    breakdown,
                    reasons,
                    warnings,
                ) = calculate_score(
                    analysis,
                    text,
                )

                checklist = build_checklist(analysis)

            results.append(
                {
                    "slot": index,
                    "analysis": analysis,
                    "score": score,
                    "breakdown": breakdown,
                    "reasons": reasons,
                    "warnings": warnings,
                    "checklist": checklist,
                }
            )

        except Exception as error:
            st.error(
                f"Opportunity {index} could not be analyzed."
            )
            st.code(str(error))

        progress.progress(position / total)

    progress.empty()
    st.session_state.opportunity_results = results


# ============================================================
# DISPLAY RESULTS
# ============================================================

results = st.session_state.opportunity_results

if results:

    st.divider()

    # --------------------------------------------------------
    # COMPARISON TABLE
    # --------------------------------------------------------

    st.header("📊 Opportunity Comparison")

    st.caption(
        "Every opportunity is evaluated independently using the same "
        "profile and scoring formula."
    )

    comparison_rows = []

    for result in results:

        analysis = result["analysis"]

        fee_display = clean_value(analysis.fee.amount)

        if normalize(analysis.fee.status) == "free":
            fee_display = "Free"

        comparison_rows.append(
            {
                "Opportunity": analysis.title,
                "Fit Score": f"{result['score']}/100",
                "Eligibility": analysis.eligibility.status,
                "Fee": fee_display,
                "Location": analysis.location.details,
                "Certificate": analysis.certificate.status,
            }
        )

    st.table(comparison_rows)

    # --------------------------------------------------------
    # SCORE CARDS
    # --------------------------------------------------------

    st.subheader("🎯 Fit Scores")

    score_columns = st.columns(len(results))

    for index, result in enumerate(results):

        with score_columns[index]:

            analysis = result["analysis"]
            score = result["score"]

            st.metric(
                analysis.title,
                f"{score}/100",
            )

            st.write(
                f"**{score_label(score)}**"
            )

            st.progress(score / 100)

    # --------------------------------------------------------
    # DETAILED RESULTS
    # --------------------------------------------------------

    st.divider()
    st.header("🔍 Detailed Analysis")

    for result_number, result in enumerate(
        results,
        start=1,
    ):

        analysis = result["analysis"]
        score = result["score"]
        breakdown = result["breakdown"]
        reasons = result["reasons"]
        warnings = result["warnings"]
        checklist = result["checklist"]

        with st.expander(
            f"Opportunity {result_number}: "
            f"{analysis.title} • {score}/100",
            expanded=True,
        ):

            st.subheader("📌 Summary")

            summary_col1, summary_col2 = st.columns(2)

            with summary_col1:
                st.write(f"**Title:** {analysis.title}")
                st.write(
                    f"**Organization:** {analysis.organization}"
                )
                st.write(f"**Type:** {analysis.type}")
                st.write(
                    f"**Deadline:** {analysis.deadline.date}"
                )

            with summary_col2:
                st.write(
                    f"**Fee:** {analysis.fee.amount}"
                )
                st.write(
                    f"**Location:** {analysis.location.details}"
                )
                st.write(
                    f"**Certificate:** {analysis.certificate.status}"
                )
                st.write(
                    f"**Eligibility:** {analysis.eligibility.status}"
                )

            st.subheader("📊 Score Breakdown")

            breakdown_rows = [
                {
                    "Category": category,
                    "Score": f"{values[0]}/{values[1]}",
                }
                for category, values in breakdown.items()
            ]

            st.table(breakdown_rows)

            st.subheader("🎓 Eligibility")

            eligibility_status = normalize(
                analysis.eligibility.status
            )

            if eligibility_status == "confirmed":
                st.success(
                    analysis.eligibility.summary
                )
            elif eligibility_status == "ineligible":
                st.error(
                    analysis.eligibility.summary
                )
            else:
                st.warning(
                    analysis.eligibility.summary
                )

            if analysis.eligibility.requirements:
                for requirement in analysis.eligibility.requirements:
                    st.write(f"• {requirement}")

            st.subheader("💻 Required Skills")

            if analysis.required_skills:

                for skill in analysis.required_skills:

                    if skill_matches(skill):
                        st.success(
                            f"✓ {skill} - matched"
                        )
                    else:
                        st.warning(
                            f"⚠ {skill} - not currently matched"
                        )

            else:
                st.info(
                    "No specific required skills were mentioned."
                )

            st.subheader("📜 Certificate")

            if (
                analysis.certificate.available
                or normalize(analysis.certificate.status)
                == "confirmed"
            ):
                st.success(
                    "Certificate availability is confirmed."
                )
            elif normalize(analysis.certificate.status) == "unclear":
                st.warning(
                    "Certificate availability is unclear."
                )
            else:
                st.info(
                    "Certificate information was not clearly mentioned."
                )

            st.subheader("📍 Location & Support")

            st.write(
                f"**Type:** {analysis.location.type}"
            )

            st.write(
                f"**Details:** {analysis.location.details}"
            )

            if analysis.travel.provided:
                st.write(
                    f"**Travel:** {analysis.travel.details}"
                )
            else:
                st.write(
                    "**Travel:** Not confirmed"
                )

            if analysis.accommodation.provided:
                st.write(
                    f"**Accommodation:** "
                    f"{analysis.accommodation.details}"
                )
            else:
                st.write(
                    "**Accommodation:** Not confirmed"
                )

            st.subheader("🏆 Benefits")

            if analysis.prizes:
                st.write("**Prizes:**")
                for prize in analysis.prizes:
                    st.write(f"• {prize}")

            if analysis.goodies:
                st.write("**Goodies:**")
                for goodie in analysis.goodies:
                    st.write(f"• {goodie}")

            if not analysis.prizes and not analysis.goodies:
                st.info(
                    "No prizes or goodies were clearly mentioned."
                )

            st.subheader("🚩 Red Flags")

            if analysis.red_flags:
                for flag in analysis.red_flags:
                    st.warning(flag)
            else:
                st.success(
                    "No factual red flags were detected from the supplied text."
                )

            st.subheader("❓ Missing Information")

            if analysis.missing_information:
                for missing in analysis.missing_information:
                    st.write(f"• {missing}")
            else:
                st.success(
                    "No major missing information was detected."
                )

            st.subheader("🧠 Why This Score?")

            for reason in reasons:
                st.write(f"✓ {reason}")

            if warnings:
                st.write("**Things to verify:**")
                for warning in warnings:
                    st.warning(warning)

            st.subheader("✅ Action Checklist")

            for checklist_index, item in enumerate(checklist):
                st.checkbox(
                    item,
                    value=False,
                    key=(
                        f"result_{result_number}_"
                        f"check_{checklist_index}"
                    ),
                )

            st.subheader("📝 Application Steps")

            if analysis.application_steps:
                for step_index, step in enumerate(
                    analysis.application_steps,
                    start=1,
                ):
                    st.write(
                        f"{step_index}. {step}"
                    )
            else:
                st.info(
                    "Application steps were not mentioned."
                )

            with st.expander("🔎 View Extracted Data"):
                st.json(analysis.model_dump())

    st.divider()

    st.caption(
        "OpportunityLens AI analyzes only the information supplied by the user. "
        "Always verify important eligibility, fee, deadline, travel, accommodation "
        "and certificate details on the official opportunity page."
    )