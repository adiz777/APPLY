import re
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models import CandidateProfile, ImmigrationProfile, RecruitmentPreferences
from app.services.visa_engine import evaluate_job_visa_intelligence


NON_ENGLISH_MANDATORY_PATTERNS = [
    (r"\b(fluent|native|c1|c2|b2|business fluent|mandatory|verhandlungssicher|fließend)\s+(in\s+)?german\b", "German"),
    (r"\bgerman\s+(is\s+)?(required|mandatory|essential|fluent|c1|b2)\b", "German"),
    (r"\bdeutschkenntnisse\s+(c1|c2|b2|zwingend|erforderlich)\b", "German"),
    (r"\b(fluent|native|c1|c2|b2|mandatory)\s+(in\s+)?dutch\b", "Dutch"),
    (r"\bdutch\s+(is\s+)?(required|mandatory|essential|fluent)\b", "Dutch"),
    (r"\b(fluent|native|c1|c2|b2|mandatory)\s+(in\s+)?french\b", "French"),
    (r"\bfrench\s+(is\s+)?(required|mandatory|essential|fluent)\b", "French"),
    (r"\b(fluent|native|jlpt\s*n1|jlpt\s*n2|mandatory)\s+(in\s+)?japanese\b", "Japanese"),
    (r"\b(fluent|native|mandatory)\s+(in\s+)?arabic\b", "Arabic"),
    (r"\barabic\s+(is\s+)?(required|mandatory|essential)\b", "Arabic"),
    (r"\b(fluent|native|mandatory)\s+(in\s+)?(swedish|norwegian|danish|finnish)\b", "Nordic Language"),
]


def detect_language_requirements(title: str, description: str, explicit_lang: str = "English") -> dict[str, Any]:
    combined = f"{title} {description} {explicit_lang}".lower()
    detected_non_english: list[str] = []

    for pattern, lang_name in NON_ENGLISH_MANDATORY_PATTERNS:
        if re.search(pattern, combined):
            if lang_name not in detected_non_english:
                detected_non_english.append(lang_name)

    if explicit_lang and explicit_lang.lower() not in ("english", "en", "english only"):
        for lang in ["German", "Dutch", "French", "Arabic", "Japanese", "Spanish", "Swedish"]:
            if lang.lower() in explicit_lang.lower() and "optional" not in explicit_lang.lower():
                if lang not in detected_non_english:
                    detected_non_english.append(lang)

    # Check if text explicitly clarifies that English is sufficient ("German is a plus, English is our working language")
    english_sufficient_override = any(
        phrase in combined
        for phrase in [
            "english is the working language",
            "working language is english",
            "no german required",
            "german is a plus",
            "german is nice to have",
            "dutch is a plus",
            "english-speaking environment",
        ]
    )

    requires_non_english = len(detected_non_english) > 0 and not english_sufficient_override
    languages = ["English"] + detected_non_english if requires_non_english else ["English"]
    return {
        "requires_non_english": requires_non_english,
        "mandatory_languages": languages,
        "language_summary": (
            f"Requires mandatory {', '.join(detected_non_english)}"
            if requires_non_english
            else "English working language acceptable"
        ),
    }


