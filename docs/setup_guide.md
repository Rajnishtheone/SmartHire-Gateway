# Setup Guide

Follow this checklist to run SmartHire Gateway locally and prepare your submission.

## 1. Prerequisites

- Python 3.10+
- Node.js 18+ (for the optional frontend)
- Tesseract OCR binary (install via `brew install tesseract`, `choco install tesseract`, or the official installer)
- (Optional) Poppler for Windows if you plan to use the PDF-to-image OCR fallback (`choco install poppler`).

## 2. Configure Environment Variables

1. Duplicate `.env.example` → `.env`.
2. Update the placeholders:
   - `JWT_SECRET`: any secure random string.
   - `ADMIN_EMAIL` / `ADMIN_PASSWORD`: bootstrap credentials.
   - `TWILIO_*`: values from the Twilio console.
   - `GOOGLE_*`: IDs from the Google Cloud configuration.

## 3. Twilio WhatsApp Sandbox

1. Create a Twilio account and open the **Messaging → Try it out → WhatsApp Sandbox** page.
2. Join the sandbox (scan the QR code or send the provided join message).
3. Note the sandbox **From** number and your **Account SID/Auth Token**.
4. In the sandbox configuration, set the **Webhook URL** to your tunnel/public endpoint (e.g., via ngrok):  
   `https://<your-ngrok-domain>/api/whatsapp/webhook`
5. (Optional) Capture the signing token if you want to enforce request validation.

## 4. Google Sheets & Drive

1. Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account** and download its JSON key. Place it somewhere safe (e.g., `backend/config/service-account.json`) and reference the path in `GOOGLE_SERVICE_ACCOUNT_JSON`.
3. Share your target Google Sheet with the service account email (Editor access).
4. Copy the Sheet ID (from the URL) into `GOOGLE_SHEETS_ID`.
5. (Optional) Create a Drive folder for attachments and copy its ID into `GOOGLE_DRIVE_FOLDER_ID`, again sharing it with the service account.

## 5. Install Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
# fallback if download fails
python -m spacy download en_core_web_sm
```

For the frontend:

```powershell
cd frontend
npm install
```

## 6. Run the Backend

```powershell
.\tasks.ps1 run-backend
# or
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

## 7. Run the Frontend (Optional)

```powershell
cd frontend
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000/api` in a `.env` file inside `frontend/` if needed.

## 8. Testing

```powershell
.\tasks.ps1 test
# or
pytest
```

The unit tests use the local storage fallback, so no external APIs are required.

## 9. Recording the Demo

1. Start backend (and frontend if showcasing the dashboard).
2. Use the Twilio Sandbox on your phone to send a resume (PDF, image, or text).
3. Show the ingested entry appearing in Google Sheets (or the local `data/dev/candidates.json` file for credential-free demos).
4. Display auto-reply on your phone and recruiter dashboard updates.
5. Follow the script in `docs/demo_script.md` for a concise 2–3 minute recording.

## 10. Production Hardening (Checklist for your report)

- Swap in Celery/Redis for OCR workloads.
- Persist users and audit logs in PostgreSQL.
- Add structured monitoring (OpenTelemetry).
- Move secrets to GCP Secret Manager.
- Harden webhook endpoint with rate limiting and log redaction.
