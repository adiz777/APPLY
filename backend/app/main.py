import csv
import io
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import BASE_DIR, EXPORTS_DIR, UPLOADS_DIR
from app.database import Base, SessionLocal, engine, get_db
from app.models import (
    ApplicationRecord,
    AuditLog,
    CandidateProfile,
    CoverLetterVersion,
    CVVersion,
    Employer,
    ImmigrationProfile,
    InterviewPrepSession,
    JobVacancy,
    ProjectDevelopmentTask,
    RecruitmentPreferences,
    SystemSettingsConfig,
    UserAccount,
    VisaCountryRule,
)
from app.security import create_access_token, encrypt_secret, hash_password, verify_password
from app.services.ai_provider import AIProviderOrchestrator
from app.services.automation_engine import (
    BulkQueueManager,
    SUPPORTED_STAGES,
    approve_application,
    execute_single_application_submission,
    log_audit_event,
    modify_application_content,
    prepare_application_for_job,
    validate_application_before_submission,
)
from app.services.cv_studio import (
    build_master_cv_text,
    export_document_to_docx,
    export_document_to_pdf,
    extract_text_from_upload,
    generate_cover_letter_and_answers,
    generate_tailored_cv_for_job,
    parse_cv_into_structured_profile,
)
from app.services.intelligence_modules import (
    CYBERSECURITY_INTERVIEW_TRACKS,
    RELOCATION_CITY_BENCHMARKS,
    build_interview_prep_session,
    calculate_relocation_comparison,
    evaluate_mock_interview_answer,
    inspect_repository_for_project_manager,
)
from app.services.job_discovery import INITIAL_JOB_CATEGORIES, discover_live_public_jobs, ingest_job_vacancy
from app.services.matching_engine import evaluate_job_match
from app.services.seed_data import seed_initial_platform_data
from app.services.visa_engine import VALID_SPONSORSHIP_STATUSES, evaluate_job_visa_intelligence


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_platform_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="APPLY — Autonomous Personal Application & Recruitment Intelligence System",
    version="1.0.0",
    description="Production-grade international recruitment, visa intelligence, CV/cover letter tailoring, and human-approved application automation API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: Optional[str] = None
    education: Optional[list[dict[str, Any]]] = None
    employment_history: Optional[list[dict[str, Any]]] = None
    technical_skills: Optional[list[str]] = None
    technical_interests: Optional[list[str]] = None
    projects: Optional[list[dict[str, Any]]] = None
    certifications: Optional[list[str]] = None
    achievements: Optional[list[str]] = None


class ImmigrationUpdate(BaseModel):
    nationality: Optional[str] = None
    current_location: Optional[str] = None
    uk_immigration_status: Optional[str] = None
    uk_visa_expiry_date: Optional[str] = None
    uk_work_eligibility: Optional[str] = None
    india_work_eligibility: Optional[str] = None
    relocation_readiness: Optional[str] = None
    notes: Optional[str] = None


class PreferencesUpdate(BaseModel):
    english_only: Optional[bool] = None
    reject_mandatory_other_language: Optional[bool] = None
    work_arrangements: Optional[list[str]] = None
    priority_countries: Optional[list[str]] = None
    additional_countries: Optional[list[str]] = None
    preferred_job_categories: Optional[list[str]] = None
    min_salary_expectation: Optional[float] = None
    preferred_currency: Optional[str] = None
    matching_weights: Optional[dict[str, int]] = None
    min_match_threshold: Optional[float] = None


class JobCreateRequest(BaseModel):
    title: str
    employer_name: str
    original_url: str
    country: str
    description: str
    location: str = ""
    city: str = ""
    work_arrangement: str = "On-site"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "GBP"
    salary_text: str = "Not specified"
    required_skills: list[str] = Field(default_factory=list)
    required_experience: str = "Entry-level / Graduate"
    education_requirements: str = "MSc / Bachelor's in Cybersecurity or Computer Science"
    language_requirements: str = "English"
    employment_type: str = "Full-time"
    date_published: str = ""
    application_deadline: Optional[str] = None
    source: str = "manual"
    provider_reference: str = ""
    explicit_sponsorship_hint: Optional[str] = None
    relocation_status: str = "Not verified"
    is_expired: bool = False
    is_demo: bool = False


class ApplicationContentUpdateRequest(BaseModel):
    form_answers: Optional[dict[str, Any]] = None
    work_eligibility_statement: Optional[str] = None
    cv_version_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    notes: Optional[str] = None


class ApplicationStatusUpdateRequest(BaseModel):
    stage: str
    notes: Optional[str] = None
    interview_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    contact_info: Optional[str] = None


class SingleSubmissionRequest(BaseModel):
    simulated_page_content: str = ""
    simulate_network_error: bool = False


class BulkSubmissionRequest(BaseModel):
    explicit_final_confirmation: bool
    selected_application_ids: Optional[list[int]] = None


class BulkPrepareJobsRequest(BaseModel):
    job_ids: list[int]


class BulkApproveApplicationsRequest(BaseModel):
    application_ids: list[int]


class BulkControlRequest(BaseModel):
    action: str  # pause, resume, cancel


class MockInterviewAnswerRequest(BaseModel):
    session_id: Optional[int] = None
    question: str
    candidate_answer: str


