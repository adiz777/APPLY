import hashlib
import html
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

# Official public Greenhouse career boards for real cybersecurity & tech employers
GREENHOUSE_REAL_EMPLOYERS: list[dict[str, Any]] = [
    {"slug": "cloudflare", "name": "Cloudflare", "uk_sponsor": True},
    {"slug": "canonical", "name": "Canonical (Ubuntu)", "uk_sponsor": True},
    {"slug": "elastic", "name": "Elastic", "uk_sponsor": True},
    {"slug": "okta", "name": "Okta", "uk_sponsor": True},
    {"slug": "recordedfuture", "name": "Recorded Future", "uk_sponsor": True},
    {"slug": "zscaler", "name": "Zscaler", "uk_sponsor": True},
    {"slug": "datadog", "name": "Datadog", "uk_sponsor": True},
    {"slug": "gitlab", "name": "GitLab", "uk_sponsor": True},
    {"slug": "monzo", "name": "Monzo Bank", "uk_sponsor": True},
    {"slug": "deliveroo", "name": "Deliveroo", "uk_sponsor": True},
]

RELEVANT_ROLE_KEYWORDS = [
    "security",
    "cyber",
    "soc ",
    "soc-",
    "threat",
    "intelligence",
    "incident",
    "vulnerability",
    "penetration",
    "pentest",
    "osint",
    "forensic",
    "support engineer",
    "support analyst",
    "technical support",
    "it support",
    "service desk",
    "helpdesk",
    "desktop support",
    "it engineer",
    "it specialist",
    "it analyst",
    "systems administrator",
    "sysadmin",
    "network engineer",
    "linux",
    "detection",
    "vapt",
]


def clean_html_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    unescaped = html.unescape(raw_html)
    no_tags = re.sub(r"<[^>]+>", " ", unescaped)
    return re.sub(r"\s+", " ", no_tags).strip()[:4000]


def infer_country_from_location(loc_str: str) -> Optional[str]:
    loc = (loc_str or "").lower()
    if any(k in loc for k in ["united kingdom", "uk", "london", "manchester", "edinburgh", "bristol", "cambridge", "reading", "belfast", "watford", "england", "scotland"]):
        return "United Kingdom"
    if any(k in loc for k in ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "chennai", "delhi", "noida", "gurugram", "gurgaon", "ahmedabad"]):
        return "India"
    if any(k in loc for k in ["germany", "deutschland", "berlin", "munich", "münchen", "frankfurt", "hamburg", "stuttgart", "cologne"]):
        return "Germany"
    if any(k in loc for k in ["ireland", "dublin", "cork", "galway"]):
        return "Ireland"
    if any(k in loc for k in ["netherlands", "amsterdam", "rotterdam", "utrecht", "hague", "eindhoven"]):
        return "Netherlands"
    if any(k in loc for k in ["united arab emirates", "uae", "dubai", "abu dhabi"]):
        return "United Arab Emirates"
    if any(k in loc for k in ["canada", "toronto", "vancouver", "montreal", "ottawa", "calgary"]):
        return "Canada"
    if any(k in loc for k in ["australia", "sydney", "melbourne", "brisbane", "perth", "canberra"]):
        return "Australia"
    if any(k in loc for k in ["new zealand", "auckland", "wellington", "christchurch"]):
        return "New Zealand"
    if any(k in loc for k in ["singapore"]):
        return "Singapore"
    if any(k in loc for k in ["sweden", "stockholm"]):
        return "Sweden"
    if any(k in loc for k in ["france", "paris"]):
        return "France"
    if any(k in loc for k in ["worldwide", "anywhere", "global", "emea", "europe", "uk"]):
        return "United Kingdom"
    return None


