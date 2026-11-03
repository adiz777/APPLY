import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.models import Employer, JobVacancy
from app.services.matching_engine import evaluate_job_match


INITIAL_JOB_CATEGORIES = [
    "Cybersecurity Analyst",
    "SOC Analyst",
    "Junior Security Analyst",
    "Information Security Analyst",
    "Security Operations",
    "Threat Intelligence Analyst",
    "OSINT Analyst",
    "Digital Forensics",
    "Penetration Testing",
    "Vulnerability Analyst",
    "IT Support Analyst",
    "Service Desk Analyst",
    "Desktop Support",
    "IT Technician",
    "Technology Analyst",
    "Graduate Technology Roles",
    "Junior Systems Administrator",
]


def compute_dedup_signature(employer_name: str, title: str, location: str, original_url: str = "") -> str:
    norm_emp = re.sub(r"[^a-z0-9]", "", (employer_name or "").lower())
    norm_title = re.sub(r"[^a-z0-9]", "", (title or "").lower())
    norm_loc = re.sub(r"[^a-z0-9]", "", (location or "").lower())
    key = f"{norm_emp}::{norm_title}::{norm_loc}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def is_duplicate_job(
    db: Session,
    employer_name: str,
    title: str,
    location: str,
    original_url: str,
    provider_reference: str = "",
) -> Optional[JobVacancy]:
    sig = compute_dedup_signature(employer_name, title, location, original_url)
    existing = db.query(JobVacancy).filter(JobVacancy.dedup_signature == sig).first()
    if existing:
        return existing
    if original_url:
        by_url = db.query(JobVacancy).filter(JobVacancy.original_url == original_url).first()
        if by_url:
            return by_url
    if provider_reference:
        by_ref = db.query(JobVacancy).filter(JobVacancy.provider_reference == provider_reference).first()
        if by_ref:
            return by_ref
    return None


