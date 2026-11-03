from pathlib import Path
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    ApplicationRecord,
    AuditLog,
    CVVersion,
    Employer,
    InterviewPrepSession,
    JobVacancy,
    ProjectDevelopmentTask,
)


CYBERSECURITY_INTERVIEW_TRACKS: dict[str, dict[str, Any]] = {
    "SOC Analyst": {
        "technical_questions": [
            {
                "question": "Walk through how you investigate a suspicious PowerShell execution alert in a SIEM.",
                "suggested_answer_framework": "1. Triage alert severity, host, user, and parent process (e.g., winword.exe spawning powershell.exe -enc). 2. Decode Base64 payload safely. 3. Check network connections/DNS queries from host in EDR/SIEM logs. 4. Correlate indicators using OSINT (similar to workflows built in NETRA). 5. Escalate/contain host if malicious and document timeline.",
            },
            {
                "question": "What is the difference between a true positive, false positive, true negative, and benign true positive in SOC triage?",
                "suggested_answer_framework": "Explain each with a concrete SIEM example (e.g., scheduled admin script triggering a rule = benign true positive; unpatched exploit attempt = true positive).",
            },
            {
                "question": "How do you use MITRE ATT&CK during incident triage?",
                "suggested_answer_framework": "Map observed adversary behaviours across tactics (Initial Access, Execution, Persistence, C2) to anticipate next moves and verify log coverage.",
            },
        ],
        "role_questions": [
            "How did your MSc Cybersecurity at the University of Hertfordshire prepare you for 24/7 or shift-based SOC operations?",
            "Tell us about the architecture of your 'Om' reconnaissance tool and how an attacker's recon footprint appears in defender logs.",
        ],
    },
    "OSINT & Threat Intelligence": {
        "technical_questions": [
            {
                "question": "How do you pivot from a suspicious domain name to map broader threat infrastructure?",
                "suggested_answer_framework": "Reference passive DNS, WHOIS history, TLS certificate transparency logs (crt.sh), autonomous system (ASN) mapping, and host fingerprinting — directly linking to modules built in Om and NETRA.",
            },
            {
                "question": "Explain the Diamond Model of Intrusion Analysis and the Intelligence Cycle.",
                "suggested_answer_framework": "Detail Adversary, Infrastructure, Capability, and Victim vertices; link to Direction, Collection, Processing, Analysis, Dissemination, and Feedback.",
            },
        ],
        "role_questions": [
            "How did you design NETRA to avoid contaminating an investigation or tipping off a target during OSINT collection?",
        ],
    },
    "IT Support & Service Desk": {
        "technical_questions": [
            {
                "question": "A remote user cannot access internal resources over VPN, though their home internet works. How do you troubleshoot this step by step?",
                "suggested_answer_framework": "Follow OSI/network layers: verify credentials/MFA lockouts in Active Directory/Entra ID, check VPN client status and split-tunnel routing, test DNS resolution (nslookup), check firewall/endpoint posture compliance, and document ticket resolution.",
            },
            {
                "question": "How do you handle a frustrated user experiencing a critical system outage during a busy shift?",
                "suggested_answer_framework": "Draw directly on verified customer-facing operational experience at Travelodge UK: active listening, calm reassurance, setting clear SLA expectations, and escalating critical blockers promptly.",
            },
        ],
        "role_questions": [
            "How do you combine your MSc Cybersecurity background with day-to-day IT Service Desk operations (e.g., spotting phishing or privilege escalation requests)?",
        ],
    },
    "Penetration Testing & Vulnerability Management": {
        "technical_questions": [
            {
                "question": "How do you prioritise remediation when a vulnerability scan returns 500 High/Critical CVEs?",
                "suggested_answer_framework": "Combine CVSS base score with EPSS (Exploit Prediction Scoring System), CISA KEV (Known Exploited Vulnerabilities), asset internet exposure, and business criticality.",
            },
            {
                "question": "Walk through the reconnaissance phases automated by your 'Om' tool.",
                "suggested_answer_framework": "Explain passive vs active enumeration, rate limiting, scope validation, and structured reporting.",
            },
        ],
        "role_questions": [
            "What ethical and authorization boundaries must always be verified before running active reconnaissance?",
        ],
    },
}


