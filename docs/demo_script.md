# Demo Script (2–3 Minutes)

## 1. Introduction (20s)
- “Hi, this is SmartHire Gateway — an AI-assisted WhatsApp CV intake workflow for recruiters.”
- “I’ll show WhatsApp ingestion, automated parsing, Google Sheets sync, and recruiter console.”

## 2. WhatsApp Intake (40s)
- Share your screen/camera showing the Twilio sandbox conversation.
- Send a short message with a PDF resume or image.
- Mention that Twilio posts to the FastAPI webhook where signature checks and ingestion occur.

## 3. Backend Processing (30s)
- Switch to VS Code terminal showing `uvicorn` logs.
- Highlight the structured JSON log lines (ingestion + parsing + storage).
- Briefly mention OCR fallback (pdfplumber → pdf2image + pytesseract) and spaCy entity extraction.

## 4. Google Sheets Update (30s)
- Open the connected Google Sheet (or `data/dev/candidates.json` if offline).
- Point out the newly appended row with extracted name/email/skills/confidence.
- Note that attachments can be archived to Google Drive for traceability.

## 5. Recruiter Dashboard (40s)
- Show the React dashboard auto-refresh or click **Refresh**.
- Highlight metrics, candidate table, and the manual ingest trigger for demos.
- Mention JWT-based admin/recruiter roles and local storage fallback for quick testing.

## 6. Wrap-up & Next Steps (20s)
- Summarize: “End-to-end resume intake with auto-replies, structured storage, and recruiter UX.”
- Mention roadmap items: ATS integration, AI ranking, analytics, multi-tenant scaling.
- Thank the reviewer and provide repo/demo link.
