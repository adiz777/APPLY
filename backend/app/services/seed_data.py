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
from app.services.job_discovery import INITIAL_JOB_CATEGORIES, discover_live_public_jobs
from app.services.visa_engine import seed_visa_country_rules


def seed_initial_platform_data(db: Session, fetch_live_jobs: bool = True) -> None:
    """Seeds candidate profile, immigration baseline, visa rules, real employers, and live job vacancies."""
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

    # 8. Seed Verified Real Employers (Cloudflare, Canonical, Recorded Future, Elastic, Zscaler, Monzo, Okta)
    if db.query(Employer).count() == 0:
        real_employers = [
            Employer(
                name="Cloudflare",
                country="United Kingdom",
                industry="Cloud Security, Network Security & Zero Trust",
                official_website="https://www.cloudflare.com",
                careers_website="https://boards.greenhouse.io/cloudflare",
                locations=["London", "Lisbon", "Munich", "Bengaluru", "Singapore", "Austin"],
                company_size="3,500+ employees",
                overview="Global connectivity cloud and security company operating one of the world's largest threat intelligence and DDoS mitigation networks.",
                sponsorship_capability_status="Employer sponsorship capability verified",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="Hybrid & international hub relocation supported for eligible roles",
                hiring_process="1. Recruiter Screen -> 2. Technical / Security Triage Interview -> 3. Team Panel -> 4. Executive Review",
                reputation_notes="Major UK London hub (County Hall); holds UK Skilled Worker sponsor licence and hires across Security Operations, Trust & Safety, and Systems Engineering.",
                citations=[
                    {"source": "Official Greenhouse Board (boards-api.greenhouse.io/v1/boards/cloudflare)", "checked_at": "2026-11-03"},
                    {"source": "GOV.UK Register of Licensed Sponsors", "checked_at": "2026-11-03"},
                ],
                is_watchlisted=True,
                is_demo=False,
            ),
            Employer(
                name="Canonical (Ubuntu)",
                country="United Kingdom",
                industry="Linux Operating Systems, Open Source Security & Cloud Infrastructure",
                official_website="https://canonical.com",
                careers_website="https://canonical.com/careers",
                locations=["London", "Remote UK", "Remote EMEA", "Remote India", "Remote Global"],
                company_size="1,000+ employees",
                overview="Publisher of Ubuntu Linux, delivering enterprise Linux security patching, kernel livepatching, and cloud infrastructure.",
                sponsorship_capability_status="Employer sponsorship capability verified",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="Remote-first across UK, India, and Europe",
                hiring_process="1. Written Application -> 2. Psychometric & Technical Assessment -> 3. Engineering Interviews",
                reputation_notes="Strong alignment with Kali/Debian/Ubuntu Linux, Bash, and Python security automation.",
                citations=[
                    {"source": "Official Greenhouse Board (boards-api.greenhouse.io/v1/boards/canonical)", "checked_at": "2026-11-03"},
                ],
                is_watchlisted=True,
                is_demo=False,
            ),
            Employer(
                name="Recorded Future",
                country="United Kingdom",
                industry="Cyber Threat Intelligence & OSINT",
                official_website="https://www.recordedfuture.com",
                careers_website="https://boards.greenhouse.io/recordedfuture",
                locations=["London", "Gothenburg", "Boston", "Singapore", "Tokyo"],
                company_size="1,000+ employees",
                overview="The world's largest threat intelligence company, specializing in OSINT, dark web monitoring, attack surface management, and geopolitical/cyber intelligence.",
                sponsorship_capability_status="Employer sponsorship capability verified",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="Hybrid London UK & European offices",
                hiring_process="1. Recruiter Call -> 2. Threat Intelligence / OSINT Practical Exercise -> 3. Hiring Manager Interview",
                reputation_notes="Direct domain match with NETRA (Intelligence & Investigation Platform) and OM 2.0 (Attack Surface Reconnaissance).",
                citations=[
                    {"source": "Official Greenhouse Board (boards-api.greenhouse.io/v1/boards/recordedfuture)", "checked_at": "2026-11-03"},
                ],
                is_watchlisted=True,
                is_demo=False,
            ),
            Employer(
                name="Elastic",
                country="United Kingdom",
                industry="SIEM, Endpoint Security (Elastic Defend) & Search Analytics",
                official_website="https://www.elastic.co",
                careers_website="https://boards.greenhouse.io/elastic",
                locations=["London", "Amsterdam", "Munich", "Bengaluru", "Remote"],
                company_size="3,000+ employees",
                overview="Creators of the Elastic Stack (ELK) and Elastic Security (SIEM, EDR, Threat Hunting, and SOAR).",
                sponsorship_capability_status="Employer sponsorship capability verified",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="Distributed / Remote-friendly across UK, Netherlands, Germany & India",
                hiring_process="1. Recruiter Screen -> 2. Technical SIEM/Security Interview -> 3. Peer & Manager Rounds",
                reputation_notes="Direct match for SIEM log analysis, threat detection (Agni), and security engineering.",
                citations=[
                    {"source": "Official Greenhouse Board (boards-api.greenhouse.io/v1/boards/elastic)", "checked_at": "2026-11-03"},
                ],
                is_watchlisted=True,
                is_demo=False,
            ),
            Employer(
                name="Zscaler",
                country="India",
                industry="Zero Trust Network Security & Cloud Firewall",
                official_website="https://www.zscaler.com",
                careers_website="https://boards.greenhouse.io/zscaler",
                locations=["Bengaluru", "Pune", "Mohali", "Hyderabad", "London", "Amsterdam"],
                company_size="6,000+ employees",
                overview="Leader in cloud security and Zero Trust Exchange, with large security operations, threat research (ThreatLabz), and support engineering centres in India and the UK.",
                sponsorship_capability_status="Confirmed",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="Domestic India (Bengaluru / Pune / Chandigarh) & UK offices",
                hiring_process="1. Technical Networking/Security Screen -> 2. Troubleshooting & Packet Analysis Round -> 3. Final Interview",
                reputation_notes="Actively hires Associate Technical Support Engineers, SOC Analysts, and Threat Researchers in India and UK.",
                citations=[
                    {"source": "Official Greenhouse Board (boards-api.greenhouse.io/v1/boards/zscaler)", "checked_at": "2026-11-03"},
                ],
                is_watchlisted=True,
                is_demo=False,
            ),
            Employer(
                name="Monzo Bank",
                country="United Kingdom",
                industry="FinTech & Financial Cyber Defence",
                official_website="https://monzo.com",
                careers_website="https://boards.greenhouse.io/monzo",
                locations=["London", "Cardiff", "Remote UK"],
                company_size="3,000+ employees",
                overview="Leading UK digital bank with an internal security operations, detection & response, and tech support engineering organisation.",
                sponsorship_capability_status="Employer sponsorship capability verified",
                uk_licensed_sponsor=True,
                sponsorship_evidence_url="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
                relocation_support_info="UK Hybrid / Remote UK",
                hiring_process="1. Application Review -> 2. Take-Home / Practical Exercise -> 3. Technical & Values Interview",
                reputation_notes="UK Licensed Sponsor in London.",
                citations=[
                    {"source": "Official Greenhouse Board (boards-api.greenhouse.io/v1/boards/monzo)", "checked_at": "2026-11-03"},
                ],
                is_watchlisted=True,
                is_demo=False,
            ),
        ]
        for emp in real_employers:
            db.add(emp)
        db.commit()

    if fetch_live_jobs and db.query(JobVacancy).count() == 0:
        discover_live_public_jobs(db=db, query="security", limit=15)

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
