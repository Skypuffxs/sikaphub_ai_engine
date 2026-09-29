import os
import re
from typing import Dict, Any, List, Optional
import PyPDF2
import docx

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except ImportError:
    nlp = None

LOCATION_KEYWORDS = [
    "nueva ecija", "cabanatuan", "guimba", "manila", "quezon", "philippines",
    "barangay", "brgy", "purok", "street", "st.", "city", "province", "avenue", "ave.", "road", "rd."
]

NON_NAME_KEYWORDS = [
    "resume", "curriculum", "cv", "email", "phone", "contact", "@", "http", "https",
    "objective", "summary", "profile", "education", "experience", "skills", "certifications",
    "career objective", "personal information", "work experience", "page"
]

# -------------------------
# SKILL DATABASES
# -------------------------
TECH_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "html", "css", "sql",
    "machine learning", "data science", "deep learning", "artificial intelligence",
    "nlp", "api", "django", "flask", "fastapi", "react", "angular", "vue", "git",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "analysis",
    "figma", "cable testing", "data analytics", "cisco", "cybersecurity",
    "network connections", "system optimization", "aws", "azure", "docker",
    "kubernetes", "linux", "nosql", "mongodb", "postgresql", "mysql", "php",
    "laravel", "node.js", "express", "tailwind", "bootstrap", "rest api", "graphql",
    "it support", "mobile application developer", "web developer", "backend developer",
    "frontend developer", "troubleshooting", "networking", "coding", "system maintenance"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "time management", "problem solving",
    "customer service", "interpersonal skills", "adaptability", "critical thinking",
    "work ethic", "collaboration", "flexibility", "multitasking", "attention to detail"
]

TOOLS_FRAMEWORKS = [
    "git", "github", "gitlab", "docker", "kubernetes", "vscode", "postman",
    "jira", "figma", "canva", "ms word", "ms excel", "powerpoint", "photoshop"
]

# Common section headers (normalized uppercase)
SECTION_HEADERS = {
    "SUMMARY": ["OBJECTIVE", "CAREER OBJECTIVE", "SUMMARY", "PROFESSIONAL SUMMARY", "PROFILE", "ABOUT ME"],
    "EDUCATION": ["EDUCATION", "EDUCATIONAL BACKGROUND", "ACADEMIC BACKGROUND", "ACADEMICS", "TERTIARY"],
    "EXPERIENCE": ["WORK EXPERIENCE", "EXPERIENCE", "EMPLOYMENT HISTORY", "WORK HISTORY", "INTERNSHIP", "PROJECTS"],
    "SKILLS": ["SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "SKILLS & COMPETENCIES", "TECHNOLOGIES"],
    "CERTIFICATIONS": ["CERTIFICATIONS", "CERTIFICATES", "SEMINARS & TRAININGS", "TRAININGS", "SEMINARS", "ACHIEVEMENTS"]
}

import os

def extract_text_from_file(file_obj_or_path, file_type: Optional[str] = None) -> str:
    """Extract raw text from PDF or DOCX file object, file path, or raw text string."""
    filename = ""
    
    if isinstance(file_obj_or_path, str):
        if os.path.isfile(file_obj_or_path):
            filename = file_obj_or_path
            file_type = file_type or ("application/pdf" if filename.lower().endswith(".pdf") else "docx")
            with open(filename, "rb") as f:
                return _extract_from_stream(f, file_type)
        else:
            return file_obj_or_path
    else:
        file_type = file_type or getattr(file_obj_or_path, "type", "")
        filename = getattr(file_obj_or_path, "name", "")
        if not file_type:
            if filename.lower().endswith(".pdf"):
                file_type = "application/pdf"
            elif filename.lower().endswith(".docx"):
                file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return _extract_from_stream(file_obj_or_path, file_type)

def _extract_from_stream(stream, file_type: str) -> str:
    text_parts = []
    try:
        if "pdf" in file_type.lower():
            # Try pdfplumber first (preserves layout/visual reading order)
            if pdfplumber is not None:
                try:
                    with pdfplumber.open(stream) as pdf:
                        for page in pdf.pages:
                            extracted = page.extract_text(layout=False)
                            if extracted:
                                text_parts.append(extracted)
                except Exception as plumber_err:
                    print(f"pdfplumber extraction warning: {plumber_err}")
                    text_parts = []
            
            # Fallback to PyPDF2 if pdfplumber is missing or failed
            if not text_parts:
                if hasattr(stream, "seek"):
                    stream.seek(0)
                pdf = PyPDF2.PdfReader(stream)
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted)
        else:
            doc = docx.Document(stream)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
    
    return "\n".join(text_parts)

