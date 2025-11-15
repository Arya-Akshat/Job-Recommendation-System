
import os
import json
import base64
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Dict, Any
import shutil # For file operations
import tempfile # For secure temporary file handling

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path to find the other modules
# This is important because skills_extraction and job_recommendor are now in the same directory as app.py
# sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# No need for sys.path.append if they are in the same directory or imported relatively

import skills_extraction
import job_recommendor
try:
    import web_scraper as web_scraper
except Exception:
    # Fall back to the local placeholder if the real scraper cannot be imported
    import web_scraper_local as web_scraper
import google.generativeai as genai
import traceback
from google.api_core import exceptions as api_exceptions

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Job Recommendation Backend API",
    description="API for processing resumes, recommending jobs, and providing upskilling suggestions.",
    version="1.0.0",
)

# Allow CORS from the frontend dev server(s) and production
# Note: FastAPI CORS doesn't support wildcard subdomains, so we use allow_origin_regex
import re

allowed_origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add custom origins if provided
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments (production + previews)
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # Do not raise on import — keep the app running but disable Gemini features.
    print("Warning: GEMINI_API_KEY not set. /upskill_suggestions will be unavailable.")
    genai = None
else:
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_SYSTEM_PROMPT = (
    "You are an expert at deciding work domain. "
    "Analyze the following prompt given by the user which has a list of skills they know:\n\n"
    "Prompt: {user_prompt}\n\n"
    "Tell job role and provide links to three educative courses of other necessary skills required in that field along with:\n"
    "1. Duration\n"
    "2. Paid or free\n"
    "3. link to resource\n"
    "4. Opportunities\n"
)

# --- Pydantic Models for Request/Response ---

class ProcessResumeResponse(BaseModel):
    skills: List[str]
    experience: int

class RecommendJobsRequest(BaseModel):
    user_skills: List[str]
    user_experience: int

class RecommendJobsResponse(BaseModel):
    recommendations: List[Dict[str, Any]]

class UpskillSuggestionsRequest(BaseModel):
    skills: List[str]

class UpskillSuggestionsResponse(BaseModel):
    suggestions: str

class FetchJobsResponse(BaseModel):
    new_jobs_count: int
    message: str

# --- API Endpoints ---

@app.get("/")
@app.head("/")
async def root():
    """Health check endpoint - supports both GET and HEAD methods"""
    return {
        "message": "Job Recommendation Backend API",
        "version": "1.0.0",
        "status": "running",
        "cors_enabled": True
    }

