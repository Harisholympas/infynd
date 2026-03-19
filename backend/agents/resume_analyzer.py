"""AI-backed resume analysis service."""
import io
import json
import re
import zipfile
from typing import Dict, Any

from core.llm import llm_client


def score_to_grade(score: int | float | None) -> str:
    try:
        value = float(score)
    except Exception:
        return "N/A"
    if value >= 85:
        return "A"
    if value >= 70:
        return "B"
    if value >= 55:
        return "C"
    if value >= 40:
        return "D"
    return "E"


def infer_shortlist_decision(score: int | float | None) -> str:
    try:
        value = float(score)
    except Exception:
        return "maybe"
    if value >= 80:
        return "yes"
    if value >= 55:
        return "maybe"
    return "no"


def extract_docx_text(content: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", xml)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def extract_pdf_text(content: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = " ".join((page.extract_text() or "") for page in reader.pages)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def extract_resume_text(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = extract_pdf_text(content)
        if text:
            return text
    if lower.endswith(".docx"):
        text = extract_docx_text(content)
        if text:
            return text
    return content.decode("utf-8", errors="ignore")


def heuristic_resume_summary(text: str, job_title: str = "", job_description: str = "") -> Dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", normalized, re.I)
    phone_match = re.search(r"(\+?\d[\d\s().-]{8,}\d)", normalized)
    skills_catalog = [
        "python", "java", "javascript", "typescript", "react", "node", "sql", "excel", "power bi",
        "machine learning", "data analysis", "recruitment", "sales", "marketing", "aws", "docker",
        "fastapi", "communication", "leadership", "project management", "html", "css"
    ]
    found_skills = [skill for skill in skills_catalog if skill in normalized.lower()]
    experience_match = re.search(r"(\d+)\+?\s+years", normalized.lower())
    top_lines = [line.strip() for line in text.splitlines() if line.strip()][:8]
    summary = " ".join(top_lines[:4])[:700] or normalized[:700]

    jd_keywords = []
    if job_title:
        jd_keywords.extend(job_title.lower().split())
    if job_description:
        jd_keywords.extend(re.findall(r"[a-zA-Z][a-zA-Z+.#-]{2,}", job_description.lower()))
    jd_keywords = [word for word in jd_keywords if len(word) > 2]
    matched_keywords = sorted({word for word in jd_keywords if word in normalized.lower()})[:12]
    missing_keywords = sorted({word for word in jd_keywords if word not in normalized.lower()})[:12]
    match_score = min(100, 35 + len(found_skills) * 5 + len(matched_keywords) * 4)

    return {
        "candidate_name": top_lines[0] if top_lines else "Unknown candidate",
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
        "skills": found_skills[:10],
        "experience_years": int(experience_match.group(1)) if experience_match else None,
        "summary": summary,
        "job_fit_score": match_score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "strengths": found_skills[:5],
        "risks": [f"Missing expected keyword: {word}" for word in missing_keywords[:5]],
        "grade": score_to_grade(match_score),
        "shortlist_decision": infer_shortlist_decision(match_score),
    }


class ResumeAnalyzer:
    async def llm_resume_summary(self, text: str, job_title: str = "", job_description: str = "") -> Dict[str, Any]:
        prompt = f"""
You are an expert recruiting analyst.
Analyze this resume and return strict JSON with:
- candidate_name
- professional_summary
- key_skills (array of strings)
- likely_experience_years
- strengths (array of strings)
- risks (array of strings)
- matched_keywords (array of strings)
- missing_keywords (array of strings)
- recommended_role
- shortlist_decision (yes/no/maybe)
- job_fit_score (0-100)

Target job title: {job_title}
Target job description: {job_description}

Resume:
{text[:8000]}
"""
        try:
            response = await llm_client.generate(prompt, temperature=0.1)
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                return {
                    "candidate_name": parsed.get("candidate_name", ""),
                    "summary": parsed.get("professional_summary", ""),
                    "skills": parsed.get("key_skills", []),
                    "experience_years": parsed.get("likely_experience_years"),
                    "strengths": parsed.get("strengths", []),
                    "risks": parsed.get("risks", []),
                    "matched_keywords": parsed.get("matched_keywords", []),
                    "missing_keywords": parsed.get("missing_keywords", []),
                    "recommended_role": parsed.get("recommended_role", ""),
                    "shortlist_decision": parsed.get("shortlist_decision", ""),
                    "job_fit_score": parsed.get("job_fit_score", 0),
                    "grade": parsed.get("grade", ""),
                }
        except Exception:
            pass
        return {}

    async def analyze_text(self, resume_text: str, job_title: str = "", job_description: str = "") -> Dict[str, Any]:
        heuristic = heuristic_resume_summary(resume_text, job_title, job_description)
        llm_summary = await self.llm_resume_summary(resume_text, job_title, job_description)
        merged = {**heuristic, **{k: v for k, v in llm_summary.items() if v not in (None, "", [], {})}}
        if not merged.get("grade"):
            merged["grade"] = score_to_grade(merged.get("job_fit_score"))
        if not merged.get("shortlist_decision"):
            merged["shortlist_decision"] = infer_shortlist_decision(merged.get("job_fit_score"))
        return {
            "analysis": merged,
            "resume_text_preview": resume_text[:1200],
        }

    async def analyze_file(self, filename: str, content: bytes, job_title: str = "", job_description: str = "") -> Dict[str, Any]:
        text = extract_resume_text(filename or "resume.txt", content)
        if not text.strip():
            raise ValueError("Could not extract text from the uploaded resume")
        result = await self.analyze_text(text, job_title, job_description)
        return {
            "file_name": filename,
            **result,
        }


resume_analyzer = ResumeAnalyzer()
