from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), default="Candidate")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    last_login_at = Column(DateTime(timezone=True), nullable=True)


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), default="Adi Zala")
    headline = Column(String(255), default="MSc Cybersecurity Graduate | SOC, Threat Intelligence, OSINT & IT Support")
    email = Column(String(255), default="")
    phone = Column(String(100), default="")
    github_url = Column(String(500), default="https://github.com/adiz777")
    website_url = Column(String(500), default="https://adizala.me")
    linkedin_url = Column(String(500), default="")
    summary = Column(Text, default="")

    education = Column(JSON, default=list)
    employment_history = Column(JSON, default=list)
    technical_skills = Column(JSON, default=list)
    technical_interests = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    achievements = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    supporting_documents = Column(JSON, default=list)

    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ImmigrationProfile(Base):
    __tablename__ = "immigration_profiles"

    id = Column(Integer, primary_key=True, index=True)
    nationality = Column(String(100), default="Indian")
    current_location = Column(String(100), default="India")
    uk_immigration_status = Column(String(100), default="Graduate visa")
    uk_visa_expiry_date = Column(String(50), default="2027-10-31")
    uk_work_eligibility = Column(
        Text,
        default="Eligible to work in the UK without employer sponsorship while Graduate visa remains valid until October 2027. Prioritise employers capable of Skilled Worker sponsorship before October 2027.",
    )
    india_work_eligibility = Column(
        Text,
        default="Full unrestricted work eligibility in India (No employer visa sponsorship required).",
    )
    other_visas_held = Column(JSON, default=list)
    relocation_readiness = Column(String(100), default="Immediate — Domestic & International")
    notes = Column(Text, default="")
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class RecruitmentPreferences(Base):
    __tablename__ = "recruitment_preferences"

    id = Column(Integer, primary_key=True, index=True)
    english_only = Column(Boolean, default=True)
    reject_mandatory_other_language = Column(Boolean, default=True)
    work_arrangements = Column(
        JSON,
        default=lambda: [
            "Remote",
            "Hybrid",
            "On-site",
            "International relocation",
            "Domestic relocation",
            "Flexible",
        ],
    )
    priority_countries = Column(
        JSON,
        default=lambda: [
            "United Kingdom",
            "Germany",
            "Ireland",
            "Netherlands",
            "United Arab Emirates",
            "Canada",
            "Australia",
            "New Zealand",
            "India",
        ],
    )
    additional_countries = Column(
        JSON,
        default=lambda: [
            "Singapore",
            "Japan",
            "Sweden",
            "Finland",
            "Denmark",
            "France",
            "Belgium",
            "Luxembourg",
            "Austria",
            "Norway",
            "Switzerland",
            "Saudi Arabia",
            "Qatar",
        ],
    )
    preferred_job_categories = Column(JSON, default=list)
    min_salary_expectation = Column(Float, nullable=True)
    preferred_currency = Column(String(20), default="GBP")
    matching_weights = Column(
        JSON,
        default=lambda: {
            "technical_skills": 30,
            "relevant_experience": 20,
            "education": 15,
            "role_suitability": 15,
            "language_eligibility": 10,
            "immigration_feasibility": 10,
        },
    )
    min_match_threshold = Column(Float, default=55.0)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SystemSettingsConfig(Base):
    __tablename__ = "system_settings_configs"

    id = Column(Integer, primary_key=True, index=True)
    ai_provider = Column(String(50), default="deterministic")
    ai_model = Column(String(100), default="gemini-2.5-flash")
    encrypted_gemini_key = Column(Text, default="")
    encrypted_anthropic_key = Column(Text, default="")
    encrypted_openai_key = Column(Text, default="")
    openai_base_url = Column(String(500), default="https://api.openai.com/v1")
    ollama_base_url = Column(String(500), default="http://localhost:11434")
    ollama_model = Column(String(100), default="llama3.2")
    token_limit = Column(Integer, default=4096)

    require_human_approval = Column(Boolean, default=True)
    playwright_headless = Column(Boolean, default=True)
    submission_concurrency = Column(Integer, default=1)
    max_retries = Column(Integer, default=2)

    enabled_job_sources = Column(
        JSON,
        default=lambda: ["remotive", "arbeitnow", "greenhouse_public", "manual", "demo_sandbox"],
    )
    discovery_schedule_cron = Column(String(100), default="0 */6 * * *")
    data_retention_days = Column(Integer, default=365)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Employer(Base):
    __tablename__ = "employers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    country = Column(String(100), index=True, default="United Kingdom")
    industry = Column(String(150), default="Cybersecurity & Technology")
    official_website = Column(String(500), default="")
    careers_website = Column(String(500), default="")
    locations = Column(JSON, default=list)
    company_size = Column(String(100), default="Not verified")
    overview = Column(Text, default="")
    sponsorship_capability_status = Column(String(100), default="Not verified")
    uk_licensed_sponsor = Column(Boolean, default=False)
    sponsorship_evidence_url = Column(String(500), default="")
    relocation_support_info = Column(Text, default="Not verified")
    hiring_process = Column(Text, default="")
    reputation_notes = Column(Text, default="")
    public_contacts = Column(JSON, default=list)
    citations = Column(JSON, default=list)
    is_watchlisted = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)
    last_checked_at = Column(DateTime(timezone=True), default=utc_now)


