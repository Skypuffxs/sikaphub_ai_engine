import streamlit as st
import json
import pandas as pd
from resume_parser import parse_resume_to_profile

st.set_page_config(page_title="S.I.K.A.P. Hub - AI Resume Profile Reader", layout="wide", page_icon="📄")

# Header & Title
st.title("📄 AI Resume Profile Reader & Builder")
st.caption("Upload candidate resumes (PDF or DOCX) to automatically extract and parse structured profile information (Name, Contact, Location, Skills, Education, Work Experience, Objective) for profile creation in S.I.K.A.P. Hub.")

# -------------------------
# MENU SELECTION
# -------------------------
menu = st.sidebar.selectbox("Navigation", ["Parse Candidate Resume", "Batch Profile Extraction"])

# =====================================================
# SINGLE RESUME PARSER & PROFILE BUILDER
# =====================================================
if menu == "Parse Candidate Resume":
    st.header("Single Resume Profile Ingestion")
    
    uploaded_file = st.file_uploader("Upload Candidate Resume / CV", type=["pdf", "docx"])

    if uploaded_file is not None:
        with st.spinner("Extracting profile information from resume..."):
            parsed_data = parse_resume_to_profile(uploaded_file)

        if parsed_data.get("status") == "error":
            st.error(f"Failed to process file: {parsed_data.get('message')}")
        else:
            profile = parsed_data["profile"]
            
            st.success("✅ Profile extracted successfully!")
            
            # --- ACTION BAR ---
            col_act1, col_act2 = st.columns([4, 1])
            with col_act1:
                st.subheader(f"👤 Candidate Profile: {profile['name']}")
            with col_act2:
                json_str = json.dumps(profile, indent=2)
                st.download_button(
                    label="📥 Download Profile JSON",
                    data=json_str,
                    file_name=f"{profile['name'].replace(' ', '_').lower()}_profile.json",
                    mime="application/json"
                )
            
            st.divider()

            # --- ROW 1: PERSONAL DETAILS & CONTACT ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📋 Personal Details")
                st.markdown(f"**Full Name:** {profile['name']}")
                st.markdown(f"**Email Address:** {profile['contact']['email']}")
                st.markdown(f"**Phone Number:** {profile['contact']['phone']}")
                st.markdown(f"**Location / Address:** {profile['location']['address']}")
                if profile['contact']['links']:
                    st.markdown(f"**Web Links:** {', '.join(profile['contact']['links'])}")
            
            with col2:
                st.markdown("### 📝 Career Objective / Summary")
                st.info(profile['summary'])

            st.divider()

            # --- ROW 2: SKILLS INVENTORY ---
            st.markdown("### 🛠️ Skills Inventory")
            skills = profile["skills"]
            
            scol1, scol2, scol3 = st.columns(3)
            
            with scol1:
                st.markdown("#### Technical Skills")
                if skills["technical_skills"]:
                    st.write(", ".join([f"`{s}`" for s in skills["technical_skills"]]))
                else:
                    st.caption("No technical skills explicitly identified.")
                    
            with scol2:
                st.markdown("#### Soft Skills")
                if skills["soft_skills"]:
                    st.write(", ".join([f"`{s}`" for s in skills["soft_skills"]]))
                else:
                    st.caption("No soft skills explicitly identified.")

            with scol3:
                st.markdown("#### Tools & Frameworks")
                if skills["tools_and_frameworks"]:
                    st.write(", ".join([f"`{s}`" for s in skills["tools_and_frameworks"]]))
                else:
                    st.caption("No tools/frameworks explicitly identified.")

            st.divider()

            # --- ROW 3: EDUCATION & EXPERIENCE ---
            ecol1, ecol2 = st.columns(2)

            with ecol1:
                st.markdown("### 🎓 Education History")
                education_list = profile["education"]
                if education_list:
                    for edu in education_list:
                        with st.container():
                            st.markdown(f"**{edu.get('degree_or_level', 'Degree / Course')}**")
                            if edu.get('institution'):
                                st.markdown(f"📍 *{edu.get('institution')}*")
                            if edu.get('year'):
                                st.caption(f"🗓️ {edu.get('year')}")
                            st.markdown("---")
                else:
                    st.caption("No education background extracted.")

            with ecol2:
                st.markdown("### 💼 Work Experience History")
                exp_list = profile["experience"]
                if exp_list:
                    for exp in exp_list:
                        with st.container():
                            st.markdown(f"**{exp.get('title', 'Position / Role')}**")
                            if exp.get('company_or_details'):
                                st.markdown(f"🏢 *{exp.get('company_or_details')}*")
                            if exp.get('duration'):
                                st.caption(f"🗓️ {exp.get('duration')}")
                            if exp.get('details'):
                                st.write(exp.get('details'))
                            st.markdown("---")
                else:
                    st.caption("No work experience entries extracted.")

            # --- ROW 4: CERTIFICATIONS & CREDENTIALS ---
            if profile["certifications"]:
                st.markdown("### 📜 Certifications & Achievements")
                for cert in profile["certifications"]:
                    st.markdown(f"- {cert}")

            # --- JSON RAW DATA VIEW ---
            with st.expander("🔍 View Raw Extracted JSON Profile"):
                st.json(profile)

# =====================================================
# BATCH PROFILE EXTRACTION
# =====================================================
else:
    st.header("Batch Resume Profile Extraction")
    
    files = st.file_uploader("Upload Multiple Candidate Resumes", type=["pdf", "docx"], accept_multiple_files=True)

    if files and st.button("Extract Profiles"):
        extracted_profiles = []
        
        progress_bar = st.progress(0)
        
        for idx, file in enumerate(files):
            parsed = parse_resume_to_profile(file)
            if parsed.get("status") == "success":
                p = parsed["profile"]
                extracted_profiles.append({
                    "Filename": file.name,
                    "Name": p["name"],
                    "Email": p["contact"]["email"],
                    "Phone": p["contact"]["phone"],
                    "Location": p["location"]["address"],
                    "Skills Count": len(p["skills"]["all_skills"]),
                    "Detected Skills": ", ".join(p["skills"]["all_skills"][:8]),
                    "Education": p["education"][0]["degree_or_level"] if p["education"] else "Not provided",
                    "Full Profile Data": p
                })
            progress_bar.progress((idx + 1) / len(files))

        if extracted_profiles:
            st.success(f"Successfully processed {len(extracted_profiles)} resumes!")
            
            df = pd.DataFrame(extracted_profiles)
            
            # Display summary table without scoring metrics
            st.subheader("Summary Table of Parsed Profiles")
            st.dataframe(df[["Name", "Email", "Phone", "Location", "Skills Count", "Education", "Filename"]])
            
            # Combined JSON Download
            combined_json = json.dumps([item["Full Profile Data"] for item in extracted_profiles], indent=2)
            st.download_button(
                label="📥 Download Batch Profiles JSON",
                data=combined_json,
                file_name="batch_extracted_profiles.json",
                mime="application/json"
            )