class EmployerCreateRequest(BaseModel):
    name: str
    country: str
    industry: str = "Cybersecurity & IT"
    official_website: str = ""
    careers_website: str = ""
    locations: list[str] = Field(default_factory=list)
    company_size: str = "Not verified"
    overview: str = ""
    sponsorship_capability_status: str = "Not verified"
    uk_licensed_sponsor: bool = False
    relocation_support_info: str = "Not verified"
    hiring_process: str = ""
    is_watchlisted: bool = True


class SystemSettingsUpdateRequest(BaseModel):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    token_limit: Optional[int] = None
    require_human_approval: Optional[bool] = None
    playwright_headless: Optional[bool] = None
    submission_concurrency: Optional[int] = None
    max_retries: Optional[int] = None
    enabled_job_sources: Optional[list[str]] = None
    data_retention_days: Optional[int] = None


class ProjectTaskCreateRequest(BaseModel):
    module_name: str
    title: str
    category: str = "Feature"
    priority: str = "High"
    status: str = "In Progress"
    assigned_agent: str = "PROJECT_MANAGER"
    description: str = ""


# ---------------------------------------------------------------------------
# 1. Health & Authentication Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    ai_info = AIProviderOrchestrator(db).get_active_provider_info()
    return {
        "status": "operational",
        "platform": "APPLY — Autonomous Personal Application & Recruitment Intelligence System",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_provider": ai_info,
    }


@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserAccount).filter(UserAccount.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        log_audit_event(db, req.email, "AUTH_LOGIN_FAILED", "UserAccount", req.email, {})
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(subject=user.email)
    log_audit_event(db, user.email, "AUTH_LOGIN_SUCCESS", "UserAccount", str(user.id), {})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
    }


# ---------------------------------------------------------------------------
# 2. Overview Dashboard Telemetry (Section 6)
# ---------------------------------------------------------------------------
@app.get("/api/overview")
def get_overview_dashboard(db: Session = Depends(get_db)):
    jobs = db.query(JobVacancy).all()
    apps = db.query(ApplicationRecord).filter(ApplicationRecord.is_archived == False).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(15).all()
    imm = db.query(ImmigrationProfile).first()

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_today = sum(1 for j in jobs if (j.date_published or "").startswith(today_str))
    matching_profile = sum(1 for j in jobs if j.match_score >= 55.0 and not j.requires_non_english)
    high_match = sum(1 for j in jobs if j.match_score >= 78.0 and not j.requires_non_english)

    sponsorship_confirmed = sum(
        1
        for j in jobs
        if j.sponsorship_status in ("Confirmed", "Employer explicitly states sponsorship available", "Employer sponsorship capability verified")
    )
    sponsorship_unverified = sum(1 for j in jobs if j.sponsorship_status == "Not verified")

    in_prep = sum(1 for a in apps if a.stage in ("Discovered", "Analysing", "Preparing", "Documents ready"))
    awaiting_approval = sum(1 for a in apps if a.stage == "Awaiting approval")
    approved_ready = sum(1 for a in apps if a.stage in ("Approved", "Queued"))
    submitted = sum(1 for a in apps if a.stage == "Submitted")
    interviews = sum(1 for a in apps if a.interview_date)
    rejected = sum(1 for a in apps if a.rejection_reason or a.stage == "Rejected")
    follow_ups = sum(1 for a in apps if a.follow_up_date)

    # Distributions
    country_counts: dict[str, int] = {}
    sponsorship_dist: dict[str, int] = {}
    match_buckets = {"High (78-100%)": 0, "Moderate (55-77%)": 0, "Barrier / Low (<55%)": 0}

    for j in jobs:
        country_counts[j.country] = country_counts.get(j.country, 0) + 1
        sponsorship_dist[j.sponsorship_status] = sponsorship_dist.get(j.sponsorship_status, 0) + 1
        if j.match_score >= 78:
            match_buckets["High (78-100%)"] += 1
        elif j.match_score >= 55:
            match_buckets["Moderate (55-77%)"] += 1
        else:
            match_buckets["Barrier / Low (<55%)"] += 1

    return {
        "metrics": {
            "total_jobs_discovered": len(jobs),
            "new_jobs_today": new_today,
            "jobs_matching_profile": matching_profile,
            "high_match_opportunities": high_match,
            "sponsorship_confirmed_opportunities": sponsorship_confirmed,
            "sponsorship_unverified_opportunities": sponsorship_unverified,
            "applications_in_preparation": in_prep,
            "applications_awaiting_approval": awaiting_approval,
            "applications_approved_ready": approved_ready,
            "applications_submitted": submitted,
            "interviews_scheduled": interviews,
            "rejected_applications": rejected,
            "upcoming_follow_ups": follow_ups,
        },
        "immigration_alert": {
            "nationality": imm.nationality if imm else "Indian",
            "current_location": imm.current_location if imm else "India",
            "uk_immigration_status": imm.uk_immigration_status if imm else "Graduate visa",
            "uk_visa_expiry_date": imm.uk_visa_expiry_date if imm else "2027-10-31",
            "uk_policy_note": "Eligible for UK roles without initial sponsorship while Graduate visa is valid; prioritise Skilled Worker sponsors before October 2027.",
        },
        "country_distribution": [{"country": k, "count": v} for k, v in sorted(country_counts.items(), key=lambda x: -x[1])],
        "sponsorship_distribution": [{"status": k, "count": v} for k, v in sponsorship_dist.items()],
        "match_distribution": [{"bucket": k, "count": v} for k, v in match_buckets.items()],
        "recent_jobs": [
            {
                "id": j.id,
                "title": j.title,
                "employer_name": j.employer_name,
                "country": j.country,
                "location": j.location,
                "work_arrangement": j.work_arrangement,
                "salary_text": j.salary_text,
                "match_score": j.match_score,
                "sponsorship_status": j.sponsorship_status,
                "is_demo": j.is_demo,
                "requires_non_english": j.requires_non_english,
            }
            for j in sorted(jobs, key=lambda x: x.id, reverse=True)[:8]
        ],
        "recent_activity": [
            {
                "id": log.id,
                "actor": log.actor,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }
            for log in audit_logs
        ],
    }