class JobVacancy(Base):
    __tablename__ = "job_vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    employer_name = Column(String(255), index=True, nullable=False)
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=True)
    original_url = Column(String(1000), nullable=False)
    provider_reference = Column(String(255), default="")
    dedup_signature = Column(String(128), index=True, nullable=False)

    location = Column(String(255), default="")
    city = Column(String(150), default="")
    country = Column(String(100), index=True, nullable=False)
    work_arrangement = Column(String(50), default="On-site")
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(20), default="GBP")
    salary_text = Column(String(255), default="Not specified")

    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    required_experience = Column(String(255), default="")
    education_requirements = Column(String(255), default="")
    language_requirements = Column(String(255), default="English")
    requires_non_english = Column(Boolean, default=False)
    mandatory_languages = Column(JSON, default=lambda: ["English"])

    employment_type = Column(String(100), default="Full-time")
    date_published = Column(String(100), default="")
    application_deadline = Column(String(100), nullable=True)
    source = Column(String(100), default="manual")
    last_verified_date = Column(DateTime(timezone=True), default=utc_now)

    job_status = Column(String(50), default="Active")
    is_expired = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)

    sponsorship_status = Column(String(100), default="Not verified")
    relocation_status = Column(String(100), default="Not verified")

    match_score = Column(Float, default=0.0)
    match_breakdown = Column(JSON, default=dict)
    visa_assessment = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class VisaCountryRule(Base):
    __tablename__ = "visa_country_rules"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), unique=True, index=True, nullable=False)
    is_priority = Column(Boolean, default=True)
    primary_visa_route = Column(String(255), nullable=False)
    authority_name = Column(String(255), nullable=False)
    official_source_url = Column(String(1000), nullable=False)
    sponsorship_required_for_candidate = Column(Boolean, default=True)
    current_candidate_eligibility_status = Column(String(255), default="")
    salary_threshold_info = Column(Text, default="")
    occupation_eligibility_info = Column(Text, default="")
    qualification_requirements = Column(Text, default="")
    labour_market_test_info = Column(Text, default="")
    language_requirements_info = Column(Text, default="")
    estimated_visa_costs = Column(String(255), default="")
    required_documents = Column(JSON, default=list)
    official_process_steps = Column(JSON, default=list)
    last_verified_date = Column(String(50), default="2026-11-03")


class CVVersion(Base):
    __tablename__ = "cv_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(255), nullable=False)
    is_master = Column(Boolean, default=False)
    target_job_id = Column(Integer, ForeignKey("job_vacancies.id"), nullable=True)
    source_filename = Column(String(255), default="")
    raw_text = Column(Text, nullable=False)
    structured_data = Column(JSON, default=dict)
    ats_keyword_coverage = Column(Float, default=0.0)
    matched_keywords = Column(JSON, default=list)
    missing_keywords = Column(JSON, default=list)
    missing_confirmations = Column(JSON, default=list)
    tailoring_notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CoverLetterVersion(Base):
    __tablename__ = "cover_letter_versions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    target_job_id = Column(Integer, ForeignKey("job_vacancies.id"), nullable=True)
    country_adapted = Column(String(100), default="United Kingdom")
    employer_name = Column(String(255), default="")
    cover_letter_text = Column(Text, nullable=False)
    supporting_statement = Column(Text, default="")
    screening_answers = Column(JSON, default=dict)
    star_examples = Column(JSON, default=list)
    work_eligibility_response = Column(Text, default="")
    relocation_response = Column(Text, default="")
    salary_expectation_response = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utc_now)


class ApplicationRecord(Base):
    __tablename__ = "application_records"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_vacancies.id"), nullable=False, index=True)
    employer_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    location = Column(String(255), default="")
    job_url = Column(String(1000), nullable=False)
    salary_text = Column(String(255), default="")

    cv_version_id = Column(Integer, ForeignKey("cv_versions.id"), nullable=True)
    cover_letter_id = Column(Integer, ForeignKey("cover_letter_versions.id"), nullable=True)

    stage = Column(String(60), index=True, default="Discovered")
    form_answers = Column(JSON, default=dict)
    detected_fields = Column(JSON, default=list)
    work_eligibility_statement = Column(Text, default="")
    sponsorship_summary = Column(Text, default="")
    unresolved_warnings = Column(JSON, default=list)

    human_approved = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_hash = Column(String(128), nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_reference = Column(String(255), nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    failure_reason = Column(Text, nullable=True)

    contact_info = Column(String(255), default="")
    interview_date = Column(String(100), nullable=True)
    follow_up_date = Column(String(100), nullable=True)
    offer_details = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)
    notes = Column(Text, default="")
    activity_history = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class InterviewPrepSession(Base):
    __tablename__ = "interview_prep_sessions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_vacancies.id"), nullable=True)
    role_track = Column(String(150), default="SOC Analyst")
    employer_name = Column(String(255), default="")
    employer_research = Column(Text, default="")
    role_questions = Column(JSON, default=list)
    technical_questions = Column(JSON, default=list)
    behavioural_questions = Column(JSON, default=list)
    star_examples = Column(JSON, default=list)
    questions_to_ask = Column(JSON, default=list)
    prep_checklist = Column(JSON, default=list)
    mock_transcript = Column(JSON, default=list)
    latest_feedback = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class ProjectDevelopmentTask(Base):
    __tablename__ = "project_development_tasks"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String(150), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="Feature")  # Feature, Bug, Security, TechDebt, Test
    priority = Column(String(30), default="High")
    status = Column(String(50), default="Completed")
    assigned_agent = Column(String(80), default="PROJECT_MANAGER")
    description = Column(Text, default="")
    verification_evidence = Column(Text, default="")
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(150), default="SYSTEM")
    action = Column(String(150), index=True, nullable=False)
    entity_type = Column(String(100), default="Application")
    entity_id = Column(String(100), default="")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
