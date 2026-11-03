import io
import re
from pathlib import Path
from typing import Any, Optional
from docx import Document
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session
from app.config import EXPORTS_DIR
from app.models import CandidateProfile, CoverLetterVersion, CVVersion, ImmigrationProfile, JobVacancy
from app.services.ai_provider import AIProviderOrchestrator


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def extract_text_from_upload(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension '{ext}'. Allowed: .pdf, .docx, .txt")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds maximum allowed size of 10 MB.")

    if ext == ".txt":
        return content.decode("utf-8", errors="replace").strip()

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    if ext == ".docx":
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()

    return ""


def parse_cv_into_structured_profile(raw_text: str, base_profile: Optional[CandidateProfile] = None) -> dict[str, Any]:
    """
    Extracts structured sections from raw CV text while preserving verified candidate facts.
    Never invents qualifications, certifications, or commercial dates.
    """
    text_lower = raw_text.lower()
    known_skills = [
        "Cybersecurity",
        "SOC Operations",
        "SIEM",
        "OSINT",
        "Reconnaissance",
        "Penetration Testing",
        "Threat Intelligence",
        "Incident Response",
        "Vulnerability Assessment",
        "Network Security",
        "Digital Forensics",
        "Python",
        "Linux",
        "Bash",
        "IT Support",
        "Service Desk",
        "Active Directory",
        "Windows Server",
        "TCP/IP",
        "Wireshark",
        "Nmap",
        "Burp Suite",
    ]
    extracted_skills = [s for s in known_skills if s.lower() in text_lower]
    if base_profile and base_profile.technical_skills:
        for s in base_profile.technical_skills:
            if s not in extracted_skills:
                extracted_skills.append(s)

    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw_text)
    github_match = re.search(r"https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+", raw_text)
    website_match = re.search(r"https?://(?:www\.)?adizala\.me[^\s]*", raw_text)

    return {
        "full_name": base_profile.full_name if base_profile else "Adi Zala",
        "email": emails[0] if emails else (base_profile.email if base_profile else ""),
        "github_url": github_match.group(0) if github_match else (base_profile.github_url if base_profile else "https://github.com/adiz777"),
        "website_url": website_match.group(0) if website_match else (base_profile.website_url if base_profile else "https://adizala.me"),
        "education": base_profile.education if base_profile else [],
        "employment_history": base_profile.employment_history if base_profile else [],
        "technical_skills": extracted_skills,
        "projects": base_profile.projects if base_profile else [],
        "certifications": base_profile.certifications if base_profile else [],
        "raw_character_count": len(raw_text),
    }


def build_master_cv_text(profile: CandidateProfile, imm: Optional[ImmigrationProfile]) -> str:
    edu_lines = []
    for e in profile.education or []:
        edu_lines.append(f"- {e.get('degree')} — {e.get('institution')} ({e.get('completion_date')})")

    proj_lines = []
    for p in profile.projects or []:
        proj_lines.append(f"- {p.get('name')} ({p.get('status', 'Active')}): {p.get('description')}")

    emp_lines = []
    for w in profile.employment_history or []:
        emp_lines.append(f"- {w.get('role')} | {w.get('employer')} ({w.get('period')}): {w.get('responsibilities')}")

    skills_str = ", ".join(profile.technical_skills or [])
    uk_elig = (
        f"UK Graduate Visa valid until {imm.uk_visa_expiry_date} (Right to work in UK without initial sponsorship); Indian Citizen (Unrestricted right to work in India)."
        if imm
        else "UK Graduate Visa (valid until Oct 2027) & Indian National."
    )

    return (
        f"{profile.full_name}\n"
        f"{profile.headline}\n"
        f"GitHub: {profile.github_url} | Website: {profile.website_url}\n"
        f"Work Eligibility: {uk_elig}\n\n"
        f"PROFESSIONAL SUMMARY\n"
        f"{profile.summary}\n\n"
        f"TECHNICAL SKILLS\n"
        f"{skills_str}\n\n"
        f"EDUCATION\n"
        + "\n".join(edu_lines)
        + "\n\nSECURITY & INTELLIGENCE PROJECTS\n"
        + "\n".join(proj_lines)
        + "\n\nEMPLOYMENT & OPERATIONAL EXPERIENCE\n"
        + "\n".join(emp_lines)
    )


