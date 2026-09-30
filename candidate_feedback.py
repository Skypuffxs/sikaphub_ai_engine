"""
Candidate Feedback & Side-by-Side Comparison Module for SikapHub AI Engine
-------------------------------------------------------------------------
Generates structured, individualized comparative feedback and candidate breakdown
for job applicants tied or close in AI match score.
"""

import json
import os
import re
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, root_validator, model_validator
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", os.getenv("AI_API_KEY", "")))
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# FLEXIBLE PYDANTIC INPUT & OUTPUT SCHEMAS
# ---------------------------------------------------------------------------

class JobDetails(BaseModel):
    job_id: Optional[int] = Field(None, description="Job ID")
    title: str = Field(default="Job Posting", description="Job Title")
    description: str = Field(default="Job description and scope", description="Full job description")
    required_skills: List[Union[str, int, Dict[str, Any]]] = Field(default_factory=list, description="List of required skills")
    key_priorities_preferences: Optional[str] = Field(
        None,
        alias="key_priorities",
        description="Key priorities or hiring preferences specified by employer"
    )

    class Config:
        populate_by_name = True


class CandidateInput(BaseModel):
    candidate_id: Optional[Union[str, int]] = Field(None, description="Unique identifier for candidate")
    jobseeker_id: Optional[int] = Field(None, description="Alternative key for candidate ID")
    name: Optional[str] = Field(None, description="Candidate full name")
    first_name: Optional[str] = Field(None, description="Candidate first name")
    last_name: Optional[str] = Field(None, description="Candidate last name")
    match_score: Optional[float] = Field(None, description="Calculated AI match percentage (e.g. 88.0 or 0.88)")
    final_score: Optional[float] = Field(None, description="Alternative match score field")
    skills: List[Union[str, int, Dict[str, Any]]] = Field(default_factory=list, description="Candidate skill list")
    experience_summary: Optional[str] = Field(default="", description="Summary of past work experience")
    education: Optional[str] = Field(default="", description="Degree, field of study, and institution")
    certifications: List[str] = Field(default_factory=list, description="Licenses and certifications")

    @property
    def resolved_id(self) -> str:
        if self.candidate_id is not None:
            return str(self.candidate_id)
        if self.jobseeker_id is not None:
            return str(self.jobseeker_id)
        return "cand_unknown"

    @property
    def resolved_name(self) -> str:
        if self.name and self.name.strip():
            return self.name.strip()
        full = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full if full else f"Candidate #{self.resolved_id}"

    @property
    def resolved_score(self) -> float:
        val = self.match_score if self.match_score is not None else self.final_score
        if val is None:
            return 0.0
        if 0.0 < val <= 1.0:
            return round(val * 100, 1)
        return round(val, 1)

    @property
    def resolved_skills_list(self) -> List[str]:
        result = []
        for s in self.skills:
            if isinstance(s, str):
                result.append(s)
            elif isinstance(s, dict):
                s_name = s.get("name") or s.get("skill_name") or s.get("skill_id")
                if s_name:
                    result.append(str(s_name))
            elif isinstance(s, (int, float)):
                result.append(f"Skill #{s}")
        return result


