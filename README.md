# SmartHire Gateway

<p align="center">
  <a href="https://github.com/Rajnishtheone/SmartHire-Gateway">
    <img src="https://readme-typing-svg.demolab.com/?font=Fira+Code&size=28&duration=2200&pause=500&color=F7931E&center=true&vCenter=true&width=600&lines=AI+Resume+Parser;WhatsApp+OCR+%2B+NLP;Sheets+%7C+Drive+Sync" alt="SmartHire typing banner" />
  </a>
</p>

SmartHire Gateway turns WhatsApp resume submissions into structured candidate records. A FastAPI backend ingests media, applies OCR + spaCy extraction, stores results in Google Sheets (or a JSON fallback), and surfaces them in a React recruiter/admin console.

## Highlights
- WhatsApp webhook (Twilio sandbox) with manual ingest fallback for demos.
- OCR + NLP pipeline for text, PDF, DOCX, and image resumes.
- Google Sheets / Drive persistence with automatic local JSON fallbacks.
- Role-based access: admin manages recruiter accounts; recruiters monitor candidates.
- Batteries included: Dockerfile, CI stub, lint/format config, pytest suite.

## Quickstart
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg || python -m spacy download en_core_web_sm
# set up .env (copy from .env.example)
.\tasks.ps1 run-backend
cd frontend
npm install
npm run dev
```

Demo login: `admin@example.com` / `admin123` · `recruiter@example.com` / `recruiter123`

## Project Map
```
backend/app/api/        # FastAPI routers: auth, candidates, whatsapp, admin tools
backend/app/core/       # Settings loader, logging config, JWT helpers
backend/app/models/     # Pydantic request/response contracts
backend/app/repositories/ # Sheets/Drive adapters + JSON fallbacks
backend/app/services/   # OCR, NLP parsing, WhatsApp orchestration, storage
backend/app/tests/      # pytest coverage for auth, parsing, webhook
backend/config/         # Twilio/Google helpers + sample credentials file
backend/scripts/        # Setup utilities (env verification, demo seeding)
frontend/src/           # React dashboard (pages, components, API clients)
docs/                   # Architecture notes, setup guide, demo script
deploy/                 # Dockerfile, compose stack, GitHub Actions sample
```

## Deploying & Twilio Notes
- Connect Render/Railway (or any host) to this repo, set env vars from `.env.example`.
- Point Twilio Sandbox “When a message comes in” to `<your-app>/api/whatsapp/webhook`.
- For local demos without tunnels, use the manual ingest endpoint showcased in docs.

SmartHire Gateway is ready for extensions—ATS hookups, AI ranking, recruiter notes, and more.
