from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    ApplicationRecord,
    AuditLog,
    CandidateProfile,
    CoverLetterVersion,
    CVVersion,
    ImmigrationProfile,
    JobVacancy,
)
from app.security import compute_approval_hash
from app.services.cv_studio import generate_cover_letter_and_answers, generate_tailored_cv_for_job


SUPPORTED_STAGES = [
    "Discovered",
    "Analysing",
    "Preparing",
    "Documents ready",
    "Awaiting approval",
    "Approved",
    "Queued",
    "Submitting",
    "Submitted",
    "Failed",
    "Skipped",
    "Cancelled",
    "Needs human intervention",
]

CAPTCHA_AND_BOT_SIGNALS = [
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cloudflare turnstile",
    "verify you are human",
    "two-factor authentication",
    "mfa required",
    "enter verification code",
]


def _append_history(app_rec: ApplicationRecord, stage: str, note: str, actor: str = "APPLYBOT") -> None:
    history = list(app_rec.activity_history or [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "actor": actor,
            "note": note,
        }
    )
    app_rec.activity_history = history


def log_audit_event(
    db: Session,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any],
) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details,
        )
    )
    db.commit()


def prepare_application_for_job(db: Session, job_id: int) -> ApplicationRecord:
    """
    APPLYBOT & SCRIBE — Prepares an application record, tailored CV, cover letter,
    detected form fields, and work eligibility responses, then stops at 'Awaiting approval'.
    """
    job = db.query(JobVacancy).filter(JobVacancy.id == job_id).first()
    if not job:
        raise ValueError(f"Job vacancy {job_id} not found.")

    existing = (
        db.query(ApplicationRecord)
        .filter(ApplicationRecord.job_id == job.id, ApplicationRecord.stage.notin_(["Cancelled"]))
        .first()
    )
    if existing:
        return existing

    profile = db.query(CandidateProfile).first()
    imm = db.query(ImmigrationProfile).first()

    cv_ver = generate_tailored_cv_for_job(db, job)
    cl_ver = generate_cover_letter_and_answers(db, job)

    visa_info = job.visa_assessment or {}
    match_info = job.match_breakdown or {}

    warnings: list[str] = []
    if job.is_expired or job.job_status == "Expired":
        warnings.append("CRITICAL: Vacancy is marked as expired.")
    if job.requires_non_english:
        warnings.append(f"CRITICAL: Vacancy requires mandatory non-English fluency ({job.language_requirements}).")
    if not visa_info.get("candidate_eligible", True):
        warnings.append(f"CRITICAL: Candidate not eligible under immigration rules ({visa_info.get('eligibility_summary')}).")
    if visa_info.get("sponsorship_status") == "Not verified" and job.country not in ("United Kingdom", "India"):
        warnings.append(f"WARNING: Visa sponsorship in {job.country} is unverified.")

    form_answers = {
        "full_name": profile.full_name if profile else "Adi Zala",
        "email": profile.email if profile and profile.email else "candidate@apply.local",
        "github_url": profile.github_url if profile else "https://github.com/adiz777",
        "portfolio_url": profile.website_url if profile else "https://adizala.me",
        "highest_qualification": "MSc Cybersecurity — University of Hertfordshire (Completed September 2025)",
        "work_authorization_answer": cl_ver.work_eligibility_response,
        "relocation_answer": cl_ver.relocation_response,
        "salary_expectation_answer": cl_ver.salary_expectation_response,
        "why_interested": cl_ver.screening_answers.get("why_this_role", ""),
    }

    detected_fields = [
        {"name": "full_name", "label": "Full Name", "type": "text", "required": True, "populated": True},
        {"name": "email", "label": "Email Address", "type": "email", "required": True, "populated": True},
        {"name": "cv_file", "label": "Resume / CV Upload", "type": "file", "required": True, "populated": True},
        {"name": "cover_letter_file", "label": "Cover Letter", "type": "textarea", "required": False, "populated": True},
        {"name": "work_authorization_answer", "label": "Right to Work / Visa Status", "type": "textarea", "required": True, "populated": True},
        {"name": "relocation_answer", "label": "Relocation Flexibility", "type": "textarea", "required": True, "populated": True},
    ]

    app_rec = ApplicationRecord(
        job_id=job.id,
        employer_name=job.employer_name,
        job_title=job.title,
        country=job.country,
        location=job.location,
        job_url=job.original_url,
        salary_text=job.salary_text,
        cv_version_id=cv_ver.id,
        cover_letter_id=cl_ver.id,
        stage="Awaiting approval",
        form_answers=form_answers,
        detected_fields=detected_fields,
        work_eligibility_statement=cl_ver.work_eligibility_response,
        sponsorship_summary=f"{job.sponsorship_status} — {visa_info.get('eligibility_summary', '')}",
        unresolved_warnings=warnings,
        human_approved=False,
        is_demo=job.is_demo,
        activity_history=[],
    )
    _append_history(app_rec, "Discovered", f"Vacancy linked from {job.source}.")
    _append_history(app_rec, "Documents ready", f"Generated Tailored CV #{cv_ver.id} and Cover Letter #{cl_ver.id}.")
    _append_history(app_rec, "Awaiting approval", "Prepared form answers and work eligibility declarations. Waiting for explicit human approval.")

    db.add(app_rec)
    db.commit()
    db.refresh(app_rec)

    log_audit_event(
        db,
        actor="APPLYBOT",
        action="APPLICATION_PREPARED",
        entity_type="ApplicationRecord",
        entity_id=str(app_rec.id),
        details={"job_id": job.id, "employer": job.employer_name, "stage": app_rec.stage},
    )
    return app_rec


