# NestMatch — Real Estate AI Agent MVP (Discovery Demo)

A polished, clickable demo for a real estate brokerage discovery meeting. It demonstrates:

- Buyer chat with free-text property requests
- Extraction of city, maximum budget, minimum bedrooms, preferences and property type
- Hybrid-style matching demonstration: hard numeric/categorical filters + preference ranking
- Matched property cards and agent contact form
- CRM lead handoff (SQLite persistence when the Python backend is running)
- Listing inventory, filters, lead dashboard and overview
- Responsive React interface

**Transparency:** This MVP is a **demo**. It does not call OpenAI or Claude, use embeddings/pgvector, import MLS listings, send email, or connect to a real brokerage CRM. It uses eight **synthetic listings** and deterministic rule-based intent extraction/ranking. The frontend works independently even if the backend is offline (leads then remain only in browser memory). If backend is online, captured leads persist to SQLite. Image URLs load from Unsplash and require network access. No authorization is present, so do not expose the demo backend to real customer data.

## Quick start

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173

### Optional FastAPI backend
Open a second terminal:
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Backend API docs: http://localhost:8000/docs

To point Vite to the local backend, create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
```
Restart Vite afterward. Without this variable, Vite sends `/api` to its own origin and automatically uses the frontend's deterministic demo fallback instead.

## Deploy
- **Vercel frontend:** Import `frontend` as the project root. Framework: Vite. Build: `npm run build`. Output: `dist`. It will work in frontend-only demo mode.
- **Backend:** Host the `backend` folder on a Python-enabled service with persistent disk storage, start with `uvicorn main:app --host 0.0.0.0 --port $PORT`, and set `VITE_API_URL` on the Vercel frontend to its public HTTPS URL. Configure `ALLOWED_ORIGINS` as your frontend domain. Never deploy this demo API with live PII without authentication, rate limits, and security hardening.

## API contracts
- `GET /api/health`
- `GET /api/listings`
- `POST /api/match` body `{ "message": "3 bedroom Austin under $650k with parking" }`
- `GET /api/leads`
- `POST /api/leads` buyer contact and preferences

## Production architecture after discovery
Use: React + FastAPI, OpenAI/Claude (structured extraction + guided qualification), PostgreSQL + pgvector (hybrid retrieval, filtering, and semantic similarity), authenticated agent/admin dashboards, actual listing ingestion/update jobs, CRM webhooks, trace logs, evaluation dataset, consent and PII protections. This is **future work**, not claimed as implemented.

## Suggested live demo flow
1. In Discover, select the first sample prompt.
2. Show extracted preferences and filtered listings.
3. Capture a buyer as a lead.
4. Go to Leads and show the new record.
5. Visit Listings and Overview.
6. Discuss extending the prototype to actual customer listing data and CRM.