def extract_name(raw_text: str, text_lines: List[str], filename: str = "", email: str = "") -> str:
    """
    Extract candidate name using a hybrid pipeline:
    1. Cleaned Header Scanning (top 5 lines) with Location/Section filters
    2. spaCy Named Entity Recognition (NER) for PERSON entities
    3. Filename candidate fallback
    4. Email username hint candidate fallback
    """
    lines = [l.strip() for l in text_lines if l.strip()]
    if not lines:
        return "Candidate Name Not Found"

    # Step 1: Cleaned Header Line Scanning (Top 5 lines)
    for line in lines[:5]:
        clean = line.strip()
        low = clean.lower()

        if any(kw in low for kw in NON_NAME_KEYWORDS):
            continue
        if any(kw in low for kw in LOCATION_KEYWORDS):
            continue

        words = clean.split()
        if 2 <= len(words) <= 5 and re.match(r'^[A-Za-z\s\.\-]{2,50}$', clean):
            if clean.isupper() and len(clean) > 35:
                continue
            return clean.title()

    # Step 2: spaCy Named Entity Recognition (NER)
    if nlp:
        header_sample = "\n".join(lines[:10])
        doc = nlp(header_sample[:1000])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                ent_clean = ent.text.strip()
                ent_low = ent_clean.lower()
                if not any(kw in ent_low for kw in NON_NAME_KEYWORDS) and not any(kw in ent_low for kw in LOCATION_KEYWORDS):
                    if 2 <= len(ent_clean.split()) <= 5 and re.match(r'^[A-Za-z\s\.\-]{2,50}$', ent_clean):
                        return ent_clean.title()

    # Step 3: Filename Smart Fallback Candidate
    if filename:
        base = os.path.splitext(os.path.basename(filename))[0]
        clean_base = re.sub(r'\b(CV|Resume|resume|Profile|draft|v\d+)\b', '', base, flags=re.IGNORECASE)
        clean_base = re.sub(r'[\_\-\.]+', ' ', clean_base).strip()
        words = clean_base.split()
        if 2 <= len(words) <= 5 and all(re.match(r'^[A-Za-z\.\-]+$', w) for w in words):
            return " ".join([w.capitalize() for w in words])

    # Step 4: Email Username Fallback Candidate
    if email and "@" in email:
        username = email.split("@")[0]
        user_alpha = re.sub(r'\d+', '', username).replace('.', ' ').replace('_', ' ').replace('-', ' ').strip()
        if len(user_alpha) >= 4:
            for line in lines[:8]:
                clean_line = re.sub(r'[^A-Za-z\s]', '', line).strip()
                if clean_line and len(clean_line.split()) <= 5:
                    line_compact = clean_line.lower().replace(' ', '')
                    if line_compact in user_alpha or user_alpha in line_compact:
                        return clean_line.title()

    return "Candidate Name Not Found"

def extract_contact_info(text: str) -> Dict[str, Any]:
    """Extract email, phone numbers, and web links."""
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    
    # Phone numbers matching Philippine formats (+63, 09xx, 09xx-xxx-xxxx, etc.) & general formats
    phone_pattern = r'(\+?63[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|09\d{2}[-.\s]?\d{3}[-.\s]?\d{4}|\(?0\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{4}[-.\s]?\d{3}[-.\s]?\d{4}\b)'
    phones = re.findall(phone_pattern, text)
    cleaned_phones = list(dict.fromkeys([p.strip() for p in phones if len(re.sub(r'\D', '', p)) >= 7]))
    
    links = re.findall(r'https?://[^\s,]+|(?:linkedin\.com|github\.com)/[^\s,]+', text, re.IGNORECASE)

    return {
        "email": emails[0] if emails else "Not provided",
        "phone": cleaned_phones[0] if cleaned_phones else "Not provided",
        "all_phones": cleaned_phones,
        "links": links
    }

