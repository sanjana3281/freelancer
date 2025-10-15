# import google.generativeai as genai
# from django.conf import settings
# import os

# DEFAULT_REPLY = (
#     "**(AI temporarily unavailable; here’s quick advice)**\n"
#     "- Add 2–3 achievements with measurable results.\n"
#     "- Include GitHub/Portfolio/LinkedIn links.\n"
#     "- Keep 8–12 focused skills.\n"
# )

# def analyze_chat_with_gemini(resume_text: str, user_msg: str) -> str:
#     api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
#     if not api_key:
#         return DEFAULT_REPLY

#     try:
#         genai.configure(api_key=api_key)
#         model_id = "gemini-flash-latest"  # or "gemini-2.5-flash"
#         model = genai.GenerativeModel(model_id)
#         prompt = f"""
# You are a friendly, concise resume coach.

# Rules:
# - Answer conversationally.
# - Give short bullets with what to ADD / REMOVE / REWRITE.
# - No JSON; plain text / markdown only.

# User question:
# {user_msg}

# Resume snippet:
# \"\"\"{(resume_text or '')[:3500]}\"\"\"
# """
#         resp = model.generate_content(prompt)
#         return (resp.text or "").strip() or DEFAULT_REPLY
#     except Exception as e:
#         # optional: log e
#         return DEFAULT_REPLY
# ai_assist/services_gemini.py
from django.conf import settings
import google.generativeai as genai

DEFAULT_REPLY = (
    "**(AI temporarily unavailable; here’s quick advice)**\n"
    "- Add 2–3 achievements with measurable results (e.g., “reduced load time by 30%”).\n"
    "- Include GitHub/Portfolio/LinkedIn links so clients can verify your work.\n"
    "- Keep 8–12 focused, role-relevant skills.\n"
    "- Use action + result bullets (Built X → Result Y%).\n"
)

def analyze_chat_with_gemini(resume_text: str, user_msg: str) -> str:
    """
    Returns a conversational, human-readable answer (Markdown OK).
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return DEFAULT_REPLY

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "temperature": 0.5,
                "max_output_tokens": 600,
            },
        )

        prompt = f"""
You are a friendly, concise resume coach for freelancers.

Rules:
- Answer conversationally.
- Give short, actionable bullets (what to ADD / REMOVE / REWRITE).
- No JSON; respond in plain text/markdown.
- If the user asks a general question (“what should I add?”), proactively suggest improvements.

User question:
{user_msg}

Resume snippet (analyze only what's here):
\"\"\"{(resume_text or '')[:3500]}\"\"\"
"""

        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        return text or DEFAULT_REPLY

    except Exception:
        # Any error → graceful fallback
        return DEFAULT_REPLY
