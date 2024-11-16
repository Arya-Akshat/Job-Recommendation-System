import streamlit as st
import os
import skills_extraction as skills_extraction
import job_recommendor as job_recommendor
import pandas as pd
import google.generativeai as genai

st.set_page_config(
    page_title="Job Recommendation System",
    layout="wide",
    initial_sidebar_state="expanded",  # Options: "auto", "expanded", "collapsed"
)

RESUME_FOLDER = "resume"
os.makedirs(RESUME_FOLDER, exist_ok=True)


def response_generator(model, user_prompt):
    response = model.generate_content(user_prompt, stream=True)
    for word in response:
        yield word.text

def improve_skills():
    API = st.secrets['GEMINI_API_KEY']
    genai.configure(api_key=str(API))

    sys_prompt = ("You are an expert at deciding work domain ",
                    "Analyze the following prompt given by the user which has a list of skills they know:\n\n",
                    "Prompt: {user_prompt}\n\n",
                    "Tell job role and provide links to three educative courses of other necessary skills required  in that field along with\n",
                    "1. Duration\n",
                    "2. Paid or free\n",
                    "3. link to resource\n",
                    "4. Opportunities\n")
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=sys_prompt)
    return model

def save_pdf(uploaded_file):
    file_path = os.path.join(RESUME_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

st.title("Job Recommender")
st.write("Upload a PDF file, and You will be provided with a list of Job Recommendations")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    file_path = save_pdf(uploaded_file)
    st.success(f"File successfully saved at: {file_path}")
    file_path = os.path.basename(file_path)

    user_skills = skills_extraction.skills_extractor(file_path)#, convert_to_string=True)
    user_work_exp = skills_extraction.workd_exp_extractor(file_path)

    skills = (user_skills)
    st.markdown("### User Job Skills")
    # Iterate over skills in chunks of 3
    for i in range(0, len(skills), 3):
        cols = st.columns(3)  # Create three columns
        for j, skill in enumerate(skills[i:i+3]):  # Select up to 3 skills per row
            with cols[j]:  # Assign each skill to a column
                st.markdown(f"- ```{skill}```")
    st.markdown("### User Work Experience ")
    st.markdown('```'+str(user_work_exp) + ' Years of Average Work Experience ```')
    job_recommendor.get_recommendations(file_path)
    path = os.path.join('data', 'job_recommendations.csv')
    df = pd.read_csv(path)
    df = df[['Title', 'Description', 'Location', 'Company Name', 'Company Apply Url', 'Required Experience', 'skills', 'Strengths', 'Weakness']]
    st.markdown("### Job Recommendations for User")
    st.dataframe(df)

    st.markdown("""
    <style>
        .stButton > button {
            display: block;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)
    button = st.button("Need Help Upskilling?")
    if button:
        prompt = "Skills = " + ','.join(skills)
        model = improve_skills()
        st.write_stream(response_generator(model, prompt))
