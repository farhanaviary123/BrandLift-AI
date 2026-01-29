# Deploy BrandLift AI to Vercel (only app-related files)

This project is set up so **only the files used by the web app** are considered for deployment. Other files in the repo are ignored via `.vercelignore`.

## Files that are deployed (used by the app)

| File / folder        | Purpose |
|---------------------|--------|
| `index.html`        | Landing page: URL input, “Generating moodboard…”, redirect to moodboard |
| `moodboard.html`    | Moodboard page: reads data from sessionStorage (or `brand_analysis.json` locally) |
| `api/analyze.py`    | Serverless API: accepts URL, runs brand analysis, returns JSON (no file write) |
| `gpt_web_descrirption.py` | Brand analyzer used by `api/analyze.py` |
| `brand_analysis.json`     | Optional: placeholder or default data; on Vercel, real data comes from API → sessionStorage |
| `requirements.txt`   | Python dependencies for the serverless function |
| `vercel.json`       | Vercel config (functions, optional rewrites) |
| `.vercelignore`     | Excludes all other files/folders from deploy |

## What gets excluded (not deployed)

Everything else is ignored by Vercel thanks to `.vercelignore`, including:

- `app.py` (Flask; not used on Vercel)
- `Demo Codes/`, `venv/`, backup files, other scrapers, tests, etc.

So only the app-related files above are part of the deployment.

---

## Procedure: How to deploy

### 1. Prerequisites

- [Vercel account](https://vercel.com/signup)
- Git repo with the project (or use Vercel CLI without Git)
- **OpenAI API key** (for brand analysis)

### 2. Set environment variable on Vercel

The serverless function needs your OpenAI key:

1. In the [Vercel dashboard](https://vercel.com/dashboard), open your project.
2. Go to **Settings → Environment Variables**.
3. Add:
   - **Name:** `OPENAI_API_KEY`
   - **Value:** your OpenAI API key
   - **Environment:** Production (and Preview if you want)

Save.

### 3. Deploy

**Option A – Deploy with Vercel (Git)**

1. Push your repo to GitHub / GitLab / Bitbucket.
2. Go to [vercel.com/new](https://vercel.com/new).
3. Import the repository.
4. **Root Directory:** leave as default (repo root).
5. **Framework Preset:** Other (or leave as detected).
6. Do **not** set a custom Build Command or Output Directory (static + serverless).
7. Add `OPENAI_API_KEY` in **Environment Variables** (if you didn’t in step 2).
8. Click **Deploy**.

Vercel will use `vercel.json` and `.vercelignore`, so only the app-related files are deployed.

**Option B – Deploy with Vercel CLI (no Git)**

1. Install CLI: `npm i -g vercel`
2. In the project root (where `vercel.json` and `index.html` are):
   ```bash
   cd "d:\BrandLift AI"
   vercel
   ```
3. Log in if asked, link to a (new or existing) Vercel project.
4. Add `OPENAI_API_KEY` in the project’s **Environment Variables** in the dashboard (see step 2 above).
5. Redeploy if you added the env var after first deploy: `vercel --prod`

### 4. After deploy

- **Landing page:** `https://<your-project>.vercel.app/` (serves `index.html`).
- **Moodboard:** `https://<your-project>.vercel.app/moodboard.html` (works after generating from home, or with `brand_analysis.json` in dev).
- **API:** `POST https://<your-project>.vercel.app/api/analyze` with body `{ "url": "https://example.com" }`.

Flow:

1. User enters URL on the landing page.
2. Page shows “Generating the moodboard for you…”
3. Frontend calls `/api/analyze` with the URL.
4. Backend runs `gpt_web_descrirption` and returns the analysis JSON (no file write).
5. Frontend saves the JSON in `sessionStorage` and redirects to `/moodboard.html`.
6. Moodboard reads from `sessionStorage` and renders; if none, it tries `brand_analysis.json` (e.g. local dev).

---

## Local run (unchanged)

- **Flask (full app):**  
  `python app.py`  
  Then open `http://localhost:5000/`.

- **Vercel dev (optional):**  
  `vercel dev`  
  Simulates Vercel (static + serverless) locally.

---

## Summary

- **Only app-related files are deployed:** `index.html`, `moodboard.html`, `api/analyze.py`, `gpt_web_descrirption.py`, `brand_analysis.json` (optional), `requirements.txt`, `vercel.json`, `.vercelignore`.
- **Procedure:** set `OPENAI_API_KEY` on Vercel → deploy via Git import or `vercel` CLI.
- **Flow:** URL on home → “Generating moodboard…” → backend runs analyzer → response stored in sessionStorage → redirect to moodboard → moodboard reads sessionStorage (or JSON locally).
