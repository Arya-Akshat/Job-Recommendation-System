import re
import json
import os
from ftfy import fix_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from typing import List, Set
import skills_extraction

# --- Constants ---
CONFIDENCE_WEIGHT = 0.7
EXPERIENCE_WEIGHT = 0.03
SKILL_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), 'skill_weights.json')
JOB_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'job_data.csv')
RECOMMENDATIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'job_recommendations.csv')

# --- Helper Functions ---

def ngrams(string: str, n: int = 3) -> list[str]:
    """Preprocesses text and creates n-grams."""
    string = fix_text(string)
    string = string.encode("ascii", errors="ignore").decode()
    string = string.lower()
    chars_to_remove = [")", "(", ".", "|", "[", "]", "{", "}", "'"]
    rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
    string = re.sub(rx, '', string)
    string = string.replace('&', 'and')
    string = string.replace(',', ' ')
    string = string.replace('-', ' ')
    string = string.title()
    string = re.sub(' +', ' ', string).strip()
    string = ' ' + string + ' '
    string = re.sub(r'[,-./]|\sBD', r'', string)
    ngrams = zip(*[string[i:] for i in range(n)])
    return [''.join(ngram) for ngram in ngrams]

def extract_skilling(jd: str) -> str:
    """Extracts and cleans skills from a job description."""
    # Ensure jd is a string before passing to skills_extraction.extract_skills
    if not isinstance(jd, str):
        jd = str(jd) # Convert to string if it's not already
    
    # Note: skills_extraction._extract_skills_from_text is an internal function
    # We should ideally pass the text to a public function or re-evaluate this.
    # For now, assuming skills_extraction.extract_skills is the public one.
    # This will be handled by the FastAPI app calling skills_extraction directly.
    # So, this function will be removed from here.
    pass # This function will be removed from here.

def calculate_experience_score(required_experience: float, user_experience: int) -> int:
    """Calculates the experience score."""
    return 1 if user_experience >= required_experience else 0

def find_strengths(job_skills: str, user_skills: Set[str]) -> str:
    """Finds matching skills between the job and the user."""
    job_skills_set = set(job_skills.split())
    strengths = job_skills_set & user_skills
    return ' '.join(list(strengths)[:5])

def find_weaknesses(job_title: str, user_skills: Set[str], job_skill_weights: dict) -> str:
    """Finds skills the user is lacking for a specific job title."""
    job_keys = list(job_skill_weights.keys())
    job_role = 'Engineer'  # Default role
    for key in job_keys:
        if key.lower() in job_title.lower():
            job_role = key
            break
    
    skills_required = set(job_skill_weights.get(job_role, {}).keys())
    skills_lacking = skills_required - user_skills
    
    # Sort lacking skills by their weight (importance)
    lacking_with_weights = [(job_skill_weights[job_role].get(skill, 0), skill) for skill in skills_lacking]
    weakness = sorted(lacking_with_weights, reverse=True)[:3]
    
    return ' '.join(i[1] for i in weakness)

# --- Main Recommendation Logic ---

