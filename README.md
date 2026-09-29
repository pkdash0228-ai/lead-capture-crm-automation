# Lead Capture to CRM Automation Pipeline

A compact, interview-friendly lead intake system. Website form submissions and CSV imports pass through the same validation, normalization, duplicate detection, SQLite persistence, email, and audit logging pipeline.

## Problem statement

Teams receive leads through different channels and need a consistent way to validate contact details, avoid duplicate records, notify the lead and sales team, and see what happened. This MVP centralizes that flow in a small Python application.

## Features

- Responsive website lead form and CSV upload.
- Shared validation and processing logic for both sources.
- Case-insensitive duplicate prevention using trimmed, lowercase email addresses and a SQLite unique constraint.
- Welcome and sales notification emails over SMTP; configuration and delivery issues are recorded without losing a lead.
- Dashboard statistics, searchable/filterable lead table, and recent activity.
- REST API for lead CRUD, CSV import, statistics, and logs.
- CSV imports report totals and keep going when individual rows are invalid or fail.

## Tech stack

Python 3.13, FastAPI, SQLite, Jinja2, HTML/CSS/JavaScript, SMTP, pytest.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the flow diagram and component responsibilities.

## Database design

`leads` stores contact details, source (`Website` or `CSV`), pipeline status, and timestamps. Email is unique with case-insensitive comparison. `logs` stores processing actions, outcomes, messages, optional lead references, and timestamps. Deleting a lead retains its log history and clears the log's lead reference.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Website lead form and CSV upload |
| GET | `/dashboard` | Dashboard UI |
| POST | `/api/leads` | Create a website lead |
| GET | `/api/leads` | List leads; optional `q` and `status` filters |
| GET | `/api/leads/{id}` | Fetch one lead |
| PATCH | `/api/leads/{id}` | Update lead fields/status |
| DELETE | `/api/leads/{id}` | Delete a lead |
| POST | `/api/leads/import` | Import multipart CSV file |
| GET | `/api/stats` | Dashboard counters |
| GET | `/api/logs` | Recent logs; optional `limit` (max 500) |

## Chatbot (free)

A floating chat widget (bottom-right on every page) answers questions and captures leads through the same `process_lead` pipeline as the form and CSV import (validation, duplicate check, emails, logs). Chatbot leads have source `Chatbot` and appear in `/api/stats` as `chatbot_leads`.

**It works with zero setup** using a built-in offline bot (FAQ + guided lead capture). For real AI answers, add a free key to `.env`:

| Provider | Free key | Env var |
|---|---|---|
| Groq (default, `llama-3.3-70b-versatile`) | https://console.groq.com/keys | `GROQ_API_KEY` |
| Google Gemini (backup, `gemini-2.5-flash`) | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |

Order: Groq, then Gemini, then the offline bot, so a rate limit or outage never leaves the visitor without an answer. Override with `CHAT_PROVIDER`, `GROQ_MODEL`, `GEMINI_MODEL`. Free-tier model names change over time; update the env vars if a model is retired.

- Teach the bot about your business by editing `app/knowledge.md` (no code changes).
- Endpoints: `POST /api/chat` (`session_id`, `messages`), `GET /api/chat/status` (active provider).
- Protection: 20 messages/minute per IP, 1000 characters per message, last 12 messages sent to the model.
- Keep API keys in `.env` only (already git-ignored); never put them in front-end code.

## Installation and setup

Requires Python 3.13. From the project directory:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set SMTP values if email delivery is desired. Email remains optional: missing configuration is recorded in the activity log. Set `DATABASE_PATH` only when you want the SQLite file at a different location. The app loads `.env` automatically.

## Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Dashboard: http://127.0.0.1:8000/dashboard. API documentation: http://127.0.0.1:8000/docs.

Docker: copy `.env.example` to `.env`, then run `docker compose up --build`. SQLite data is held in the `lead_data` named volume.

## Import CSV

Use a UTF-8 `.csv` file with headers `name,email,company,message`. A sample is in `sample_data/sample_leads.csv`. The UI shows total rows, successful imports, duplicates, invalid rows, failed rows, and row-level errors. The API accepts the file as multipart field `file`.

## Duplicate handling

The system trims and lowercases email addresses before storage. The unique database index uses `COLLATE NOCASE`, so capitalization variants are also rejected atomically. Duplicate submissions create a log entry and return HTTP 409; CSV duplicates are counted and skipped.

## Validation and error handling

Name, email, company, and message are required. Email is checked for a valid basic address shape and normalized. API input errors return useful 422 responses, duplicates return 409, missing records return 404, and malformed CSV files return 400. Individual import row errors are logged and do not interrupt later rows. SMTP settings and delivery problems are logged while the lead remains saved. Database exceptions are handled per CSV row where possible; application-level failures are visible through FastAPI error responses.

## Tests

```bash
python -m pytest
```

Tests use a temporary SQLite database and cover lead creation, invalid and missing values, duplicate behavior, CSV import, and statistics.

## Future improvements

- Add authentication and role-based access to the dashboard and API.
- Add pagination, richer filtering, and export.
- Use a background task queue for email retries and delivery state.
- Add migrations and structured application metrics for larger deployments.
- Add stricter internationalized email validation and configurable lead status workflows.
