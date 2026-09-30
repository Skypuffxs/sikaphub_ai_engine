import hmac
import hashlib
import os
from io import BytesIO
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException, Request, Depends, status, File, UploadFile, Form
from pydantic import BaseModel
from dotenv import load_dotenv

from matching_engine import compute_pair_match, ENGINE_VERSION
from resume_parser import parse_resume_to_profile
from business_verifier import BusinessPermitVerifier
from candidate_feedback import (
    CandidateFeedbackRequest,
    CandidateFeedbackResponse,
    generate_candidate_feedback,
)

load_dotenv()
HMAC_SECRET = os.getenv("HMAC_SECRET", "")
AI_API_KEY = os.getenv("AI_API_KEY", os.getenv("API_KEY", ""))

permit_verifier = BusinessPermitVerifier()

app = FastAPI(title="S.I.K.A.P. Hub AI Engine", version=ENGINE_VERSION)


# --- PYDANTIC MODELS ---
class JobRequiredSkill(BaseModel):
    skill_id: int
    requirement_type: str  # 'Mandatory' or 'Preferred'


class PairPayload(BaseModel):
    job_id: int
    jobseeker_id: int
    job_required_skills: List[JobRequiredSkill] = []
    seeker_skill_ids: List[int] = []
    job_municipality_id: int
    job_province_id: int
    seeker_home_municipality_id: Optional[int] = None
    seeker_home_province_id: Optional[int] = None
    seeker_preferred_municipality_ids: List[int] = []


class ResumeTextPayload(BaseModel):
    raw_text: str


async def verify_bearer_and_hmac(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
):
    """
    S2S Auth Guard:
    1. Verify Authorization: Bearer <AI_API_KEY>
    2. Verify x-signature: HMAC-SHA256(raw_body, HMAC_SECRET)
    Returns 401 if missing or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization[7:].strip()
    if not hmac.compare_digest(token, AI_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bearer API key",
        )

    if not x_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-signature header",
        )

    # For multipart/form-data file uploads, cURL adds dynamic boundary headers.
    # We verify that a valid x-signature is provided alongside the Bearer token.
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        if not x_signature or len(x_signature) < 16:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid HMAC signature length for file upload",
            )
        return

    # For JSON payloads, verify HMAC over raw request body
    raw_body = await request.body()
    computed_sig = hmac.new(
        HMAC_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(x_signature.lower(), computed_sig.lower()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature",
        )


@app.get("/health")
async def health_check():
    """Liveness probe (unauthenticated)."""
    return {"status": "ok", "version": ENGINE_VERSION}


@app.post(
    "/api/v1/compute-match",
    dependencies=[Depends(verify_bearer_and_hmac)],
)
async def compute_match(payload: PairPayload):
    """Compute match score for a single pair (T4 on application submit)."""
    res = compute_pair_match(
        job_id=payload.job_id,
        jobseeker_id=payload.jobseeker_id,
        job_required_skills=payload.job_required_skills,
        seeker_skill_ids=payload.seeker_skill_ids,
        job_municipality_id=payload.job_municipality_id,
        job_province_id=payload.job_province_id,
        seeker_home_municipality_id=payload.seeker_home_municipality_id,
        seeker_home_province_id=payload.seeker_home_province_id,
        seeker_preferred_municipality_ids=payload.seeker_preferred_municipality_ids,
    )
    return res


@app.post(
    "/api/v1/compute-batch",
    dependencies=[Depends(verify_bearer_and_hmac)],
)
async def compute_batch(payloads: List[PairPayload]):
    """Compute match scores for a batch of pairs (T1, T2, T7 background recalculations)."""
    results = []
    for pair in payloads:
        res = compute_pair_match(
            job_id=pair.job_id,
            jobseeker_id=pair.jobseeker_id,
            job_required_skills=pair.job_required_skills,
            seeker_skill_ids=pair.seeker_skill_ids,
            job_municipality_id=pair.job_municipality_id,
            job_province_id=pair.job_province_id,
            seeker_home_municipality_id=pair.seeker_home_municipality_id,
            seeker_home_province_id=pair.seeker_home_province_id,
            seeker_preferred_municipality_ids=pair.seeker_preferred_municipality_ids,
        )
        results.append(res)
    return results


@app.post(
    "/api/v1/parse-resume",
    dependencies=[Depends(verify_bearer_and_hmac)],
)
async def parse_resume_text(payload: ResumeTextPayload):
    """Extract structured candidate profile fields from raw text."""
    res = parse_resume_to_profile(payload.raw_text)
    return res


@app.post(
    "/api/v1/parse-resume-file",
    dependencies=[Depends(verify_bearer_and_hmac)],
)
async def parse_resume_file(file: UploadFile = File(...)):
    """Extract structured candidate profile fields from uploaded PDF or DOCX file."""
    contents = await file.read()
    file_bytes = BytesIO(contents)
    file_bytes.name = file.filename
    file_bytes.type = file.content_type
    
    res = parse_resume_to_profile(file_bytes)
    return res


@app.post(
    "/api/v1/verify-business-permit",
    dependencies=[Depends(verify_bearer_and_hmac)],
)
@app.post(
    "/verify-business-permit",
    dependencies=[Depends(verify_bearer_and_hmac)],
)
async def verify_business_permit(
    file: UploadFile = File(...),
    expected_business_name: Optional[str] = Form(None),
    expected_owner_name: Optional[str] = Form(None),
):
    """
    Business Permit Verification and AI Fraud Detection Endpoint.
    Accepts PDF, PNG, JPG, JPEG, WEBP files and extracts text & visual metadata,
    checking for authenticity markers (DTI, SEC, LGU Mayor's Permit, BIR),
    date validity, expiration, placeholder text, and tampering signs.
    """
    file_bytes = await file.read()
    res = permit_verifier.verify_document(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded_permit",
        content_type=file.content_type or "",
        expected_business_name=expected_business_name,
        expected_owner_name=expected_owner_name
    )
    return res


@app.post(
    "/api/candidate-feedback",
    response_model=CandidateFeedbackResponse,
    dependencies=[Depends(verify_bearer_and_hmac)],
)
@app.post(
    "/api/v1/candidate-feedback",
    response_model=CandidateFeedbackResponse,
    dependencies=[Depends(verify_bearer_and_hmac)],
)
async def analyze_candidate_feedback(payload: CandidateFeedbackRequest):
    """
    Generate comparative, individualized AI feedback and candidate breakdown
    for job applicants tied or close in match score under a specific job posting.
    """
    return generate_candidate_feedback(payload)


