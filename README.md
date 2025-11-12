
# Job Recommendation System

A modern job recommendation system that ingests a candidate's resume, extracts skills and experience, and returns ranked job matches and AI-powered upskill suggestions.

This repository contains a full-stack prototype with:
- a Python FastAPI backend that handles resume parsing, skill extraction, job scoring, and optional AI (Gemini) upskill suggestions;
- a React + TypeScript frontend (Vite) that provides a UI for uploading resumes, requesting recommendations, and viewing AI suggestions;
- a small corpus of sample data and utilities for scraping and preparing job listings.

## High-level architecture

1. User uploads a resume from the frontend (drag-and-drop or file picker).
2. Frontend posts the resume to the backend `/process_resume` endpoint.
3. Backend parses the PDF (PyPDF2 or helper scripts), extracts skills using `skills_extraction.py`, and returns a JSON payload with detected skills and experience.
4. The frontend displays the parsed skills and lets the user request job recommendations or AI upskill suggestions.
5. When the user requests recommendations the frontend calls `/recommend_jobs` with the parsed skills; the backend's `job_recommendor.py` ranks jobs from `data/job_data.csv` using TF-IDF + cosine similarity and returns a ranked list.
6. If enabled, the frontend can call `/upskill_suggestions` which uses the configured Gemini API key to call the AI model and receive personalized upskill suggestions.

## Repository layout (important files)

- `backend/`
	- `app.py` - FastAPI application and HTTP endpoints (resume processing, recommendations, suggestions).
	- `skills_extraction.py` - logic to normalize text and extract technical skills from resumes using token patterns and the skills CSV.
	- `job_recommendor.py` - ranking logic (TF-IDF, cosine similarity) that scores jobs from `data/job_data.csv` against user skills.
	- `web_scraper.py` - web scraper to gather job listings (can be replaced by `web_scraper_local.py` as a safe fallback).
	- `create_test_pdf.py` - helper used to generate a `data/test_resume.pdf` for testing.
	- `venv_backend/` - Python virtual environment (not tracked in git; should be ignored).

- `frontend/` (Vite + React + TypeScript)
	- `src/pages/Index.tsx` - main landing page, resume upload UI and buttons for "AI suggestions" and "Fetch new jobs".
	- `src/components/ResumeUpload.tsx` - resume file input and upload handling.
	- `src/components/JobCard.tsx` - present job results.
	- `package.json` / `vite.config.ts` / `tailwind.config.ts` - frontend tooling and dependencies.

- `data/`
	- `job_data.csv` - scraped and deduped job listings used for ranking.
	- `tech_skills_clean.csv` - canonical list of technical skills used by the extractor.
	- `test_resume.pdf` - a sample resume used for testing the pipeline.

- top-level
	- `clean_csv.py`, `web_scraper.py` (legacy), and utilities for data preparation.
	- `.gitignore` - updated to ignore `backend/.env` and the backend venv.

## How components connect (detailed flows)

- Resume upload flow
	- Frontend: user selects a PDF; `ResumeUpload.tsx` sends a POST multipart/form-data to `http://localhost:8000/process_resume`.
	- Backend: `app.py` receives file → `skills_extraction.py` extracts skills & experience → backend returns JSON shape:
		```json
		{
			"skills": ["python", "pandas", "sql"],
			"years_experience": 3.5,
			"raw_text": "..."
		}
		```

- Recommendation flow
	- Frontend sends parsed skills (or lets backend re-run extraction) to `POST /recommend_jobs`.
	- Backend loads `data/job_data.csv`, vectorizes job descriptions and candidate profile (TF-IDF), computes cosine similarity, and returns a list of top-N jobs with metadata and score.

- AI upskill suggestions (optional)
	- Requires `GEMINI_API_KEY` set in `backend/.env` (or ENV). If not set, the endpoint returns a helpful message indicating AI suggestions are disabled.
	- Endpoint: `POST /upskill_suggestions` with skills and optionally desired role. Backend forwards request to the configured Gemini model and formats response for the frontend.

## Running locally (development)

1. Backend

	- Create & activate Python venv (recommended):

		```bash
		cd backend
		python3 -m venv venv_backend
		source venv_backend/bin/activate
		pip install -r ../requirements.txt
		```

	- Start the FastAPI server (from `backend/`):

		```bash
		./venv_backend/bin/python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
		```

	- Endpoints:
		- GET `/docs` - OpenAPI docs
		- POST `/process_resume` - accepts resume file
		- POST `/recommend_jobs` - accepts skills/profile and returns ranked jobs
		- POST `/upskill_suggestions` - optional AI suggestions (requires GEMINI API key)

2. Frontend

	- From the repo root:

		```bash
		cd frontend
		npm install
		npm run dev
		```

	- Open the Vite dev server (usually http://localhost:5173) and use the UI to upload a resume and request results.

## Environment variables

- `backend/.env` (recommended, not checked into git):
	- GEMINI_API_KEY=your_gemini_api_key_here

The repository `.gitignore` already contains `backend/.env` entries — do not commit secrets.

## Testing quick examples

- Process the sample resume with curl (backend must be running):

	```bash
	curl -X POST "http://127.0.0.1:8000/process_resume" -F "file=@data/test_resume.pdf"
	```

- Request recommendations (JSON example):

	```bash
	curl -X POST "http://127.0.0.1:8000/recommend_jobs" -H "Content-Type: application/json" \
		-d '{"skills": ["python","pandas","sql"], "years_experience": 3}'
	```

## Notes, caveats and maintenance

- Large files: there are large binaries in the repository history (for example under `backend/venv_backend/...`). These increase clone size and trigger GitHub warnings. To remove them fully from history use `git-filter-repo` or BFG and then force-push the cleaned history. (This repo already contains a backup branch `backup-before-author-rewrite`.)
- Don't commit virtual environments or `.env` files. Keep secrets out of git.
- If you recreate the frontend `node_modules` or the backend venv, run the install commands above rather than checking them in.

## Who to contact / authorship

This copy of the repo has been prepared and normalized to the primary maintainer: `Arya-Akshat <akshat.arya13@gmail.com>`.

---

If you'd like, I can add a short CONTRIBUTING.md with developer notes (test matrix, linters, or CI) or remove the backup branch from the remote once you confirm everything looks correct.