def evaluate_job_match(
    db: Session,
    title: str,
    employer_name: str,
    country: str,
    location: str,
    work_arrangement: str,
    description: str,
    required_skills: list[str],
    required_experience: str = "",
    education_requirements: str = "",
    language_requirements: str = "English",
    salary_min: Optional[float] = None,
    explicit_sponsorship_hint: Optional[str] = None,
) -> dict[str, Any]:
    """
    ORACLE — Transparent Weighted Job Matching Engine.
    Compares job against verified CandidateProfile, ImmigrationProfile, and RecruitmentPreferences.
    Never fabricates skills or experience. Never hides language or immigration barriers behind a high score.
    """
    profile = db.query(CandidateProfile).first()
    prefs = db.query(RecruitmentPreferences).first()

    weights = (
        prefs.matching_weights
        if prefs and prefs.matching_weights
        else {
            "technical_skills": 30,
            "relevant_experience": 20,
            "education": 15,
            "role_suitability": 15,
            "language_eligibility": 10,
            "immigration_feasibility": 10,
        }
    )

    candidate_skills = {s.lower().strip() for s in (profile.technical_skills if profile and profile.technical_skills else [])}
    # Add skills evidenced by projects (Om, NETRA, Agni) and MSc Cybersecurity
    default_verified_skills = {
        "cybersecurity",
        "soc",
        "security operations",
        "siem",
        "osint",
        "reconnaissance",
        "threat intelligence",
        "incident response",
        "vulnerability assessment",
        "penetration testing",
        "network security",
        "linux",
        "python",
        "it support",
        "service desk",
        "active directory",
        "troubleshooting",
        "digital investigations",
        "log analysis",
    }
    all_candidate_skills = candidate_skills.union(default_verified_skills)

    # 1. Technical Skills Match (0 - 100)
    job_skills = [s.strip() for s in (required_skills or []) if s.strip()]
    if not job_skills:
        # Extract known keywords from description
        desc_lower = description.lower()
        job_skills = [s for s in default_verified_skills if s in desc_lower]

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    for js in job_skills:
        js_low = js.lower()
        if any(js_low in cs or cs in js_low for cs in all_candidate_skills):
            matched_skills.append(js)
        else:
            missing_skills.append(js)

    if job_skills:
        skills_score = min(100.0, round((len(matched_skills) / len(job_skills)) * 100.0, 1))
    else:
        skills_score = 75.0

    # 2. Relevant Experience Match (0 - 100)
    # Candidate has MSc Cybersecurity (Sept 2025), BCA (2023), projects (Om, NETRA, Agni), and Travelodge UK customer/operations experience.
    # Never misrepresent hospitality experience as commercial SOC tenure.
    exp_text = f"{title} {required_experience} {description}".lower()
    missing_qualifications: list[str] = []
    potential_concerns: list[str] = []

    if any(k in exp_text for k in ["senior", "principal", "lead", "director", "head of", "5+ years", "7+ years", "cissp required"]):
        experience_score = 35.0
        potential_concerns.append(
            "Role requests Senior/5+ years commercial cybersecurity tenure; candidate holds MSc Cybersecurity (2025), academic/project security portfolio (Om, NETRA), and UK customer operations experience (Travelodge)."
        )
        if "cissp" in exp_text:
            missing_qualifications.append("CISSP certification (requires 5 years paid security work experience)")
    elif any(k in exp_text for k in ["3+ years", "mid-level", "intermediate"]):
        experience_score = 62.0
        potential_concerns.append(
            "Vacancy mentions mid-level commercial experience; highlight MSc Cybersecurity research and hands-on reconnaissance/OSINT projects (Om, NETRA) without overstating commercial tenure."
        )
    else:
        # Junior, Graduate, Entry-Level, Analyst, Tier 1 SOC, IT Support, Service Desk
        experience_score = 92.0

    # 3. Education Match (0 - 100)
    # Candidate holds MSc Cybersecurity (University of Hertfordshire, Sept 2025) & BCA (2023)
    edu_text = f"{education_requirements} {description}".lower()
    if "phd" in edu_text and "required" in edu_text:
        education_score = 60.0
        missing_qualifications.append("PhD requirement noted in job specification")
    else:
        education_score = 98.0

    # 4. Role Suitability (0 - 100)
    title_low = title.lower()
    high_fit_roles = [
        "cybersecurity",
        "cyber security",
        "soc",
        "security analyst",
        "threat intelligence",
        "osint",
        "incident response",
        "vulnerability",
        "penetration",
        "it support",
        "service desk",
        "desktop support",
        "it technician",
        "technology analyst",
        "graduate",
        "junior",
        "information security",
        "digital forensics",
    ]
    if any(r in title_low for r in high_fit_roles):
        suitability_score = 95.0
    else:
        suitability_score = 65.0

    # 5. Language Eligibility (0 - 100)
    lang_eval = detect_language_requirements(title, description, language_requirements)
    english_only_pref = prefs.english_only if prefs else True
    if lang_eval["requires_non_english"] and english_only_pref:
        language_score = 0.0
        potential_concerns.append(f"CRITICAL LANGUAGE BARRIER: {lang_eval['language_summary']}.")
    else:
        language_score = 100.0

    # 6. Immigration & Sponsorship Feasibility (0 - 100)
    visa_eval = evaluate_job_visa_intelligence(
        db=db,
        country=country,
        title=title,
        description=description,
        employer_name=employer_name,
        salary_min=salary_min,
        explicit_sponsorship_hint=explicit_sponsorship_hint,
    )
    immigration_score = float(visa_eval["feasibility_score"])
    if not visa_eval["candidate_eligible"]:
        potential_concerns.append(f"CRITICAL IMMIGRATION BARRIER: {visa_eval['eligibility_summary']}")
    elif visa_eval["sponsorship_status"] == "Not verified" and country not in ("United Kingdom", "India"):
        potential_concerns.append(f"Unverified Visa Sponsorship in {country}: Confirm employer sponsorship capability before applying.")

    # Compute Weighted Score
    total_weight = sum(weights.values()) or 100
    raw_weighted = (
        skills_score * weights.get("technical_skills", 30)
        + experience_score * weights.get("relevant_experience", 20)
        + education_score * weights.get("education", 15)
        + suitability_score * weights.get("role_suitability", 15)
        + language_score * weights.get("language_eligibility", 10)
        + immigration_score * weights.get("immigration_feasibility", 10)
    ) / total_weight

    # Critical Barrier Cap: Never allow a high compatibility score to hide a critical immigration or language barrier!
    critical_barrier = False
    if language_score == 0.0 or not visa_eval["candidate_eligible"]:
        overall_score = min(round(raw_weighted, 1), 34.0)
        critical_barrier = True
    else:
        overall_score = round(raw_weighted, 1)

    should_apply = overall_score >= (prefs.min_match_threshold if prefs else 55.0) and not critical_barrier

    why_matches = [
        f"Academic credentials strongly align: MSc Cybersecurity (University of Hertfordshire, Sept 2025) and BCA (2023).",
        f"Matched {len(matched_skills)} key technical competencies ({', '.join(matched_skills[:6]) or 'Core Security & IT Foundations'}).",
        f"Practical project portfolio (Om reconnaissance tool, NETRA OSINT/investigation platform) and UK customer-facing operational reliability (Travelodge UK).",
        visa_eval["eligibility_summary"],
    ]

    why_might_not_match = potential_concerns + (
        [f"Unconfirmed skills in job spec: {', '.join(missing_skills[:5])}."] if missing_skills else []
    )

    what_to_verify = list(visa_eval.get("missing_information", []))
    if missing_skills:
        what_to_verify.append(f"Verify whether candidate has hands-on evidence for: {', '.join(missing_skills[:4])}.")

    return {
        "overall_score": overall_score,
        "raw_unclamped_score": round(raw_weighted, 1),
        "critical_barrier_triggered": critical_barrier,
        "should_apply": should_apply,
        "recommendation": (
            "DO NOT APPLY — Critical Language or Visa Eligibility Barrier"
            if critical_barrier
            else ("HIGH PRIORITY — Strong Match & Eligible" if overall_score >= 78 else "REVIEW & VERIFY — Moderate Match")
        ),
        "component_scores": {
            "technical_skills": skills_score,
            "relevant_experience": experience_score,
            "education": education_score,
            "role_suitability": suitability_score,
            "language_eligibility": language_score,
            "immigration_feasibility": immigration_score,
        },
        "weights_used": weights,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "missing_qualifications": missing_qualifications,
        "potential_concerns": potential_concerns,
        "language_evaluation": lang_eval,
        "visa_evaluation": visa_eval,
        "ai_explanation": {
            "why_matches": why_matches,
            "why_might_not_match": why_might_not_match or ["No major blockers identified."],
            "what_needs_improvement": (
                [f"Address or confirm familiarity with {', '.join(missing_skills[:4])} in tailored CV/cover letter without fabricating experience."]
                if missing_skills
                else ["Tailor CV project bullets (Om, NETRA) to mirror exact ATS terminology."]
            ),
            "should_apply_verdict": (
                "Recommended to apply after human review."
                if should_apply
                else "Hold / Reject due to eligibility, language, or seniority mismatch."
            ),
            "verification_checklist": what_to_verify,
        },
    }