def get_recommendations(user_skills_list: List[str], user_work_experience: int) -> pd.DataFrame:
    """
    Loads data, processes user profile, and generates job recommendations.
    """
    # --- 1. Load Data and Config ---
    try:
        jd_df = pd.read_csv(JOB_DATA_PATH)
    except FileNotFoundError:
        print(f"Error: {JOB_DATA_PATH} not found.")
        return pd.DataFrame() # Return empty DataFrame on error

    # Ensure a usable Link/apply URL column exists. Some datasets use different
    # column names (e.g. 'Link', 'Detail URL', 'Company Apply Url'). Normalize
    # into a single 'Link' column so the API always returns a consistent field.
    alt_cols = ['Link', 'Company Apply Url', 'Detail URL', 'Detail URL', 'Company']
    if 'Link' not in jd_df.columns:
        jd_df['Link'] = ''

    # For each alternative column, if Link is empty for a row, try to fill it
    # from the alternative column's value.
    for col in ['Company Apply Url', 'Detail URL', 'Company']:
        if col in jd_df.columns:
            def choose_link(row):
                cur = row.get('Link')
                alt = row.get(col)
                if cur is None or cur == '' or (isinstance(cur, float) and pd.isna(cur)):
                    return alt if alt is not None else ''
                return cur
            jd_df['Link'] = jd_df.apply(choose_link, axis=1)

    try:
        with open(SKILL_WEIGHTS_PATH, 'r') as f:
            job_skill_weights = json.load(f)
    except FileNotFoundError:
        print(f"Error: {SKILL_WEIGHTS_PATH} not found.")
        return pd.DataFrame() # Return empty DataFrame on error

    # --- 2. Process User Profile ---
    # Normalize user skills to Title case to match the ngrams/title-casing pipeline used
    # by the `ngrams` function and job skills generation.
    user_skills_str = ' '.join(user_skills_list).title()
    user_skills_set = set(s.title() for s in user_skills_list)
    
    if user_work_experience == 0:
        user_work_experience = 10  # Default experience if not found

    # --- 3. Process Job Descriptions ---
    # This part needs to call skills_extraction.extract_skills directly
    # as extract_skilling is removed.
    jd_df['skills'] = jd_df['Description'].fillna('').apply(
        lambda desc: ' '.join(sorted(list(skills_extraction._extract_skills_from_text(str(desc)))))
    )

    # --- 4. Calculate Similarity ---
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams, lowercase=False)
    tfidf = vectorizer.fit_transform([user_skills_str] + list(jd_df['skills'].values.astype('U')))
    
    skills_tfidf = tfidf[0:1, :]
    jd_tfidf = tfidf[1:, :]
    
    cosine_similarities = cosine_similarity(skills_tfidf, jd_tfidf)
    
    matches = pd.DataFrame(cosine_similarities.T, columns=['Match Confidence'])
    jd_df['Match Confidence'] = matches['Match Confidence']

    # --- 5. Score and Rank Jobs ---
    # Calculate scores for ALL jobs, not just those matching experience requirements
    jd_df['Experience Score'] = jd_df['Required Experience'].apply(
        lambda x: calculate_experience_score(x, user_work_experience)
    )

    # Calculate combined score for all jobs
    jd_df['Combined Score'] = (jd_df['Match Confidence'] * CONFIDENCE_WEIGHT) + (jd_df['Experience Score'] * EXPERIENCE_WEIGHT)
    
    # Normalize the combined scores
    min_score = jd_df['Combined Score'].min()
    max_score = jd_df['Combined Score'].max()
    if max_score > min_score:
        jd_df['Combined Score'] = (jd_df['Combined Score'] - min_score) / (max_score - min_score)
    else:
        jd_df['Combined Score'] = 0.5 # Handle case where all scores are the same

    # --- 6. Finalize Recommendations ---
    # Show jobs with ANY match confidence (even if very low)
    # This ensures we always show at least 10-15 jobs
    recommended_jobs = jd_df[jd_df['Match Confidence'] > 0].copy()
    
    # If still not enough jobs, show all jobs
    if len(recommended_jobs) < 10:
        print(f"Only {len(recommended_jobs)} jobs matched, showing all {len(jd_df)} jobs")
        recommended_jobs = jd_df.copy()

    recommended_jobs['Strengths'] = recommended_jobs['skills'].apply(lambda x: find_strengths(x, user_skills_set))
    recommended_jobs['Weakness'] = recommended_jobs['Title'].apply(lambda x: find_weaknesses(x, user_skills_set, job_skill_weights))
    
    recommended_jobs = recommended_jobs.sort_values(by='Combined Score', ascending=False)

    # Ensure we return at least 10 jobs if available, maximum 25
    min_jobs = min(10, len(recommended_jobs))
    max_jobs = min(25, len(recommended_jobs))
    
    # Return at least 10 jobs, or all if less than 10 available
    if len(recommended_jobs) >= min_jobs:
        recommended_jobs = recommended_jobs.head(max_jobs)
    
    print(f"Returning {len(recommended_jobs)} job recommendations")

    # --- 7. Return Results ---
    # The FastAPI app will handle saving to CSV if needed, or return directly
    return recommended_jobs

if __name__ == '__main__':
    # Example usage for testing
    # This block will not be executed when imported by FastAPI
    print("Running example recommendation...")
    # Create dummy skills_extraction module for testing
    class MockSkillsExtraction:
        def _extract_skills_from_text(self, text):
            # Simple mock for testing
            return set(text.lower().split())
    
    skills_extraction = MockSkillsExtraction()

    dummy_skills = ["Python", "SQL", "AWS", "Machine Learning"]
    dummy_experience = 5
    recommendations_df = get_recommendations(dummy_skills, dummy_experience)
    if not recommendations_df.empty:
        print(recommendations_df[['Title', 'Company Name', 'Combined Score']].head())
    else:
        print("No recommendations generated.")