PH_LOCATION_KEYWORDS = [
    "purok", "street", "st.", "city", "province", "barangay", "brgy", "brgy.",
    "nueva ecija", "manila", "quezon", "guimba", "cabanatuan", "philippines", "philippine",
    "tarlac", "pampanga", "bulacan", "bataan", "zambales", "pangasinan", "la union", "ilocos",
    "cavite", "laguna", "batangas", "rizal", "quezon city", "makati", "pasig", "taguig",
    "mandaluyong", "paranaque", "las pinas", "muntinlupa", "marikina", "valenzuela",
    "malabon", "navotas", "pasay", "cebu", "davao", "iloilo", "bacolod", "cagayan", "general santos"
]

NON_LOCATION_KEYWORDS = [
    "student", "full-stack", "building", "systems", "backend", "frontend", "database",
    "security", "developer", "engineer", "experience", "skills", "education", "objective",
    "summary", "contact", "@", "http", "https", "proficient", "knowledge", "worked", "year", "seeking", "career"
]

def extract_location(text_lines: List[str]) -> Dict[str, str]:
    """Extract address/location keywords from early lines, filtering non-location text."""
    for line in text_lines[:10]:
        clean = line.strip()
        low = clean.lower()

        # Skip non-location noise and summary sentences
        if any(kw in low for kw in NON_LOCATION_KEYWORDS):
            continue

        # Check explicit Philippine location keywords
        if any(kw in low for kw in PH_LOCATION_KEYWORDS):
            return {"address": clean}

        # Check spaCy GPE/LOC entities
        if nlp:
            doc = nlp(clean)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"] and not any(kw in ent.text.lower() for kw in NON_LOCATION_KEYWORDS):
                    return {"address": clean}

    return {"address": "Not provided"}

def extract_sections(text: str) -> Dict[str, List[str]]:
    """Parse resume into logical sections based on common headers."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections: Dict[str, List[str]] = {
        "HEADER": [],
        "SUMMARY": [],
        "EDUCATION": [],
        "EXPERIENCE": [],
        "SKILLS": [],
        "CERTIFICATIONS": [],
        "OTHER": []
    }
    
    current_section = "HEADER"
    
    for line in lines:
        upper_line = line.upper()
        # Check if line matches a section header
        found_section = None
        for sec_name, keywords in SECTION_HEADERS.items():
            if any(upper_line == kw or upper_line.startswith(kw + ":") or upper_line.endswith(":") and kw in upper_line for kw in keywords):
                found_section = sec_name
                break
                
        if found_section:
            current_section = found_section
        else:
            sections[current_section].append(line)
            
    return sections

def extract_summary(sections: Dict[str, List[str]]) -> str:
    """Extract summary/objective text."""
    summary_lines = sections.get("SUMMARY", [])
    if summary_lines:
        return " ".join(summary_lines)
    return "Not provided"

def extract_skills_categorized(text: str) -> Dict[str, List[str]]:
    """Extract technical skills, soft skills, and tools matching predefined lists."""
    text_lower = text.lower()
    
    tech_detected = [skill.title() for skill in TECH_SKILLS if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]
    soft_detected = [skill.title() for skill in SOFT_SKILLS if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]
    tools_detected = [tool.title() for tool in TOOLS_FRAMEWORKS if re.search(r'\b' + re.escape(tool) + r'\b', text_lower)]
    
    return {
        "technical_skills": sorted(list(set(tech_detected))),
        "soft_skills": sorted(list(set(soft_detected))),
        "tools_and_frameworks": sorted(list(set(tools_detected))),
        "all_skills": sorted(list(set(tech_detected + soft_detected + tools_detected)))
    }

def extract_education(sections: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Extract education entries."""
    edu_lines = sections.get("EDUCATION", [])
    if not edu_lines:
        return []
    
    education_entries = []
    current_entry = {}
    
    degree_keywords = ["bachelor", "bs", "master", "ms", "associate", "diploma", "doctor", "phd", "tertiary", "secondary", "high school"]
    
    for line in edu_lines:
        line_clean = line.strip()
        # Look for degree/level
        is_degree = any(re.search(r'\b' + re.escape(deg) + r'\b', line_clean, re.IGNORECASE) for deg in degree_keywords)
        # Look for year (e.g. 2023, 2019-2023)
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', line_clean)
        
        if is_degree or years:
            if current_entry:
                education_entries.append(current_entry)
            current_entry = {
                "degree_or_level": line_clean,
                "institution": "",
                "year": "-".join(years) if years else ""
            }
        elif current_entry and not current_entry["institution"]:
            current_entry["institution"] = line_clean
        elif current_entry:
            current_entry["degree_or_level"] += " " + line_clean
            
    if current_entry:
        education_entries.append(current_entry)
        
    return education_entries if education_entries else [{"degree_or_level": " ".join(edu_lines[:3]), "institution": "", "year": ""}]

