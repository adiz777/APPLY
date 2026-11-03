from datetime import datetime
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models import Employer, ImmigrationProfile, RecruitmentPreferences, VisaCountryRule


AUTHORITATIVE_VISA_SOURCES: list[dict[str, Any]] = [
    {
        "country": "United Kingdom",
        "is_priority": True,
        "primary_visa_route": "Graduate Visa (Current until Oct 2027) -> Skilled Worker Visa (Future Transition)",
        "authority_name": "UK Visas and Immigration (GOV.UK)",
        "official_source_url": "https://www.gov.uk/skilled-worker-visa",
        "sponsorship_required_for_candidate": False,
        "current_candidate_eligibility_status": "Eligible without employer sponsorship until October 2027 under valid UK Graduate Visa. Requires licensed Skilled Worker sponsor for long-term post-Oct 2027 employment.",
        "salary_threshold_info": "General Skilled Worker threshold £38,700/year or going rate for SOC occupation code (New Entrant discount £30,960 or 70% of going rate applicable when switching from Graduate visa).",
        "occupation_eligibility_info": "Eligible SOC 2020 codes include 2135 (Cyber Security Professionals), 2139 (IT Professionals), 3131 (IT Operations Technicians), 3132 (IT User Support Technicians).",
        "qualification_requirements": "RQF Level 3+ for eligible skilled occupations (Candidate holds UK RQF Level 7 MSc Cybersecurity).",
        "labour_market_test_info": "No Resident Labour Market Test required; employer must hold valid Skilled Worker Sponsor Licence and assign a Certificate of Sponsorship (CoS).",
        "language_requirements_info": "B1 CEFR English (Already satisfied via UK MSc degree taught in English).",
        "estimated_visa_costs": "Graduate Visa active; future Skilled Worker switch: £719-£1,639 fee + £1,035/yr Immigration Health Surcharge.",
        "required_documents": [
            "Valid Indian Passport",
            "Current UK Graduate Visa eVisa / Share Code",
            "University of Hertfordshire MSc Cybersecurity Certificate",
            "Certificate of Sponsorship (CoS) for future Skilled Worker transition",
        ],
        "official_process_steps": [
            "1. Apply and commence work immediately using existing UK Graduate Visa work permission (valid until Oct 2027).",
            "2. Verify whether employer appears on the official GOV.UK Register of Licensed Sponsors (Worker route).",
            "3. Before October 2027, transition to Skilled Worker visa via New Entrant route with a CoS from licensed employer.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "India",
        "is_priority": True,
        "primary_visa_route": "Domestic Citizen — Unrestricted Right to Work",
        "authority_name": "Government of India",
        "official_source_url": "https://www.india.gov.in/",
        "sponsorship_required_for_candidate": False,
        "current_candidate_eligibility_status": "Full unrestricted work eligibility (Indian National). No visa or employer sponsorship required.",
        "salary_threshold_info": "No immigration salary threshold applies.",
        "occupation_eligibility_info": "All roles eligible (Remote, Hybrid, On-site across all Indian cities).",
        "qualification_requirements": "Employer-specific role qualifications only.",
        "labour_market_test_info": "Not applicable.",
        "language_requirements_info": "English working proficiency.",
        "estimated_visa_costs": "0 INR (Citizen)",
        "required_documents": ["PAN Card / Aadhaar / Indian Passport", "Academic Degree Certificates"],
        "official_process_steps": ["Direct onboarding with employer — zero immigration steps required."],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "Germany",
        "is_priority": True,
        "primary_visa_route": "EU Blue Card / Skilled Workers with Academic Degrees (§ 18b AufenthG)",
        "authority_name": "Make it in Germany — Federal Government Portal",
        "official_source_url": "https://www.make-it-in-germany.com/en/visa-residence/types/eu-blue-card",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Requires concrete job offer / employment contract meeting EU Blue Card or Skilled Worker criteria.",
        "salary_threshold_info": "EU Blue Card bottleneck/IT professions & recent graduates (graduated within 3 years): ~€41,041.80 gross/year (standard threshold ~€45,300+).",
        "occupation_eligibility_info": "ISCO-08 Group 25 (Information and Communications Technology Professionals) qualifies for lower bottleneck threshold.",
        "qualification_requirements": "Recognized university degree (anabin H+ status — UK MSc Cybersecurity & BCA).",
        "labour_market_test_info": "Federal Employment Agency (BA) approval may apply for reduced threshold Blue Card; no priority check for standard academic Blue Card.",
        "language_requirements_info": "No mandatory German required by immigration law for EU Blue Card if working language at employer is English.",
        "estimated_visa_costs": "€75 National Visa fee + ~€100 EU Blue Card residence permit fee.",
        "required_documents": [
            "Valid Passport",
            "Signed Employment Contract / Binding Job Offer stating gross annual salary",
            "Declaration of Employment (Erklärung zum Beschäftigungsverhältnis)",
            "University Degree Certificates (MSc & BCA)",
            "Health Insurance proof",
        ],
        "official_process_steps": [
            "1. Secure binding employment contract from German employer in an English-speaking IT/Cybersecurity role.",
            "2. Employer completes 'Erklärung zum Beschäftigungsverhältnis'.",
            "3. Apply for EU Blue Card visa at German Embassy/Consulate.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "Ireland",
        "is_priority": True,
        "primary_visa_route": "Critical Skills Employment Permit (CSEP)",
        "authority_name": "Department of Enterprise, Trade and Employment (DETE) & Irish Immigration",
        "official_source_url": "https://enterprise.gov.ie/en/what-we-do/workplace-and-skills/employment-permits/permit-types/critical-skills-employment-permit/",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Requires Critical Skills or General Employment Permit sponsored/supported by Irish-registered employer.",
        "salary_threshold_info": "Critical Skills Employment Permit with relevant degree: minimum €38,000+ (subject to DETE statutory increases to €44,000 phased roadmap).",
        "occupation_eligibility_info": "ICT Professionals (SOC 2135 Cyber Security, 2136, 2139) are on the Critical Skills Occupations List.",
        "qualification_requirements": "Relevant degree in ICT/Cybersecurity (MSc Cybersecurity satisfies this requirement).",
        "labour_market_test_info": "Waived for occupations on the Critical Skills Occupations List.",
        "language_requirements_info": "English is the primary working language.",
        "estimated_visa_costs": "€1,000 Critical Skills Employment Permit fee + Entry Visa fee.",
        "required_documents": [
            "Signed contract of employment (minimum 2-year duration for CSEP)",
            "MSc Cybersecurity degree transcript & certificate",
            "Employer registration details with Revenue & CRO",
        ],
        "official_process_steps": [
            "1. Receive 2-year contract offer in eligible ICT Critical Skills occupation.",
            "2. Submit CSEP application via Employment Permits Online System (EPOS).",
            "3. Apply for Irish Employment Entry Visa once permit is granted.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "Netherlands",
        "is_priority": True,
        "primary_visa_route": "Highly Skilled Migrant (Kennismigrant) / EU Blue Card",
        "authority_name": "Immigration and Naturalisation Service (IND)",
        "official_source_url": "https://ind.nl/en/residence-permits/work/highly-skilled-migrant",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Employer must be an IND Recognised Sponsor (Erkend Referent).",
        "salary_threshold_info": "Highly Skilled Migrant under 30 years old: ~€3,909 gross/month (excluding 8% holiday allowance); 30 or older: ~€5,331 gross/month.",
        "occupation_eligibility_info": "Skilled specialist roles at IND-recognised sponsor companies.",
        "qualification_requirements": "Higher education degree (MSc Cybersecurity) and market-conform salary.",
        "labour_market_test_info": "Waived for IND Recognised Sponsors meeting salary threshold.",
        "language_requirements_info": "English widely accepted in Dutch tech & security firms.",
        "estimated_visa_costs": "~€380 IND application fee (often covered by recognised sponsor).",
        "required_documents": [
            "Employment contract with an IND Recognised Sponsor",
            "Antecedents Certificate",
            "Valid Passport",
        ],
        "official_process_steps": [
            "1. Verify employer is listed on the official IND Public Register of Recognised Sponsors.",
            "2. Employer submits Entry and Residence (TEV) application directly to IND.",
            "3. Collect MVV sticker at Dutch embassy and relocate.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "United Arab Emirates",
        "is_priority": True,
        "primary_visa_route": "Standard Sponsored Work Permit & Residence Visa / Green Visa",
        "authority_name": "MOHRE & ICP (Federal Authority for Identity, Citizenship, Customs & Port Security)",
        "official_source_url": "https://u.ae/en/information-and-services/visa-and-emirates-id/residence-visas/residence-visa-for-working-in-the-uae",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Employer sponsors work permit and UAE residence visa upon job offer.",
        "salary_threshold_info": "No tax on personal income; Skilled Level 1/2 work permit requires attested bachelor's/master's degree.",
        "occupation_eligibility_info": "Information Security Analyst, SOC Analyst, and IT roles eligible under MOHRE skilled categories.",
        "qualification_requirements": "Attested university degree certificate (MSc / BCA) for skilled visa classification.",
        "labour_market_test_info": "Managed by employer quota & MOHRE establishment card.",
        "language_requirements_info": "English is the standard business language across private sector cybersecurity roles.",
        "estimated_visa_costs": "By UAE law, recruitment and work visa sponsorship costs are borne by the employer.",
        "required_documents": [
            "Passport valid for 6+ months",
            "Attested University Degree Certificate",
            "Signed MOHRE Offer Letter",
            "Medical fitness test & Emirates ID biometrics upon arrival",
        ],
        "official_process_steps": [
            "1. Sign official MOHRE/Free-Zone job offer.",
            "2. Employer issues entry work permit (e-visa).",
            "3. Complete medical test and Emirates ID in UAE.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "Canada",
        "is_priority": True,
        "primary_visa_route": "Global Talent Stream (TFWP LMIA) / Express Entry STEM",
        "authority_name": "Immigration, Refugees and Citizenship Canada (IRCC)",
        "official_source_url": "https://www.canada.ca/en/employment-social-development/services/foreign-workers/global-talent.html",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Requires employer-specific LMIA/Global Talent Stream work permit or Express Entry invitation.",
        "salary_threshold_info": "Global Talent Stream Category B: Prevailing median wage for NOC 21220 (Cybersecurity specialists).",
        "occupation_eligibility_info": "NOC 21220 (Cybersecurity specialists) and NOC 21221 (Business systems specialists) qualify under Global Talent Stream Category B.",
        "qualification_requirements": "Master's degree (ECA verifiable) + relevant technical skills.",
        "labour_market_test_info": "Global Talent Stream replaces standard recruitment advertisement with a Labour Market Benefits Plan (2-week processing target).",
        "language_requirements_info": "English (CLB 7+ recommended for work/PR pathways).",
        "estimated_visa_costs": "CAD $155 Work Permit fee + CAD $85 Biometrics (Employer pays CAD $1,000 LMIA fee).",
        "required_documents": ["Positive LMIA / GTS decision letter", "Job Offer number", "Valid Passport", "Degree transcripts"],
        "official_process_steps": [
            "1. Employer applies for Global Talent Stream LMIA under NOC 21220.",
            "2. Candidate applies for employer-specific Work Permit online via IRCC.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "Australia",
        "is_priority": True,
        "primary_visa_route": "Skills in Demand Visa (Subclass 482) / Skilled Nominated (190)",
        "authority_name": "Australian Government Department of Home Affairs",
        "official_source_url": "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/skills-in-demand-482",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Requires Approved Standard Business Sponsor nomination and relevant post-qualification work experience.",
        "salary_threshold_info": "Core Skills Income Threshold (CSIT) AUD $73,150+ and market salary rate.",
        "occupation_eligibility_info": "ANZSCO 262112 (ICT Security Specialist) & 263212 (ICT Support Engineer).",
        "qualification_requirements": "Relevant degree + minimum 1 year full-time relevant work experience required for Subclass 482.",
        "labour_market_test_info": "Labour Market Testing (LMT) required by sponsoring employer unless international trade obligation applies.",
        "language_requirements_info": "English proficiency (IELTS 5.0+ or equivalent / 5 years full-time study in English).",
        "estimated_visa_costs": "AUD $3,115 primary applicant fee.",
        "required_documents": ["Approved Employer Nomination TRN", "Passport", "English & qualification evidence", "Police clearances"],
        "official_process_steps": [
            "1. Confirm candidate meets post-qualification work experience requirement.",
            "2. Employer lodges nomination under Subclass 482.",
            "3. Candidate lodges Subclass 482 visa application.",
        ],
        "last_verified_date": "2026-11-03",
    },
    {
        "country": "New Zealand",
        "is_priority": True,
        "primary_visa_route": "Accredited Employer Work Visa (AEWV) / Green List Tier 1 & 2",
        "authority_name": "Immigration New Zealand (INZ)",
        "official_source_url": "https://www.immigration.govt.nz/new-zealand-visas/visas/visa/accredited-employer-work-visa",
        "sponsorship_required_for_candidate": True,
        "current_candidate_eligibility_status": "Requires job token from an INZ Accredited Employer.",
        "salary_threshold_info": "NZ Median Wage threshold (NZD $29.66/hr+) or Green List role remuneration requirement.",
        "occupation_eligibility_info": "ANZSCO 262112 ICT Security Specialist is on the New Zealand Green List (Tier 1 Straight to Residence if salary/qualification criteria met).",
        "qualification_requirements": "Level 7+ qualification in Computer Science/Cybersecurity (MSc Cybersecurity).",
        "labour_market_test_info": "Job Check required unless role meets Green List exemption.",
        "language_requirements_info": "English is the primary language.",
        "estimated_visa_costs": "NZD $1,540 AEWV application fee.",
        "required_documents": ["INZ Accredited Employer Job Check Token", "Signed employment agreement", "Qualification evidence"],
        "official_process_steps": [
            "1. Verify employer holds active INZ Accreditation.",
            "2. Employer completes Job Check and sends AEWV application token.",
            "3. Submit AEWV online application.",
        ],
        "last_verified_date": "2026-11-03",
    },
]

ADDITIONAL_CONFIGURABLE_COUNTRIES = [
    ("Singapore", "Employment Pass (COMPASS)", "Ministry of Manpower (MOM)", "https://www.mom.gov.sg/passes-and-permits/employment-pass"),
    ("Japan", "Engineer / Specialist in Humanities / International Services", "Immigration Services Agency of Japan", "https://www.isa.go.jp/en/"),
    ("Sweden", "EU Blue Card / Work Permit", "Migrationsverket", "https://www.migrationsverket.se/English/Private-individuals/Working-in-Sweden.html"),
    ("Finland", "Specialist Residence Permit / EU Blue Card", "Migri (Finnish Immigration Service)", "https://migri.fi/en/specialist"),
    ("Denmark", "Pay Limit Scheme / Positive List for Higher Education", "SIRI (nyidanmark.dk)", "https://www.nyidanmark.dk/en-GB/You-want-to-apply/Work"),
    ("France", "Talent Passport — Qualified Employee / EU Blue Card", "France-Visas", "https://france-visas.gouv.fr/en/web/france-visas/international-talents-and-economic-attractiveness"),
    ("Belgium", "Single Permit / EU Blue Card", "Immigration Office Belgium", "https://dofi.ibz.be/en"),
    ("Luxembourg", "Salaried Worker / EU Blue Card", "Guichet.lu (Ministry of Foreign and European Affairs)", "https://guichet.public.lu/en/citoyens/immigration.html"),
    ("Austria", "Red-White-Red Card / EU Blue Card", "migration.gv.at", "https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/"),
    ("Norway", "Skilled Worker Residence Permit", "UDI (Norwegian Directorate of Immigration)", "https://www.udi.no/en/want-to-apply/work-immigration/skilled-workers/"),
    ("Switzerland", "Third-Country National Quota Work Permit (L/B)", "State Secretariat for Migration (SEM)", "https://www.sem.admin.ch/sem/en/home/themen/arbeit/nicht-eu_efta-angehoerige.html"),
    ("Saudi Arabia", "Employment Work Visa (Iqama)", "Ministry of Human Resources and Social Development", "https://www.hrsd.gov.sa/en"),
    ("Qatar", "Employer-Sponsored Work Residence Permit", "Ministry of Labour Qatar", "https://www.mol.gov.qa/En/Pages/default.aspx"),
]


VALID_SPONSORSHIP_STATUSES = [
    "Confirmed",
    "Employer explicitly states sponsorship available",
    "Employer sponsorship capability verified",
    "Potentially available",
    "Not verified",
    "No sponsorship",
    "Not eligible",
    "Requires further investigation",
]


def seed_visa_country_rules(db: Session) -> None:
    existing = {r.country for r in db.query(VisaCountryRule).all()}
    for item in AUTHORITATIVE_VISA_SOURCES:
        if item["country"] not in existing:
            db.add(VisaCountryRule(**item))
    for country, route, auth, url in ADDITIONAL_CONFIGURABLE_COUNTRIES:
        if country not in existing:
            db.add(
                VisaCountryRule(
                    country=country,
                    is_priority=False,
                    primary_visa_route=route,
                    authority_name=auth,
                    official_source_url=url,
                    sponsorship_required_for_candidate=True,
                    current_candidate_eligibility_status=f"Requires verified employer work visa sponsorship in {country}.",
                    salary_threshold_info="Must meet statutory skilled worker / Blue Card salary threshold.",
                    occupation_eligibility_info="Cybersecurity, SOC, and IT Analyst roles.",
                    qualification_requirements="University degree (MSc Cybersecurity).",
                    labour_market_test_info="Subject to national labour market test unless exempt under shortage/salary rules.",
                    language_requirements_info="English working language roles only.",
                    estimated_visa_costs="Varies by statutory permit fee schedule.",
                    required_documents=["Valid Passport", "Signed Employment Contract", "Degree Certificates"],
                    official_process_steps=["1. Confirm employer sponsorship.", "2. Submit work permit application via official portal."],
                    last_verified_date="2026-11-03",
                )
            )
    db.commit()


def evaluate_job_visa_intelligence(
    db: Session,
    country: str,
    title: str,
    description: str,
    employer_name: str,
    salary_min: Optional[float] = None,
    explicit_sponsorship_hint: Optional[str] = None,
) -> dict[str, Any]:
    """
    LEXICON — Country-specific Visa & Sponsorship Evaluation Engine.
    Enforces UK Graduate Visa rules (valid until Oct 2027 without sponsorship),
    India domestic rules (zero sponsorship required), and strict verification for all other countries.
    """
    imm = db.query(ImmigrationProfile).first()
    rule = db.query(VisaCountryRule).filter(VisaCountryRule.country == country).first()
    employer = db.query(Employer).filter(Employer.name.ilike(employer_name)).first()

    text_lower = f"{title} {description}".lower()
    uk_expiry = imm.uk_visa_expiry_date if imm else "2027-10-31"
    uk_status = imm.uk_immigration_status if imm else "Graduate visa"

    # Detect explicit signals in job description
    explicit_no_sponsor = any(
        phrase in text_lower
        for phrase in [
            "no visa sponsorship",
            "cannot sponsor",
            "unable to sponsor",
            "do not offer sponsorship",
            "must have permanent right to work",
            "sc clearance required - uk nationals only",
            "uk eyes only",
        ]
    )
    explicit_yes_sponsor = any(
        phrase in text_lower
        for phrase in [
            "visa sponsorship available",
            "visa sponsorship provided",
            "we sponsor visas",
            "skilled worker sponsorship available",
            "relocation and visa support",
            "eu blue card sponsorship",
            "critical skills permit sponsorship",
        ]
    )
    relocation_offered = any(
        phrase in text_lower for phrase in ["relocation package", "relocation assistance", "relocation support", "visa and relocation"]
    )

    if explicit_sponsorship_hint in VALID_SPONSORSHIP_STATUSES:
        sponsorship_status = explicit_sponsorship_hint
    elif explicit_no_sponsor:
        sponsorship_status = "No sponsorship"
    elif explicit_yes_sponsor:
        sponsorship_status = "Employer explicitly states sponsorship available"
    elif employer and employer.uk_licensed_sponsor and country == "United Kingdom":
        sponsorship_status = "Employer sponsorship capability verified"
    elif employer and employer.sponsorship_capability_status in VALID_SPONSORSHIP_STATUSES:
        sponsorship_status = employer.sponsorship_capability_status
    elif country == "India":
        sponsorship_status = "Confirmed"
    else:
        sponsorship_status = "Not verified"

    # Country-specific eligibility determination
    if country == "India":
        candidate_eligible = True
        sponsorship_required_now = False
        future_sponsorship_needed = False
        eligibility_summary = (
            "ELIGIBLE IMMEDIATELY (Indian National): No employer visa sponsorship required for remote, hybrid, or on-site roles in India."
        )
        feasibility_score = 100.0
        missing_info = []
    elif country == "United Kingdom":
        # Check if UK eyes only / SC clearance blocks graduate visa holder
        if "uk nationals only" in text_lower or "uk eyes only" in text_lower:
            candidate_eligible = False
            sponsorship_status = "Not eligible"
            sponsorship_required_now = True
            future_sponsorship_needed = True
            eligibility_summary = "NOT ELIGIBLE: Role requires sole UK nationality / UK Eyes Only clearance."
            feasibility_score = 0.0
            missing_info = ["Nationality restriction cannot be waived."]
        else:
            candidate_eligible = True
            sponsorship_required_now = False
            future_sponsorship_needed = True
            if sponsorship_status in ("Confirmed", "Employer explicitly states sponsorship available", "Employer sponsorship capability verified"):
                feasibility_score = 98.0
                eligibility_summary = (
                    f"ELIGIBLE NOW via {uk_status} (expires {uk_expiry}) — No initial sponsorship needed. "
                    f"HIGH PRIORITY: Employer has verified/stated Skilled Worker sponsorship capability for long-term transition before {uk_expiry}."
                )
            elif sponsorship_status == "No sponsorship":
                feasibility_score = 78.0
                eligibility_summary = (
                    f"ELIGIBLE NOW via {uk_status} (valid until {uk_expiry}) even without employer sponsorship. "
                    f"NOTE: Employer states no Skilled Worker sponsorship; candidate will need to transition to a sponsoring employer before {uk_expiry}."
                )
            else:
                feasibility_score = 88.0
                eligibility_summary = (
                    f"ELIGIBLE NOW via {uk_status} (valid until {uk_expiry}) without employer sponsorship. "
                    f"Verify during interview whether {employer_name} holds a Skilled Worker licence for post-{uk_expiry} retention."
                )
            missing_info = [
                f"Confirm employer's willingness to issue a Skilled Worker CoS under New Entrant rules prior to {uk_expiry}."
            ]
    else:
        # All other international countries
        sponsorship_required_now = True
        future_sponsorship_needed = True
        if sponsorship_status == "No sponsorship":
            candidate_eligible = False
            feasibility_score = 10.0
            eligibility_summary = f"BARRIER: {country} requires employer work visa sponsorship, and this vacancy explicitly states no sponsorship."
            missing_info = ["Employer does not sponsor foreign applicants for this vacancy."]
        elif sponsorship_status in ("Confirmed", "Employer explicitly states sponsorship available"):
            candidate_eligible = True
            feasibility_score = 92.0
            eligibility_summary = (
                f"SPONSORSHIP CONFIRMED/STATED: Vacancy indicates work visa sponsorship in {country}. "
                f"Evaluate occupation and salary threshold against {rule.primary_visa_route if rule else 'national work permit'} rules."
            )
            missing_info = ["Verify exact gross salary on contract meets statutory visa threshold."]
        elif sponsorship_status in ("Employer sponsorship capability verified", "Potentially available"):
            candidate_eligible = True
            feasibility_score = 75.0
            eligibility_summary = (
                f"POTENTIALLY SPONSORED: Employer has sponsorship capability in {country}, but sponsorship for this specific vacancy must be confirmed."
            )
            missing_info = ["Confirm whether employer will sponsor this specific vacancy."]
        else:
            candidate_eligible = True
            feasibility_score = 50.0
            eligibility_summary = (
                f"UNVERIFIED SPONSORSHIP: {country} requires an employer-sponsored work visa. Sponsorship is currently unverified for this listing."
            )
            missing_info = [
                f"Confirm whether {employer_name} sponsors international candidates in {country}.",
                "Verify salary meets minimum statutory visa threshold.",
            ]

    return {
        "country": country,
        "candidate_eligible": candidate_eligible,
        "sponsorship_status": sponsorship_status,
        "sponsorship_required_immediately": sponsorship_required_now,
        "future_sponsorship_needed": future_sponsorship_needed,
        "uk_graduate_visa_applicable": country == "United Kingdom",
        "uk_graduate_visa_expiry": uk_expiry if country == "United Kingdom" else None,
        "current_visa_route": rule.primary_visa_route if rule else "National Skilled Work Visa",
        "authority_name": rule.authority_name if rule else "National Immigration Authority",
        "official_government_url": rule.official_source_url if rule else "",
        "salary_requirements": rule.salary_threshold_info if rule else "Verify statutory threshold",
        "occupation_requirements": rule.occupation_eligibility_info if rule else "Skilled IT/Cybersecurity occupation",
        "labour_market_test": rule.labour_market_test_info if rule else "Verify national rules",
        "relocation_assistance": "Offered" if relocation_offered else "Not verified",
        "feasibility_score": feasibility_score,
        "eligibility_summary": eligibility_summary,
        "missing_information": missing_info,
        "last_checked_date": datetime.now().strftime("%Y-%m-%d"),
    }