# ---------------------------------------------------------------------------
# 3. Candidate Profile, Immigration & Preferences (Sections 2 & 3)
# ---------------------------------------------------------------------------
@app.get("/api/profile")
def get_candidate_profile(db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).first()
    imm = db.query(ImmigrationProfile).first()
    prefs = db.query(RecruitmentPreferences).first()
    return {
        "profile": {
            "id": profile.id,
            "full_name": profile.full_name,
            "headline": profile.headline,
            "email": profile.email,
            "phone": profile.phone,
            "github_url": profile.github_url,
            "website_url": profile.website_url,
            "linkedin_url": profile.linkedin_url,
            "summary": profile.summary,
            "education": profile.education,
            "employment_history": profile.employment_history,
            "technical_skills": profile.technical_skills,
            "technical_interests": profile.technical_interests,
            "projects": profile.projects,
            "certifications": profile.certifications,
            "achievements": profile.achievements,
            "languages": profile.languages,
        },
        "immigration": {
            "id": imm.id,
            "nationality": imm.nationality,
            "current_location": imm.current_location,
            "uk_immigration_status": imm.uk_immigration_status,
            "uk_visa_expiry_date": imm.uk_visa_expiry_date,
            "uk_work_eligibility": imm.uk_work_eligibility,
            "india_work_eligibility": imm.india_work_eligibility,
            "relocation_readiness": imm.relocation_readiness,
            "notes": imm.notes,
        },
        "preferences": {
            "english_only": prefs.english_only,
            "reject_mandatory_other_language": prefs.reject_mandatory_other_language,
            "work_arrangements": prefs.work_arrangements,
            "priority_countries": prefs.priority_countries,
            "additional_countries": prefs.additional_countries,
            "preferred_job_categories": prefs.preferred_job_categories,
            "min_salary_expectation": prefs.min_salary_expectation,
            "preferred_currency": prefs.preferred_currency,
            "matching_weights": prefs.matching_weights,
            "min_match_threshold": prefs.min_match_threshold,
        },
    }


@app.put("/api/profile")
def update_candidate_profile(req: CandidateProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).first()
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(profile, field, val)
    db.commit()
    db.refresh(profile)
    log_audit_event(db, "CANDIDATE", "PROFILE_UPDATED", "CandidateProfile", str(profile.id), {})
    return {"status": "updated", "full_name": profile.full_name}


@app.put("/api/profile/immigration")
def update_immigration_profile(req: ImmigrationUpdate, db: Session = Depends(get_db)):
    imm = db.query(ImmigrationProfile).first()
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(imm, field, val)
    db.commit()
    db.refresh(imm)
    log_audit_event(
        db,
        "CANDIDATE",
        "IMMIGRATION_UPDATED",
        "ImmigrationProfile",
        str(imm.id),
        {"uk_immigration_status": imm.uk_immigration_status, "uk_visa_expiry_date": imm.uk_visa_expiry_date},
    )
    return {"status": "updated", "immigration": req.model_dump(exclude_unset=True)}


@app.put("/api/profile/preferences")
def update_recruitment_preferences(req: PreferencesUpdate, db: Session = Depends(get_db)):
    prefs = db.query(RecruitmentPreferences).first()
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(prefs, field, val)
    db.commit()
    db.refresh(prefs)
    log_audit_event(db, "CANDIDATE", "PREFERENCES_UPDATED", "RecruitmentPreferences", str(prefs.id), {})
    return {"status": "updated"}


