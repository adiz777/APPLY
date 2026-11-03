# Privacy & Backup Documentation — APPLY

## 1. Candidate Privacy Architecture

APPLY is designed as a **Self-Hosted Personal Recruitment Intelligence System**.

- **Local-First Ownership**: All candidate profile information, immigration status, master CVs, tailored documents, and application tracking records are stored in your local database (`backend/data/apply.db` or your private PostgreSQL instance).
- **Public Repository Safety**: No private candidate documents, personal phone numbers, street addresses, or API credentials are committed to Git. Initial profile seeding uses only user-approved public portfolio context (`github.com/adiz777`, `adizala.me`) and verifiable academic/immigration baseline metadata, which can be edited or wiped at any time.
- **AI Provider Transparency**: When using cloud AI providers (Gemini, Claude, OpenAI), only the necessary job description and structured CV context are sent to generate matching scores or tailored documents. For 100% offline privacy, select **Ollama (Local)** or **Deterministic Rule Engine** in Settings.

## 2. Data Export & Right to Erasure

From **Settings -> Security, Privacy & Data**:
- **Export All Personal Data**: Download a complete JSON bundle of your profile, immigration records, CVs, cover letters, applications, and audit trail.
- **Wipe / Reset Account Data**: Permanently delete all personal documents, applications, and profile records from the database and filesystem.

## 3. Backup & Recovery Guide

### SQLite Local Development Backup
1. Stop the backend server or trigger a safe backup snapshot.
2. Copy `D:\apply\backend\data\apply.db` and `D:\apply\backend\uploads\` to an encrypted backup volume.
3. Restore by placing `apply.db` back into `D:\apply\backend\data\apply.db`.

### PostgreSQL Production Backup
```bash
# Backup
pg_dump -U apply_user -F c -b -v -f "apply_backup_$(date +%Y%m%d).dump" apply_db

# Restore
pg_restore -U apply_user -d apply_db -v "apply_backup_YYYYMMDD.dump"
```