def generate_tailored_cv_for_job(db: Session, job: JobVacancy) -> CVVersion:
    """
    SCRIBE — Tailors Master CV for a specific job vacancy.
    Strictly preserves factual accuracy: never invents employment, certifications, skills, or dates.
    Highlights missing keywords for human confirmation.
    """
    profile = db.query(CandidateProfile).first()
    imm = db.query(ImmigrationProfile).first()
    master_cv = db.query(CVVersion).filter(CVVersion.is_master == True).first()

    candidate_skills = list(profile.technical_skills if profile and profile.technical_skills else [])
    job_skills = list(job.required_skills or [])

    matched_kw = [kw for kw in job_skills if any(kw.lower() in cs.lower() or cs.lower() in kw.lower() for cs in candidate_skills)]
    missing_kw = [kw for kw in job_skills if kw not in matched_kw]

    coverage = round((len(matched_kw) / len(job_skills)) * 100.0, 1) if job_skills else 85.0

    # Emphasise relevant verified projects and education based on job title/description
    role_focus = "Cybersecurity Operations, Threat Detection & OSINT"
    if any(k in job.title.lower() for k in ["it support", "service desk", "desktop", "technician"]):
        role_focus = "IT Support, Incident Triage, System Troubleshooting & Customer Operations"

    tailored_summary = (
        f"MSc Cybersecurity graduate (University of Hertfordshire, September 2025) and BCA graduate (2023) "
        f"targeting the {job.title} position at {job.employer_name} ({job.country}). "
        f"Brings hands-on technical capability in {', '.join(matched_kw[:6] or candidate_skills[:6])}, "
        f"demonstrated through security engineering projects including Om (Automated Reconnaissance Tool) and "
        f"NETRA (Intelligence & Investigation Platform), alongside customer-facing operational reliability at Travelodge UK."
    )

    base_text = build_master_cv_text(profile, imm) if profile else (master_cv.raw_text if master_cv else "")
    tailored_text = (
        f"TAILORED CV — {job.title.upper()} ({job.employer_name.upper()})\n"
        f"Focus Area: {role_focus}\n"
        f"====================================================================\n\n"
        f"TARGETED PROFILE SUMMARY\n{tailored_summary}\n\n"
        f"RELEVANT VERIFIED SKILLS MATCHED TO ROLE\n"
        f"{', '.join(matched_kw or candidate_skills)}\n\n"
        f"{base_text}\n\n"
        f"[FACTUAL INTEGRITY NOTICE: Hospitality experience at Travelodge UK is presented strictly as customer-facing and operational experience. "
        f"No unverified skills or certifications have been added.]"
    )

    missing_confirmations = [
        f"Confirm whether you have verifiable coursework or lab evidence for '{kw}' before adding to CV."
        for kw in missing_kw
    ]

    version = CVVersion(
        version_name=f"Tailored CV — {job.employer_name} ({job.title})",
        is_master=False,
        target_job_id=job.id,
        source_filename="generated_from_master_cv",
        raw_text=tailored_text,
        structured_data=parse_cv_into_structured_profile(tailored_text, profile),
        ats_keyword_coverage=coverage,
        matched_keywords=matched_kw,
        missing_keywords=missing_kw,
        missing_confirmations=missing_confirmations,
        tailoring_notes=(
            f"Tailored for {job.title} at {job.employer_name} ({job.country}). "
            f"ATS Keyword Coverage: {coverage}%. Preserved exact academic dates (MSc Sept 2025, BCA 2023) and Travelodge UK operational scope."
        ),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def generate_cover_letter_and_answers(db: Session, job: JobVacancy) -> CoverLetterVersion:
    """
    SCRIBE — Generates country-adapted cover letter, STAR examples, and screening answers
    strictly grounded in the candidate's verified profile and immigration status.
    """
    profile = db.query(CandidateProfile).first()
    imm = db.query(ImmigrationProfile).first()
    ai = AIProviderOrchestrator(db)

    uk_expiry = imm.uk_visa_expiry_date if imm else "October 2027"
    if job.country == "United Kingdom":
        work_elig_resp = (
            f"I hold a valid UK Graduate Visa expiring in {uk_expiry}, which grants me the full right to work in the United Kingdom "
            f"for any employer without requiring initial visa sponsorship. For long-term career progression beyond {uk_expiry}, "
            f"I would welcome the opportunity to transition to a Skilled Worker visa (qualifying under the New Entrant criteria)."
        )
    elif job.country == "India":
        work_elig_resp = (
            "As an Indian citizen currently based in India, I have full, unrestricted right to work across India with zero visa or sponsorship requirements."
        )
    else:
        work_elig_resp = (
            f"I am an Indian national holding a UK MSc in Cybersecurity (University of Hertfordshire, September 2025). "
            f"I am fully prepared for international relocation to {job.country} and require employer work visa support in accordance with {job.country}'s skilled migration framework."
        )

    relocation_resp = (
        f"I am fully flexible regarding work arrangements ({job.work_arrangement}) and ready to relocate domestically or internationally to {job.location or job.country}."
    )

    salary_resp = (
        f"My salary expectations are aligned with {job.employer_name}'s remuneration band for this level ({job.salary_text}) and the statutory skilled worker thresholds where applicable."
    )

    fallback_cover_letter = (
        f"Dear Hiring Team at {job.employer_name},\n\n"
        f"I am writing to apply for the {job.title} role in {job.location or job.country}. "
        f"Having completed my MSc in Cybersecurity at the University of Hertfordshire in September 2025 following my Bachelor of Computer Applications (BCA, 2023), "
        f"I have built a practical foundation across security operations, reconnaissance, OSINT investigations, and IT systems support.\n\n"
        f"Alongside my postgraduate research, I designed and built Om, an automated reconnaissance tool, and NETRA, a modular intelligence and digital investigation platform "
        f"(available at https://github.com/adiz777 and https://adizala.me). These projects required structured log analysis, vulnerability discovery, and clear technical reporting "
        f"directly applicable to the responsibilities of a {job.title}.\n\n"
        f"In addition to my technical background, my operational and customer-facing experience with Travelodge UK strengthened my ability to communicate calmly under pressure, "
        f"resolve live service issues methodically, and follow strict operational procedures.\n\n"
        f"{work_elig_resp}\n\n"
        f"Thank you for considering my application. I look forward to discussing how my cybersecurity training and technical projects can support {job.employer_name}.\n\n"
        f"Sincerely,\n"
        f"{profile.full_name if profile else 'Adi Zala'}\n"
        f"GitHub: https://github.com/adiz777 | Portfolio: https://adizala.me"
    )

    cover_letter_text = ai.generate_text(
        system_prompt="You are SCRIBE, a factual recruitment writing assistant. Never invent experience or certifications. Use natural professional English.",
        user_prompt=f"Write a concise, natural cover letter for {job.title} at {job.employer_name} in {job.country}. Fallback reference:\n{fallback_cover_letter}",
        fallback_text=fallback_cover_letter,
    )

    star_examples = [
        {
            "competency": "Technical Reconnaissance & Security Automation (Om Project)",
            "situation": "Manual reconnaissance and attack-surface mapping during security assessments involved repetitive multi-tool execution.",
            "task": "Design a modular, repeatable reconnaissance workflow to consolidate subdomain, port, and service enumeration.",
            "action": "Developed 'Om' (Automated Reconnaissance Tool), integrating structured enumeration pipelines and clean output reporting on GitHub (adiz777).",
            "result": "Reduced manual triage steps during lab assessments and created reusable reconnaissance telemetry.",
        },
        {
            "competency": "OSINT & Digital Investigation (NETRA Platform)",
            "situation": "Open-source intelligence investigations require correlating fragmented indicators across multiple public sources.",
            "task": "Build a central investigation platform to structure OSINT queries and preserve evidence context.",
            "action": "Engineered 'NETRA' (Intelligence and Investigation Platform) during MSc Cybersecurity studies to streamline indicator correlation.",
            "result": "Delivered a working investigative workflow documented on adizala.me without fabricating commercial threat feeds.",
        },
        {
            "competency": "High-Pressure Customer & Incident Handling (Travelodge UK)",
            "situation": "High-occupancy operational shifts at Travelodge UK required managing concurrent guest issues and safety procedures.",
            "task": "Maintain service continuity, resolve guest escalations promptly, and uphold site operational standards.",
            "action": "Triaged requests by urgency, communicated clearly with diverse customers, and documented shift handovers accurately.",
            "result": "Maintained smooth front-of-house operations and transferable service-desk communication discipline.",
        },
    ]

    screening_answers = {
        "why_this_role": f"The {job.title} role at {job.employer_name} aligns directly with my MSc Cybersecurity training (University of Hertfordshire, Sept 2025) and my hands-on development of Om and NETRA.",
        "work_authorization": work_elig_resp,
        "relocation_flexibility": relocation_resp,
        "salary_expectations": salary_resp,
        "practical_security_experience": "My technical security experience comes from my MSc Cybersecurity coursework and building Om (reconnaissance automation) and NETRA (OSINT investigation platform), complemented by customer-facing operational experience at Travelodge UK.",
    }

    cl = CoverLetterVersion(
        title=f"Cover Letter & Answers — {job.employer_name} ({job.title})",
        target_job_id=job.id,
        country_adapted=job.country,
        employer_name=job.employer_name,
        cover_letter_text=cover_letter_text,
        supporting_statement=f"Targeted supporting statement for {job.title} ({job.country}) emphasizing MSc Cybersecurity, Om, NETRA, and verified work eligibility.",
        screening_answers=screening_answers,
        star_examples=star_examples,
        work_eligibility_response=work_elig_resp,
        relocation_response=relocation_resp,
        salary_expectation_response=salary_resp,
    )
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


def export_document_to_pdf(title: str, body_text: str, filename_prefix: str = "document") -> Path:
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", filename_prefix)[:40]
    out_path = EXPORTS_DIR / f"{safe_prefix}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=45, rightMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ApplyTitle", parent=styles["Heading1"], fontSize=14, spaceAfter=12)
    body_style = ParagraphStyle("ApplyBody", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)

    story = [Paragraph(title.replace("&", "&amp;"), title_style), Spacer(1, 8)]
    for line in body_text.splitlines():
        clean = line.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if clean:
            story.append(Paragraph(clean, body_style))
        else:
            story.append(Spacer(1, 6))
    doc.build(story)
    return out_path


def export_document_to_docx(title: str, body_text: str, filename_prefix: str = "document") -> Path:
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", filename_prefix)[:40]
    out_path = EXPORTS_DIR / f"{safe_prefix}.docx"
    doc = Document()
    doc.add_heading(title, level=1)
    for line in body_text.splitlines():
        doc.add_paragraph(line)
    doc.save(str(out_path))
    return out_path