# ---------------------------------------------------------------------------
# 4. Job Discovery & Job Intelligence (Sections 7 & 8)
# ---------------------------------------------------------------------------
@app.get("/api/jobs")
def list_jobs(
    country: Optional[str] = None,
    work_arrangement: Optional[str] = None,
    sponsorship_status: Optional[str] = None,
    english_only: Optional[bool] = None,
    search: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(JobVacancy)
    if country and country != "All":
        countries = [c.strip() for c in country.split(",") if c.strip() and c.strip() != "All"]
        if len(countries) == 1:
            query = query.filter(JobVacancy.country == countries[0])
        elif len(countries) > 1:
            query = query.filter(JobVacancy.country.in_(countries))
    if work_arrangement and work_arrangement != "All":
        arrangements = [w.strip() for w in work_arrangement.split(",") if w.strip() and w.strip() != "All"]
        if len(arrangements) == 1:
            query = query.filter(JobVacancy.work_arrangement.ilike(f"%{arrangements[0]}%"))
        elif len(arrangements) > 1:
            from sqlalchemy import or_
            query = query.filter(or_(*[JobVacancy.work_arrangement.ilike(f"%{w}%") for w in arrangements]))
    if sponsorship_status and sponsorship_status != "All":
        query = query.filter(JobVacancy.sponsorship_status == sponsorship_status)
    if english_only is True:
        query = query.filter(JobVacancy.requires_non_english == False)
    if min_score is not None:
        query = query.filter(JobVacancy.match_score >= min_score)

    jobs = query.order_by(JobVacancy.match_score.desc(), JobVacancy.id.desc()).all()
    if search:
        s_low = search.lower()
        jobs = [
            j
            for j in jobs
            if s_low in j.title.lower()
            or s_low in j.employer_name.lower()
            or s_low in j.description.lower()
            or any(s_low in sk.lower() for sk in (j.required_skills or []))
        ]

    return {
        "total": len(jobs),
        "categories": INITIAL_JOB_CATEGORIES,
        "sponsorship_statuses": VALID_SPONSORSHIP_STATUSES,
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "employer_name": j.employer_name,
                "original_url": j.original_url,
                "location": j.location,
                "city": j.city,
                "country": j.country,
                "work_arrangement": j.work_arrangement,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "salary_currency": j.salary_currency,
                "salary_text": j.salary_text,
                "description": j.description,
                "required_skills": j.required_skills,
                "required_experience": j.required_experience,
                "education_requirements": j.education_requirements,
                "language_requirements": j.language_requirements,
                "requires_non_english": j.requires_non_english,
                "mandatory_languages": j.mandatory_languages,
                "employment_type": j.employment_type,
                "date_published": j.date_published,
                "application_deadline": j.application_deadline,
                "source": j.source,
                "job_status": j.job_status,
                "is_expired": j.is_expired,
                "is_demo": j.is_demo,
                "sponsorship_status": j.sponsorship_status,
                "relocation_status": j.relocation_status,
                "match_score": j.match_score,
                "match_breakdown": j.match_breakdown,
                "visa_assessment": j.visa_assessment,
            }
            for j in jobs
        ],
    }


@app.post("/api/jobs")
def create_or_ingest_job(req: JobCreateRequest, db: Session = Depends(get_db)):
    job, is_new = ingest_job_vacancy(db=db, **req.model_dump())
    return {
        "is_new": is_new,
        "duplicate_prevented": not is_new,
        "job": {
            "id": job.id,
            "title": job.title,
            "employer_name": job.employer_name,
            "country": job.country,
            "match_score": job.match_score,
            "sponsorship_status": job.sponsorship_status,
            "requires_non_english": job.requires_non_english,
            "is_expired": job.is_expired,
            "match_breakdown": job.match_breakdown,
            "visa_assessment": job.visa_assessment,
        },
    }


@app.post("/api/jobs/discover-live")
def trigger_live_job_discovery(
    query: str = Query(default="cybersecurity"),
    limit: int = Query(default=8, ge=1, le=25),
    db: Session = Depends(get_db),
):
    result = discover_live_public_jobs(db=db, query=query, limit=limit)
    log_audit_event(db, "ATLAS", "LIVE_DISCOVERY_RUN", "JobVacancy", query, result)
    return result


