import re
from typing import Any

import spacy

_nlp: Any = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            _nlp = spacy.blank("en")
    return _nlp


def _normalize_skill_list(skills_text: str) -> list[str]:
    if not skills_text or not skills_text.strip():
        return []
    parts = re.split(r"[,;\n]+", skills_text)
    return [p.strip() for p in parts if p.strip()]


def extract_resume_skills_experience(resume_text: str, job_skills_required: str) -> dict[str, Any]:
    job_skills = _normalize_skill_list(job_skills_required)
    resume_lower = (resume_text or "").lower()
    nlp = _get_nlp()
    doc = nlp(resume_text or "")

    matching: list[str] = []
    missing: list[str] = []
    for skill in job_skills:
        sl = skill.lower()
        if sl in resume_lower:
            matching.append(skill)
        else:
            missing.append(skill)

    denom = max(len(job_skills), 1)
    score = round((len(matching) / denom) * 100, 2)

    experience_match = bool(
        re.search(r"\d+\s*\+?\s*(?:year|yr)s?", resume_lower)
        or re.search(r"\b(?:internship|experience|worked|employment)\b", resume_lower)
    )

    titles = [chunk.text.strip() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 2][:20]
    return {
        "matching_skills": matching,
        "missing_skills": missing,
        "experience_match": experience_match,
        "score": score,
        "extracted_titles": titles,
    }
