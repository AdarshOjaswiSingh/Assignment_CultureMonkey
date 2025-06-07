import streamlit as st
import pandas as pd
import os
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys

DB_PATH = "dataset_cultureMonkey.xlsx"

# ========== File Text Extractors ==========
def extract_pdf_text(file):
    try:
        reader = PdfReader(file)
        return '\n'.join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")
        return ""

def extract_word_text(file):
    try:
        doc = Document(file)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"❌ Error reading Word document: {e}")
        return ""

# ========== Resume Info Extraction ==========
def extract_resume_details(text):
    lines = text.split("\n")
    summary_sections = {
        "Skills": ["Skills", "Technical Skills", "Core Competencies"],
        "Achievements": ["Achievements", "Accomplishments", "Key Highlights"],
        "Experience": ["Experience", "Work Experience", "Professional Experience"],
        "Projects": ["Projects", "Key Projects", "Academic Projects"]
    }
    extracted_info = {key: [] for key in summary_sections}
    current_section = None
    for line in lines:
        line = line.strip()
        for section, keywords in summary_sections.items():
            if any(line.lower().startswith(keyword.lower()) for keyword in keywords):
                current_section = section
                break
        else:
            if current_section:
                extracted_info[current_section].append(line)
    formatted_output = {key: "\n".join(value) for key, value in extracted_info.items() if value}
    return formatted_output if formatted_output else "No structured data found. Please label resume sections clearly."