def ingest_job_vacancy(
    db: Session,
    title: str,
    employer_name: str,
    original_url: str,
    country: str,
    description: str,
    location: str = "",
    city: str = "",
    work_arrangement: str = "On-site",
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
    salary_currency: str = "GBP",
    salary_text: str = "Not specified",
    required_skills: Optional[list[str]] = None,
    required_experience: str = "Entry-level / Graduate",
    education_requirements: str = "Bachelor's or Master's in Computer Science / Cybersecurity",
    language_requirements: str = "English",
    employment_type: str = "Full-time",
    date_published: str = "",
    application_deadline: Optional[str] = None,
    source: str = "manual",
    provider_reference: str = "",
    explicit_sponsorship_hint: Optional[str] = None,
    relocation_status: str = "Not verified",
    is_expired: bool = False,
    is_demo: bool = False,
) -> tuple[JobVacancy, bool]:
    """Ingests a job, prevents duplicates, runs ORACLE matching + LEXICON visa evaluation, and persists."""
    dup = is_duplicate_job(db, employer_name, title, location or country, original_url, provider_reference)
    if dup:
        return dup, False

    emp = db.query(Employer).filter(Employer.name.ilike(employer_name)).first()
    match_eval = evaluate_job_match(
        db=db,
        title=title,
        employer_name=employer_name,
        country=country,
        location=location or country,
        work_arrangement=work_arrangement,
        description=description,
        required_skills=required_skills or [],
        required_experience=required_experience,
        education_requirements=education_requirements,
        language_requirements=language_requirements,
        salary_min=salary_min,
        explicit_sponsorship_hint=explicit_sponsorship_hint,
    )

    visa_eval = match_eval["visa_evaluation"]
    lang_eval = match_eval["language_evaluation"]

    # Check deadline expiry
    expired_flag = is_expired
    if application_deadline:
        try:
            dl = datetime.strptime(application_deadline[:10], "%Y-%m-%d").date()
            if dl < datetime.now(timezone.utc).date():
                expired_flag = True
        except Exception:
            pass

    job = JobVacancy(
        title=title,
        employer_name=employer_name,
        employer_id=emp.id if emp else None,
        original_url=original_url,
        provider_reference=provider_reference,
        dedup_signature=compute_dedup_signature(employer_name, title, location or country, original_url),
        location=location or f"{city}, {country}".strip(", "),
        city=city,
        country=country,
        work_arrangement=work_arrangement,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
        salary_text=salary_text,
        description=description,
        required_skills=required_skills or match_eval["matched_skills"],
        required_experience=required_experience,
        education_requirements=education_requirements,
        language_requirements=lang_eval["language_summary"],
        requires_non_english=lang_eval["requires_non_english"],
        mandatory_languages=lang_eval["mandatory_languages"],
        employment_type=employment_type,
        date_published=date_published or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        application_deadline=application_deadline,
        source=source,
        job_status="Expired" if expired_flag else "Active",
        is_expired=expired_flag,
        is_demo=is_demo,
        sponsorship_status=visa_eval["sponsorship_status"],
        relocation_status=relocation_status if relocation_status != "Not verified" else visa_eval["relocation_assistance"],
        match_score=match_eval["overall_score"],
        match_breakdown=match_eval,
        visa_assessment=visa_eval,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job, True


def discover_live_public_jobs(db: Session, query: str = "security", limit: int = 10) -> dict[str, Any]:
    """
    ATLAS — Queries legally accessible public job APIs (Remotive & Arbeitnow) respecting rate limits.
    Never fabricates live listings; all fetched jobs preserve original provider URLs and metadata.
    """
    added = 0
    skipped_duplicates = 0
    errors: list[str] = []

    # 1. Remotive Public API (Official public API for remote tech/security roles)
    try:
        with httpx.Client(timeout=8.0, headers={"User-Agent": "APPLY-Personal-Job-Discovery/1.0"}) as client:
            resp = client.get("https://remotive.com/api/remote-jobs", params={"search": query, "limit": limit})
            if resp.status_code == 200:
                jobs_data = resp.json().get("jobs", [])[:limit]
                for item in jobs_data:
                    loc = item.get("candidate_required_location", "Remote")
                    country = "United Kingdom" if "uk" in loc.lower() or "united kingdom" in loc.lower() else (
                        "India" if "india" in loc.lower() else "United Kingdom"
                    )
                    clean_desc = re.sub(r"<[^>]+>", " ", item.get("description", ""))
                    clean_desc = re.sub(r"\s+", " ", clean_desc).strip()[:3000]
                    _, is_new = ingest_job_vacancy(
                        db=db,
                        title=item.get("title", "Security / IT Role"),
                        employer_name=item.get("company_name", "Remotive Employer"),
                        original_url=item.get("url", "https://remotive.com"),
                        country=country,
                        location=loc,
                        work_arrangement="Remote",
                        salary_text=item.get("salary", "Not specified") or "Not specified",
                        description=clean_desc or "Remote vacancy via Remotive Public API.",
                        required_skills=item.get("tags", []),
                        date_published=str(item.get("publication_date", ""))[:10],
                        source="remotive_public_api",
                        provider_reference=f"remotive-{item.get('id')}",
                        is_demo=False,
                    )
                    if is_new:
                        added += 1
                    else:
                        skipped_duplicates += 1
    except Exception as exc:
        errors.append(f"Remotive API unreachable or rate-limited: {str(exc)[:120]}")

    # 2. Arbeitnow Public API (European / German Visa-Sponsored & English job board API)
    try:
        with httpx.Client(timeout=8.0, headers={"User-Agent": "APPLY-Personal-Job-Discovery/1.0"}) as client:
            resp = client.get("https://www.arbeitnow.com/api/job-board-api")
            if resp.status_code == 200:
                jobs_data = resp.json().get("data", [])
                matched_items = [
                    j for j in jobs_data
                    if any(k in (j.get("title", "") + " " + " ".join(j.get("tags", []))).lower() for k in [query.lower(), "security", "soc", "support", "it", "cyber", "analyst"])
                ][:limit]
                for item in matched_items:
                    clean_desc = re.sub(r"<[^>]+>", " ", item.get("description", ""))
                    clean_desc = re.sub(r"\s+", " ", clean_desc).strip()[:3000]
                    visa_sponsored = "Visa Sponsorship" in item.get("tags", [])
                    _, is_new = ingest_job_vacancy(
                        db=db,
                        title=item.get("title", "IT / Security Specialist"),
                        employer_name=item.get("company_name", "European Employer"),
                        original_url=item.get("url", "https://www.arbeitnow.com"),
                        country="Germany",
                        location=item.get("location", "Berlin, Germany"),
                        city=item.get("location", "Berlin"),
                        work_arrangement="Remote" if item.get("remote") else "Hybrid",
                        description=clean_desc or "Vacancy discovered via Arbeitnow Public API.",
                        required_skills=item.get("tags", []),
                        source="arbeitnow_public_api",
                        provider_reference=f"arbeitnow-{item.get('slug', '')}",
                        explicit_sponsorship_hint="Employer explicitly states sponsorship available" if visa_sponsored else None,
                        is_demo=False,
                    )
                    if is_new:
                        added += 1
                    else:
                        skipped_duplicates += 1
    except Exception as exc:
        errors.append(f"Arbeitnow API unreachable or rate-limited: {str(exc)[:120]}")

    return {
        "new_jobs_added": added,
        "duplicates_skipped": skipped_duplicates,
        "provider_warnings": errors,
    }
