# SmartHire Gateway

<p align="center">
  <a href="https://github.com/Rajnishtheone/SmartHire-Gateway">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=2200&pause=500&color=F7931E&center=true&vCenter=true&width=600&lines=AI+Resume+Parser+in+Your+Pocket;WhatsApp+✨+OCR+%2B+NLP+✨+Sheets" alt="AI Resume Parser Animation">
  </a>
</p>

AI-driven WhatsApp CV management demo that ingests resumes shared via Twilio's sandbox, parses structured data with OCR + NLP, and writes normalized records to Google Sheets (with optional Drive archival). A secure React dashboard lets recruiters review the latest profiles while candidates receive automated acknowledgements.

## Key Features
- **WhatsApp-first intake** with Twilio sandbox integration, signature validation, and optional auto-replies.
- **Multi-format resume parsing** (text, PDF, DOCX, images) using pdfplumber, python-docx, pdf2image, and pytesseract.
- **spaCy-powered NLP** to extract names, contact details, skills, education, experience, and last job titles.
- **Google Workspace sync** that appends structured rows to Google Sheets and archives raw files to Drive, with local fallbacks for offline demos.
- **Role-based access control** using JWT + bcrypt (demo admin/recruiter accounts pre-provisioned, admin can manage recruiter users).
- **Recruiter dashboard** (React + Vite) featuring metrics, candidate table, and a manual ingest trigger.
- **Production-ready scaffolding**: logging, config via `.env`, Docker assets, automated tests, linting/formatting, and CI starter workflow.

## Repository Layout (annotated)

```
SmartHireGateway/
├── backend/                 # FastAPI backend powering ingestion, parsing, auth
│   ├── app/
│   │   ├── api/             # REST routers (auth, candidates, whatsapp, admin)
│   │   ├── core/            # Settings, logging, security helpers
│   │   ├── models/          # Pydantic request/response schemas
│   │   ├── repositories/    # Google Sheets/Drive + local JSON fallbacks
│   │   ├── services/        # OCR, NLP, storage, WhatsApp orchestration
│   │   ├── utils/           # File IO, resume extraction helpers
│   │   ├── workers/         # Async task stubs for future Celery/RQ jobs
│   │   └── tests/           # Pytest suite (manual ingest, auth, parsing)
│   ├── config/              # Twilio/Google client factories and samples
│   └── scripts/             # Bootstrap demo data & env verification tools
├── frontend/                # React + Vite recruiter/admin dashboard
│   ├── public/              # Static HTML entrypoint
│   └── src/                 # Components, pages, services, global styles
├── docs/                    # Architecture notes, setup guide, demo script
├── deploy/                  # Dockerfile, compose stack, GitHub Actions CI
├── requirements.txt         # Python dependencies (FastAPI, spaCy, OCR stack)
├── pyproject.toml           # Formatting/linting configuration (black, ruff, mypy)
├── Makefile / tasks.ps1     # Friendly shortcuts for install/run/test commands
├── .env.example             # Safe template for required environment variables
└── README.md                # Project overview + instructions
```

## Quickstart

```powershell
# 1. Python environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg || python -m spacy download en_core_web_sm

# 2. Configure environment
copy .env.example .env
# edit .env with Twilio + Google credentials (or leave blank for local fallbacks)

# 3. Run backend
.\tasks.ps1 run-backend
# or
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Open API docs
start http://localhost:8000/docs

# 5. (Optional) Frontend dashboard
cd frontend
npm install
npm run dev
```

## Demo Accounts

- Admin: `admin@example.com` / `admin123`
- Recruiter: `recruiter@example.com` / `recruiter123`

## Testing & Quality

```powershell
.\tasks.ps1 test         # pytest suite (uses local JSON storage by default)
.\tasks.ps1 lint         # ruff + isort + black --check
.\tasks.ps1 format       # auto-format backend code
```

The repo ships with `pyproject.toml` configurations, a `Makefile`, and a Windows-friendly `tasks.ps1`.

## Deployment

- `deploy/Dockerfile`: FastAPI + Uvicorn container with optional spaCy model download.
- `deploy/docker-compose.yml`: Spins up the backend alongside a watchtower service for local prototyping.
- `deploy/ci.yml`: Sample GitHub Actions workflow (lint + tests) for quick automation.

## How It Works

1. **Webhook ingestion**: Twilio posts WhatsApp messages to `/api/whatsapp/webhook`. The service checks signatures (when configured), downloads media securely, and queues ingestion.
2. **OCR + parsing**: Attachments flow through pdfplumber, python-docx, or pytesseract/pdf2image depending on file type. spaCy NER + regex heuristics extract candidate attributes, while a curated skills library enriches results.
3. **Storage**: Parsed records append to Google Sheets with timestamps and confidence scores. Attachments optionally archive to Google Drive, otherwise to `data/dev/uploads`.
4. **Recruiter access**: Recruiters authenticate via `/api/auth/login` (demo accounts included). The React dashboard retrieves candidate data, surfaces quick metrics, and offers a manual ingest trigger for demos.
5. **Audit & extensibility**: All ingests create audit events. Worker stubs (`workers/tasks.py`) illustrate how to offload OCR to Celery/RQ for production scaling. Admin-created recruiter accounts persist in `data/dev/users.json` (hashed passwords only).

## Demo Workflow

- Follow `docs/setup_guide.md` to provision Twilio sandbox + Google APIs.
- Record the sequence described in `docs/demo_script.md` to showcase:
  - WhatsApp submission + auto-reply.
  - Backend logs and Sheets update.
  - Dashboard refresh with new candidate row.

## Future Enhancements

- AI ranking of candidates + semantic skill matching.
- ATS integrations (Lever, Greenhouse) via webhooks.
- Recruiter collaboration (notes, assignments, feedback loops).
- Analytics dashboards (conversion rates, sourcing insights).
- Multi-tenant architecture with organization-level isolation.
- Full async processing pipeline (Celery/Redis, Pub/Sub) and event-driven notifications.

## Security Considerations

- Store secrets in a managed vault (GCP Secret Manager / AWS Secrets Manager) in production.
- Enforce HTTPS termination and webhook rate limiting.
- Extend JWT service to federate with enterprise IdPs (Azure AD, Okta).
- Enable structured audit exports and integrate with SIEM tooling.

---

Made with ❤️ to fast-track recruiting ops.