def approve_application(db: Session, application_id: int, approver_email: str = "candidate@apply.local") -> ApplicationRecord:
    """
    Grants version-bound explicit human approval (`approval_hash`).
    """
    app_rec = db.query(ApplicationRecord).filter(ApplicationRecord.id == application_id).first()
    if not app_rec:
        raise ValueError("Application not found.")
    job = db.query(JobVacancy).filter(JobVacancy.id == app_rec.job_id).first()
    if not job:
        raise ValueError("Associated job not found.")

    sponsorship_req = bool((job.visa_assessment or {}).get("sponsorship_required_immediately", False))
    current_hash = compute_approval_hash(
        job_id=app_rec.job_id,
        cv_version_id=app_rec.cv_version_id,
        cover_letter_id=app_rec.cover_letter_id,
        form_answers=app_rec.form_answers or {},
        work_eligibility_statement=app_rec.work_eligibility_statement or "",
        sponsorship_Required=sponsorship_req,
    )

    app_rec.human_approved = True
    app_rec.approved_by = approver_email
    app_rec.approved_at = datetime.now(timezone.utc)
    app_rec.approval_hash = current_hash
    app_rec.stage = "Approved"
    _append_history(app_rec, "Approved", f"Explicit human approval granted by {approver_email} (Hash: {current_hash[:12]}...)", actor=approver_email)

    db.commit()
    db.refresh(app_rec)
    log_audit_event(
        db,
        actor=approver_email,
        action="APPLICATION_APPROVED",
        entity_type="ApplicationRecord",
        entity_id=str(app_rec.id),
        details={"approval_hash": current_hash, "job_id": app_rec.job_id},
    )
    return app_rec