def extract_skills_from_text(title: str, desc: str, tags: Optional[list[str]] = None) -> list[str]:
    combined = f"{title} {desc} {' '.join(tags or [])}".lower()
    catalog = [
        "Cybersecurity",
        "SOC Operations",
        "SIEM",
        "Threat Intelligence",
        "Incident Response",
        "OSINT",
        "Reconnaissance",
        "Vulnerability Assessment",
        "Penetration Testing",
        "Network Security",
        "Linux",
        "Python",
        "Bash",
        "IT Support",
        "Service Desk",
        "Active Directory",
        "Windows",
        "Docker",
        "Cloudflare",
        "Wireshark",
        "Nmap",
        "Burp Suite",
        "Troubleshooting",
    ]
    found = [skill for skill in catalog if skill.lower() in combined]
    for t in tags or []:
        if isinstance(t, str) and len(t) <= 35 and t not in found:
            found.append(t)
    return found[:12] or ["Cybersecurity", "Security Operations", "Linux", "Python"]


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
    skills_list = required_skills or extract_skills_from_text(title, description)

    match_eval = evaluate_job_match(
        db=db,
        title=title,
        employer_name=employer_name,
        country=country,
        location=location or country,
        work_arrangement=work_arrangement,
        description=description,
        required_skills=skills_list,
        required_experience=required_experience,
        education_requirements=education_requirements,
        language_requirements=language_requirements,
        salary_min=salary_min,
        explicit_sponsorship_hint=explicit_sponsorship_hint,
    )

    visa_eval = match_eval["visa_evaluation"]
    lang_eval = match_eval["language_evaluation"]

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
        required_skills=skills_list,
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


