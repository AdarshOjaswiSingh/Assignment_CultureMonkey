# app.py

import streamlit as st
import pandas as pd
import os
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

DB_PATH = "dataset_cultureMonkey.xlsx"

# ========== Extract Text ==========
def extract_pdf_text(file):
    try:
        return '\n'.join([p.extract_text() for p in PdfReader(file).pages if p.extract_text()])
    except Exception as e:
        st.error(f"❌ PDF error: {e}")
        return ""

def extract_word_text(file):
    try:
        return '\n'.join([para.text for para in Document(file).paragraphs])
    except Exception as e:
        st.error(f"❌ DOCX error: {e}")
        return ""

# ========== Extract Info ==========
def extract_resume_details(text):
    lines = text.split("\n")
    sections = {
        "Skills": ["Skills", "Technical Skills"],
        "Achievements": ["Achievements", "Accomplishments"],
        "Experience": ["Experience", "Work Experience"],
        "Projects": ["Projects", "Academic Projects"]
    }
    extracted = {key: [] for key in sections}
    current = None
    for line in lines:
        line = line.strip()
        for sec, keys in sections.items():
            if any(line.lower().startswith(k.lower()) for k in keys):
                current = sec
                break
        elif current:
            extracted[current].append(line)
    output = {k: "\n".join(v) for k, v in extracted.items() if v}
    return output if output else "No structured info found."

# ========== Upload Resume ==========
def upload_resume():
    st.subheader("📤 Upload Resume")
    uploaded = st.file_uploader("Choose PDF/DOCX/XLSX", type=["pdf", "docx", "xlsx"])
    if uploaded:
        if uploaded.name.endswith(".pdf"):
            text = extract_pdf_text(uploaded)
        elif uploaded.name.endswith(".docx"):
            text = extract_word_text(uploaded)
        elif uploaded.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded)
            st.write("📊 Data Preview")
            st.dataframe(df.head())
            return
        else:
            st.error("❌ Unsupported file")
            return
        summary = extract_resume_details(text)
        st.session_state.resume_summary = summary
        st.success("✅ Resume processed")
        st.json(summary)

# ========== Load Database ==========
def load_database():
    if os.path.exists(DB_PATH):
        try:
            df = pd.read_excel(DB_PATH, engine='openpyxl')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.error(f"❌ DB load error: {e}")
    return pd.DataFrame(columns=["job_title", "job_description_text"])

# ========== Role Matching ==========
def match_resume_to_roles(resume_text, job_df, top_n=3):
    if job_df.empty:
        return []
    corpus = job_df["job_description_text"].fillna("").tolist() + [resume_text]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
    top_indices = scores.argsort()[-top_n:][::-1]
    return [job_df["job_title"].iloc[i] for i in top_indices]

# ========== Visual Analysis ==========
def generate_visualizations(job_df):
    if job_df.empty:
        st.warning("⚠️ No data")
        return

    st.subheader("📊 Visual Insights")

    if "company_address_region" in job_df:
        top_locations = job_df["company_address_region"].value_counts().head(10)
        st.bar_chart(top_locations)

    if "job_title" in job_df:
        st.bar_chart(job_df["job_title"].value_counts().head(10))

    if "job_posted_date" in job_df:
        job_df["job_posted_date"] = pd.to_datetime(job_df["job_posted_date"], errors='coerce')
        monthly = job_df["job_posted_date"].dt.to_period("M").value_counts().sort_index()
        st.line_chart(monthly)

    if "job_description_text" in job_df:
        all_text = job_df["job_description_text"].dropna().str.cat(sep=" ")
        wordcloud = WordCloud(width=600, height=300, background_color='white').generate(all_text)
        st.image(wordcloud.to_array(), caption="🔤 WordCloud of Job Descriptions")

# ========== Main App ==========
def main():
    st.set_page_config("AI Interview Assistant", layout="wide")
    st.title("🤖 AI Interview Assistant")
    st.markdown("Upload your resume and prep for interviews smartly! 🚀")

    menu = st.sidebar.radio("📌 Navigation", ["🏠 Home", "📄 Resume & Interview", "📥 Download", "ℹ️ About"])

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

    if menu == "🏠 Home":
        st.markdown("Welcome to the AI Interview Assistant. Start by uploading your resume!")

    elif menu == "ℹ️ About":
        st.markdown("📘 This app is built by **Adarsh Ojaswi Singh** to simulate a recruitment pipeline using Streamlit.")

    elif menu == "📄 Resume & Interview":
        col1, col2 = st.columns(2)
        with col1:
            upload_resume()
        with col2:
            st.subheader("🎯 Role Matching & Interview")
            db = load_database()
            matched = []
            if st.session_state.resume_summary:
                resume_text = "\n".join(st.session_state.resume_summary.values()) if isinstance(st.session_state.resume_summary, dict) else st.session_state.resume_summary
                matched = match_resume_to_roles(resume_text, db)

            selected = st.selectbox("🎓 Select Role", matched or db["job_title"].dropna().unique())
            if st.button("▶️ Start Interview"):
                if selected:
                    st.session_state.role = selected
                    st.session_state.conversation = []
                    st.session_state.transcripts = db[db["job_title"] == selected]["job_description_text"].dropna().tolist()
                    if st.session_state.transcripts:
                        st.session_state.current_question = st.session_state.transcripts.pop(0)
                        st.session_state.conversation.append(("Interviewer", st.session_state.current_question))

            if st.session_state.get("current_question"):
                st.markdown(f"**👔 Interviewer:** {st.session_state.current_question}")
                ans = st.text_area("🗣️ Your Answer")
                if st.button("📤 Submit Answer"):
                    if ans.strip():
                        st.session_state.conversation.append(("Candidate", ans))
                        if st.session_state.transcripts:
                            st.session_state.current_question = st.session_state.transcripts.pop(0)
                            st.session_state.conversation.append(("Interviewer", st.session_state.current_question))
                        else:
                            st.success("🎉 Interview Completed!")
                            st.session_state.current_question = None
                    else:
                        st.warning("Answer cannot be empty!")

            st.markdown("---")
            if st.button("📈 Visualize Dataset"):
                generate_visualizations(db)

    elif menu == "📥 Download":
        st.subheader("⬇️ Download Your Results")
        if st.session_state.conversation:
            transcript = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.conversation])
            summary = ""
            if isinstance(st.session_state.resume_summary, dict):
                summary = "\n\n".join([f"{sec}:\n{cont}" for sec, cont in st.session_state.resume_summary.items()])
            full_report = f"{transcript}\n\nResume Summary:\n{summary}"

            st.download_button("💾 Full Report", full_report, file_name="interview_summary.txt")
            st.download_button("💾 Resume Summary", summary, file_name="resume_summary.txt")
        else:
            st.info("Nothing to download yet.")

if __name__ == "__main__":
    main()
