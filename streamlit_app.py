import streamlit as st
import pandas as pd
import os
from PyPDF2 import PdfReader
from docx import Document

DB_PATH = "dataset_cultureMonkey.csv"

# ========== File Text Extractors ==========
def extract_pdf_text(file):
    try:
        reader = PdfReader(file)
        return '\n'.join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_word_text(file):
    try:
        doc = Document(file)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error reading Word document: {e}")
        return ""

# ========== Resume Info Extraction ==========
def extract_resume_details(text):
    """Extracts only Skills, Achievements, Experiences, and Projects."""
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
    uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, or Excel)", type=["pdf", "docx", "xlsx"])
    
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
                st.write("✅ Data Preview:")
                st.dataframe(df.head())
                st.write(f"Rows: {len(df)} | Columns: {', '.join(df.columns)}")
                return
            else:
                st.error("❌ Unsupported file format!")
                return

            st.session_state.resume_summary = summary
            st.success("✅ Resume processed successfully!")
            st.write(summary)

        except Exception as e:
            st.error(f"Error processing file: {e}")

# ========== Load Predefined Interview Questions ==========
def load_database():
    try:
        if os.path.exists(DB_PATH):
            df = pd.read_excel(DB_PATH)
            df.columns = df.columns.str.strip()
            if not all(col in df.columns for col in ["Role", "Transcript"]):
                st.error("⚠️ CSV format error: Expected 'Role' and 'Transcript' columns.")
                return pd.DataFrame(columns=["Role", "Transcript"])
            return df
        else:
            st.warning("⚠️ Database not found! Using an empty one.")
            return pd.DataFrame(columns=["Role", "Transcript"])
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

# ========== Streamlit Main UI ==========
def main():
    st.set_page_config(page_title="AI Interview Assistant", layout="wide")

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

    st.title("🤖 AI Interview Assistant - Assignment Demo")
    st.markdown("Welcome to the AI-powered interview system built for Assignment purposes by **Adarsh Ojaswi Singh**.")

    st.sidebar.header("📌 Navigation")
    options = st.sidebar.radio("Go to:", ["🏠 Home", "📂 Resume Upload & Interview", "📥 Download Output", "ℹ️ About"])

    if options == "🏠 Home":
        st.header("Dashboard Overview")
        st.write("""
            This demo showcases how AI can streamline candidate evaluation.
            - Upload a resume
            - Simulate an interview
            - Download results
        """)

    elif options == "ℹ️ About":
        st.header("About This App")
        st.write("""
            This system is designed as part of an academic project to simulate an **AI-assisted recruitment process**.
            It includes:
            - Resume parsing
            - Interview simulation
            - Transcript generation
        """)
        st.markdown("**Created by:** Adarsh Ojaswi Singh, VIT Chennai")

    elif options == "📂 Resume Upload & Interview":
        col1, col2 = st.columns(2)

        with col1:
            upload_data()

        with col2:
            st.subheader("🎤 Interview Mode")
            database = load_database()
            roles = database["Role"].dropna().unique().tolist() if not database.empty else []
            role = st.selectbox("Select Role:", roles or ["No roles found"])
            
            if st.button("🚀 Start Interview"):
                if role and role != "No roles found":
                    st.session_state.role = role
                    st.session_state.conversation = []
                    st.session_state.transcripts = database[database["Role"] == role]["Transcript"].dropna().tolist()
                    if st.session_state.transcripts:
                        st.session_state.current_question = st.session_state.transcripts.pop(0)
                        st.session_state.conversation.append(("Interviewer", st.session_state.current_question))

            if "current_question" in st.session_state and st.session_state.current_question:
                st.markdown(f"**🗣 Interviewer:** {st.session_state.current_question}")
                answer = st.text_area("✍️ Your Answer:")
                if st.button("Submit Response"):
                    if answer.strip():
                        st.session_state.conversation.append(("Candidate", answer))
                        if st.session_state.transcripts:
                            st.session_state.current_question = st.session_state.transcripts.pop(0)
                            st.session_state.conversation.append(("Interviewer", st.session_state.current_question))
                        else:
                            st.success("🎉 Interview completed!")
                            st.session_state.current_question = None
                    else:
                        st.warning("Please enter an answer before submitting.")

    elif options == "📥 Download Output":
        st.header("📤 Export Interview & Resume Summary")
        if st.session_state.conversation:
            transcript = "\n".join([f"{role}: {text}" for role, text in st.session_state.conversation])
            resume_summary = ""
            if st.session_state.resume_summary:
                if isinstance(st.session_state.resume_summary, dict):
                    for section, content in st.session_state.resume_summary.items():
                        resume_summary += f"{section}:\n{content}\n\n"
                else:
                    resume_summary = str(st.session_state.resume_summary)

            full_output = transcript + "\n\n" + ("Resume Summary:\n" + resume_summary if resume_summary else "")
            
            st.download_button("📄 Download Full Report", data=full_output, file_name="AI_interview_summary.txt", mime="text/plain")
            if resume_summary:
                st.download_button("📄 Download Resume Summary Only", data=resume_summary, file_name="resume_summary.txt", mime="text/plain")
        else:
            st.info("No conversation or summary available yet.")

if __name__ == "__main__":
    main()
