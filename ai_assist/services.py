# ai_assist/services.py
from datetime import datetime
from django.conf import settings

# Optional OpenAI import
try:
    from openai import OpenAI
    _openai_available = True
except Exception:
    _openai_available = False


# -------------------------
# Helpers
# -------------------------
def _fmt_date(d):
    if not d:
        return None
    try:
        return datetime.fromisoformat(str(d)).strftime("%b %Y")
    except Exception:
        return str(d)


# -------------------------
# Core Markdown builder (string)
# -------------------------
def _build_resume_md_core(data: dict) -> str:
    """
    Build clean, ATS-friendly Markdown from profile JSON.
    Expected keys:
      name, headline, email, links{github,linkedin,portfolio}, bio,
      skills[], roles[], projects[], achievements[]
    Each project may have: title, role_title/role, start_date, end_date,
      description, demo_url, github_url
    """
    name     = data.get("name") or ""
    headline = data.get("headline") or ""
    email    = data.get("email") or ""
    links    = data.get("links") or {}
    github   = links.get("github") or ""
    linkedin = links.get("linkedin") or ""
    portfolio= links.get("portfolio") or ""
    bio      = (data.get("bio") or "").strip()

    skills   = [s for s in (data.get("skills") or []) if s]
    roles    = [r for r in (data.get("roles") or []) if r]
    projects = data.get("projects") or []
    achievements = data.get("achievements") or []

    lines = []

    # Header
    lines.append(f"# {name or 'Your Name'}")
    if headline:
        lines.append(f"_{headline}_")
    contact_bits = [x for x in [email, linkedin, github, portfolio] if x]
    if contact_bits:
        lines.append("")
        lines.append(" | ".join(contact_bits))

    # Summary
    if bio:
        lines.append("")
        lines.append("## Summary")
        lines.append(bio)

    # Skills
    if skills:
        lines.append("")
        lines.append("## Skills")
        lines.append(", ".join(skills))

    # Roles (optional)
    if roles:
        lines.append("")
        lines.append("## Roles")
        lines.append(", ".join(roles))

    # Projects
    if projects:
        lines.append("")
        lines.append("## Projects")
        for p in projects:
            title = p.get("title") or "Untitled"
            role  = p.get("role_title") or p.get("role") or ""
            s     = _fmt_date(p.get("start_date"))
            e     = _fmt_date(p.get("end_date")) or "Present"
            when  = f" ({s} – {e})" if s else ""
            lines.append(f"- **{title}**{when}" + (f" — _{role}_" if role else ""))
            desc  = (p.get("description") or "").strip()
            if desc:
                for bullet in [x.strip("•- ").strip() for x in desc.split("\n") if x.strip()]:
                    lines.append(f"  - {bullet}")
            # links
            demo = p.get("demo_url") or p.get("live_demo") or p.get("link")
            repo = p.get("github_url") or p.get("repo_url") or p.get("repository") or p.get("repo")
            link_bits = [("Live", demo), ("Repo", repo)]
            link_bits = [f"[{k}]({v})" for k, v in link_bits if v]
            if link_bits:
                lines.append("  - " + " • ".join(link_bits))

    # Achievements
    if achievements:
        lines.append("")
        lines.append("## Achievements")
        for a in achievements:
            t = a.get("title") or a.get("name") or "Achievement"
            d = (a.get("description") or a.get("details") or "").strip()
            y = a.get("date") or a.get("year")
            if y:
                t = f"{t} ({y})"
            lines.append(f"- **{t}**" + (f": {d}" if d else ""))

    return "\n".join(lines).strip() or "# Resume\n(placeholder)"


# Backwards-compatible alias for your earlier naming
def _build_resume_md_offline(d: dict) -> str:
    return _build_resume_md_core(d)


# -------------------------
# Offline analyzer (no AI)
# -------------------------
def analyze_profile_json(profile_json: dict) -> dict:
    """
    Offline, safe suggestions. You can later merge AI results into this.
    """
    tips = {
        "summary": "Baseline suggestions generated offline.",
        "quick_wins": [
            "Add measurable results to your top 1–2 projects.",
            "Include GitHub/portfolio links.",
            "List 6–10 relevant skills; keep generic ones lower.",
        ],
        "missing_sections": [],
        "project_improvements": [],
        "portfolio_advice": "Add a link to your portfolio or GitHub if you apply to technical roles.",
        "sample_achievement_bullets": [
            "Improved X by Y% by doing Z.",
            "Delivered FEATURE within TIMELINE resulting in OUTCOME.",
        ],
    }
    return {"ok": True, "suggestions": tips}


# -------------------------
# Public API: AI-aware wrapper
# -------------------------
def generate_resume_md(profile_json: dict) -> dict:
    """
    Public function your views should call.
    Tries AI (optional), else falls back to the core builder.
    Returns: {"ok": bool, "markdown": str, "source": "ai"|"fallback"|"fallback_on_error"}
    """
    offline_md = _build_resume_md_core(profile_json)

    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not (api_key and _openai_available):
        return {"ok": True, "markdown": offline_md, "source": "fallback"}

    try:
        # If you choose to use AI later, call it here and **build markdown from its response**.
        # For now we keep it offline to avoid quota/latency while wiring everything else.
        client = OpenAI(api_key=api_key)
        # Example (disabled):
        # resp = client.chat.completions.create(...)
        # md = postprocess(resp) or offline_md
        return {"ok": True, "markdown": offline_md, "source": "ai_or_fallback"}
    except Exception:
        return {"ok": True, "markdown": offline_md, "source": "fallback_on_error"}
