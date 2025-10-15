# ai_assist/services_resume.py
import io, re
from typing import Tuple, Dict, Any
from PyPDF2 import PdfReader
from docx import Document
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR"


SECTION_HINTS = {
    "skills": re.compile(r"\bskills?\b", re.I),
    "projects": re.compile(r"\bprojects?\b|\bexperience\b", re.I),
    "education": re.compile(r"\beducation\b", re.I),
    "achievements": re.compile(r"\bachievements?\b|\bawards?\b|\bcertifications?\b", re.I),
    "links": re.compile(r"\bgithub\.com|\bbehance\.net|\blinked?in\.com|\bportfolio\b|\bwebsite\b", re.I),
}

def _read_pdf(buff: bytes) -> str:
    text = []
    reader = PdfReader(io.BytesIO(buff))
    for p in reader.pages:
        text.append(p.extract_text() or "")
    return "\n".join(text)

def _read_docx(buff: bytes) -> str:
    f = io.BytesIO(buff)
    doc = Document(f)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_file(dj_file) -> Tuple[str, str]:
    """Return (text, ext)."""
    data = dj_file.read()
    name = dj_file.name.lower()
    if name.endswith(".pdf"):
        return _read_pdf(data), "pdf"
    if name.endswith(".docx"):
        return _read_docx(data), "docx"
    return data.decode(errors="ignore"), "txt"

def analyze_resume_text(text: str) -> Dict[str, Any]:
    t = text or ""
    low = t.lower()

    # crude signals
    has_skills = bool(SECTION_HINTS["skills"].search(low))
    has_projects = bool(SECTION_HINTS["projects"].search(low))
    has_ach = bool(SECTION_HINTS["achievements"].search(low))
    has_links = bool(SECTION_HINTS["links"].search(low))
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", t)
    phones = re.findall(r"(?:\+?\d[\s-]?){8,}", t)

    # simple skill count (comma/line separated)
    skill_lines = re.findall(r"(skills?:?)(.*)", t, re.I)
    approx_skill_count = 0
    for _, line in skill_lines:
        approx_skill_count += max(len([s for s in re.split(r"[,\|•;]", line) if s.strip()]), 0)

    score = 60
    findings = []

    def add(level, msg): findings.append({"level": level, "message": msg})

    if not emails: add("warn", "No email detected."); score -= 4
    if not phones: add("info", "Phone number not detected."); score -= 2

    if not has_skills: 
        add("warn", "No clear Skills section."); score -= 8
    else:
        if approx_skill_count < 5: 
            add("info", "Skills look sparse; target 8–12 focused skills."); score -= 3

    if not has_projects:
        add("warn", "Projects/Experience section missing."); score -= 10
    if not has_ach:
        add("info", "Add Achievements/Certifications to stand out."); score -= 3
    if not has_links:
        add("tip", "Add GitHub/Portfolio/LinkedIn links (helps clients verify)."); score -= 3

    # metric/impact language
    if not re.search(r"\b\d+%|\b(increased|reduced|improved|optimized|saved)\b", low):
        add("tip", "Use action verbs + metrics (e.g., “reduced load time 30%”)."); score -= 3

    score = max(0, min(100, score))

    suggestions = {
        "profile_strength": score,
        "checks": findings,
        "summary": f"Profile Strength: {score}/100",
        "headlines": [
            "✅ Skills present" if has_skills else "⚠️ Skills section missing",
            "✅ Links present" if has_links else "⚠️ Missing portfolio/GitHub/LinkedIn",
            "✅ Projects/Experience present" if has_projects else "⚠️ Missing Projects/Experience",
        ],
        "ai_suggestions_like": [
            "Add 2–3 achievements with measurable results.",
            "Include GitHub/portfolio link for technical roles.",
            "Use action verbs + metrics in project bullets."
        ],
    }
    return suggestions
