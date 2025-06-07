import streamlit as st
import pandas as pd
import os
from PyPDF2 import PdfReader
from docx import Document

DB_PATH = "dataset_cultureMonkey.csv"

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
    
    if not formatted_output:
        return "No structured data found. Please ensure your resume has clearly labeled sections."
    
    return formatted_output

def upload_data():
    st.header("Upload Resume for Summary")
    uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, or Excel)", type=["pdf", "docx", "xlsx"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".pdf"):
                text = extract_pdf_text(uploaded_file)
                summary = extract_resume_details(text)
                st.session_state.resume_summary = summary
                st.subheader("Resume Summary")
                st.write(summary)

            elif uploaded_file.name.endswith(".docx"):
                text = extract_word_text(uploaded_file)
                summary = extract_resume_details(text)
                st.session_state.resume_summary = summary
                st.subheader("Resume Summary")
                st.write(summary)
                
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
                st.write("Data loaded successfully! Here is a preview of the first few rows:")
                st.dataframe(df.head())  # Display first 5 rows of the uploaded Excel file
                
                # Display some statistics about the data
                st.write("Data Overview:")
                st.write(f"Total rows: {len(df)}")
                st.write(f"Columns: {', '.join(df.columns)}")
                
                st.write("Note: You can also upload resumes (PDF or DOCX) for further analysis.")
                
            else:
                st.error("Unsupported file type!")
                return

        except Exception as e:
            st.error(f"Error processing file: {e}")

def load_database():
    try:
        if os.path.exists(DB_PATH):
            df = pd.read_excel(DB_PATH)
            df.columns = df.columns.str.strip()
            required_columns = ["Role", "Transcript"]
            if not all(col in df.columns for col in required_columns):
                st.error("Database format is incorrect. Ensure it has 'Role' and 'Transcript' columns.")
                return pd.DataFrame(columns=required_columns)
            return df
        else:
            st.warning("Database not found! Initializing a new database.")
            return pd.DataFrame(columns=["Role", "Transcript"])
    except Exception as e:
        st.error(f"Failed to load database: {e}")
        return pd.DataFrame()

def main():
    # Initialize session state for the first time
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

    st.title("End-to-End AI-Driven Recruitment Pipeline with Real-Time Insights")
    
    # Sidebar navigation
    st.sidebar.header("Navigation")
    options = st.sidebar.radio("Select a page:", ["Home", "Data Upload", "Download Conversation", "About"])

    if options == "Home":
        st.header("Welcome to the Infosys Project Dashboard")
        st.write("This app is designed to showcase the key features and outputs of my project.")
        st.write("Use the sidebar to navigate through the app.")

    elif options == "About":
        st.header("About This App")
        st.write("The End-to-End AI-Driven Recruitment Pipeline streamlines hiring by automating key processes like resume screening, skill assessment, and interview analysis.")
        st.write("Author: Adarsh Ojaswi Singh")

    elif options == "Data Upload":
        # Create two columns for data upload and interview mode side by side
        col1, col2 = st.columns([1, 1])  # Create 2 columns (left and right)

        with col1:  # Data Upload section (left side)
            upload_data()

        with col2:  # Interview Mode section (right side)
            st.header("Interview Mode:")
            database = load_database()
            roles = database["Role"].dropna().unique().tolist() if not database.empty else []
            if not roles:
                roles = ["No roles available"]
            role = st.selectbox("Select the role you are applying for:", roles)
            
            if st.button("Start Interview"):
                if role and role != "No roles available":
                    st.session_state.role = role
                    st.session_state.conversation = []
                    st.session_state.transcripts = database[database["Role"] == role]["Transcript"].dropna().tolist()
                    if st.session_state.transcripts:
                        st.session_state.current_question = st.session_state.transcripts.pop(0)
                        st.session_state.conversation.append(("Interviewer", st.session_state.current_question))

            if "current_question" in st.session_state:
                st.write(f"**Interviewer:** {st.session_state.current_question}")
                answer = st.text_area("Your Response:")
                if st.button("Submit Answer"):
                    if answer.strip():
                        st.session_state.conversation.append(("Candidate", answer))
                        if st.session_state.transcripts:
                            st.session_state.current_question = st.session_state.transcripts.pop(0)
                            st.session_state.conversation.append(("Interviewer", st.session_state.current_question))
                        else:
                            st.success("Interview completed!")
                    else:
                        st.warning("Please provide an answer before submitting.")

    elif options == "Download Conversation":
        st.header("Download Interview Transcript and Resume Summary")
        if "conversation" in st.session_state and st.session_state.conversation:
            conversation_text = "\n".join([f"{speaker}: {text}" for speaker, text in st.session_state.conversation])
            
            # Ensure resume_summary is a string
            resume_summary_text = ""
            if st.session_state.resume_summary:
                if isinstance(st.session_state.resume_summary, dict):
                    # Convert the dictionary to a string format
                    for section, content in st.session_state.resume_summary.items():
                        resume_summary_text += f"{section}:\n{content}\n\n"
                else:
                    resume_summary_text = str(st.session_state.resume_summary)
                
            # Combine the resume summary and interview transcript
            download_text = conversation_text
            if resume_summary_text:
                download_text += "\n\nResume Summary:\n" + resume_summary_text
                
            # Button for downloading the interview transcript with resume summary
            st.download_button(label="Download Transcript with Resume Summary", 
                               data=download_text, 
                               file_name="interview_transcript_with_resume_summary.txt", 
                               mime="text/plain")
            
            # Separate download button for the resume summary
            if resume_summary_text:
                st.download_button(label="Download Resume Summary Only", 
                                   data=resume_summary_text, 
                                   file_name="resume_summary.txt", 
                                   mime="text/plain")
        else:
            st.warning("No conversation available to download.")

if __name__ == "__main__":
    main()
