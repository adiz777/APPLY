from sqlalchemy.orm import Session
from app.config import settings
from app.models import (
    CandidateProfile,
    CVVersion,
    Employer,
    ImmigrationProfile,
    JobVacancy,
    ProjectDevelopmentTask,
    RecruitmentPreferences,
    SystemSettingsConfig,
    UserAccount,
)
from app.security import hash_password
from app.services.cv_studio import build_master_cv_text, parse_cv_into_structured_profile
from app.services.job_discovery import INITIAL_JOB_CATEGORIES, ingest_job_vacancy
from app.services.visa_engine import seed_visa_country_rules


def seed_initial_platform_data(db: Session) -> None:
    """Seeds candidate profile, immigration baseline, visa rules, system settings, and clearly-labelled DEMO reference data."""
    # 1. Default User Account
    if not db.query(UserAccount).first():
        db.add(
            UserAccount(
                email=settings.apply_default_admin_email,
                password_hash=hash_password(settings.apply_default_admin_password),
                full_name="Adi Zala",
                is_active=True,
            )
        )
        db.commit()

    # 2. Candidate Profile (Verified from portfolio adizala.me, LinkedIn & GitHub adiz777)
    profile = db.query(CandidateProfile).first()
    if not profile:
        profile = CandidateProfile(
            full_name="Adityarajsinh (Adi) Zala",
            headline="MSc Cybersecurity Graduate | SOC Analyst, Threat Detection, OSINT & Reconnaissance",
            email="adizala7303@gmail.com",
            phone="",
            github_url="https://github.com/adiz777",
            website_url="https://adizala.me",
            linkedin_url="https://www.linkedin.com/in/adityarajsinh-zala",
            summary=(
                "MSc Cybersecurity graduate from the University of Hertfordshire (2024–September 2025) and BCA graduate "
                "from Bhavan's Shree H. J. Doshi Information Technology Institute, Saurashtra University (2020–2023). "
                "Creator of open-source security platforms including OM 2.0 (Automated Reconnaissance & Intelligence Platform), "
                "NETRA (Intelligence & Identity Investigation Workspace), and Agni (Cross-Platform Endpoint Defense & SOC Threat Detection), "
                "paired with customer-facing operational reliability at Travelodge UK."
            ),
            education=[
                {
                    "degree": "MSc Cybersecurity",
                    "institution": "University of Hertfordshire, United Kingdom",
                    "completion_date": "2024 – September 2025",
                    "verified": True,
                },
                {
                    "degree": "Bachelor of Computer Applications (BCA)",
                    "institution": "Bhavan's Shree H. J. Doshi Information Technology Institute, Saurashtra University",
                    "completion_date": "2020 – 2023",
                    "verified": True,
                },
            ],
            employment_history=[
                {
                    "role": "Customer Operations & Hospitality Team Member",
                    "employer": "Travelodge UK (Watford / United Kingdom)",
                    "period": "UK Operations Experience",
                    "category": "Customer-Facing Hospitality & Operational Experience (Non-Cybersecurity)",
                    "responsibilities": (
                        "Delivered high-pressure customer-facing service, front-desk incident triage, shift handover reporting, "
                        "and operational compliance in the UK. (Strictly classified as customer/operational experience, never misrepresented as commercial cybersecurity tenure.)"
                    ),
                }
            ],
            technical_skills=[
                "Cybersecurity",
                "SOC Operations",
                "Security Analyst Triage",
                "OSINT & Digital Investigations",
                "Penetration Testing & Reconnaissance",
                "Threat Intelligence & Detection",
                "Vulnerability Assessment",
                "IT Support & Service Desk",
                "Kali Linux & Debian Administration",
                "Windows & Active Directory",
                "Network Security (Nmap, Wireshark, TCP/IP, DNS)",
                "Web App Security (Burp Suite, SQLMap, WhatWeb, WafW00f)",
                "Python, Bash, TypeScript & SQL",
                "Docker & Cloudflare",
                "SIEM Log Analysis & System Hardening",
            ],
            technical_interests=[
                "Cybersecurity",
                "SOC and Security Analyst positions",
                "OSINT and digital investigations",
                "Penetration testing and reconnaissance",
                "IT Support and Service Desk",
                "Junior IT and Technology Analyst roles",
                "Security Operations",
                "Threat Intelligence",
            ],
            projects=[
                {
                    "name": "OM 2.0 — Automated Reconnaissance & Intelligence Platform",
                    "status": "Active (Python, Bash, SQLite, 8-View Web Dashboard)",
                    "url": "https://github.com/adiz777/Om",
                    "description": (
                        "Modular automated reconnaissance platform orchestrating 10 tools (Nmap, Amass, Sublist3r, WhatWeb, DNSRecon, "
                        "WafW00f, SSLScan, theHarvester, Gobuster, CMSeeK) with strict scope validation, evidence-graded output normalization, "
                        "SQLite scan history, session diffing, and HTML reporting."
                    ),
                },
                {
                    "name": "NETRA — Intelligence & Digital Investigation Platform",
                    "status": "Active (TypeScript / Web Intelligence Workspace)",
                    "url": "https://github.com/adiz777/NETRA",
                    "description": (
                        "Cybersecurity intelligence and digital investigation workspace supporting domain/IP intelligence, case management, "
                        "timelines, relationship graphing, and structured investigation reports."
                    ),
                },
                {
                    "name": "Agni — Cross-Platform Endpoint Defense & SOC Threat Detection",
                    "status": "Active / Developing (Python, React, TypeScript, Bash)",
                    "url": "https://github.com/adiz777/Agni",
                    "description": (
                        "Local-first threat detection and endpoint security operations platform featuring Agni-Core, Vayu, and Varuna modules "
                        "for real-time suspicious process/file monitoring and network anomaly detection."
                    ),
                },
            ],
            certifications=[],
            achievements=[
                "Completed MSc Cybersecurity at University of Hertfordshire (September 2025)",
                "Built and open-sourced OM 2.0, NETRA, and Agni across 220+ public repositories on GitHub (@adiz777)",
            ],
            languages=[{"language": "English", "proficiency": "Full Professional Working Proficiency"}],
            supporting_documents=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # 3. Immigration Profile
    imm = db.query(ImmigrationProfile).first()
    if not imm:
        imm = ImmigrationProfile(
            nationality="Indian",
            current_location="India",
            uk_immigration_status="Graduate visa",
            uk_visa_expiry_date="2027-10-31",
            uk_work_eligibility=(
                "Valid UK Graduate Visa until October 2027. Full right to work in the UK without employer sponsorship while valid. "
                "Prioritise employers capable of Skilled Worker sponsorship (New Entrant route) before October 2027."
            ),
            india_work_eligibility="Indian Citizen — Unrestricted right to work across India with no employer visa sponsorship required.",
            other_visas_held=[],
            relocation_readiness="Fully flexible: Remote, Hybrid, On-site, Domestic & International relocation.",
            notes="Always verify exact visa expiry date upon status updates.",
        )
        db.add(imm)
        db.commit()
        db.refresh(imm)

    # 4. Recruitment Preferences
    if not db.query(RecruitmentPreferences).first():
        db.add(
            RecruitmentPreferences(
                english_only=True,
                reject_mandatory_other_language=True,
                preferred_job_categories=INITIAL_JOB_CATEGORIES,
            )
        )
        db.commit()

    # 5. System Settings
    if not db.query(SystemSettingsConfig).first():
        db.add(SystemSettingsConfig())
        db.commit()

    # 6. Visa Country Rules
    seed_visa_country_rules(db)

    # 7. Master CV Version
    if not db.query(CVVersion).filter(CVVersion.is_master == True).first():
        master_text = build_master_cv_text(profile, imm)
        db.add(
            CVVersion(
                version_name="Master CV — Verified Baseline Profile",
                is_master=True,
                source_filename="initial_verified_profile.txt",
                raw_text=master_text,
                structured_data=parse_cv_into_structured_profile(master_text, profile),
                ats_keyword_coverage=100.0,
                matched_keywords=profile.technical_skills,
                missing_keywords=[],
                missing_confirmations=["Upload latest PDF/DOCX CV in CV Studio to sync exact Travelodge UK employment dates."],
                tailoring_notes="Initial Master CV constructed strictly from verified candidate profile.",
            )
        )
        db.commit()

    # 8. Seed Employers & Visibly Labelled [DEMO] Vacancies for Immediate Verification
    if db.query(Employer).count() == 0:
        demo_employers = [
            Employer(
                name="[DEMO] Aegis Cyber Defence UK Ltd",
                country="United Kingdom",
                industry="Managed Security Service Provider (MSSP) & SOC",
                official_website="https://example.com/aegis-uk-demo",
                careers_website="https://example.com/aegis-uk-demo/careers",
                locations=["London", "Reading", "Manchester"],
                company_size="250-500 employees",
                overview="[DEMO] UK-based 24/7 Managed SOC provider supporting enterprise SIEM, EDR, and threat intelligence.",
                sponsorship_capability_status="Employer sponsorship capability verified",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="Hybrid onboarding supported",
                hiring_process="1. CV Screen -> 2. Technical SOC Triage Assessment -> 3. Panel Interview",
                reputation_notes="[DEMO] Known for graduate SOC training pathways and New Entrant Skilled Worker transitions.",
                citations=[{"source": "GOV.UK Register of Licensed Sponsors (Demo Reference)", "checked_at": "2026-11-03"}],
                is_watchlisted=True,
                is_demo=True,
            ),
            Employer(
                name="[DEMO] Thames Valley IT Services",
                country="United Kingdom",
                industry="Managed IT & Service Desk",
                official_website="https://example.com/thames-it-demo",
                careers_website="https://example.com/thames-it-demo/jobs",
                locations=["Slough", "Hatfield"],
                company_size="50-150 employees",
                overview="[DEMO] Regional UK IT service desk and infrastructure support firm.",
                sponsorship_capability_status="No sponsorship",
                uk_licensed_sponsor=False,
                relocation_support_info="Domestic UK",
                hiring_process="1. Telephone Screen -> 2. Practical Troubleshooting Interview",
                reputation_notes="[DEMO] Does not hold a Skilled Worker licence, but hires candidates on valid Graduate visas.",
                citations=[{"source": "Employer Careers Page (Demo Reference)", "checked_at": "2026-11-03"}],
                is_watchlisted=False,
                is_demo=True,
            ),
            Employer(
                name="[DEMO] Sentinel Grid GmbH",
                country="Germany",
                industry="Threat Intelligence & Cloud Security",
                official_website="https://example.com/sentinel-berlin-demo",
                careers_website="https://example.com/sentinel-berlin-demo/jobs",
                locations=["Berlin", "Munich"],
                company_size="200-400 employees",
                overview="[DEMO] English-speaking cybersecurity engineering company in Berlin offering EU Blue Card sponsorship.",
                sponsorship_capability_status="Employer explicitly states sponsorship available",
                uk_licensed_sponsor=False,
                relocation_support_info="Offered — EU Blue Card visa support & relocation allowance",
                hiring_process="1. Recruiter Call -> 2. OSINT / Recon Case Study -> 3. Final Team Call",
                reputation_notes="[DEMO] English working environment; supports international relocation.",
                citations=[{"source": "Make it in Germany / Company Careers (Demo Reference)", "checked_at": "2026-11-03"}],
                is_watchlisted=True,
                is_demo=True,
            ),
            Employer(
                name="[DEMO] BharatSec Infotech Pvt Ltd",
                country="India",
                industry="Cybersecurity & SOC Consulting",
                official_website="https://example.com/bharatsec-demo",
                careers_website="https://example.com/bharatsec-demo/careers",
                locations=["Bengaluru", "Hyderabad", "Pune", "Remote India"],
                company_size="500-1000 employees",
                overview="[DEMO] Indian cybersecurity operations and vulnerability management consultancy.",
                sponsorship_capability_status="Confirmed",
                uk_licensed_sponsor=False,
                relocation_support_info="Domestic relocation or Remote across India",
                hiring_process="1. Technical Screening -> 2. SOC & VAPT Interview -> 3. HR Offer",
                reputation_notes="[DEMO] Immediate onboarding for Indian citizens.",
                citations=[{"source": "Direct Careers Portal (Demo Reference)", "checked_at": "2026-11-03"}],
                is_watchlisted=True,
                is_demo=True,
            ),
        ]
        for emp in demo_employers:
            db.add(emp)
        db.commit()

    if db.query(JobVacancy).count() == 0:
        demo_jobs = [
            {
                "title": "[DEMO] Junior SOC & Threat Intelligence Analyst",
                "employer_name": "[DEMO] Aegis Cyber Defence UK Ltd",
                "original_url": "https://example.com/aegis-uk-demo/jobs/soc-analyst-01",
                "country": "United Kingdom",
                "location": "London / Hybrid, United Kingdom",
                "city": "London",
                "work_arrangement": "Hybrid",
                "salary_min": 34000,
                "salary_max": 38000,
                "salary_currency": "GBP",
                "salary_text": "£34,000 - £38,000 per annum",
                "description": (
                    "[DEMO] Join our 24/7 Security Operations Centre in London (Hybrid). Ideal for an MSc Cybersecurity graduate "
                    "with hands-on experience in SIEM log triage, OSINT investigations, reconnaissance tooling, and incident response. "
                    "English is our working language. Licensed UK Skilled Worker sponsor for long-term career progression."
                ),
                "required_skills": ["Cybersecurity", "SOC Operations", "SIEM", "OSINT", "Incident Response", "Python", "Linux"],
                "explicit_sponsorship_hint": "Employer sponsorship capability verified",
                "source": "demo_sandbox",
                "is_demo": True,
            },
            {
                "title": "[DEMO] Graduate IT Support & Service Desk Analyst",
                "employer_name": "[DEMO] Thames Valley IT Services",
                "original_url": "https://example.com/thames-it-demo/jobs/it-support-02",
                "country": "United Kingdom",
                "location": "Hatfield, United Kingdom",
                "city": "Hatfield",
                "work_arrangement": "On-site",
                "salary_min": 28000,
                "salary_max": 31000,
                "salary_currency": "GBP",
                "salary_text": "£28,000 - £31,000 per annum",
                "description": (
                    "[DEMO] 1st/2nd Line IT Support and Service Desk Analyst supporting Windows, Active Directory, Linux, and network troubleshooting. "
                    "Strong customer-facing communication required. Note: We do not offer visa sponsorship, but candidates with an existing valid "
                    "UK Graduate Visa right to work are welcome to apply."
                ),
                "required_skills": ["IT Support", "Service Desk", "Troubleshooting", "Active Directory", "Network Security", "Linux"],
                "explicit_sponsorship_hint": "No sponsorship",
                "source": "demo_sandbox",
                "is_demo": True,
            },
            {
                "title": "[DEMO] Junior Security & OSINT Analyst (Visa Sponsorship Provided)",
                "employer_name": "[DEMO] Sentinel Grid GmbH",
                "original_url": "https://example.com/sentinel-berlin-demo/jobs/osint-berlin-03",
                "country": "Germany",
                "location": "Berlin, Germany",
                "city": "Berlin",
                "work_arrangement": "Hybrid",
                "salary_min": 46000,
                "salary_max": 52000,
                "salary_currency": "EUR",
                "salary_text": "€46,000 - €52,000 gross/year",
                "description": (
                    "[DEMO] English is the working language in our Berlin security engineering team (no German required). "
                    "Visa sponsorship available under the German EU Blue Card route along with relocation assistance. "
                    "Responsibilities include automated reconnaissance, OSINT threat intelligence tracking, and vulnerability triage."
                ),
                "required_skills": ["OSINT", "Reconnaissance", "Threat Intelligence", "Python", "Vulnerability Assessment", "Cybersecurity"],
                "explicit_sponsorship_hint": "Employer explicitly states sponsorship available",
                "relocation_status": "Offered",
                "source": "demo_sandbox",
                "is_demo": True,
            },
            {
                "title": "[DEMO] Cyber Security Analyst — India SOC (Remote / Bengaluru)",
                "employer_name": "[DEMO] BharatSec Infotech Pvt Ltd",
                "original_url": "https://example.com/bharatsec-demo/jobs/india-soc-04",
                "country": "India",
                "location": "Bengaluru / Remote, India",
                "city": "Bengaluru",
                "work_arrangement": "Remote",
                "salary_min": 800000,
                "salary_max": 1200000,
                "salary_currency": "INR",
                "salary_text": "₹8,00,000 - ₹12,00,000 LPA",
                "description": (
                    "[DEMO] Seeking a Cybersecurity & SOC Analyst in India (Remote or Bengaluru hybrid). "
                    "Work on SIEM alert triage, vulnerability scanning, penetration testing reconnaissance, and threat intelligence."
                ),
                "required_skills": ["Cybersecurity", "SOC", "SIEM", "Vulnerability Assessment", "Reconnaissance", "Threat Intelligence"],
                "source": "demo_sandbox",
                "is_demo": True,
            },
            {
                "title": "[DEMO] IT Security Consultant (Fluent C1 German Required)",
                "employer_name": "[DEMO] Munich Mittelstand IT GmbH",
                "original_url": "https://example.com/munich-it-demo/jobs/de-c1-05",
                "country": "Germany",
                "location": "Munich, Germany",
                "city": "Munich",
                "work_arrangement": "On-site",
                "salary_min": 48000,
                "salary_max": 54000,
                "salary_currency": "EUR",
                "salary_text": "€48,000 - €54,000",
                "description": (
                    "[DEMO] Security Consultant role in Munich. Fluent German is mandatory (Deutschkenntnisse C1 erforderlich) "
                    "for client-facing documentation. Sponsorship is not verified."
                ),
                "required_skills": ["Cybersecurity", "Network Security"],
                "language_requirements": "German C1 mandatory",
                "source": "demo_sandbox",
                "is_demo": True,
            },
        ]
        for j in demo_jobs:
            ingest_job_vacancy(db=db, **j)

    # 9. Seed AI Project Manager Development Tasks
    if db.query(ProjectDevelopmentTask).count() == 0:
        tasks = [
            ProjectDevelopmentTask(
                module_name="Phase 1 — Foundation",
                title="FastAPI Backend, SQLAlchemy DB, Bcrypt/JWT Auth & Fernet Secret Encryption",
                category="Feature",
                priority="Critical",
                status="Completed",
                assigned_agent="PROJECT_MANAGER",
                description="Core database models, authentication, encrypted API key storage, and candidate profile seeding.",
                verification_evidence="Verified via automated pytest suite.",
            ),
            ProjectDevelopmentTask(
                module_name="Phase 2 — ATLAS & ORACLE",
                title="Global Job Discovery, Deduplication & Weighted Matching with Barrier Caps",
                category="Feature",
                priority="Critical",
                status="Completed",
                assigned_agent="ATLAS",
                description="Multi-country discovery engine, duplicate signature check, and transparent matching model.",
                verification_evidence="Verified language & immigration barrier cap rules.",
            ),
            ProjectDevelopmentTask(
                module_name="Phase 3 — LEXICON",
                title="UK Graduate Visa (Oct 2027), India Domestic & Global Sponsorship Intelligence",
                category="Feature",
                priority="Critical",
                status="Completed",
                assigned_agent="LEXICON",
                description="Authoritative government sources and 8-tier sponsorship classification.",
                verification_evidence="Tested UK no-sponsorship eligibility vs German sponsored/unverified rules.",
            ),
            ProjectDevelopmentTask(
                module_name="Phase 4 — SCRIBE",
                title="CV Studio & Cover Letter Studio with Factual Integrity & PDF/DOCX Export",
                category="Feature",
                priority="High",
                status="Completed",
                assigned_agent="SCRIBE",
                description="PDF/DOCX/TXT ingestion, Master CV management, side-by-side comparison, and factual tailoring.",
                verification_evidence="Verified PDF/DOCX generation and zero experience fabrication.",
            ),
            ProjectDevelopmentTask(
                module_name="Phase 6 & 7 — APPLYBOT & SENTINEL",
                title="Version-Bound Human Approval Checkpoints, CAPTCHA Pause & Bulk Submission Engine",
                category="Security",
                priority="Critical",
                status="Completed",
                assigned_agent="SENTINEL",
                description="SHA-256 approval hash invalidation on edit, CAPTCHA pause to Needs human intervention, and Bulk Approved queue.",
                verification_evidence="All 12 mandatory QA & security safeguard scenarios tested.",
            ),
        ]
        for t in tasks:
            db.add(t)
        db.commit()
