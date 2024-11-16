import spacy
from spacy.matcher import Matcher
import PyPDF2
import os
from datetime import datetime
import re
import math

# Load the Spacy English model
nlp = spacy.load('en_core_web_sm')
import csv
from spacy.matcher import Matcher
import csv

# Read skills from CSV file
file_path=os.path.join('data', 'tech_skills_clean.csv')
with open(file_path, 'r') as file:
    csv_reader = csv.reader(file)
    skills = [row for row in csv_reader]

# Create pattern dictionaries from skills
skill_patterns = [[{'LOWER': skill}] for skill in skills[0]]

#print(skill_patterns)

# Create a Matcher object
matcher = Matcher(nlp.vocab)

# Add skill patterns to the matcher
for pattern in skill_patterns:
    matcher.add('Skills', [pattern])

# Function to extract skills from text
def extract_skills(text):
    doc = nlp(text)
    matches = matcher(doc)
    skills = set()
    for match_id, start, end in matches:
        skill = doc[start:end].text
        skills.add(skill)
    l = []
    for i in list(skills):
        if not i.isnumeric() and i.lower() != 'computer':
            l.append(i)
    skills = sorted(l)
    return skills

# Function to extract text from PDF
def extract_text_from_pdf(file_path:str):
    with open(file_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def parse_date(date_str):  
    # Attempt to parse both full and abbreviated month names  
    for fmt in ("%B %Y", "%b %Y"):  # Full and abbreviated month formats  
        try:  
            return datetime.strptime(date_str.strip(), fmt)  
        except ValueError:  
            continue  
    raise ValueError(f"Date format not recognized: {date_str}")  

def calculate_years_of_experience(work_experience_text):  
    total_years = 0  
    # Pattern to match various date formats (e.g., "Jan 2020 - Dec 2022", "2018 - 2021", "March 2015 to Present")  
    pattern = re.compile(r'(\w+\s\d{4})\s*[-to]+\s*(\w+\s\d{4}|Present)', re.IGNORECASE)  
    matches = pattern.findall(work_experience_text)  
    
    for start_date, end_date in matches:  
        if end_date.lower() == 'present':  
            end_date = datetime.now().strftime("%b %Y")  # Get the current date in 'Jan 2024' format  

        # Convert the string dates to actual date objects  
        start = parse_date(start_date)  # Example: 'Jan 2020'  
        end = parse_date(end_date)      # Example: 'Dec 2022'  
        
        years = (end - start).days / 365.25  # Approximate year calculation  
        total_years += years  
    
    return math.ceil(total_years) 

def workd_exp_extractor(file_path):
    path=r'resume'
    full_file_path = os.path.join(path, file_path)
    resume_text = extract_text_from_pdf(full_file_path)
    total_years = 0
    #if work_experience_text:
    total_years = calculate_years_of_experience(resume_text)
    if total_years == 0: total_years = 10
    #print('Work Experience = ', total_years)
    return total_years


def skills_extractor(file_path, convert_to_string = False):
    # Extract text from PDF
    path=r'resume'
    full_file_path = os.path.join(path, file_path)
    resume_text = extract_text_from_pdf(full_file_path)

     # Extract skills from resume text
    skills = list(extract_skills(resume_text))
    skills = list(set([skill.title() for skill in skills]))
    l = []
    for i in range(len(skills)):
        if not skills[i].isnumeric():
            l.append(skills[i])
    skills = sorted(l)
    #print(skills)
     #print(resume_text)
    
    if convert_to_string:
        return ' '.join(skills)
    return skills
