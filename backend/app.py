
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

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Job Recommendation Backend API",
    description="API for processing resumes, recommending jobs, and providing upskilling suggestions.",
    version="1.0.0",
)

# Allow CORS from the frontend dev server(s)
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    """
    model = genai.GenerativeModel(
        model_name="models/gemini-2.5-flash", # Use the model confirmed to be available
        system_instruction=GEMINI_SYSTEM_PROMPT
    )
    if not model:
        raise HTTPException(status_code=500, detail="Gemini model not configured.")

    user_prompt = "Skills = " + ','.join(request.skills)
    
    try:
        response = model.generate_content(user_prompt, stream=True)
        suggestions = "".join(word.text for word in response)
        return UpskillSuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating upskilling suggestions: {e}")

@app.post("/fetch_new_jobs", response_model=FetchJobsResponse)
async def fetch_new_jobs_endpoint():
    """
    Triggers the web scraper to fetch new job listings and update job_data.csv.
    """
    try:
        new_jobs_count = web_scraper.fetch_and_update_jobs()
        return FetchJobsResponse(
            new_jobs_count=new_jobs_count,
            message=f"Successfully fetched and updated {new_jobs_count} new job listings."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching new jobs: {e}")

# --- Main execution for Uvicorn ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
