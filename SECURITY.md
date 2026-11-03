# Security Policy — APPLY

## Core Security Principles

APPLY handles sensitive personal recruitment data, CVs, immigration records, and job application workflows. Security and candidate privacy are built into every layer of the platform:

1. **Zero Unauthorized Submissions**: No application can ever enter the submission queue or be submitted by Playwright without explicit, version-bound human approval (`approval_hash` matching the exact SHA-256 digest of the job, CV version, cover letter version, and form answers).
2. **No Anti-Bot or Access Control Circumvention**: APPLY strictly respects `robots.txt`, rate limits, authentication boundaries, MFA, and CAPTCHA challenges. If a CAPTCHA or MFA prompt is detected, automation immediately pauses and transitions the application to `NEEDS_HUMAN_INTERVENTION`.
3. **Secret & Credential Protection**:
   - Passwords are hashed using `bcrypt`.
   - Sensitive API keys and tokens configured in Settings are encrypted at rest using Fernet (`cryptography.fernet`) before database storage.
   - Session tokens use signed HTTP/Bearer JWTs with expiration.
   - `.gitignore` strictly blocks `.env`, SQLite databases (`*.db`), uploaded CVs (`backend/uploads/`), and screenshots (`backend/screenshots/`).
4. **File Upload Validation**:
   - CV Studio only accepts validated `.pdf`, `.docx`, and `.txt` files with strict size limits and filename sanitization.
5. **Audit Logging**:
   - Every security-sensitive event (login, profile change, immigration update, approval granted/invalidated, automation step, bulk queue action, data export, account deletion) is recorded in an immutable `audit_logs` table.
6. **Data Privacy & Retention Controls**:
   - Full candidate data export (`JSON` / `CSV` / `PDF`) and immediate account/data wipe endpoints are available in Settings.

## Reporting a Vulnerability

If you discover a security issue in APPLY, do not open a public issue containing sensitive exploit details. Document the finding in the AI Project Manager Security Audit panel or contact the repository owner (`@adiz777`).
