import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services.seed_data import seed_initial_platform_data


TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE, future=True)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_clean_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestingSessionLocal()
    try:
        seed_initial_platform_data(db, fetch_live_jobs=False)
    finally:
        db.close()
    yield


def _create_sample_eligible_job(suffix: str = "1") -> int:
    resp = client.post(
        "/api/jobs",
        json={
            "title": f"Junior SOC & Threat Intelligence Analyst {suffix}",
            "employer_name": f"Cloudflare UK {suffix}",
            "original_url": f"https://boards.greenhouse.io/cloudflare/jobs/{suffix}",
            "country": "United Kingdom",
            "location": "London, United Kingdom",
            "description": "English-speaking SOC & Threat Intelligence role in London.",
            "required_skills": ["Cybersecurity", "SOC Operations", "SIEM", "OSINT", "Python"],
        },
    )
    return resp.json()["job"]["id"]


client = TestClient(app)


def test_scenario_1_uk_job_without_sponsorship_remains_eligible_on_graduate_visa():
    """1. UK job without sponsorship — must remain eligible while the Graduate visa is valid."""
    resp = client.post(
        "/api/jobs",
        json={
            "title": "Junior SOC Analyst",
            "employer_name": "UK Regional Cyber Ltd",
            "original_url": "https://example.com/uk-no-sponsor-job",
            "country": "United Kingdom",
            "description": "Entry-level SOC Analyst role in London. Please note we cannot sponsor visas at this time.",
            "required_skills": ["SOC", "SIEM", "Cybersecurity"],
        },
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["sponsorship_status"] == "No sponsorship"
    assert job["visa_assessment"]["candidate_eligible"] is True
    assert job["visa_assessment"]["uk_graduate_visa_applicable"] is True
    assert "2027" in job["visa_assessment"]["uk_graduate_visa_expiry"]
    assert job["match_score"] >= 60.0


def test_scenario_2_india_job_does_not_require_sponsorship():
    """2. India job — must not require employer visa sponsorship."""
    resp = client.post(
        "/api/jobs",
        json={
            "title": "Security Operations Analyst",
            "employer_name": "Mumbai Cyber Operations",
            "original_url": "https://example.com/india-job-1",
            "country": "India",
            "location": "Mumbai / Hybrid",
            "description": "SOC Analyst role in India supporting SIEM and threat hunting.",
            "required_skills": ["SOC", "SIEM", "Threat Intelligence"],
        },
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["visa_assessment"]["candidate_eligible"] is True
    assert job["visa_assessment"]["sponsorship_required_immediately"] is False
    assert job["sponsorship_status"] == "Confirmed"


def test_scenario_3_german_job_with_confirmed_sponsorship_evaluated_for_visa():
    """3. German job with confirmed sponsorship — must be evaluated for the relevant visa requirements."""
    resp = client.post(
        "/api/jobs",
        json={
            "title": "Threat Intelligence & OSINT Analyst",
            "employer_name": "Berlin Cyber GmbH",
            "original_url": "https://example.com/de-sponsored",
            "country": "Germany",
            "location": "Berlin, Germany",
            "description": "English is the working language. Visa sponsorship available under EU Blue Card along with relocation support.",
            "required_skills": ["OSINT", "Threat Intelligence", "Reconnaissance", "Python"],
        },
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["sponsorship_status"] == "Employer explicitly states sponsorship available"
    assert "EU Blue Card" in job["visa_assessment"]["current_visa_route"]
    assert job["visa_assessment"]["candidate_eligible"] is True


def test_scenario_4_german_job_no_sponsorship_evidence_flagged_unverified():
    """4. German job with no sponsorship evidence — must be flagged as unverified."""
    resp = client.post(
        "/api/jobs",
        json={
            "title": "Junior IT Support Engineer",
            "employer_name": "Frankfurt Systems GmbH",
            "original_url": "https://example.com/de-unverified",
            "country": "Germany",
            "location": "Frankfurt, Germany",
            "description": "English-speaking IT support role in Frankfurt.",
            "required_skills": ["IT Support", "Linux", "Troubleshooting"],
        },
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["sponsorship_status"] == "Not verified"
    assert any("Unverified" in c for c in job["match_breakdown"]["potential_concerns"])


def test_scenario_5_job_requiring_another_language_filtered_and_capped():
    """5. Job requiring another language — must be filtered out unless English is sufficient, and never hidden behind a high score."""
    resp = client.post(
        "/api/jobs",
        json={
            "title": "SOC Analyst (Fluent German Required)",
            "employer_name": "Stuttgart Security AG",
            "original_url": "https://example.com/de-fluent-german",
            "country": "Germany",
            "description": "SOC Analyst role. Fluent in German is mandatory for customer calls.",
            "required_skills": ["Cybersecurity", "SOC", "SIEM", "OSINT", "Python", "Linux"],
        },
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["requires_non_english"] is True
    assert job["match_breakdown"]["critical_barrier_triggered"] is True
    assert job["match_score"] <= 34.0

    # Check english_only filter excludes it
    filtered = client.get("/api/jobs?english_only=true").json()["jobs"]
    assert all(j["id"] != job["id"] for j in filtered)


def test_scenario_6_remote_job_included_when_eligible():
    """6. Remote job — must be included when otherwise eligible."""
    resp = client.post(
        "/api/jobs",
        json={
            "title": "Remote OSINT & Security Analyst",
            "employer_name": "UK Remote Cyber Ltd",
            "original_url": "https://example.com/uk-remote-osint",
            "country": "United Kingdom",
            "work_arrangement": "Remote",
            "description": "100% Remote UK role for an MSc Cybersecurity graduate skilled in OSINT and Reconnaissance.",
            "required_skills": ["OSINT", "Reconnaissance", "Cybersecurity"],
        },
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["match_breakdown"]["should_apply"] is True
    remote_list = client.get("/api/jobs?work_arrangement=Remote").json()["jobs"]
    assert any(j["id"] == job["id"] for j in remote_list)


def test_scenario_7_expired_vacancy_must_not_be_submitted():
    """7. Expired vacancy — must not be submitted."""
    job_resp = client.post(
        "/api/jobs",
        json={
            "title": "Expired SOC Role",
            "employer_name": "Old Employer Ltd",
            "original_url": "https://example.com/expired-soc",
            "country": "United Kingdom",
            "description": "SOC role in London.",
            "application_deadline": "2020-01-01",
            "is_expired": True,
        },
    )
    job_id = job_resp.json()["job"]["id"]
    prep_resp = client.post(f"/api/applications/prepare/{job_id}")
    app_id = prep_resp.json()["id"]
    client.post(f"/api/applications/{app_id}/approve")

    sub_resp = client.post(f"/api/applications/{app_id}/submit")
    assert sub_resp.json()["status"] == "blocked"
    assert "Expired vacancy blocked" in sub_resp.json()["reason"]


def test_scenario_8_duplicate_vacancy_and_duplicate_submission_blocked():
    """8. Duplicate vacancy — must not be ingested or submitted twice."""
    payload = {
        "title": "Unique Junior Penetration Tester",
        "employer_name": "RedTeam UK Ltd",
        "original_url": "https://example.com/redteam-uk-unique",
        "country": "United Kingdom",
        "location": "London",
        "description": "Junior penetration testing and reconnaissance role.",
        "required_skills": ["Penetration Testing", "Reconnaissance", "Python"],
    }
    first = client.post("/api/jobs", json=payload).json()
    second = client.post("/api/jobs", json=payload).json()
    assert first["is_new"] is True
    assert second["is_new"] is False
    assert second["duplicate_prevented"] is True
    assert first["job"]["id"] == second["job"]["id"]

    # Prepare, approve, submit once -> succeeds; second submit -> blocked
    job_id = first["job"]["id"]
    app_id = client.post(f"/api/applications/prepare/{job_id}").json()["id"]
    client.post(f"/api/applications/{app_id}/approve")
    sub1 = client.post(f"/api/applications/{app_id}/submit").json()
    assert sub1["status"] == "submitted"

    sub2 = client.post(f"/api/applications/{app_id}/submit").json()
    assert sub2["status"] == "blocked"
    assert "Duplicate submission blocked" in sub2["reason"]


def test_scenario_9_unapproved_application_must_never_be_submitted():
    """9. Unapproved application — must never be submitted."""
    job_id = _create_sample_eligible_job("s9")
    app_id = client.post(f"/api/applications/prepare/{job_id}").json()["id"]

    sub_resp = client.post(f"/api/applications/{app_id}/submit").json()
    assert sub_resp["status"] == "blocked"
    assert "Unapproved application blocked" in sub_resp["reason"]


def test_scenario_10_application_modified_after_approval_requires_fresh_approval():
    """10. Application modified after approval — must require fresh approval."""
    job_id = _create_sample_eligible_job("s10")
    app_id = client.post(f"/api/applications/prepare/{job_id}").json()["id"]

    approve_res = client.post(f"/api/applications/{app_id}/approve").json()
    assert approve_res["human_approved"] is True
    assert approve_res["approval_hash"] is not None

    # Modify work eligibility statement after approval
    mod_res = client.put(
        f"/api/applications/{app_id}/content",
        json={"work_eligibility_statement": "Modified statement requiring re-verification."},
    ).json()
    assert mod_res["human_approved"] is False
    assert mod_res["approval_hash"] is None
    assert mod_res["stage"] == "Awaiting approval"

    # Attempt submission without re-approving -> must be blocked
    sub_res = client.post(f"/api/applications/{app_id}/submit").json()
    assert sub_res["status"] == "blocked"


def test_scenario_11_captcha_encountered_pauses_for_human_intervention():
    """11. CAPTCHA encountered — automation must pause for human intervention."""
    job_id = _create_sample_eligible_job("s11")
    app_id = client.post(f"/api/applications/prepare/{job_id}").json()["id"]
    client.post(f"/api/applications/{app_id}/approve")

    sub_res = client.post(
        f"/api/applications/{app_id}/submit",
        json={"simulated_page_content": "Cloudflare Turnstile: Please complete this reCAPTCHA to verify you are human"},
    ).json()
    assert sub_res["status"] == "paused_human_intervention"
    assert sub_res["stage"] == "Needs human intervention"


def test_scenario_12_failed_submission_must_not_be_marked_successful():
    """12. Failed submission — must not be marked as successful."""
    job_id = _create_sample_eligible_job("s12")
    app_id = client.post(f"/api/applications/prepare/{job_id}").json()["id"]
    client.post(f"/api/applications/{app_id}/approve")

    sub_res = client.post(
        f"/api/applications/{app_id}/submit",
        json={"simulate_network_error": True},
    ).json()
    assert sub_res["status"] == "failed"
    assert sub_res["stage"] == "Failed"


def test_bulk_submission_engine_and_studios():
    """Tests CV tailoring, Cover Letter studio, Bulk Queue safeguards, Relocation, and Interview modules."""
    job_1 = _create_sample_eligible_job("b1")
    job_2 = _create_sample_eligible_job("b2")

    # Tailor CV & export PDF/DOCX
    cv_res = client.post(f"/api/cv/tailor/{job_1}").json()
    assert cv_res["id"] > 0
    pdf_res = client.get(f"/api/cv/{cv_res['id']}/export/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

    # Prepare 2 apps, approve only 1
    app1 = client.post(f"/api/applications/prepare/{job_1}").json()["id"]
    app2 = client.post(f"/api/applications/prepare/{job_2}").json()["id"]
    client.post(f"/api/applications/{app1}/approve")

    summary = client.get("/api/applications/bulk/summary").json()
    assert summary["applications_ready_to_submit_count"] == 1

    bulk_res = client.post(
        "/api/applications/bulk/submit-approved",
        json={"explicit_final_confirmation": True},
    ).json()
    assert bulk_res["submitted_count"] == 1

    # Relocation & Interview checks
    reloc = client.get("/api/relocation?city=London,%20United%20Kingdom").json()
    assert reloc["selected_city"]["country"] == "United Kingdom"
    assert "UNVERIFIED FINANCIAL ESTIMATE" in reloc["selected_city"]["is_estimate_disclaimer"]

    mock_eval = client.post(
        "/api/interviews/mock-evaluate",
        json={
            "question": "How do you investigate a SIEM alert?",
            "candidate_answer": "In this situation my task was to triage SIEM and EDR logs, check network DNS indicators using OSINT workflows built in NETRA and Om, and escalate the incident.",
        },
    ).json()
    assert mock_eval["overall_score"] >= 70


def test_authentication_and_secret_encryption():
    """Tests user authentication, invalid password rejection, and encrypted API key persistence."""
    bad = client.post("/api/auth/login", json={"email": "candidate@apply.local", "password": "WrongPassword"})
    assert bad.status_code == 401

    good = client.post(
        "/api/auth/login",
        json={"email": "candidate@apply.local", "password": "ChangeMeImmediately!2026"},
    )
    assert good.status_code == 200
    assert "access_token" in good.json()

    # Save Gemini key -> verify it is encrypted and never returned in plaintext
    upd = client.put(
        "/api/settings",
        json={"ai_provider": "gemini", "gemini_api_key": "test-secret-api-key-do-not-expose"},
    )
    assert upd.status_code == 200
    cfg = client.get("/api/settings").json()
    assert cfg["has_gemini_key"] is True
    assert "test-secret-api-key-do-not-expose" not in str(cfg)


def test_file_upload_validation_and_cv_extraction():
    """Tests valid TXT/DOCX upload and blocks disallowed file extensions."""
    bad_upload = client.post(
        "/api/cv/upload",
        files={"file": ("malicious.exe", b"MZ-binary-payload", "application/octet-stream")},
    )
    assert bad_upload.status_code == 400

    valid_cv_text = (
        b"Adi Zala\nMSc Cybersecurity - University of Hertfordshire (Sept 2025)\n"
        b"Skills: Cybersecurity, SOC Operations, SIEM, OSINT, Python, Linux\n"
        b"GitHub: https://github.com/adiz777 | Website: https://adizala.me\n"
    )
    good_upload = client.post(
        "/api/cv/upload",
        files={"file": ("master_cv.txt", valid_cv_text, "text/plain")},
    )
    assert good_upload.status_code == 200
    data = good_upload.json()
    assert "SIEM" in data["extracted_skills"]
    assert "OSINT" in data["extracted_skills"]


def test_reports_and_project_manager_inspection():
    """Tests CSV/PDF report exports and AI Project Manager repository telemetry."""
    csv_res = client.get("/api/reports/export/csv")
    assert csv_res.status_code == 200
    assert "Job ID,Title,Employer" in csv_res.text

    pdf_res = client.get("/api/reports/export/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

    pm = client.get("/api/project-manager").json()
    assert pm["security_posture"]["human_approval_enforced"] is True
    assert len(pm["agents"]) == 9


def test_multi_select_filtering_and_batch_actions():
    """Tests multi-country / multi-arrangement filtering and batch prepare/approve/submit."""
    job_a = _create_sample_eligible_job("ms_a")
    job_b = _create_sample_eligible_job("ms_b")

    # Multi-country filter
    multi_jobs = client.get("/api/jobs?country=United%20Kingdom,India&work_arrangement=Hybrid,Remote,On-site").json()
    assert multi_jobs["total"] >= 2

    # Batch prepare selected jobs
    prep_res = client.post("/api/applications/prepare-selected", json={"job_ids": [job_a, job_b]}).json()
    assert prep_res["prepared_count"] == 2
    app_ids = prep_res["application_ids"]
    assert len(app_ids) == 2

    # Batch approve selected applications
    app_res = client.post("/api/applications/approve-selected", json={"application_ids": app_ids}).json()
    assert app_res["approved_count"] == 2

    # Submit only the first selected application
    sub_res = client.post(
        "/api/applications/bulk/submit-approved",
        json={"explicit_final_confirmation": True, "selected_application_ids": [app_ids[0]]},
    ).json()
    assert sub_res["submitted_count"] == 1


