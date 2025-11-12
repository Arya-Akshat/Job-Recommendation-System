import os
import re
import math
import csv
from datetime import datetime
import spacy
from spacy.matcher import Matcher
import PyPDF2

# --- Constants ---
SKILLS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tech_skills_clean.csv')

# --- Globals for Lazy Loading ---
nlp = None
matcher = None

# Flag set when spaCy is unavailable
SPACY_AVAILABLE = True

# --- Initialization ---

def initialize_matcher():
    """
    Loads the spacy model and skills matcher on first use.
    This avoids loading them on module import.
    """
    global nlp, matcher, spacy, Matcher, SPACY_AVAILABLE
    if nlp is not None or not SPACY_AVAILABLE:
        return  # Already initialized or previously disabled

    print("Attempting to load spaCy model and skills matcher...")
    try:
        # Lazy import so the rest of the app can run without spaCy installed
        import importlib
        spacy = importlib.import_module('spacy')
        spacy_matcher = importlib.import_module('spacy.matcher')
        Matcher = getattr(spacy_matcher, 'Matcher')
    except Exception:
        # If spaCy isn't available, note it and disable matcher functionality.
        SPACY_AVAILABLE = False
        print("spaCy not available: skill extraction will be disabled.")
        return

    try:
        nlp = spacy.load('en_core_web_sm')
    except OSError:
        print("Error: 'en_core_web_sm' model not found. Skill matching will be disabled.")
        SPACY_AVAILABLE = False
        return

    matcher = Matcher(nlp.vocab)
    
    try:
        # Read all skills from the CSV, flatten rows and columns
        skills = []
        with open(SKILLS_CSV_PATH, 'r', newline='') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                for cell in row:
                    cell = cell.strip()
                    if cell:
                        skills.append(cell)

        # Build token-based patterns that tolerate punctuation and multi-word skills.
        def _normalize_skill_text(s: str) -> str:
            # Replace common punctuation used in skill names with spaces so tokens match
            return re.sub(r'[\.#\+\-/]', ' ', s).strip()

        patterns_added = 0
        for skill in skills:
            norm = _normalize_skill_text(skill)
            tokens = [t for t in norm.split() if t]
            if not tokens:
                continue
            pattern = [{'LOWER': t.lower()} for t in tokens]
            try:
                # Use skill text as the matcher ID so we can see what matched
                matcher.add(skill, [pattern])
                patterns_added += 1
            except Exception:
                # Some matcher implementations require unique ids; ignore duplicates
                try:
                    matcher.add('SKILL', [pattern])
                    patterns_added += 1
                except Exception:
                    continue

        if patterns_added == 0:
            print(f"Warning: No skill patterns were added from {SKILLS_CSV_PATH}. Skill matching will be limited.")
        else:
            print(f"Loaded {patterns_added} skill patterns from {SKILLS_CSV_PATH}.")
    except FileNotFoundError:
        print(f"Warning: Skill file not found at {SKILLS_CSV_PATH}. Skill matching will be disabled.")
    
    print("Initialization complete.")

# --- Core Functions ---

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ''.join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        return text
    except FileNotFoundError:
        print(f"Error: Resume file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""

def _extract_skills_from_text(text: str) -> set[str]:
    """Extracts skills from text using the spaCy matcher."""
    initialize_matcher()
    if not text or nlp is None:
        return set()

    doc = nlp(text)
    matches = matcher(doc)
    
    skills = set()
    for _, start, end in matches:
        skill = doc[start:end].text
        if not skill.isnumeric() and skill.lower() != 'computer':
            skills.add(skill.title())
            
    return skills

def _extract_work_experience_from_text(text: str) -> int:
    """Calculates total years of work experience from text."""
    
    def parse_date(date_str: str):
        """Helper to parse various date formats."""
        for fmt in ("%B %Y", "%b %Y"):  # Full and abbreviated month
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    total_years = 0
    pattern = re.compile(r'(\w+\s\d{4})\s*[-to]+\s*(\w+\s\d{4}|Present)', re.IGNORECASE)
    matches = pattern.findall(text)
    
    for start_date_str, end_date_str in matches:
        start_date = parse_date(start_date_str)
        
        if end_date_str.lower() == 'present':
            end_date = datetime.now()
        else:
            end_date = parse_date(end_date_str)
            
        if start_date and end_date:
            years = (end_date - start_date).days / 365.25
            total_years += years
            
    return math.ceil(total_years) if total_years > 0 else 10 # Return default 10 if 0

# --- Public Functions (to be called from other modules) ---

def process_resume_from_path(file_path: str) -> tuple[list[str], int]:
    """
    Processes a resume file to extract skills and work experience.
    Returns a tuple of (skills_list, experience_years).
    """
    resume_text = extract_text_from_pdf(file_path)
    skills_set = _extract_skills_from_text(resume_text)
    experience = _extract_work_experience_from_text(resume_text)
    
    return sorted(list(skills_set)), experience

# Deprecated functions, kept for compatibility if needed elsewhere
def skills_extractor(file_path: str, convert_to_string: bool = False):
    """
    High-level function to extract skills from a resume file.
    Maintained for compatibility with job_recommendor.py
    """
    skills_list, _ = process_resume_from_path(file_path)
    if convert_to_string:
        return ' '.join(skills_list)
    return skills_list

def workd_exp_extractor(file_path: str) -> int:
    """
    High-level function to extract work experience from a resume file.
    Maintained for compatibility with job_recommendor.py
    """
    _, experience = process_resume_from_path(file_path)
    return experience
