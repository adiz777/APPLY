# Contributing to APPLY

Thank you for your interest in contributing to **APPLY — Autonomous Personal Application & Recruitment Intelligence System**.

## Engineering & Security Guardrails

1. **Zero Unauthorized Automation**: Never submit or modify code that bypasses the explicit human approval checkpoint (`approval_hash`) or attempts to defeat CAPTCHA, MFA, or bot protection.
2. **Factual Integrity**: All AI prompts and document tailoring services (`SCRIBE`) must strictly preserve candidate facts without fabricating employment dates, certifications, or skills.
3. **No Secrets or Personal Data in Git**: Ensure `.env`, `*.db`, and `backend/uploads/` remain ignored.
4. **Testing Requirement**: Run `python -m pytest -v` in `backend/` and `npm run build` in `frontend/` before committing.
