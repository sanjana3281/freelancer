import os, re
from google import genai
from pdfminer.high_level import extract_text as pdf_extract
from docx import Document

def extract_text_from_file(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return pdf_extract(path)
    if path.lower().endswith(".docx"):
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Unsupported file type")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_ID = "models/gemini-2.0-flash"   # fast & widely available for text

SUGGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "missing_sections": {"type": "array", "items": {"type": "string"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "rewrites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string"},
                    "before": {"type": "string"},
                    "suggested_rewrite": {"type": "string"},
                },
                "required": ["section", "suggested_rewrite"]
            }
        },
        "keywords_to_add": {"type": "array", "items": {"type": "string"}},
        "links_to_add": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["suggestions"]
}

SYSTEM = (
  "You are an expert technical resume editor for software roles. "
  "Return only JSON that matches the schema."
)

PROMPT = """Given the resume text, produce concrete changes—no generic advice.
- 'missing_sections': major sections absent (e.g., Projects, Achievements, Links)
- 'suggestions': 8–15 crisp, imperative edits (measurable when possible)
- 'rewrites': drop-in rewrites for weak bullets/summary (1–2 lines). If original unclear, leave 'before' empty.
- 'keywords_to_add': role-relevant terms missing (e.g., Django ORM, REST, CI/CD, PostgreSQL)
- 'links_to_add': concrete placeholders if links are missing (GitHub, portfolio, LinkedIn)
Resume:
---
{resume_text}
---
Rules:
- Be specific; show examples (“Replace ‘worked on website’ with ‘Built…’ …”).
- ATS safe (no emojis).
"""
def suggest_changes(resume_text: str) -> dict:
    import json, re
    resume_text = (resume_text or "").strip()[:40000]

    prompt = (
        SYSTEM
        + "\n\nRespond ONLY with a valid JSON object matching this schema:\n"
        + json.dumps(SUGGEST_SCHEMA)  # give schema verbatim
        + "\n\n"
        + PROMPT.format(resume_text=resume_text)
    )

    try:
        # New surface (structured output)
        if hasattr(client, "responses"):
            resp = client.responses.generate(
                model=MODEL_ID,                 # e.g., "models/gemini-2.0-flash"
                input=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": SUGGEST_SCHEMA,
                    "max_output_tokens": 1400,
                },
            )
            data = getattr(resp, "parsed", None)
            if data:
                return data
            txt = getattr(resp, "output_text", "") or ""
        else:
            # Classic surface
            resp = client.models.generate_content(
                model=MODEL_ID,
                contents=[{"role":"user","parts":[{"text":prompt}]}],
                config={"max_output_tokens": 1400},
            )
            txt = getattr(resp, "text", "") or ""

        # Be forgiving: extract the first JSON object anywhere in the output
        m = re.search(r"(\{(?:.|\n)*\})", txt)
        if m:
            return json.loads(m.group(1))

        # Debug help if something goes wrong
        print("RAW (no JSON):", txt[:500])
        return {"suggestions": ["Model did not return JSON."]}
    except Exception as e:
        print("Analyzer error:", e)
        return {"suggestions": [f"Analyzer error: {e}"]}

