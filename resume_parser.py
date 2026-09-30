import re
from typing import Dict, Any, List, Optional
import PyPDF2
import docx

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
    "frontend developer", "troubleshooting", "networking", "coding", "system maintenance",
    "full-stack", "full stack", "fullstack", "software development", "web development",
    "ethical hacking", "ethical hacker", "penetration testing", "network security",
    "cloud fundamentals", "database management", "data entry", "bookkeeping", "accounting",
    "graphic design", "video editing", "project management", "system administration",
    "customer service", "sales", "marketing", "content writing", "technical writing",
    "quality assurance", "software testing", "ui/ux", "ui/ux design"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "time management", "problem solving",
    "customer service", "interpersonal skills", "adaptability", "critical thinking",
    "work ethic", "collaboration", "flexibility", "multitasking", "attention to detail",
    "organization", "decision making", "management", "active listening", "event planning"
]

TOOLS_FRAMEWORKS = [
    "git", "github", "gitlab", "docker", "kubernetes", "vscode", "postman",
    "jira", "figma", "canva", "ms word", "ms excel", "powerpoint", "photoshop",
    "fortinet", "cisco networking academy", "autocad", "wordpress", "elementor"
]

# Common section headers (normalized uppercase)
SECTION_HEADERS = {
    "SUMMARY": ["OBJECTIVE", "CAREER OBJECTIVE", "SUMMARY", "PROFESSIONAL SUMMARY", "PROFILE", "ABOUT ME"],
    "EDUCATION": ["EDUCATION", "EDUCATIONAL BACKGROUND", "EDUCATIONAL ATTAINMENT", "ACADEMIC BACKGROUND", "ACADEMIC ATTAINMENT", "EDUCATION AND TRAINING", "EDUCATION & TRAINING", "QUALIFICATIONS", "ACADEMICS", "TERTIARY", "SCHOOL", "EDUCATIONAL HISTORY"],
    "EXPERIENCE": ["WORK EXPERIENCE", "EXPERIENCE", "EMPLOYMENT HISTORY", "WORK HISTORY", "INTERNSHIP", "PROJECTS", "JOB HISTORY", "CAREER HISTORY", "PROFESSIONAL EXPERIENCE"],
    "SKILLS": ["SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "SKILLS & COMPETENCIES", "TECHNOLOGIES", "SKILLS & EXPERTISE", "SKILLS & QUALIFICATIONS", "PROFESSIONAL SKILLS"],
    "CERTIFICATIONS": ["CERTIFICATIONS", "CERTIFICATES", "SEMINARS & TRAININGS", "TRAININGS", "SEMINARS", "ACHIEVEMENTS", "HONORS & AWARDS", "AWARDS"]
}

import os

def clean_spaced_text(text: str) -> str:
    """Fix PDFs with spaced-out characters (e.g. 'W O R K   E X P E R I E N C E') or tabbed letters."""
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        line_tab_fixed = line.replace('\t', '  ')
        tokens = line_tab_fixed.split()
        if len(tokens) >= 3 and sum(1 for t in tokens if len(t) == 1) / len(tokens) > 0.35:
            words = []
            curr_word = ''
            parts = re.split(r'(\s{2,})', line_tab_fixed)
            for part in parts:
                if re.match(r'^\s{2,}$', part):
                    if curr_word:
                        words.append(curr_word)
                        curr_word = ''
                else:
                    letters = part.split()
                    curr_word += ''.join(letters)
            if curr_word:
                words.append(curr_word)
            line = ' '.join(words)
        else:
            line = re.sub(r'\s+', ' ', line).strip()
        if line:
            lines.append(line)
    return '\n'.join(lines)

def extract_text_from_file(file_obj_or_path, file_type: Optional[str] = None) -> str:
    """Extract raw text from PDF or DOCX file object, file path, or raw text string."""
    text = ""
    filename = ""
    
    if isinstance(file_obj_or_path, str):
        if os.path.isfile(file_obj_or_path):
            filename = file_obj_or_path
            file_type = file_type or ("application/pdf" if filename.lower().endswith(".pdf") else "docx")
            with open(filename, "rb") as f:
                text = _extract_from_stream(f, file_type)
        else:
            text = file_obj_or_path
    else:
        file_type = file_type or getattr(file_obj_or_path, "type", "")
        filename = getattr(file_obj_or_path, "name", "")
        if not file_type:
            if filename.lower().endswith(".pdf"):
                file_type = "application/pdf"
            elif filename.lower().endswith(".docx"):
                file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        text = _extract_from_stream(file_obj_or_path, file_type)

    return clean_spaced_text(text)

def _extract_from_stream(stream, file_type: str) -> str:
    text_parts = []
    try:
        if "pdf" in file_type.lower():
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

def extract_name(text_lines: List[str]) -> str:
    """Extract candidate name from header text lines."""
    for idx, line in enumerate(text_lines[:6]):
        clean = line.strip()
        if not clean:
            continue
        clean = re.sub(r'\b(project portfolio|curriculum vitae|resume|cv|profile|portfolio)\b.*$', '', clean, flags=re.IGNORECASE).strip()
        if not clean:
            continue
        if any(kw in clean.lower() for kw in ["resume", "curriculum", "cv", "email", "phone", "contact", "@", "http", "objective", "address", "profile", "portfolio"]):
            continue

        if "," in clean:
            parts = [p.strip() for p in clean.split(",") if p.strip()]
            if len(parts) == 2 and all(re.match(r'^[A-Za-z\s\.\-]{2,40}$', p) for p in parts):
                last_name, first_name = parts[0], parts[1]
                return f"{first_name.title()} {last_name.title()}"

        if idx + 1 < len(text_lines[:6]):
            next_clean = text_lines[idx + 1].strip()
            next_clean = re.sub(r'\b(project portfolio|curriculum vitae|resume|cv|profile|portfolio)\b.*$', '', next_clean, flags=re.IGNORECASE).strip()
            if re.match(r'^[A-Za-z\s\.\-]{2,30}$', clean) and (not next_clean or re.match(r'^[A-Za-z\s\.\-]{2,30}$', next_clean)):
                if not next_clean:
                    return clean.title()
                if not any(kw in next_clean.lower() for kw in ["email", "phone", "@", "http", "resume", "cv", "address", "objective", "expertise", "education", "portfolio"]):
                    return f"{clean.title()} {next_clean.title()}"

        if re.match(r'^[A-Za-z\s\.\-]{2,50}$', clean) and len(clean.split()) <= 6:
            if clean.isupper() and len(clean.split()) < 2:
                continue
            return clean.title()

    return "Candidate Name Not Found"

def extract_contact_info(text: str) -> Dict[str, Any]:
    """Extract email, phone numbers, and web links."""
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[,.][A-Z|a-z]{2,}\b', text)
    cleaned_emails = [e.replace(',', '.') for e in emails]
    
    phone_pattern = r'(\+?63[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|09\d{2}[-.\s]?\d{3}[-.\s]?\d{4}|\(?0\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{4}[-.\s]?\d{3}[-.\s]?\d{4}\b)'
    phones = re.findall(phone_pattern, text)
    cleaned_phones = list(dict.fromkeys([p.strip() for p in phones if len(re.sub(r'\D', '', p)) >= 7]))
    
    links = re.findall(r'https?://[^\s,]+|(?:linkedin\.com|github\.com)/[^\s,]+', text, re.IGNORECASE)

    return {
        "email": cleaned_emails[0] if cleaned_emails else "Not provided",
        "phone": cleaned_phones[0] if cleaned_phones else "Not provided",
        "all_phones": cleaned_phones,
        "links": links
    }

def extract_location(text_lines: List[str]) -> Dict[str, str]:
    """Extract address/location keywords from early lines."""
    location_keywords = ["purok", "street", "st.", "city", "province", "barangay", "brgy", "nueva ecija", "manila", "quezon", "guimba", "cabanatuan", "philippines"]
    
    for i, line in enumerate(text_lines[:25]):
        clean = line.strip()
        if not clean:
            continue
        if any(kw in clean.lower() for kw in location_keywords):
            if not "@" in clean and not "http" in clean and not "objective" in clean.lower():
                full_addr = clean
                if i + 1 < len(text_lines) and any(kw in text_lines[i+1].lower() for kw in location_keywords):
                    full_addr += ", " + text_lines[i+1].strip()
                    
                brgy_match = re.search(r'(?:brgy\.?|barangay|purok\s+\d+,\s*)\s*([A-Za-z0-9\s\.-]+?)(?:,|$)', full_addr, re.IGNORECASE)
                brgy_name = brgy_match.group(1).strip() if brgy_match else ""
                
                mun_match = re.search(r'\b(aliaga|bongabon|cabanatuan|cabiao|carranglan|cuyapo|gabaldon|gapan|gen\.?\s*natividad|general natividad|guimba|jaen|laur|licab|llanera|lupao|muñoz|munoz|nampicuan|palayan|pantabangan|penaranda|peñaranda|quezon|rizal|san antonio|san isidro|san jose|san leonardo|santa rosa|sta\.?\s*rosa|talavera|talugtug|zaragoza)\b', full_addr, re.IGNORECASE)
                mun_name = mun_match.group(1).strip() if mun_match else ""
                
                return {
                    "address": full_addr,
                    "barangay": brgy_name,
                    "municipality": mun_name
                }
    return {"address": "Not provided", "barangay": "", "municipality": ""}

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
        # Clean section header numbers/bullets e.g. "1. EDUCATION" -> "EDUCATION"
        cleaned_header = re.sub(r'^[0-9IVXLCDM\.\-\*\u2022\s]+', '', upper_line).strip()
        cleaned_header = re.sub(r'[\:\-\s]+$', '', cleaned_header).strip()

        header_matched = None
        for sec_name, keywords in SECTION_HEADERS.items():
            if any(cleaned_header == kw or cleaned_header.startswith(kw + ":") or cleaned_header.startswith(kw + " ") for kw in keywords):
                header_matched = sec_name
                break
        
        if header_matched:
            current_section = header_matched
        else:
            sections[current_section].append(line)
            
    return sections

def extract_summary(sections: Dict[str, List[str]]) -> str:
    """Extract summary/objective statement."""
    summary_lines = sections.get("SUMMARY", [])
    if summary_lines:
        return " ".join(summary_lines)
    
    # Fallback to lines after contact info in header if objective words present
    header_lines = sections.get("HEADER", [])
    for idx, line in enumerate(header_lines):
        if "objective" in line.lower() or "summary" in line.lower():
            return " ".join(header_lines[idx+1:idx+4])
            
    return "Not provided"

def extract_skills_categorized(text: str, sections: Optional[Dict[str, List[str]]] = None) -> Dict[str, List[str]]:
    """Extract and categorize tech, soft, tool, and custom listed skills from full text and SKILLS section."""
    text_clean = text.lower()
    
    tech_detected = [s.title() for s in TECH_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', text_clean)]
    soft_detected = [s.title() for s in SOFT_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', text_clean)]
    tools_detected = [s.title() for s in TOOLS_FRAMEWORKS if re.search(r'\b' + re.escape(s) + r'\b', text_clean)]
    
    custom_detected = []
    if sections and "SKILLS" in sections:
        for line in sections["SKILLS"]:
            clean_line = line.strip()
            if not clean_line:
                continue
            # Remove header prefixes like "Technical Skills:", "Soft Skills:"
            clean_line = re.sub(r'^(technical|soft|core|key|other)?\s*skills?\s*:?\s*', '', clean_line, flags=re.IGNORECASE)
            # Split line by bullets, commas, pipes, or semicolons
            tokens = re.split(r'[\u2022\u25cf\u25cb\u25a0\u2013\u2014\-\*\|,;]', clean_line)
            for tok in tokens:
                t = tok.strip()
                t_clean = re.sub(r'^[^\w]+|[^\w]+$', '', t)
                if t_clean and 2 <= len(t_clean) <= 40 and not any(kw in t_clean.lower() for kw in ["objective", "experience", "education", "references", "summary"]):
                    custom_detected.append(t_clean.title())
    
    all_combined = list(dict.fromkeys(tech_detected + soft_detected + tools_detected + custom_detected))
    
    return {
        "technical_skills": sorted(list(set(tech_detected))),
        "soft_skills": sorted(list(set(soft_detected))),
        "tools_and_frameworks": sorted(list(set(tools_detected))),
        "all_skills": all_combined
    }

def extract_education(sections: Dict[str, List[str]], raw_text: str = "") -> List[Dict[str, str]]:
    """Extract education entries with degree level, institution, and graduation year."""
    edu_lines = sections.get("EDUCATION", [])
    if not edu_lines and raw_text:
        all_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        edu_lines = [l for l in all_lines if any(re.search(r'\b' + re.escape(k) + r'\b', l, re.IGNORECASE) for k in ["bachelor", "bs", "master", "doctor", "phd", "college", "university", "highschool", "high school", "elementary", "tesda", "vocational"])]

    if not edu_lines:
        return []

    education_entries = []
    current_entry = None

    degree_keywords = [
        "bachelor of science", "bachelor of arts", "bachelor", "bs", "ba", "bsit", "bscs", "bsba", "bsn", "bse",
        "master", "ms", "ma", "associate", "diploma", "doctor", "phd", "doctorate", "secondary",
        "senior highschool", "highschool", "high school", "elementary", "vocational", "tesda", "senior high", "junior high", "shs", "jhs"
    ]
    institution_keywords = ["university", "college", "institute", "academy", "polytechnic", "campus", "national high school", "school", "elem", "foundation", "inc"]

    for line in edu_lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        lower_line = line_clean.lower()
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', line_clean)
        
        has_degree = any(re.search(r'\b' + re.escape(deg) + r'\b', lower_line) for deg in degree_keywords)
        has_institution = any(re.search(r'\b' + re.escape(inst) + r'\b', lower_line) for inst in institution_keywords)

        if has_degree and not has_institution:
            if current_entry and (current_entry.get("degree_or_level") or current_entry.get("institution")):
                education_entries.append(current_entry)
            current_entry = {
                "degree_or_level": line_clean,
                "institution": "",
                "year": "-".join(years) if years else ""
            }
        elif has_institution:
            if current_entry and not current_entry["institution"]:
                current_entry["institution"] = line_clean
                if years and not current_entry["year"]:
                    current_entry["year"] = "-".join(years)
            else:
                if current_entry and (current_entry.get("degree_or_level") or current_entry.get("institution")):
                    education_entries.append(current_entry)
                current_entry = {
                    "degree_or_level": line_clean if has_degree else "",
                    "institution": line_clean,
                    "year": "-".join(years) if years else ""
                }
        elif years:
            if current_entry:
                if not current_entry["year"]:
                    current_entry["year"] = "-".join(years)
            else:
                current_entry = {
                    "degree_or_level": line_clean,
                    "institution": "",
                    "year": "-".join(years)
                }
        elif current_entry:
            if not current_entry["institution"]:
                current_entry["institution"] = line_clean
            elif not current_entry["degree_or_level"]:
                current_entry["degree_or_level"] = line_clean
        else:
            current_entry = {
                "degree_or_level": line_clean,
                "institution": "",
                "year": "-".join(years) if years else ""
            }

    if current_entry and (current_entry.get("degree_or_level") or current_entry.get("institution")):
        education_entries.append(current_entry)

    # Post-process merging
    merged_entries = []
    for entry in education_entries:
        deg = entry.get("degree_or_level", "").strip()
        inst = entry.get("institution", "").strip()
        yr = entry.get("year", "").strip()

        if merged_entries:
            prev = merged_entries[-1]
            if not prev["degree_or_level"] and deg:
                prev["degree_or_level"] = deg
                if yr and not prev["year"]:
                    prev["year"] = yr
                continue
            if not prev["institution"] and inst and not any(k in inst.lower() for k in ["major:", "gpa", "honors", "certifications"]):
                prev["institution"] = inst
                if yr and not prev["year"]:
                    prev["year"] = yr
                continue

        if deg or inst:
            merged_entries.append({"degree_or_level": deg, "institution": inst, "year": yr})

    return [e for e in merged_entries if e.get("degree_or_level") or e.get("institution")]

def extract_experience(sections: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Extract work experience entries."""
    exp_lines = sections.get("EXPERIENCE", [])
    if not exp_lines:
        return []
    
    experience_entries = []
    current_exp = {}
    
    role_keywords = [
        "developer", "engineer", "crew", "assistant", "manager", "specialist", "intern", "support",
        "analyst", "cashier", "waiter", "waitress", "barista", "agent", "officer", "teacher",
        "accountant", "clerk", "sales", "consultant", "lead", "supervisor", "coordinator", "designer",
        "writer", "executive", "admin", "representative", "worker", "technician", "operator", "staff",
        "associate", "driver", "nursing", "nurse", "trainee", "freelancer", "encoder", "bookkeeper", "chef", "cook"
    ]
    
    for line in exp_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
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
        else:
            current_exp = {
                "title": line_clean,
                "company_or_details": "",
                "duration": "-".join(years) if years else "",
                "description": []
            }
                
    if current_exp and (current_exp.get("title") or current_exp.get("company_or_details")):
        experience_entries.append(current_exp)
        
    for exp in experience_entries:
        exp["details"] = " ".join(exp.get("description", []))
        if "description" in exp:
            del exp["description"]
        
    return [e for e in experience_entries if e.get("title") or e.get("company_or_details")]

def extract_certifications(sections: Dict[str, List[str]]) -> List[str]:
    """Extract certification lines."""
    cert_lines = sections.get("CERTIFICATIONS", [])
    return [c for c in cert_lines if len(c) > 3]

def parse_resume_to_profile(file_obj_or_path, file_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to parse user resume / CV into structured candidate profile data.
    Does NOT calculate match scores or qualification evaluation.
    """
    raw_text = extract_text_from_file(file_obj_or_path, file_type)
    if not raw_text.strip():
        return {
            "status": "error",
            "message": "Unable to extract text from file or file is empty."
        }
    
    text_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    sections = extract_sections(raw_text)
    
    name = extract_name(text_lines)
    contact = extract_contact_info(raw_text)
    location = extract_location(text_lines)
    summary = extract_summary(sections)
    skills = extract_skills_categorized(raw_text, sections)
    education = extract_education(sections, raw_text)
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