@app.post("/process_resume", response_model=ProcessResumeResponse)
async def process_resume_endpoint(file: UploadFile = File(...)):
    """
    Uploads a PDF resume, extracts skills and work experience.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # Save the uploaded file temporarily
    # Use tempfile to create a secure temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name

    try:
        skills, experience = skills_extraction.process_resume_from_path(temp_file_path)
        return ProcessResumeResponse(skills=skills, experience=experience)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/recommend_jobs", response_model=RecommendJobsResponse)
async def recommend_jobs_endpoint(request: RecommendJobsRequest):
    """
    Generates job recommendations based on user skills and experience.
    """
    try:
        recommendations_df = job_recommendor.get_recommendations(
            user_skills_list=request.user_skills,
            user_work_experience=request.user_experience
        )
        # Convert DataFrame to a list of dictionaries for JSON response
        recommendations_list = recommendations_df.to_dict(orient="records")
        return RecommendJobsResponse(recommendations=recommendations_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {e}")


@app.post("/upskill_suggestions", response_model=UpskillSuggestionsResponse)
async def upskill_suggestions_endpoint(request: UpskillSuggestionsRequest):
    """
    Provides AI-powered upskilling suggestions based on user skills.
    Uses Gemini Flash (faster model) with optimized prompting.
    """
    if not genai:
        raise HTTPException(status_code=503, detail="AI service not configured. Set GEMINI_API_KEY environment variable.")
    
    # Use Flash model for faster responses
    model = genai.GenerativeModel(
        model_name="models/gemini-2.0-flash-exp",  # Faster Flash model
        system_instruction=GEMINI_SYSTEM_PROMPT
    )

    # Optimized prompt for faster response
    user_prompt = f"Skills: {', '.join(request.skills[:10])}"  # Limit to 10 skills for speed
    
    try:
        # Use non-streaming for simpler response
        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=800,  # Limit response length for speed
                temperature=0.7,
            )
        )
        suggestions = response.text
        return UpskillSuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        # Log full traceback for debugging
        tb = traceback.format_exc()
        print("Gemini API error (traceback):", tb)
        # Additional diagnostics: print exception type, repr, and common attributes
        try:
            print("Gemini exception type:", type(e))
            print("Gemini exception repr:", repr(e))
            # Print useful diagnostic attributes if present
            for attr in ('status_code', 'code', 'status', 'message', 'errors'):
                try:
                    val = getattr(e, attr, None)
                    if val is not None:
                        print(f"Gemini exception {attr}:", val)
                except Exception:
                    pass
        except Exception:
            # If even printing diagnostics fails, ignore to avoid masking original traceback
            pass

        # Normalize text for string checks
        error_str = str(e).lower()

        # 1) Prefer checking well-known google api exception classes
        try:
                debug_name = type(e).__name__ if e is not None else "UnknownException"
                if isinstance(e, api_exceptions.ResourceExhausted):
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            "AI service quota exceeded. The free tier has daily limits. Please try again later or upgrade your Gemini API plan."
                            f" (debug_exception: {debug_name})"
                        )
                    )
                if isinstance(e, api_exceptions.RateLimitExceeded):
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            "AI service rate limit exceeded. Please retry later."
                            f" (debug_exception: {debug_name})"
                        )
                    )
                if isinstance(e, api_exceptions.Unauthenticated) or isinstance(e, api_exceptions.PermissionDenied):
                    raise HTTPException(
                        status_code=401,
                        detail=(
                            "AI service authentication failed. Please check your GEMINI_API_KEY."
                            f" (debug_exception: {debug_name})"
                        )
                    )
        except NameError:
            # api_exceptions may not define all names on every version; ignore and fall back to string checks
            pass

        # 2) Fallback to robust string / attribute checks
        status_code = None
        for attr in ('status_code', 'code', 'status'):
            if hasattr(e, attr):
                try:
                    status_code = int(getattr(e, attr))
                    break
                except Exception:
                    # sometimes code is an enum or string
                    val = getattr(e, attr)
                    try:
                        if hasattr(val, 'value'):
                            status_code = int(val.value)
                            break
                    except Exception:
                        pass

        debug_name = type(e).__name__ if e is not None else "UnknownException"
        if status_code == 429 or any(k in error_str for k in ['quota', 'resource_exhausted', 'rate limit', 'rate_limit', '429']):
            raise HTTPException(
                status_code=429,
                detail=(
                    "AI service quota or rate limit exceeded. The free tier has daily limits. Please try again later or upgrade your Gemini API plan."
                    f" (debug_exception: {debug_name})"
                )
            )

        if status_code in (401, 403) or any(k in error_str for k in ['api key', 'authentication', 'permission denied', 'unauthorized']):
            raise HTTPException(
                status_code=401,
                detail=(
                    "AI service authentication failed. Please check your GEMINI_API_KEY."
                    f" (debug_exception: {debug_name})"
                )
            )

        # Default: surface the raw error for easier debugging
        # Default: surface the raw error message but append only the exception class name for quick debugging
        raise HTTPException(
            status_code=500,
            detail=(f"AI service error: {str(e)} (debug_exception: {type(e).__name__})")
        )

@app.post("/fetch_new_jobs", response_model=FetchJobsResponse)
async def fetch_new_jobs_endpoint():
    """
    Triggers the web scraper to fetch new job listings and completely refresh job_data.csv.
    This replaces the entire job list with fresh data from the website.
    """
    try:
        total_jobs_count = web_scraper.fetch_and_update_jobs()
        message = f"Job database refreshed. Total jobs in database: {total_jobs_count}"
        
        return FetchJobsResponse(
            new_jobs_count=total_jobs_count,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching new jobs: {e}")

# --- Main execution for Uvicorn ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