@app.post("/api/jobs/{job_id}/recalculate")
def recalculate_job_intelligence(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobVacancy).filter(JobVacancy.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    match_eval = evaluate_job_match(
        db=db,
        title=job.title,
        employer_name=job.employer_name,
        country=job.country,
        location=job.location,
        work_arrangement=job.work_arrangement,
        description=job.description,
        required_skills=job.required_skills or [],
        required_experience=job.required_experience or "",
        education_requirements=job.education_requirements or "",
        language_requirements=job.language_requirements or "English",
        salary_min=job.salary_min,
        explicit_sponsorship_hint=job.sponsorship_status if job.sponsorship_status in VALID_SPONSORSHIP_STATUSES else None,
    )
    job.match_score = match_eval["overall_score"]
    job.match_breakdown = match_eval
    job.visa_assessment = match_eval["visa_evaluation"]
    job.sponsorship_status = match_eval["visa_evaluation"]["sponsorship_status"]
    db.commit()
    db.refresh(job)
    return {"id": job.id, "match_score": job.match_score, "match_breakdown": job.match_breakdown, "visa_assessment": job.visa_assessment}


# ---------------------------------------------------------------------------
# 5. Visa & Immigration Intelligence (Section 9)
# ---------------------------------------------------------------------------
@app.get("/api/visa/countries")
def get_visa_country_rules(db: Session = Depends(get_db)):
    rules = db.query(VisaCountryRule).order_by(VisaCountryRule.is_priority.desc(), VisaCountryRule.country.asc()).all()
    imm = db.query(ImmigrationProfile).first()
    return {
        "candidate_immigration": {
            "nationality": imm.nationality if imm else "Indian",
            "current_location": imm.current_location if imm else "India",
            "uk_immigration_status": imm.uk_immigration_status if imm else "Graduate visa",
            "uk_visa_expiry_date": imm.uk_visa_expiry_date if imm else "2027-10-31",
            "uk_work_eligibility": imm.uk_work_eligibility if imm else "",
            "india_work_eligibility": imm.india_work_eligibility if imm else "",
        },
        "sponsorship_classifications": VALID_SPONSORSHIP_STATUSES,
        "countries": [
            {
                "id": r.id,
                "country": r.country,
                "is_priority": r.is_priority,
                "primary_visa_route": r.primary_visa_route,
                "authority_name": r.authority_name,
                "official_source_url": r.official_source_url,
                "sponsorship_required_for_candidate": r.sponsorship_required_for_candidate,
                "current_candidate_eligibility_status": r.current_candidate_eligibility_status,
                "salary_threshold_info": r.salary_threshold_info,
                "occupation_eligibility_info": r.occupation_eligibility_info,
                "qualification_requirements": r.qualification_requirements,
                "labour_market_test_info": r.labour_market_test_info,
                "language_requirements_info": r.language_requirements_info,
                "estimated_visa_costs": r.estimated_visa_costs,
                "required_documents": r.required_documents,
                "official_process_steps": r.official_process_steps,
                "last_verified_date": r.last_verified_date,
            }
            for r in rules
        ],
    }


# ---------------------------------------------------------------------------
# 6. CV Studio & Cover Letter Studio (Sections 10 & 11)
# ---------------------------------------------------------------------------
@app.get("/api/cv/versions")
def list_cv_versions(db: Session = Depends(get_db)):
    versions = db.query(CVVersion).order_by(CVVersion.is_master.desc(), CVVersion.id.desc()).all()
    return {
        "versions": [
            {
                "id": v.id,
                "version_name": v.version_name,
                "is_master": v.is_master,
                "target_job_id": v.target_job_id,
                "source_filename": v.source_filename,
                "raw_text": v.raw_text,
                "structured_data": v.structured_data,
                "ats_keyword_coverage": v.ats_keyword_coverage,
                "matched_keywords": v.matched_keywords,
                "missing_keywords": v.missing_keywords,
                "missing_confirmations": v.missing_confirmations,
                "tailoring_notes": v.tailoring_notes,
                "created_at": v.created_at.isoformat() if v.created_at else "",
            }
            for v in versions
        ]
    }


@app.post("/api/cv/upload")
async def upload_master_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        raw_text = extract_text_from_upload(file.filename or "cv.txt", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    safe_name = Path(file.filename or "uploaded_cv.txt").name
    saved_path = UPLOADS_DIR / safe_name
    saved_path.write_bytes(content)

    profile = db.query(CandidateProfile).first()
    structured = parse_cv_into_structured_profile(raw_text, profile)

    # Demote previous master CVs
    for old_master in db.query(CVVersion).filter(CVVersion.is_master == True).all():
        old_master.is_master = False

    new_master = CVVersion(
        version_name=f"Master CV — Uploaded ({safe_name})",
        is_master=True,
        source_filename=safe_name,
        raw_text=raw_text,
        structured_data=structured,
        ats_keyword_coverage=100.0,
        matched_keywords=structured.get("technical_skills", []),
        missing_keywords=[],
        missing_confirmations=[],
        tailoring_notes="Uploaded by candidate and parsed into structured Master CV.",
    )
    db.add(new_master)
    db.commit()
    db.refresh(new_master)

    log_audit_event(db, "CANDIDATE", "MASTER_CV_UPLOADED", "CVVersion", str(new_master.id), {"filename": safe_name})
    return {
        "id": new_master.id,
        "version_name": new_master.version_name,
        "extracted_skills": structured.get("technical_skills", []),
        "character_count": len(raw_text),
    }


@app.post("/api/cv/tailor/{job_id}")
def tailor_cv_endpoint(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobVacancy).filter(JobVacancy.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    version = generate_tailored_cv_for_job(db, job)
    return {
        "id": version.id,
        "version_name": version.version_name,
        "raw_text": version.raw_text,
        "ats_keyword_coverage": version.ats_keyword_coverage,
        "matched_keywords": version.matched_keywords,
        "missing_keywords": version.missing_keywords,
        "missing_confirmations": version.missing_confirmations,
        "tailoring_notes": version.tailoring_notes,
    }


@app.get("/api/cv/{cv_id}/export/{fmt}")
def export_cv_file(cv_id: int, fmt: str, db: Session = Depends(get_db)):
    cv = db.query(CVVersion).filter(CVVersion.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV version not found.")
    if fmt.lower() == "pdf":
        path = export_document_to_pdf(cv.version_name, cv.raw_text, f"cv_v{cv.id}")
        return FileResponse(path, media_type="application/pdf", filename=path.name)
    elif fmt.lower() == "docx":
        path = export_document_to_docx(cv.version_name, cv.raw_text, f"cv_v{cv.id}")
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=path.name,
        )
    raise HTTPException(status_code=400, detail="Unsupported export format. Use 'pdf' or 'docx'.")


@app.get("/api/cover-letters")
def list_cover_letters(db: Session = Depends(get_db)):
    items = db.query(CoverLetterVersion).order_by(CoverLetterVersion.id.desc()).all()
    return {
        "cover_letters": [
            {
                "id": cl.id,
                "title": cl.title,
                "target_job_id": cl.target_job_id,
                "country_adapted": cl.country_adapted,
                "employer_name": cl.employer_name,
                "cover_letter_text": cl.cover_letter_text,
                "supporting_statement": cl.supporting_statement,
                "screening_answers": cl.screening_answers,
                "star_examples": cl.star_examples,
                "work_eligibility_response": cl.work_eligibility_response,
                "relocation_response": cl.relocation_response,
                "salary_expectation_response": cl.salary_expectation_response,
                "created_at": cl.created_at.isoformat() if cl.created_at else "",
            }
            for cl in items
        ]
    }


@app.post("/api/cover-letters/generate/{job_id}")
def generate_cover_letter_endpoint(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobVacancy).filter(JobVacancy.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    cl = generate_cover_letter_and_answers(db, job)
    return {
        "id": cl.id,
        "title": cl.title,
        "cover_letter_text": cl.cover_letter_text,
        "screening_answers": cl.screening_answers,
        "star_examples": cl.star_examples,
        "work_eligibility_response": cl.work_eligibility_response,
        "relocation_response": cl.relocation_response,
        "salary_expectation_response": cl.salary_expectation_response,
    }


# ---------------------------------------------------------------------------
# 7. Application Queue, Command Centre & Bulk Submission (Sections 13, 14, 15)
# ---------------------------------------------------------------------------
@app.get("/api/applications")
def list_applications(db: Session = Depends(get_db)):
    apps = db.query(ApplicationRecord).filter(ApplicationRecord.is_archived == False).order_by(ApplicationRecord.id.desc()).all()
    return {
        "supported_stages": SUPPORTED_STAGES,
        "applications": [
            {
                "id": a.id,
                "job_id": a.job_id,
                "employer_name": a.employer_name,
                "job_title": a.job_title,
                "country": a.country,
                "location": a.location,
                "job_url": a.job_url,
                "salary_text": a.salary_text,
                "cv_version_id": a.cv_version_id,
                "cover_letter_id": a.cover_letter_id,
                "stage": a.stage,
                "form_answers": a.form_answers,
                "detected_fields": a.detected_fields,
                "work_eligibility_statement": a.work_eligibility_statement,
                "sponsorship_summary": a.sponsorship_summary,
                "unresolved_warnings": a.unresolved_warnings,
                "human_approved": a.human_approved,
                "approved_by": a.approved_by,
                "approved_at": a.approved_at.isoformat() if a.approved_at else None,
                "approval_hash": a.approval_hash,
                "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
                "confirmation_reference": a.confirmation_reference,
                "failure_reason": a.failure_reason,
                "contact_info": a.contact_info,
                "interview_date": a.interview_date,
                "follow_up_date": a.follow_up_date,
                "notes": a.notes,
                "is_demo": a.is_demo,
                "activity_history": a.activity_history,
            }
            for a in apps
        ],
    }


@app.post("/api/applications/prepare/{job_id}")
def prepare_application_endpoint(job_id: int, db: Session = Depends(get_db)):
    try:
        app_rec = prepare_application_for_job(db, job_id)
        return {"id": app_rec.id, "stage": app_rec.stage, "human_approved": app_rec.human_approved}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/applications/prepare-selected")
def prepare_selected_applications_endpoint(req: BulkPrepareJobsRequest, db: Session = Depends(get_db)):
    prepared = []
    for jid in req.job_ids:
        try:
            app_rec = prepare_application_for_job(db, jid)
            prepared.append({"id": app_rec.id, "job_id": jid, "stage": app_rec.stage})
        except ValueError:
            pass
    return {
        "prepared_count": len(prepared),
        "skipped_existing_count": 0,
        "application_ids": [p["id"] for p in prepared],
        "prepared": prepared,
    }


@app.post("/api/applications/approve-selected")
def approve_selected_applications_endpoint(req: BulkApproveApplicationsRequest, db: Session = Depends(get_db)):
    approved = []
    for aid in req.application_ids:
        try:
            app_rec = approve_application(db, aid)
            approved.append({"id": app_rec.id, "stage": app_rec.stage, "approval_hash": app_rec.approval_hash})
        except ValueError:
            pass
    return {"approved_count": len(approved), "approved": approved}


@app.post("/api/applications/{app_id}/approve")
def approve_application_endpoint(app_id: int, db: Session = Depends(get_db)):
    try:
        app_rec = approve_application(db, app_id)
        return {
            "id": app_rec.id,
            "stage": app_rec.stage,
            "human_approved": app_rec.human_approved,
            "approval_hash": app_rec.approval_hash,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.put("/api/applications/{app_id}/content")
def update_application_content_endpoint(
    app_id: int,
    req: ApplicationContentUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        app_rec = modify_application_content(
            db=db,
            application_id=app_id,
            updated_form_answers=req.form_answers,
            updated_work_eligibility=req.work_eligibility_statement,
            updated_cv_version_id=req.cv_version_id,
            updated_cover_letter_id=req.cover_letter_id,
            notes=req.notes,
        )
        return {
            "id": app_rec.id,
            "stage": app_rec.stage,
            "human_approved": app_rec.human_approved,
            "approval_hash": app_rec.approval_hash,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.put("/api/applications/{app_id}/status")
def update_application_status_endpoint(
    app_id: int,
    req: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    app_rec = db.query(ApplicationRecord).filter(ApplicationRecord.id == app_id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail="Application not found.")
    app_rec.stage = req.stage
    if req.notes is not None:
        app_rec.notes = req.notes
    if req.interview_date is not None:
        app_rec.interview_date = req.interview_date
    if req.follow_up_date is not None:
        app_rec.follow_up_date = req.follow_up_date
    if req.contact_info is not None:
        app_rec.contact_info = req.contact_info
    db.commit()
    return {"id": app_rec.id, "stage": app_rec.stage}


@app.post("/api/applications/{app_id}/submit")
def submit_single_application_endpoint(
    app_id: int,
    req: Optional[SingleSubmissionRequest] = None,
    db: Session = Depends(get_db),
):
    try:
        res = execute_single_application_submission(
            db=db,
            application_id=app_id,
            simulated_page_content=req.simulated_page_content if req else "",
            simulate_network_error=req.simulate_network_error if req else False,
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/applications/bulk/summary")
def get_bulk_submission_summary(db: Session = Depends(get_db)):
    return BulkQueueManager.get_pre_submission_summary(db)


@app.post("/api/applications/bulk/submit-approved")
def submit_all_approved_applications(req: BulkSubmissionRequest, db: Session = Depends(get_db)):
    try:
        return BulkQueueManager.run_bulk_submission(
            db=db,
            explicit_final_confirmation=req.explicit_final_confirmation,
            selected_ids=req.selected_application_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/applications/bulk/control")
def control_bulk_queue(req: BulkControlRequest):
    action = req.action.lower()
    if action == "pause":
        BulkQueueManager.state = "paused"
    elif action == "resume":
        BulkQueueManager.state = "idle"
    elif action == "cancel":
        BulkQueueManager.state = "cancelled"
    else:
        raise HTTPException(status_code=400, detail="Unsupported action. Use pause, resume, or cancel.")
    return {"queue_state": BulkQueueManager.state}


# ---------------------------------------------------------------------------
# 8. Employer Intelligence (Section 12)
# ---------------------------------------------------------------------------
@app.get("/api/employers")
def list_employers(db: Session = Depends(get_db)):
    employers = db.query(Employer).order_by(Employer.is_watchlisted.desc(), Employer.name.asc()).all()
    return {
        "employers": [
            {
                "id": e.id,
                "name": e.name,
                "country": e.country,
                "industry": e.industry,
                "official_website": e.official_website,
                "careers_website": e.careers_website,
                "locations": e.locations,
                "company_size": e.company_size,
                "overview": e.overview,
                "sponsorship_capability_status": e.sponsorship_capability_status,
                "uk_licensed_sponsor": e.uk_licensed_sponsor,
                "sponsorship_evidence_url": e.sponsorship_evidence_url,
                "relocation_support_info": e.relocation_support_info,
                "hiring_process": e.hiring_process,
                "reputation_notes": e.reputation_notes,
                "citations": e.citations,
                "is_watchlisted": e.is_watchlisted,
                "is_demo": e.is_demo,
                "last_checked_at": e.last_checked_at.strftime("%Y-%m-%d") if e.last_checked_at else "2026-11-03",
            }
            for e in employers
        ]
    }


@app.post("/api/employers")
def create_employer(req: EmployerCreateRequest, db: Session = Depends(get_db)):
    emp = Employer(**req.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {"id": emp.id, "name": emp.name}


@app.post("/api/employers/{emp_id}/toggle-watchlist")
def toggle_employer_watchlist(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employer).filter(Employer.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employer not found.")
    emp.is_watchlisted = not emp.is_watchlisted
    db.commit()
    return {"id": emp.id, "is_watchlisted": emp.is_watchlisted}


# ---------------------------------------------------------------------------
# 9. Interview Intelligence & Relocation Intelligence (Sections 16 & 17)
# ---------------------------------------------------------------------------
@app.get("/api/interviews")
def get_interview_intelligence(
    role_track: str = Query(default="SOC Analyst"),
    job_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    session = build_interview_prep_session(db, role_track=role_track, job_id=job_id)
    return {
        "available_tracks": list(CYBERSECURITY_INTERVIEW_TRACKS.keys()),
        "session": {
            "id": session.id,
            "role_track": session.role_track,
            "employer_name": session.employer_name,
            "employer_research": session.employer_research,
            "role_questions": session.role_questions,
            "technical_questions": session.technical_questions,
            "behavioural_questions": session.behavioural_questions,
            "questions_to_ask": session.questions_to_ask,
            "prep_checklist": session.prep_checklist,
        },
    }


@app.post("/api/interviews/mock-evaluate")
def evaluate_mock_interview(req: MockInterviewAnswerRequest):
    return evaluate_mock_interview_answer(req.question, req.candidate_answer)


@app.get("/api/relocation")
def get_relocation_intelligence(
    city: str = Query(default="London, United Kingdom"),
    gross_annual: Optional[float] = None,
):
    comparison = calculate_relocation_comparison(city, gross_annual)
    all_cities = [calculate_relocation_comparison(c) for c in RELOCATION_CITY_BENCHMARKS.keys()]
    return {
        "available_cities": list(RELOCATION_CITY_BENCHMARKS.keys()),
        "selected_city": comparison,
        "city_matrix": all_cities,
    }


# ---------------------------------------------------------------------------
# 10. Reports & Analytics (Section 20)
# ---------------------------------------------------------------------------
@app.get("/api/reports/export/{fmt}")
def export_recruitment_report(fmt: str, db: Session = Depends(get_db)):
    jobs = db.query(JobVacancy).all()
    apps = db.query(ApplicationRecord).all()

    if fmt.lower() == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["Job ID", "Title", "Employer", "Country", "Match Score", "Sponsorship Status", "English Eligible", "Application Stage"])
        app_by_job = {a.job_id: a.stage for a in apps}
        for j in jobs:
            writer.writerow([
                j.id,
                j.title,
                j.employer_name,
                j.country,
                j.match_score,
                j.sponsorship_status,
                not j.requires_non_english,
                app_by_job.get(j.id, "Not started"),
            ])
        stream.seek(0)
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=apply_recruitment_report.csv"},
        )

    elif fmt.lower() == "pdf":
        lines = [
            f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Total Jobs Discovered: {len(jobs)}",
            f"Total Applications Tracked: {len(apps)}",
            "",
            "TOP DISCOVERED OPPORTUNITIES:",
        ]
        for j in sorted(jobs, key=lambda x: x.match_score, reverse=True)[:15]:
            lines.append(f"- [{j.country}] {j.title} @ {j.employer_name} | Match: {j.match_score}% | Sponsorship: {j.sponsorship_status}")
        path = export_document_to_pdf("APPLY — Executive Recruitment & Sponsorship Intelligence Report", "\n".join(lines), "apply_report")
        return FileResponse(path, media_type="application/pdf", filename=path.name)

    raise HTTPException(status_code=400, detail="Unsupported report format. Use 'csv' or 'pdf'.")


# ---------------------------------------------------------------------------
# 11. AI Project Manager & Settings (Sections 18, 19, 21, 22)
# ---------------------------------------------------------------------------
@app.get("/api/project-manager")
def get_project_manager_dashboard(db: Session = Depends(get_db)):
    return inspect_repository_for_project_manager(db, BASE_DIR.parent)


@app.post("/api/project-manager/tasks")
def create_project_task(req: ProjectTaskCreateRequest, db: Session = Depends(get_db)):
    task = ProjectDevelopmentTask(**req.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status}


@app.get("/api/settings")
def get_system_settings(db: Session = Depends(get_db)):
    cfg = db.query(SystemSettingsConfig).first()
    return {
        "ai_provider": cfg.ai_provider,
        "ai_model": cfg.ai_model,
        "has_gemini_key": bool(cfg.encrypted_gemini_key),
        "has_anthropic_key": bool(cfg.encrypted_anthropic_key),
        "has_openai_key": bool(cfg.encrypted_openai_key),
        "openai_base_url": cfg.openai_base_url,
        "ollama_base_url": cfg.ollama_base_url,
        "ollama_model": cfg.ollama_model,
        "token_limit": cfg.token_limit,
        "require_human_approval": cfg.require_human_approval,
        "playwright_headless": cfg.playwright_headless,
        "submission_concurrency": cfg.submission_concurrency,
        "max_retries": cfg.max_retries,
        "enabled_job_sources": cfg.enabled_job_sources,
        "discovery_schedule_cron": cfg.discovery_schedule_cron,
        "data_retention_days": cfg.data_retention_days,
    }


@app.put("/api/settings")
def update_system_settings(req: SystemSettingsUpdateRequest, db: Session = Depends(get_db)):
    cfg = db.query(SystemSettingsConfig).first()
    data = req.model_dump(exclude_unset=True)
    if "gemini_api_key" in data and data["gemini_api_key"] is not None:
        cfg.encrypted_gemini_key = encrypt_secret(data.pop("gemini_api_key"))
    if "anthropic_api_key" in data and data["anthropic_api_key"] is not None:
        cfg.encrypted_anthropic_key = encrypt_secret(data.pop("anthropic_api_key"))
    if "openai_api_key" in data and data["openai_api_key"] is not None:
        cfg.encrypted_openai_key = encrypt_secret(data.pop("openai_api_key"))

    for k, v in data.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    # Human approval must always remain enforced per security rule
    cfg.require_human_approval = True
    db.commit()
    log_audit_event(db, "CANDIDATE", "SYSTEM_SETTINGS_UPDATED", "SystemSettingsConfig", str(cfg.id), {"ai_provider": cfg.ai_provider})
    return {"status": "updated", "ai_provider": cfg.ai_provider}


@app.get("/api/privacy/export-all")
def export_all_candidate_data(db: Session = Depends(get_db)):
    profile = get_candidate_profile(db)
    jobs = list_jobs(db=db)
    apps = list_applications(db=db)
    log_audit_event(db, "CANDIDATE", "FULL_DATA_EXPORTED", "Privacy", "ALL", {})
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "candidate_profile": profile,
        "jobs_count": jobs["total"],
        "applications": apps["applications"],
    }