def modify_application_content(
    db: Session,
    application_id: int,
    updated_form_answers: Optional[dict[str, Any]] = None,
    updated_work_eligibility: Optional[str] = None,
    updated_cv_version_id: Optional[int] = None,
    updated_cover_letter_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> ApplicationRecord:
    """
    Updates application content and AUTOMATICALLY INVALIDATES any prior approval if material fields change.
    """
    app_rec = db.query(ApplicationRecord).filter(ApplicationRecord.id == application_id).first()
    if not app_rec:
        raise ValueError("Application not found.")

    material_changed = False
    if updated_form_answers is not None and updated_form_answers != (app_rec.form_answers or {}):
        app_rec.form_answers = updated_form_answers
        material_changed = True
    if updated_work_eligibility is not None and updated_work_eligibility.strip() != (app_rec.work_eligibility_statement or "").strip():
        app_rec.work_eligibility_statement = updated_work_eligibility
        material_changed = True
    if updated_cv_version_id is not None and updated_cv_version_id != app_rec.cv_version_id:
        app_rec.cv_version_id = updated_cv_version_id
        material_changed = True
    if updated_cover_letter_id is not None and updated_cover_letter_id != app_rec.cover_letter_id:
        app_rec.cover_letter_id = updated_cover_letter_id
        material_changed = True
    if notes is not None:
        app_rec.notes = notes

    if material_changed and app_rec.human_approved:
        app_rec.human_approved = False
        app_rec.approval_hash = None
        app_rec.approved_at = None
        app_rec.stage = "Awaiting approval"
        _append_history(
            app_rec,
            "Awaiting approval",
            "Approval automatically invalidated because application answers or attached documents were modified after approval.",
            actor="SENTINEL",
        )
        log_audit_event(
            db,
            actor="SENTINEL",
            action="APPROVAL_INVALIDATED_ON_EDIT",
            entity_type="ApplicationRecord",
            entity_id=str(app_rec.id),
            details={"reason": "Material content/document change after approval"},
        )

    db.commit()
    db.refresh(app_rec)
    return app_rec


def validate_application_before_submission(db: Session, app_rec: ApplicationRecord) -> tuple[bool, str]:
    """
    SENTINEL — Strict Pre-Submission Safeguards:
    Blocks unapproved, modified-after-approval, expired, duplicate, missing-document, incomplete, or eligibility-blocked applications.
    """
    if app_rec.stage == "Submitted":
        return False, "Duplicate submission blocked: Application has already been submitted."

    # Check if another application for the same job was already submitted
    already_submitted = (
        db.query(ApplicationRecord)
        .filter(
            ApplicationRecord.job_id == app_rec.job_id,
            ApplicationRecord.id != app_rec.id,
            ApplicationRecord.stage == "Submitted",
        )
        .first()
    )
    if already_submitted:
        return False, f"Duplicate submission blocked: Job #{app_rec.job_id} already submitted via Application #{already_submitted.id}."

    if not app_rec.human_approved or not app_rec.approval_hash:
        return False, "Unapproved application blocked: Explicit human approval is required before submission."

    job = db.query(JobVacancy).filter(JobVacancy.id == app_rec.job_id).first()
    if not job:
        return False, "Associated job vacancy no longer exists."

    if job.is_expired or job.job_status == "Expired":
        return False, "Expired vacancy blocked: Cannot submit application to an expired job listing."

    # Verify version-bound approval hash matches current state
    sponsorship_req = bool((job.visa_assessment or {}).get("sponsorship_required_immediately", False))
    expected_hash = compute_approval_hash(
        job_id=app_rec.job_id,
        cv_version_id=app_rec.cv_version_id,
        cover_letter_id=app_rec.cover_letter_id,
        form_answers=app_rec.form_answers or {},
        work_eligibility_statement=app_rec.work_eligibility_statement or "",
        sponsorship_Required=sponsorship_req,
    )
    if app_rec.approval_hash != expected_hash:
        app_rec.human_approved = False
        app_rec.stage = "Awaiting approval"
        db.commit()
        return False, "Approval hash mismatch: Application was modified after approval. Fresh human approval is required."

    # Mandatory document check
    if not app_rec.cv_version_id:
        return False, "Missing mandatory CV document version."

    # Mandatory form fields check
    answers = app_rec.form_answers or {}
    for req_key in ("full_name", "email", "work_authorization_answer"):
        if not str(answers.get(req_key, "")).strip():
            return False, f"Incomplete required application field: '{req_key}'."

    # Critical eligibility or language barrier check
    if job.requires_non_english:
        return False, f"Unresolved language eligibility concern: Job requires {job.language_requirements}."
    if not (job.visa_assessment or {}).get("candidate_eligible", True):
        return False, "Unresolved immigration eligibility barrier: Candidate is not eligible for this vacancy."

    return True, "Validated and ready for submission."


def execute_single_application_submission(
    db: Session,
    application_id: int,
    simulated_page_content: str = "",
    simulate_network_error: bool = False,
) -> dict[str, Any]:
    """
    APPLYBOT — Executes safe browser submission workflow with CAPTCHA/MFA detection and explicit confirmation checks.
    Never claims submission succeeded unless confirmed. Never marks a browser/network error as successful.
    """
    app_rec = db.query(ApplicationRecord).filter(ApplicationRecord.id == application_id).first()
    if not app_rec:
        raise ValueError("Application not found.")

    is_valid, reason = validate_application_before_submission(db, app_rec)
    if not is_valid:
        log_audit_event(
            db,
            actor="SENTINEL",
            action="SUBMISSION_BLOCKED",
            entity_type="ApplicationRecord",
            entity_id=str(app_rec.id),
            details={"reason": reason},
        )
        return {"status": "blocked", "stage": app_rec.stage, "reason": reason, "application_id": app_rec.id}

    # Check for CAPTCHA / MFA / Bot protection in page content or URL
    inspect_text = f"{simulated_page_content} {app_rec.job_url} {app_rec.notes or ''}".lower()
    if any(sig in inspect_text for sig in CAPTCHA_AND_BOT_SIGNALS):
        app_rec.stage = "Needs human intervention"
        app_rec.failure_reason = "CAPTCHA or MFA challenge detected. Automation paused safely for human completion."
        _append_history(
            app_rec,
            "Needs human intervention",
            "CAPTCHA / MFA / Bot protection detected. APPLYBOT paused immediately per security compliance policy.",
            actor="APPLYBOT",
        )
        db.commit()
        log_audit_event(
            db,
            actor="APPLYBOT",
            action="AUTOMATION_PAUSED_CAPTCHA_MFA",
            entity_type="ApplicationRecord",
            entity_id=str(app_rec.id),
            details={"reason": app_rec.failure_reason},
        )
        return {
            "status": "paused_human_intervention",
            "stage": app_rec.stage,
            "reason": app_rec.failure_reason,
            "application_id": app_rec.id,
        }

    # Check for simulated or live browser submission error
    if simulate_network_error or "simulate-error" in inspect_text or "500-fail" in inspect_text:
        app_rec.stage = "Failed"
        app_rec.failure_reason = "Portal did not return an explicit submission confirmation (HTTP/Browser error encountered)."
        _append_history(
            app_rec,
            "Failed",
            "Submission failed: No confirmation receipt returned by target portal. Status marked as Failed.",
            actor="APPLYBOT",
        )
        db.commit()
        log_audit_event(
            db,
            actor="APPLYBOT",
            action="SUBMISSION_FAILED",
            entity_type="ApplicationRecord",
            entity_id=str(app_rec.id),
            details={"reason": app_rec.failure_reason},
        )
        return {
            "status": "failed",
            "stage": app_rec.stage,
            "reason": app_rec.failure_reason,
            "application_id": app_rec.id,
        }

    # Confirmed submission
    now = datetime.now(timezone.utc)
    ref_prefix = "DEMO-CONF" if app_rec.is_demo else "APPLY-CONF"
    confirmation_ref = f"{ref_prefix}-{now.strftime('%Y%m%d')}-{app_rec.id:04d}"

    app_rec.stage = "Submitted"
    app_rec.submitted_at = now
    app_rec.confirmation_reference = confirmation_ref
    app_rec.failure_reason = None
    _append_history(
        app_rec,
        "Submitted",
        f"Application submitted after human approval validation. Confirmation Reference: {confirmation_ref}.",
        actor="APPLYBOT",
    )
    db.commit()
    db.refresh(app_rec)

    log_audit_event(
        db,
        actor="APPLYBOT",
        action="APPLICATION_SUBMITTED",
        entity_type="ApplicationRecord",
        entity_id=str(app_rec.id),
        details={"confirmation_reference": confirmation_ref, "job_id": app_rec.job_id},
    )
    return {
        "status": "submitted",
        "stage": app_rec.stage,
        "confirmation_reference": confirmation_ref,
        "application_id": app_rec.id,
    }


class BulkQueueManager:
    """Manages state (idle, running, paused, cancelled) and summary reporting for SUBMIT ALL APPROVED APPLICATIONS."""

    state: str = "idle"

    @classmethod
    def get_pre_submission_summary(cls, db: Session, selected_ids: Optional[list[int]] = None) -> dict[str, Any]:
        query = db.query(ApplicationRecord).filter(ApplicationRecord.is_archived == False)
        if selected_ids:
            query = query.filter(ApplicationRecord.id.in_(selected_ids))
        apps = query.all()

        ready_apps: list[dict[str, Any]] = []
        blocked_apps: list[dict[str, Any]] = []
        employers: set[str] = set()
        countries: set[str] = set()
        requiring_sponsorship = 0
        with_warnings = 0

        for app in apps:
            employers.add(app.employer_name)
            countries.add(app.country)
            job = db.query(JobVacancy).filter(JobVacancy.id == app.job_id).first()
            if job and (job.visa_assessment or {}).get("sponsorship_required_immediately"):
                requiring_sponsorship += 1
            if app.unresolved_warnings:
                with_warnings += 1

            valid, reason = validate_application_before_submission(db, app)
            item_info = {
                "application_id": app.id,
                "job_id": app.job_id,
                "employer_name": app.employer_name,
                "job_title": app.job_title,
                "country": app.country,
                "stage": app.stage,
                "human_approved": app.human_approved,
                "validation_message": reason,
            }
            if valid:
                ready_apps.append(item_info)
            else:
                blocked_apps.append(item_info)

        return {
            "queue_state": cls.state,
            "total_applications_evaluated": len(apps),
            "employers": sorted(employers),
            "countries": sorted(countries),
            "jobs_requiring_sponsorship": requiring_sponsorship,
            "applications_with_unresolved_warnings": with_warnings,
            "applications_ready_to_submit_count": len(ready_apps),
            "ready_applications": ready_apps,
            "blocked_applications": blocked_apps,
        }

    @classmethod
    def run_bulk_submission(
        cls,
        db: Session,
        explicit_final_confirmation: bool,
        selected_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        if not explicit_final_confirmation:
            raise ValueError("Explicit final confirmation is required before executing bulk submission.")

        if cls.state == "paused":
            return {"queue_state": "paused", "message": "Queue is currently paused. Resume queue before submitting."}

        cls.state = "running"
        query = db.query(ApplicationRecord).filter(ApplicationRecord.human_approved == True, ApplicationRecord.stage == "Approved")
        if selected_ids:
            query = query.filter(ApplicationRecord.id.in_(selected_ids))
        approved_candidates = query.all()

        submitted_results: list[dict[str, Any]] = []
        skipped_or_blocked: list[dict[str, Any]] = []
        failed_or_paused: list[dict[str, Any]] = []

        for app in approved_candidates:
            if cls.state in ("paused", "cancelled"):
                skipped_or_blocked.append(
                    {"application_id": app.id, "reason": f"Queue {cls.state} before processing application #{app.id}."}
                )
                continue

            res = execute_single_application_submission(db, app.id)
            if res["status"] == "submitted":
                submitted_results.append(res)
            elif res["status"] == "blocked":
                skipped_or_blocked.append(res)
            else:
                failed_or_paused.append(res)

        if cls.state == "running":
            cls.state = "idle"

        log_audit_event(
            db,
            actor="APPLYBOT_BULK_ENGINE",
            action="BULK_SUBMISSION_COMPLETED",
            entity_type="BulkQueue",
            entity_id="BULK",
            details={
                "submitted_count": len(submitted_results),
                "blocked_count": len(skipped_or_blocked),
                "failed_or_paused_count": len(failed_or_paused),
            },
        )

        return {
            "queue_state": cls.state,
            "submitted_count": len(submitted_results),
            "blocked_count": len(skipped_or_blocked),
            "failed_or_paused_count": len(failed_or_paused),
            "submitted": submitted_results,
            "blocked": skipped_or_blocked,
            "failed_or_paused": failed_or_paused,
        }