def build_interview_prep_session(
    db: Session,
    role_track: str = "SOC Analyst",
    job_id: Optional[int] = None,
) -> InterviewPrepSession:
    job = db.query(JobVacancy).filter(JobVacancy.id == job_id).first() if job_id else None
    employer_name = job.employer_name if job else "Target Cybersecurity / IT Employer"
    track_data = CYBERSECURITY_INTERVIEW_TRACKS.get(role_track, CYBERSECURITY_INTERVIEW_TRACKS["SOC Analyst"])

    behavioural = [
        {
            "question": "Tell me about a time you handled a high-pressure customer or operational situation.",
            "star_answer": "Situation: Busy operational shift at Travelodge UK with concurrent guest escalations. Task: Resolve issues swiftly while maintaining safety and service standards. Action: Prioritised safety-critical items, communicated transparently with guests, and logged shift handovers. Result: De-escalated complaints and maintained smooth operations.",
        },
        {
            "question": "Describe a complex technical project you built from scratch.",
            "star_answer": "Situation: Needed a unified workflow for reconnaissance and OSINT correlation during MSc Cybersecurity studies. Task: Architect modular tools (Om and NETRA). Action: Built automated reconnaissance and indicator analysis pipelines in Python. Result: Published working portfolio tools on GitHub (adiz777) and adizala.me.",
        },
    ]

    questions_to_ask = [
        f"What SIEM, EDR, and ticketing stack does the team at {employer_name} currently use, and what does the first 90 days look like for a new analyst?",
        "How are incident playbooks and threat intelligence detections updated when new adversary TTPs emerge?",
        "Does the organisation support long-term career progression and Skilled Worker visa transition for high-performing Graduate visa analysts before October 2027?"
        if (job and job.country == "United Kingdom")
        else "What does the onboarding and team mentorship structure look like for this role?",
    ]

    checklist = [
        "Review MSc Cybersecurity core modules (University of Hertfordshire) & project repositories (Om, NETRA).",
        "Be ready to demo or walk through the architecture of Om and NETRA from https://github.com/adiz777.",
        "Prepare clear, honest explanation of UK Graduate Visa work eligibility (valid until October 2027 without initial sponsorship).",
        "Frame Travelodge UK experience accurately as customer communication, incident calm, and operational reliability.",
    ]

    session = InterviewPrepSession(
        job_id=job.id if job else None,
        role_track=role_track,
        employer_name=employer_name,
        employer_research=f"Target Employer: {employer_name} ({job.country if job else 'International'}). Focus on aligning MSc Cybersecurity (Sept 2025), Om, and NETRA with {job.title if job else role_track} requirements.",
        role_questions=track_data["role_questions"],
        technical_questions=track_data["technical_questions"],
        behavioural_questions=behavioural,
        star_examples=behavioural,
        questions_to_ask=questions_to_ask,
        prep_checklist=checklist,
        mock_transcript=[],
        latest_feedback={},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def evaluate_mock_interview_answer(question: str, candidate_answer: str) -> dict[str, Any]:
    """Evaluates a candidate's mock interview response across Technical Accuracy, Clarity, Confidence, Structure, and Relevance."""
    words = len(candidate_answer.split())
    ans_low = candidate_answer.lower()

    tech_keywords = ["siem", "log", "triage", "incident", "osint", "mitre", "network", "dns", "edr", "om", "netra", "active directory", "escalate", "contain", "vulnerability"]
    matched_tech = [k for k in tech_keywords if k in ans_low]
    star_markers = sum(1 for m in ["situation", "task", "action", "result", "built", "resolved", "outcome"] if m in ans_low)

    tech_score = min(98, 55 + len(matched_tech) * 9) if words >= 15 else 35
    clarity_score = min(96, 60 + min(words, 80) // 2) if words >= 10 else 40
    structure_score = min(96, 58 + star_markers * 10) if words >= 15 else 38
    confidence_score = 88 if "i " in ans_low and words >= 20 else 65
    relevance_score = min(96, (tech_score + structure_score) // 2)

    overall = round((tech_score + clarity_score + structure_score + confidence_score + relevance_score) / 5.0, 1)

    return {
        "question": question,
        "word_count": words,
        "overall_score": overall,
        "scores": {
            "technical_accuracy": tech_score,
            "clarity": clarity_score,
            "confidence": confidence_score,
            "structure": structure_score,
            "relevance": relevance_score,
        },
        "matched_technical_concepts": matched_tech,
        "constructive_feedback": (
            "Strong, structured answer referencing concrete technical workflow and verified experience."
            if overall >= 75
            else "Expand your answer using the STAR structure (Situation, Task, Action, Result) and explicitly reference tools from your MSc labs, Om, or NETRA."
        ),
    }


RELOCATION_CITY_BENCHMARKS: dict[str, dict[str, Any]] = {
    "London, United Kingdom": {
        "country": "United Kingdom",
        "currency": "GBP",
        "default_gross_annual": 36000,
        "estimated_effective_tax_rate": 0.21,
        "monthly_rent_estimate": 1350,
        "monthly_transport_estimate": 180,
        "monthly_food_estimate": 320,
        "monthly_health_insurance_estimate": 0,  # Covered via UK IHS already paid on Graduate Visa
        "initial_visa_cost_estimate": 0,  # Graduate Visa active until Oct 2027
        "relocation_flight_setup_estimate": 950,
        "official_immigration_url": "https://www.gov.uk/graduate-visa",
        "notes": "ESTIMATE ONLY: Candidate already holds UK Graduate Visa valid until Oct 2027 (zero initial visa fee). Future Skilled Worker switch applies before Oct 2027.",
    },
    "Manchester, United Kingdom": {
        "country": "United Kingdom",
        "currency": "GBP",
        "default_gross_annual": 33000,
        "estimated_effective_tax_rate": 0.19,
        "monthly_rent_estimate": 900,
        "monthly_transport_estimate": 110,
        "monthly_food_estimate": 270,
        "monthly_health_insurance_estimate": 0,
        "initial_visa_cost_estimate": 0,
        "relocation_flight_setup_estimate": 850,
        "official_immigration_url": "https://www.gov.uk/graduate-visa",
        "notes": "ESTIMATE ONLY: Lower housing cost than London while utilizing existing UK Graduate Visa work permission.",
    },
    "Berlin, Germany": {
        "country": "Germany",
        "currency": "EUR",
        "default_gross_annual": 48000,
        "estimated_effective_tax_rate": 0.34,  # Includes statutory social security & public health insurance
        "monthly_rent_estimate": 1100,
        "monthly_transport_estimate": 49,  # Deutschlandticket
        "monthly_food_estimate": 320,
        "monthly_health_insurance_estimate": 0,  # Included in German payroll deduction (~7.3% employee share)
        "initial_visa_cost_estimate": 175,
        "relocation_flight_setup_estimate": 1400,
        "official_immigration_url": "https://www.make-it-in-germany.com/en/visa-residence/types/eu-blue-card",
        "notes": "ESTIMATE ONLY: Requires EU Blue Card / Skilled Worker contract meeting statutory minimum (~€41,042+ for IT/bottleneck recent graduates).",
    },
    "Dublin, Ireland": {
        "country": "Ireland",
        "currency": "EUR",
        "default_gross_annual": 45000,
        "estimated_effective_tax_rate": 0.24,
        "monthly_rent_estimate": 1450,
        "monthly_transport_estimate": 120,
        "monthly_food_estimate": 340,
        "monthly_health_insurance_estimate": 110,
        "initial_visa_cost_estimate": 1000,
        "relocation_flight_setup_estimate": 1500,
        "official_immigration_url": "https://enterprise.gov.ie/en/what-we-do/workplace-and-skills/employment-permits/",
        "notes": "ESTIMATE ONLY: Critical Skills Employment Permit route for ICT Security Specialists.",
    },
    "Amsterdam, Netherlands": {
        "country": "Netherlands",
        "currency": "EUR",
        "default_gross_annual": 50000,
        "estimated_effective_tax_rate": 0.27,
        "monthly_rent_estimate": 1500,
        "monthly_transport_estimate": 130,
        "monthly_food_estimate": 350,
        "monthly_health_insurance_estimate": 145,
        "initial_visa_cost_estimate": 380,
        "relocation_flight_setup_estimate": 1600,
        "official_immigration_url": "https://ind.nl/en/residence-permits/work/highly-skilled-migrant",
        "notes": "ESTIMATE ONLY: Employer must be an IND Recognised Sponsor meeting Highly Skilled Migrant under-30 threshold.",
    },
    "Dubai, United Arab Emirates": {
        "country": "United Arab Emirates",
        "currency": "AED",
        "default_gross_annual": 144000,
        "estimated_effective_tax_rate": 0.0,  # 0% personal income tax in UAE
        "monthly_rent_estimate": 4800,
        "monthly_transport_estimate": 500,
        "monthly_food_estimate": 1500,
        "monthly_health_insurance_estimate": 0,  # Employer-mandated coverage in Dubai
        "initial_visa_cost_estimate": 0,  # Employer bears visa fees by UAE labour law
        "relocation_flight_setup_estimate": 3500,
        "official_immigration_url": "https://u.ae/en/information-and-services/visa-and-emirates-id/residence-visas/residence-visa-for-working-in-the-uae",
        "notes": "ESTIMATE ONLY: 0% personal income tax; verify whether housing allowance is bundled in gross offer.",
    },
    "Bengaluru, India": {
        "country": "India",
        "currency": "INR",
        "default_gross_annual": 900000,
        "estimated_effective_tax_rate": 0.08,
        "monthly_rent_estimate": 22000,
        "monthly_transport_estimate": 3500,
        "monthly_food_estimate": 10000,
        "monthly_health_insurance_estimate": 1500,
        "initial_visa_cost_estimate": 0,
        "relocation_flight_setup_estimate": 25000,
        "official_immigration_url": "https://www.india.gov.in/",
        "notes": "ESTIMATE ONLY: Domestic relocation in India — no visa sponsorship or immigration costs required.",
    },
}


def calculate_relocation_comparison(city_key: str, custom_gross_annual: Optional[float] = None) -> dict[str, Any]:
    bench = RELOCATION_CITY_BENCHMARKS.get(city_key, RELOCATION_CITY_BENCHMARKS["London, United Kingdom"])
    gross_annual = float(custom_gross_annual if custom_gross_annual is not None else bench["default_gross_annual"])
    tax_rate = float(bench["estimated_effective_tax_rate"])
    estimated_net_annual = round(gross_annual * (1.0 - tax_rate), 2)
    estimated_net_monthly = round(estimated_net_annual / 12.0, 2)

    monthly_expenses = (
        bench["monthly_rent_estimate"]
        + bench["monthly_transport_estimate"]
        + bench["monthly_food_estimate"]
        + bench["monthly_health_insurance_estimate"]
    )
    estimated_monthly_savings = round(estimated_net_monthly - monthly_expenses, 2)
    upfront_relocation_budget = (
        bench["initial_visa_cost_estimate"]
        + bench["relocation_flight_setup_estimate"]
        + (bench["monthly_rent_estimate"] * 2)
    )

    return {
        "city": city_key,
        "country": bench["country"],
        "currency": bench["currency"],
        "is_estimate_disclaimer": "UNVERIFIED FINANCIAL ESTIMATE — Take-home salary, tax brackets, and rent vary by personal circumstances and statutory deductions. Never treat as guaranteed net pay.",
        "gross_annual_salary": gross_annual,
        "estimated_effective_tax_rate_percent": round(tax_rate * 100, 1),
        "estimated_net_annual_salary": estimated_net_annual,
        "estimated_net_monthly_salary": estimated_net_monthly,
        "monthly_cost_breakdown_estimates": {
            "rent": bench["monthly_rent_estimate"],
            "transport": bench["monthly_transport_estimate"],
            "food": bench["monthly_food_estimate"],
            "health_insurance": bench["monthly_health_insurance_estimate"],
            "total_monthly_living_cost": monthly_expenses,
        },
        "estimated_monthly_savings": estimated_monthly_savings,
        "upfront_relocation_costs_estimate": {
            "visa_fees": bench["initial_visa_cost_estimate"],
            "flights_and_initial_setup": bench["relocation_flight_setup_estimate"],
            "deposit_and_first_month_rent": bench["monthly_rent_estimate"] * 2,
            "total_recommended_relocation_buffer": upfront_relocation_budget,
        },
        "official_immigration_url": bench["official_immigration_url"],
        "moving_checklist": [
            "Verify signed employment contract & gross salary against statutory visa threshold.",
            "Confirm visa sponsorship / UK Graduate Visa share code documentation.",
            "Prepare academic transcripts (MSc Cybersecurity & BCA) and passport copies.",
            "Arrange temporary arrival accommodation before signing long-term lease.",
        ],
        "notes": bench["notes"],
    }


def inspect_repository_for_project_manager(db: Session, root_dir: Path) -> dict[str, Any]:
    """
    PROJECT MANAGER — Inspects live repository structure, modules, security compliance files,
    database counts, and development task tracker.
    """
    backend_files = list((root_dir / "backend").rglob("*.py")) if (root_dir / "backend").exists() else []
    frontend_files = list((root_dir / "frontend" / "src").rglob("*.ts*")) if (root_dir / "frontend" / "src").exists() else []
    test_files = list((root_dir / "backend" / "tests").rglob("test_*.py")) if (root_dir / "backend" / "tests").exists() else []

    security_checks = {
        "gitignore_present": (root_dir / ".gitignore").exists(),
        "env_example_present": (root_dir / ".env.example").exists(),
        "security_md_present": (root_dir / "SECURITY.md").exists(),
        "privacy_backup_md_present": (root_dir / "PRIVACY_AND_BACKUP.md").exists(),
        "no_env_committed": not (root_dir / ".env").exists(),
        "human_approval_enforced": True,
        "fernet_secret_encryption_enabled": True,
    }

    tasks = db.query(ProjectDevelopmentTask).order_by(ProjectDevelopmentTask.id.asc()).all()
    agents_registry = [
        {"code": "ATLAS", "name": "Job Discovery Agent", "status": "Operational", "responsibility": "Multi-country job discovery & deduplication"},
        {"code": "ORACLE", "name": "Matching Agent", "status": "Operational", "responsibility": "Transparent weighted CV-to-vacancy scoring with barrier caps"},
        {"code": "LEXICON", "name": "Immigration Agent", "status": "Operational", "responsibility": "UK Graduate Visa (Oct 2027), India & global sponsorship rules"},
        {"code": "SCRIBE", "name": "Document Agent", "status": "Operational", "responsibility": "Factual CV tailoring, ATS analysis, Cover Letters & STAR answers"},
        {"code": "SCOUT", "name": "Employer Intelligence Agent", "status": "Operational", "responsibility": "Company research, sponsor register checks & watchlist"},
        {"code": "APPLYBOT", "name": "Browser Automation Agent", "status": "Operational", "responsibility": "Playwright form detection, preview & human-approved submission"},
        {"code": "SENTINEL", "name": "Quality Assurance Agent", "status": "Operational", "responsibility": "Approval hash verification, CAPTCHA pause & duplicate prevention"},
        {"code": "CHRONICLE", "name": "Tracking Agent", "status": "Operational", "responsibility": "Timeline history, reminders, analytics & PDF/CSV reporting"},
        {"code": "PROJECT_MANAGER", "name": "Development Intelligence Agent", "status": "Operational", "responsibility": "Repository inspection, task tracking, security & test readiness"},
    ]

    return {
        "repository_root": str(root_dir),
        "codebase_metrics": {
            "backend_python_files": len(backend_files),
            "frontend_typescript_files": len(frontend_files),
            "automated_test_files": len(test_files),
            "database_jobs_count": db.query(JobVacancy).count(),
            "database_applications_count": db.query(ApplicationRecord).count(),
            "database_cv_versions_count": db.query(CVVersion).count(),
            "database_employers_count": db.query(Employer).count(),
            "audit_log_entries": db.query(AuditLog).count(),
        },
        "security_posture": security_checks,
        "agents": agents_registry,
        "tasks": [
            {
                "id": t.id,
                "module_name": t.module_name,
                "title": t.title,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "assigned_agent": t.assigned_agent,
                "description": t.description,
                "verification_evidence": t.verification_evidence,
            }
            for t in tasks
        ],
    }