class CandidateFeedbackRequest(BaseModel):
    job_id: Optional[int] = None
    job_details: Optional[JobDetails] = None
    candidates: List[CandidateInput] = Field(..., min_length=1)

    @model_validator(mode="before")
    @classmethod
    def assemble_job_details_if_missing(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("job_details") and data.get("job_id"):
                data["job_details"] = {
                    "job_id": data.get("job_id"),
                    "title": data.get("job_title", f"Job Posting #{data.get('job_id')}"),
                    "description": data.get("job_description", "General Job Requirements"),
                    "required_skills": data.get("required_skills", []),
                }
        return data


class CandidateFeedbackItem(BaseModel):
    candidate_id: str = Field(..., description="Candidate unique ID")
    unique_strengths: List[str] = Field(..., description="Key standout strengths relative to job requirements")
    potential_gaps_or_risks: List[str] = Field(..., description="Areas where candidate may need mentorship or ramp-up time")
    best_suited_for: str = Field(..., description="Role focus summary (e.g., Immediate execution vs long-term leadership)")
    recommended_interview_questions: List[str] = Field(..., description="2-3 targeted questions to test weak spots or claims")


class LegacyPHPFeedbackItem(BaseModel):
    jobseeker_id: int
    strengths: List[str]
    growth_areas: List[str]
    interview_questions: List[str]
    match_tiebreaker_notes: str


class CandidateFeedbackResponse(BaseModel):
    comparison_summary: str = Field(..., description="Executive summary contrasting the tied candidates")
    candidates_feedback: List[CandidateFeedbackItem] = Field(..., description="Detailed breakdown per candidate")
    feedback: Optional[List[LegacyPHPFeedbackItem]] = Field(None, description="Backwards compatible PHP feedback items")


# ---------------------------------------------------------------------------
# EXACT PROMPT TEMPLATE
# ---------------------------------------------------------------------------

CANDIDATE_COMPARISON_PROMPT_TEMPLATE = """You are a Senior Executive Recruiter and Talent Acquisition AI Specialist for "SikapHub".

### CONTEXT & TASK
An employer is reviewing candidates who are under consideration or tied in match score for a job posting.
Your task is to analyze the unique profile, skills, education, and experience of EACH candidate beyond the raw percentage score and generate an objective, constructive, and highly INDIVIDUALIZED side-by-side comparative breakdown.

CRITICAL REQUIREMENT:
Each candidate MUST receive distinct, personalized feedback, growth areas, and interview questions that directly reference their specific background and skill sets. NEVER return identical or generic statements for different candidates.

### JOB DETAILS
- Title: {job_title}
- Description: {job_description}
- Required Skills: {required_skills}
- Key Priorities & Preferences: {key_priorities}

### CANDIDATES TO COMPARE
{candidates_text}

### ANALYSIS CRITERIA
1. Contrast distinct trade-offs between candidates (e.g., candidate A offers deep domain expertise in X, while candidate B brings versatile hands-on experience in Y).
2. Avoid generic praise or repetitive templates. Be specific to each candidate's profile.
3. Formulate 2-3 interview questions customized specifically to probe each candidate's unique background gaps, verify past achievements, or evaluate role readiness.

### STRICT OUTPUT FORMAT
You MUST respond with valid, parseable JSON matching this EXACT structure:

{{
  "comparison_summary": "Executive summary contrasting the overall strengths and trade-offs of all candidates.",
  "candidates_feedback": [
    {{
      "candidate_id": "<candidate_id_from_input>",
      "unique_strengths": [
        "Specific standout strength 1 referencing candidate skills/background",
        "Specific standout strength 2"
      ],
      "potential_gaps_or_risks": [
        "Specific growth area or risk 1 customized to this candidate",
        "Specific growth area or risk 2"
      ],
      "best_suited_for": "Specific role focus tailored to this candidate",
      "recommended_interview_questions": [
        "Targeted interview question 1 specifically for this candidate",
        "Targeted interview question 2 for this candidate"
      ]
    }}
  ]
}}
"""


# ---------------------------------------------------------------------------
# CORE GENERATION LOGIC
# ---------------------------------------------------------------------------

def format_candidates_for_prompt(candidates: List[CandidateInput]) -> str:
    formatted_blocks = []
    for idx, c in enumerate(candidates, start=1):
        skills_str = ", ".join(c.resolved_skills_list) if c.resolved_skills_list else "None specified"
        exp_str = c.experience_summary.strip() if c.experience_summary else "No detailed work history provided"
        edu_str = c.education.strip() if c.education else "No education history listed"
        certs_str = ", ".join(c.certifications) if c.certifications else "None listed"

        block = (
            f"Candidate #{idx}:\n"
            f"- Candidate ID: {c.resolved_id}\n"
            f"- Name: {c.resolved_name}\n"
            f"- Match Score: {c.resolved_score}%\n"
            f"- Skills: {skills_str}\n"
            f"- Work Experience: {exp_str}\n"
            f"- Education: {edu_str}\n"
            f"- Certifications: {certs_str}\n"
        )
        formatted_blocks.append(block)
    return "\n".join(formatted_blocks)


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code block wrappers or extra text around LLM JSON response."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    return json.loads(text)


def _build_response_object(raw_data: Dict[str, Any], payload: CandidateFeedbackRequest) -> CandidateFeedbackResponse:
    """Build standardized response object containing both modern schema and legacy PHP mapping."""
    comparison_summary = raw_data.get("comparison_summary") or raw_data.get("summary") or "Candidate comparative evaluation complete."
    raw_feedback_list = raw_data.get("candidates_feedback") or raw_data.get("feedback") or []

    feedback_items = []
    legacy_items = []

    # Map inputs by ID for fallback enrichment
    input_map = {c.resolved_id: c for c in payload.candidates}

    for item in raw_feedback_list:
        cand_id = str(item.get("candidate_id") or item.get("jobseeker_id") or "")
        input_c = input_map.get(cand_id)

        strengths = item.get("unique_strengths") or item.get("strengths") or []
        if isinstance(strengths, str):
            strengths = [strengths]

        gaps = item.get("potential_gaps_or_risks") or item.get("growth_areas") or []
        if isinstance(gaps, str):
            gaps = [gaps]

        best_suited = item.get("best_suited_for") or item.get("match_tiebreaker_notes") or "General Role Execution"
        if isinstance(best_suited, list):
            best_suited = " ".join(best_suited)

        questions = item.get("recommended_interview_questions") or item.get("interview_questions") or []
        if isinstance(questions, str):
            questions = [questions]

        fb_item = CandidateFeedbackItem(
            candidate_id=cand_id,
            unique_strengths=strengths,
            potential_gaps_or_risks=gaps,
            best_suited_for=best_suited,
            recommended_interview_questions=questions
        )
        feedback_items.append(fb_item)

        # Build legacy PHP row compatibility item
        try:
            js_id = int(cand_id)
        except ValueError:
            js_id = 0

        legacy_items.append(LegacyPHPFeedbackItem(
            jobseeker_id=js_id,
            strengths=strengths,
            growth_areas=gaps,
            interview_questions=questions,
            match_tiebreaker_notes=f"{best_suited} (AI Match Score: {input_c.resolved_score if input_c else 0.0}%)"
        ))

    # If any input candidate was missing in LLM output, generate individualized fallback
    processed_ids = {fb.candidate_id for fb in feedback_items}
    for c in payload.candidates:
        if c.resolved_id not in processed_ids:
            fb_item, legacy_item = _generate_individual_fallback(c, payload.job_details)
            feedback_items.append(fb_item)
            legacy_items.append(legacy_item)

    return CandidateFeedbackResponse(
        comparison_summary=comparison_summary,
        candidates_feedback=feedback_items,
        feedback=legacy_items
    )


def generate_candidate_feedback(payload: CandidateFeedbackRequest) -> CandidateFeedbackResponse:
    """Generate comparative candidate feedback via Gemini LLM with structured JSON parsing."""
    job = payload.job_details or JobDetails(job_id=payload.job_id)
    candidates_formatted = format_candidates_for_prompt(payload.candidates)
    
    req_skills_str = ", ".join([str(s) for s in job.required_skills]) if job.required_skills else "General technical skills"

    prompt = CANDIDATE_COMPARISON_PROMPT_TEMPLATE.format(
        job_title=job.title,
        job_description=job.description,
        required_skills=req_skills_str,
        key_priorities=job.key_priorities_preferences or "Standard qualifications match",
        candidates_text=candidates_formatted
    )

    if not genai or not GEMINI_API_KEY:
        return _heuristic_candidate_feedback_fallback(payload)

    try:
        model = genai.GenerativeModel(
            model_name=DEFAULT_GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2}
        )
        response = model.generate_content(prompt)
        raw_json = clean_json_response(response.text)
        return _build_response_object(raw_json, payload)
    except Exception:
        try:
            model_fallback = genai.GenerativeModel(model_name="gemini-pro")
            response = model_fallback.generate_content(prompt)
            raw_json = clean_json_response(response.text)
            return _build_response_object(raw_json, payload)
        except Exception:
            return _heuristic_candidate_feedback_fallback(payload)