def extract_experience(sections: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Extract work experience entries."""
    exp_lines = sections.get("EXPERIENCE", [])
    if not exp_lines:
        return []
    
    experience_entries = []
    current_exp = {}
    
    role_keywords = ["developer", "engineer", "crew", "assistant", "manager", "specialist", "intern", "support", "analyst", "cashier", "waiter", "waitress", "barista", "agent", "officer"]
    
    for line in exp_lines:
        line_clean = line.strip()
        years = re.findall(r'\b(19\d{2}|20\d{2}|present)\b', line_clean, re.IGNORECASE)
        has_role = any(re.search(r'\b' + re.escape(role) + r'\b', line_clean, re.IGNORECASE) for role in role_keywords)
        
        if (has_role or years) and not current_exp:
            current_exp = {
                "title": line_clean,
                "company_or_details": "",
                "duration": "-".join(years) if years else "",
                "description": []
            }
        elif (has_role or years) and current_exp:
            experience_entries.append(current_exp)
            current_exp = {
                "title": line_clean,
                "company_or_details": "",
                "duration": "-".join(years) if years else "",
                "description": []
            }
        elif current_exp:
            if not current_exp["company_or_details"]:
                current_exp["company_or_details"] = line_clean
            else:
                current_exp["description"].append(line_clean)
                
    if current_exp:
        experience_entries.append(current_exp)
        
    # Format description lists into strings
    for exp in experience_entries:
        exp["details"] = " ".join(exp["description"])
        del exp["description"]
        
    return experience_entries if experience_entries else [{"title": " ".join(exp_lines[:3]), "company_or_details": "", "duration": "", "details": ""}]

def extract_certifications(sections: Dict[str, List[str]]) -> List[str]:
    """Extract certification lines."""
    cert_lines = sections.get("CERTIFICATIONS", [])
    return [c for c in cert_lines if len(c) > 3]

def parse_resume_to_profile(file_obj_or_path, file_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to parse user resume / CV into structured candidate profile data.
    Does NOT calculate match scores or qualification evaluation.
    """
    filename = ""
    if isinstance(file_obj_or_path, str):
        if os.path.isfile(file_obj_or_path):
            filename = file_obj_or_path
    else:
        filename = getattr(file_obj_or_path, "name", "")

    raw_text = extract_text_from_file(file_obj_or_path, file_type)
    if not raw_text.strip():
        return {
            "status": "error",
            "message": "Unable to extract text from file or file is empty."
        }
    
    text_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    sections = extract_sections(raw_text)
    
    contact = extract_contact_info(raw_text)
    name = extract_name(raw_text, text_lines, filename=filename, email=contact.get("email", ""))
    location = extract_location(text_lines)
    summary = extract_summary(sections)
    skills = extract_skills_categorized(raw_text)
    education = extract_education(sections)
    experience = extract_experience(sections)
    certifications = extract_certifications(sections)
    
    return {
        "status": "success",
        "profile": {
            "name": name,
            "contact": contact,
            "location": location,
            "summary": summary,
            "skills": skills,
            "education": education,
            "experience": experience,
            "certifications": certifications
        },
        "raw_text_length": len(raw_text)
    }
