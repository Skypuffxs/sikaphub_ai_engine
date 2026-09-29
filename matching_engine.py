"""
S.I.K.A.P. Hub AI Matching Engine (DFD 4.0 / Decoupled V2).

Stateless matching logic for job postings and job seekers.
Formula:
    skill_score = (2 * mandatory_met + preferred_met) / (2 * mandatory_total + preferred_total)

    location_score (Subtle Tie-Breaker Weight: 5%):
        1.00 (100% / +5.0 pts) same municipality / town or neutral
        0.80 ( 80% / +4.0 pts) in seeker's preferred municipalities
        0.60 ( 60% / +3.0 pts) same province
        0.20 ( 20% / +1.0 pts) different province

    raw_score = (skill_score * 0.95) + (location_score * 0.05)
    final_score = min(raw_score, 0.9500)  # Capped at 95.00% to avoid misleading 100% match expectations

Diagnostic metrics:
    raw_jaccard: intersection(required, seeker) / union(required, seeker)
"""

ENGINE_VERSION = "2.2.0"


def compute_pair_match(
    job_id: int,
    jobseeker_id: int,
    job_required_skills: list,
    seeker_skill_ids: list,
    job_municipality_id: int,
    job_province_id: int,
    seeker_home_municipality_id: int | None = None,
    seeker_home_province_id: int | None = None,
    seeker_preferred_municipality_ids: list[int] | None = None,
) -> dict:
    # 1. Parse and categorize job skills
    mandatory_reqs = set()
    preferred_reqs = set()
    for skill in job_required_skills or []:
        s_id = skill.get("skill_id") if isinstance(skill, dict) else getattr(skill, "skill_id", None)
        r_type = skill.get("requirement_type") if isinstance(skill, dict) else getattr(skill, "requirement_type", "")
        if s_id is not None:
            if r_type == "Mandatory":
                mandatory_reqs.add(s_id)
            elif r_type == "Preferred":
                preferred_reqs.add(s_id)

    mandatory_total = len(mandatory_reqs)
    preferred_total = len(preferred_reqs)
    total_denom = (2 * mandatory_total) + (1 * preferred_total)

    # Scorable guardrail (C-22, UC-05 BR-7):
    if total_denom == 0:
        return {
            "job_id": job_id,
            "jobseeker_id": jobseeker_id,
            "error": "No scorable required skills provided for job",
        }

    # 2. Parse seeker skills
    seeker_skills_set = set(seeker_skill_ids or [])

    # 3. Met skills calculations
    mandatory_met = len(mandatory_reqs.intersection(seeker_skills_set))
    preferred_met = len(preferred_reqs.intersection(seeker_skills_set))

    # 4. Skill score (0.0000 - 1.0000)
    skill_score = round(((2 * mandatory_met) + (1 * preferred_met)) / total_denom, 4)

    # 5. Raw Jaccard (Intersection / Union of required & seeker skills)
    all_reqs = mandatory_reqs.union(preferred_reqs)
    intersection = all_reqs.intersection(seeker_skills_set)
    union = all_reqs.union(seeker_skills_set)
    raw_jaccard = round(len(intersection) / len(union), 4) if union else 0.0000

    # 6. Geographic Proximity Location Score & Tier (Subtle 5% Tie-Breaker Weight)
    pref_locs = set(seeker_preferred_municipality_ids or [])

    if seeker_home_municipality_id is None or seeker_home_province_id is None:
        location_data_present = False
        geo_tier = "neutral"
        location_score = 1.00
    elif job_municipality_id == seeker_home_municipality_id:
        location_data_present = True
        geo_tier = "home_municipality"
        location_score = 1.00
    elif job_municipality_id in pref_locs:
        location_data_present = True
        geo_tier = "preferred_municipality"
        location_score = 0.80
    elif job_province_id == seeker_home_province_id:
        location_data_present = True
        geo_tier = "home_province"
        location_score = 0.60
    else:
        location_data_present = True
        geo_tier = "other_province"
        location_score = 0.20

    # 7. Weighted Final Score: 95% Skill Match + 5% Location Tie-Breaker
    SKILL_WEIGHT = 0.95
    LOCATION_WEIGHT = 0.05
    MAX_CAP = 0.9500  # Cap maximum match score at 95.00% to prevent unrealistic 100% hire expectations

    raw_final = (skill_score * SKILL_WEIGHT) + (location_score * LOCATION_WEIGHT)
    final_score = round(min(raw_final, MAX_CAP), 4)

    return {
        "job_id": job_id,
        "jobseeker_id": jobseeker_id,
        "skill_score": skill_score,
        "location_score": location_score,
        "geo_multiplier": location_score,
        "final_score": final_score,
        "raw_jaccard": raw_jaccard,
        "engine_version": ENGINE_VERSION,
        "diagnostics": {
            "mandatory_met": mandatory_met,
            "mandatory_total": mandatory_total,
            "preferred_met": preferred_met,
            "preferred_total": preferred_total,
            "location_data_present": location_data_present,
            "geo_tier": geo_tier,
            "skill_weight": SKILL_WEIGHT,
            "location_weight": LOCATION_WEIGHT,
            "max_score_cap": MAX_CAP,
        },
    }