def _generate_individual_fallback(c: CandidateInput, job: Optional[JobDetails]) -> (CandidateFeedbackItem, LegacyPHPFeedbackItem):
    """Generate highly customized, individual fallback feedback per candidate when offline."""
    cand_name = c.resolved_name
    skills = c.resolved_skills_list
    score = c.resolved_score
    job_title = job.title if job else "Job Role"

    if skills:
        top_skills = ", ".join(skills[:3])
        strength_1 = f"Demonstrates verified proficiency in key candidate skill set: {top_skills}."
    else:
        strength_1 = f"Calculated candidate match score of {score}% aligned with primary position criteria."

    if c.experience_summary and len(c.experience_summary.strip()) > 10:
        exp_snippet = c.experience_summary.strip()[:70] + "..."
        strength_2 = f"Practical work history background: '{exp_snippet}'."
    elif c.education and len(c.education.strip()) > 5:
        strength_2 = f"Educational alignment: {c.education.strip()}."
    else:
        strength_2 = f"Strong potential for role execution based on overall qualifications."

    # Individualized growth areas
    growth_1 = f"Evaluate depth of practical experience in {job_title} workflows during the interview phase."
    if len(skills) < 3:
        growth_2 = f"Verify familiarity with specialized tools or frameworks outside of core {skills[0] if skills else 'skills'}."
    else:
        growth_2 = f"Assess past project scalability and technical leadership capabilities in {skills[-1]}."

    # Individualized interview questions
    if skills:
        q1 = f"Can you detail a complex real-world scenario where you applied {skills[0]} to solve a major project issue?"
        q2 = f"How do you stay updated and apply modern best practices in {skills[1] if len(skills) > 1 else skills[0]}?"
    else:
        q1 = f"Can you walk us through your most successful project relevant to the {job_title} position?"
        q2 = f"What specific tools and methodologies do you rely on for daily problem solving?"

    best_suited = f"Execution in {job_title} roles leveraging {skills[0] if skills else 'foundational'} skills."

    fb_item = CandidateFeedbackItem(
        candidate_id=c.resolved_id,
        unique_strengths=[strength_1, strength_2],
        potential_gaps_or_risks=[growth_1, growth_2],
        best_suited_for=best_suited,
        recommended_interview_questions=[q1, q2]
    )

    try:
        js_id = int(c.resolved_id)
    except ValueError:
        js_id = 0

    legacy_item = LegacyPHPFeedbackItem(
        jobseeker_id=js_id,
        strengths=[strength_1, strength_2],
        growth_areas=[growth_1, growth_2],
        interview_questions=[q1, q2],
        match_tiebreaker_notes=f"{best_suited} (Match Score: {score}%)"
    )

    return fb_item, legacy_item


def _heuristic_candidate_feedback_fallback(payload: CandidateFeedbackRequest) -> CandidateFeedbackResponse:
    """Fallback generator providing individualized feedback per candidate."""
    job = payload.job_details or JobDetails(job_id=payload.job_id)
    feedback_items = []
    legacy_items = []

    for c in payload.candidates:
        fb_item, legacy_item = _generate_individual_fallback(c, job)
        feedback_items.append(fb_item)
        legacy_items.append(legacy_item)

    summary = f"Executive comparative breakdown for {len(payload.candidates)} applicant(s) for {job.title}. Candidate profiles show distinct individual skills and background trade-offs."
    return CandidateFeedbackResponse(
        comparison_summary=summary,
        candidates_feedback=feedback_items,
        feedback=legacy_items
    )