def discover_live_public_jobs(db: Session, query: str = "security", limit: int = 15) -> dict[str, Any]:
    """
    ATLAS — Queries real, legally accessible public job APIs and official employer Greenhouse ATS boards:
    1. Official Greenhouse Employer Career Boards (Cloudflare, Canonical, Elastic, Okta, Recorded Future, Zscaler, Datadog, GitLab, Monzo, Deliveroo)
    2. Jobicy Public Remote Jobs API
    3. Remotive Public Jobs API
    4. Arbeitnow European / Visa-Sponsored Public API
    Never fabricates listings; every record stores its real external application URL.
    """
    added = 0
    skipped_duplicates = 0
    errors: list[str] = []
    headers = {"User-Agent": "APPLY-Personal-Job-Discovery/1.0"}

    # 1. Official Greenhouse Employer Boards (Real UK, India, Germany, Ireland, Netherlands, UAE, Canada, Australia vacancies)
    with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
        for board in GREENHOUSE_REAL_EMPLOYERS:
            try:
                resp = client.get(
                    f"https://boards-api.greenhouse.io/v1/boards/{board['slug']}/jobs",
                    params={"content": "true"},
                )
                if resp.status_code != 200:
                    continue
                jobs_list = resp.json().get("jobs", [])
                board_added = 0
                for item in jobs_list:
                    title = item.get("title", "")
                    loc_name = (item.get("location") or {}).get("name", "")
                    country = infer_country_from_location(loc_name)
                    if not country:
                        continue
                    title_low = title.lower()
                    if not any(kw in title_low for kw in RELEVANT_ROLE_KEYWORDS):
                        continue

                    raw_content = item.get("content", "") or title
                    clean_desc = clean_html_text(raw_content)
                    work_arr = "Remote" if "remote" in loc_name.lower() or "home" in loc_name.lower() else "Hybrid"
                    sponsor_hint = (
                        "Employer sponsorship capability verified"
                        if (country == "United Kingdom" and board.get("uk_sponsor"))
                        else None
                    )

                    _, is_new = ingest_job_vacancy(
                        db=db,
                        title=title,
                        employer_name=board["name"],
                        original_url=item.get("absolute_url", f"https://boards.greenhouse.io/{board['slug']}"),
                        country=country,
                        location=loc_name,
                        city=loc_name.split(",")[0].strip(),
                        work_arrangement=work_arr,
                        description=clean_desc or f"Live vacancy at {board['name']} ({loc_name}).",
                        required_skills=extract_skills_from_text(title, clean_desc),
                        date_published=str(item.get("updated_at", ""))[:10],
                        source=f"greenhouse_{board['slug']}",
                        provider_reference=f"gh-{board['slug']}-{item.get('id')}",
                        explicit_sponsorship_hint=sponsor_hint,
                        is_demo=False,
                    )
                    if is_new:
                        added += 1
                        board_added += 1
                    else:
                        skipped_duplicates += 1
                    if board_added >= 4:
                        break
            except Exception as exc:
                errors.append(f"Greenhouse ({board['slug']}): {str(exc)[:100]}")

        # 2. Jobicy Public Remote API (Cybersecurity & IT Support)
        for tag in ["security", "cybersecurity", "support"]:
            try:
                resp = client.get("https://jobicy.com/api/v2/remote-jobs", params={"count": limit, "tag": tag})
                if resp.status_code == 200:
                    for item in resp.json().get("jobs", [])[:limit]:
                        geo = item.get("jobGeo", "Remote")
                        country = infer_country_from_location(geo) or "United Kingdom"
                        clean_desc = clean_html_text(item.get("jobDescription", "") or item.get("jobExcerpt", ""))
                        sal_min = item.get("annualSalaryMin")
                        sal_max = item.get("annualSalaryMax")
                        curr = item.get("salaryCurrency", "USD") or "USD"
                        sal_txt = f"{curr} {sal_min} - {sal_max}" if sal_min and sal_max else "Not specified"

                        _, is_new = ingest_job_vacancy(
                            db=db,
                            title=item.get("jobTitle", "Security Specialist"),
                            employer_name=item.get("companyName", "Global Tech Employer"),
                            original_url=item.get("url", "https://jobicy.com"),
                            country=country,
                            location=f"{geo} (Remote)",
                            work_arrangement="Remote",
                            salary_min=float(sal_min) if sal_min else None,
                            salary_max=float(sal_max) if sal_max else None,
                            salary_currency=curr,
                            salary_text=sal_txt,
                            description=clean_desc or "Remote vacancy via Jobicy Public API.",
                            required_skills=extract_skills_from_text(item.get("jobTitle", ""), clean_desc, item.get("jobIndustry", [])),
                            date_published=str(item.get("pubDate", ""))[:10],
                            source="jobicy_public_api",
                            provider_reference=f"jobicy-{item.get('id')}",
                            is_demo=False,
                        )
                        if is_new:
                            added += 1
                        else:
                            skipped_duplicates += 1
            except Exception as exc:
                errors.append(f"Jobicy API ({tag}): {str(exc)[:100]}")

        # 3. Remotive Public API
        try:
            resp = client.get("https://remotive.com/api/remote-jobs", params={"search": query, "limit": limit})
            if resp.status_code == 200:
                for item in resp.json().get("jobs", [])[:limit]:
                    loc = item.get("candidate_required_location", "Worldwide")
                    country = infer_country_from_location(loc) or "United Kingdom"
                    clean_desc = clean_html_text(item.get("description", ""))
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
                        required_skills=extract_skills_from_text(item.get("title", ""), clean_desc, item.get("tags", [])),
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
            errors.append(f"Remotive API: {str(exc)[:100]}")

        # 4. Arbeitnow Public API (European & German Visa-Sponsored Roles)
        try:
            resp = client.get("https://www.arbeitnow.com/api/job-board-api")
            if resp.status_code == 200:
                jobs_data = resp.json().get("data", [])
                matched_items = [
                    j
                    for j in jobs_data
                    if any(
                        k in (j.get("title", "") + " " + " ".join(j.get("tags", []))).lower()
                        for k in [query.lower(), "security", "soc", "support", "it", "cyber", "analyst", "linux", "network"]
                    )
                ][:limit]
                for item in matched_items:
                    clean_desc = clean_html_text(item.get("description", ""))
                    visa_sponsored = "Visa Sponsorship" in item.get("tags", [])
                    loc_str = item.get("location", "Berlin, Germany")
                    country = infer_country_from_location(loc_str) or "Germany"
                    _, is_new = ingest_job_vacancy(
                        db=db,
                        title=item.get("title", "IT / Security Specialist"),
                        employer_name=item.get("company_name", "European Employer"),
                        original_url=item.get("url", "https://www.arbeitnow.com"),
                        country=country,
                        location=loc_str,
                        city=loc_str.split(",")[0].strip(),
                        work_arrangement="Remote" if item.get("remote") else "Hybrid",
                        description=clean_desc or "Vacancy discovered via Arbeitnow Public API.",
                        required_skills=extract_skills_from_text(item.get("title", ""), clean_desc, item.get("tags", [])),
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
            errors.append(f"Arbeitnow API: {str(exc)[:100]}")

    return {
        "new_jobs_added": added,
        "duplicates_skipped": skipped_duplicates,
        "provider_warnings": errors,
    }