# ========== Resume Upload Logic ==========
def upload_data():
    st.subheader("📤 Upload Resume")
    uploaded_file = st.file_uploader("📄 Upload a file (PDF, DOCX, or Excel)", type=["pdf", "docx", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".pdf"):
                text = extract_pdf_text(uploaded_file)
                summary = extract_resume_details(text)
            elif uploaded_file.name.endswith(".docx"):
                text = extract_word_text(uploaded_file)
                summary = extract_resume_details(text)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
                st.write("📊 Data Preview:")
                st.dataframe(df.head())
                st.write(f"📝 Rows: {len(df)} | Columns: {', '.join(df.columns)}")
                return
            else:
                st.error("❌ Unsupported file format!")
                return
            st.session_state.resume_summary = summary
            st.success("✅ Resume processed successfully!")
            st.write(summary)
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")

# ========== Resume to Role Matching ==========
def match_resume_to_roles(resume_text, job_df, top_n=3):
    if job_df.empty or "job_description_text" not in job_df.columns or "job_title" not in job_df.columns:
        return []
    descriptions = job_df["job_description_text"].fillna("").tolist()
    roles = job_df["job_title"].fillna("Unknown Role").tolist()
    corpus = descriptions + [resume_text]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    top_indices = similarity_scores.argsort()[-top_n:][::-1]
    matched_roles = [roles[i] for i in top_indices]
    return matched_roles

# ========== Experience-Level Based Interview Questions ==========
experience_questions = {
    "Internship": [
        "Explain the difference between supervised and unsupervised learning.",
        "What is overfitting and how can you prevent it?",
        "Describe a project where you used machine learning.",
        "What Python libraries are you familiar with for ML?",
        "How would you evaluate the performance of a model?"
    ],
    "Entry level": [
        "How does a decision tree algorithm work?",
        "What are precision, recall, and F1-score?",
        "Describe how gradient descent works.",
        "How would you clean a large dataset with missing values?",
        "What are common activation functions in neural networks?"
    ],
    "Associate": [
        "Explain the concept of regularization in machine learning.",
        "How do you handle class imbalance in a dataset?",
        "What’s the difference between bagging and boosting?",
        "Describe your experience with deploying ML models.",
        "What’s your approach to feature selection?"
    ],
    "Mid-Senior level": [
        "Describe the architecture of a recent ML project you led.",
        "How do you scale machine learning solutions in production?",
        "What is your approach to model interpretability?",
        "Discuss the tradeoffs between model complexity and performance.",
        "How do you stay updated with the latest ML research?"
    ],
    "Director": [
        "How do you align data science initiatives with business goals?",
        "Describe a time you managed a cross-functional data team.",
        "How do you prioritize ML projects?",
        "What’s your strategy for talent development in your team?",
        "How do you measure the impact of ML in your organization?"
    ],
    "Executive": [
        "How do you define the data vision for an organization?",
        "What are your strategies for data governance and compliance?",
        "How do you collaborate with other executives on data strategy?",
        "Describe a time you led a digital transformation initiative.",
        "How do you balance innovation with operational efficiency?"
    ]
}

# ========== Streamlit Main UI ==========
def main():
    st.set_page_config(page_title="🤖 AI Interview Assistant", layout="wide")

    st.title("🤖 AI Interview Assistant")
    st.markdown("This is a lightweight demo for automating resume analysis and mock interview simulation. Created by **Adarsh Ojaswi Singh**. 🚀")
    st.sidebar.title("🧭 Navigation")
    options = st.sidebar.radio("Choose a section:", ["🏠 Home", "📄 Resume & Interview", "⬇️ Download", "ℹ️ About"])

    if "resume_summary" not in st.session_state:
        st.session_state.resume_summary = None
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "role" not in st.session_state:
        st.session_state.role = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "transcripts" not in st.session_state:
        st.session_state.transcripts = []

    if options == "🏠 Home":
        st.header("👋 Welcome")
        st.write("Upload your resume, match to roles, and practice your interview! 🎯")

    elif options == "ℹ️ About":
        st.header("📚 About This App")
        st.write("Built as a part of a recruitment system simulation using Python and Streamlit. 💼")

    elif options == "📄 Resume & Interview":
        col1, col2 = st.columns(2)
        with col1:
            upload_data()
        with col2:
            st.subheader("🎤 Interview Mode")

            experience_level = st.selectbox("🧑‍💼 Select Experience Level:", list(["Select"] + list(experience_questions.keys())))

            if experience_level != "Select":
                try:
                    xls = pd.ExcelFile(DB_PATH)
                    available_sheets = xls.sheet_names
                    sheet_map = {
                        "Internship": "Fresher_Level",
                        "Entry level": "Fresher_Level",
                        "Associate": "Fresher_Level",
                        "Mid-Senior level": "Senior_Level",
                        "Director": "Senior_Level",
                        "Executive": "Senior_Level"
                    }
                    sheet_name = sheet_map.get(experience_level, available_sheets[0])
                    if sheet_name not in available_sheets:
                        raise ValueError(f"Worksheet named '{sheet_name}' not found")
                    database = pd.read_excel(DB_PATH, sheet_name=sheet_name, engine='openpyxl')
                except Exception as e:
                    st.error(f"❌ Error loading data: {e}")
                    database = pd.DataFrame(columns=["job_title", "job_description_text"])

                matched_roles = []
                if st.session_state.resume_summary:
                    resume_text = "\n".join(st.session_state.resume_summary.values()) if isinstance(st.session_state.resume_summary, dict) else str(st.session_state.resume_summary)
                    matched_roles = match_resume_to_roles(resume_text, database)

                selected_role = st.selectbox("🔍 Select matched role:", matched_roles or database["job_title"].dropna().unique().tolist())

                if st.button("▶️ Start Interview"):
                    if selected_role:
                        st.session_state.role = selected_role
                        st.session_state.conversation = []
                        st.session_state.transcripts = experience_questions.get(experience_level, []) + database[database["job_title"] == selected_role]["job_description_text"].dropna().tolist()
                        if st.session_state.transcripts:
                            st.session_state.current_question = st.session_state.transcripts.pop(0)
                            st.session_state.conversation.append(("Interviewer", st.session_state.current_question))

                if st.session_state.get("current_question"):
                    st.write(f"**👔 Interviewer:** {st.session_state.current_question}")
                    answer = st.text_area("✍️ Your Answer:")
                    if st.button("📤 Submit Response"):
                        if answer.strip():
                            st.session_state.conversation.append(("Candidate", answer))
                            if st.session_state.transcripts:
                                st.session_state.current_question = st.session_state.transcripts.pop(0)
                                st.session_state.conversation.append(("Interviewer", st.session_state.current_question))
                            else:
                                st.success("🎉 Interview complete!")
                                st.session_state.current_question = None
                        else:
                            st.warning("⚠️ Answer cannot be empty.")

    elif options == "⬇️ Download":
        st.header("📥 Download Results")
        if st.session_state.conversation:
            transcript = "\n".join([f"{role}: {text}" for role, text in st.session_state.conversation])
            resume_summary = ""
            if st.session_state.resume_summary:
                resume_summary = "\n\n".join([f"{sec}:\n{cont}" for sec, cont in st.session_state.resume_summary.items()]) if isinstance(st.session_state.resume_summary, dict) else str(st.session_state.resume_summary)
            full_output = transcript + ("\n\nResume Summary:\n" + resume_summary if resume_summary else "")
            st.download_button("💾 Download Full Report", data=full_output, file_name="interview_summary.txt", mime="text/plain")
            if resume_summary:
                st.download_button("💾 Download Resume Summary", data=resume_summary, file_name="resume_summary.txt", mime="text/plain")
        else:
            st.info("ℹ️ Nothing to download yet.")

if __name__ == "__main__":
    main()
