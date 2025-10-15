from django.shortcuts import render

# Create your views here.
# ai_assist/views.py
import os
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib import messages

from .forms import ProfileForm, ProjectFormSet, AchievementFormSet, PublicationFormSet
from myapp.models import Freelancer, FreelancerProfile
from .services import analyze_profile_json, generate_resume_md
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from .forms import ResumeForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from .forms import ResumeUploadForm
from .models import ResumeAnalysis
from .services_resume import extract_text_from_file, analyze_resume_text
from .services import analyze_profile_json 
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

import google.generativeai as genai


# from .utils_resume_text import extract_resume_text
 # optional to mix in AI-style tips
# If you already have a utils.profile_to_json you can use it instead of _serialize_profile.
# from .utils import profile_to_json


# ---------- helpers ----------

def _profile_from_session(request):
    fid = request.session.get("freelancer_id")
    if not fid:
        return None
    try:
        f = Freelancer.objects.get(id=fid)
    except Freelancer.DoesNotExist:
        return None
    return getattr(f, "profile", None) or FreelancerProfile.objects.create(freelancer=f)


def _first_attr(obj, *names, default=None):
    """Return the first non-empty attribute from names."""
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v not in (None, ""):
                return v
    return default

def _bullets_from(p):
    """
    Return an array of bullet strings for a project `p`.
    Looks for common attributes; if none exist, derives bullets from description lines.
    """
    candidates = ("bullets_list", "bullets", "bullet_points", "points")
    for attr in candidates:
        if hasattr(p, attr):
            v = getattr(p, attr)
            # list/tuple -> clean strings
            if isinstance(v, (list, tuple)):
                return [str(x).strip() for x in v if str(x).strip()]
            # string with newlines or prefixed bullets
            if isinstance(v, str):
                return [
                    ln.strip().lstrip("•*- ").rstrip()
                    for ln in v.splitlines()
                    if ln.strip()
                ]

    # Fallback: derive from description/details/summary
    desc = _first_attr(p, "description", "details", "summary", "about", default="")
    if desc:
        items = []
        for ln in desc.splitlines():
            t = ln.strip().lstrip("•*- ").rstrip()
            if t:
                items.append(t)
            if len(items) >= 5:  # cap to keep resume compact
                break
        return items

    return []



def _serialize_profile(fp: FreelancerProfile) -> dict:
    def iso(d):
        return d.isoformat() if d else None

    skills = [fs.skill.name for fs in fp.freelancerskill_set.select_related("skill").all()]

    roles = []
    for fr in fp.freelancerrole_set.select_related("role").all():
        roles.append(getattr(fr.role, "name", str(fr.role)))

    projects = []
    for p in fp.freelancerproject_set.all():
        role_title = _first_attr(p, "role_title") or (
            getattr(getattr(p, "role", None), "name", None) or _first_attr(p, "role") or ""
        )
        projects.append({
            "title":       _first_attr(p, "title", "name", default=""),
            "role_title":  role_title,
            "description": _first_attr(p, "description", "details", "summary", "about", default=""),
            "bullets":     _bullets_from(p),                      # ← safe bullets
            "start_date":  iso(getattr(p, "start_date", None)),
            "end_date":    iso(getattr(p, "end_date", None)),
            "github_url":  _first_attr(p, "github_url", "repo_url", "repository", "repo"),
            "demo_url":    _first_attr(p, "demo_url", "live_demo", "demo", "link"),
        })

    achievements = []
    for a in fp.achievement_set.all():
        achievements.append({
            "title":       _first_attr(a, "title", "name", default=""),
            "description": _first_attr(a, "description", "details", default=""),
            "date":        _first_attr(a, "date", "year"),
        })

    links = {
        "portfolio": getattr(fp, "portfolio_link", None) or getattr(fp, "portfolio_url", None),
        "github":    getattr(fp, "github_url", None),
        # Only include LinkedIn if you actually have this field:
        "linkedin":  getattr(fp, "linkedin_url", None) if hasattr(fp, "linkedin_url") else None,
    }

    name  = _first_attr(fp, "full_name", default=None) or getattr(fp.freelancer, "name", "")
    email = _first_attr(fp, "contact_email", "email", default=None) or getattr(fp.freelancer, "email", "")

    return {
        "name":         name,
        "headline":     getattr(fp, "headline", ""),
        "summary":      getattr(fp, "summary", "") or getattr(fp, "bio", ""),
        "email":        email,
        "phone":        _first_attr(fp, "contact_phone", "phone"),
        "city":         _first_attr(fp, "location_city", "city"),
        "country":      _first_attr(fp, "location_country", "country"),
        "skills":       skills,
        "roles":        roles,
        "projects":     projects,
        "achievements": achievements,
        "links":        links,
    }


def _fallback_md(d: dict) -> str:
    """Minimal offline markdown if API call fails / quota exceeded."""
    name = d.get("name", "Your Name")
    headline = d.get("headline", "")
    email = d.get("email", "")
    links = d.get("links", {}) or {}
    skills = ", ".join(d.get("skills", []))
    roles = ", ".join(d.get("roles", []))

    parts = [
        f"# {name}",
        f"_{headline}_" if headline else "",
        "",
        f"{email}" + (f" | {links.get('github')}" if links.get("github") else ""),
        "",
    ]
    if skills:
        parts += ["## Skills", skills, ""]
    if roles:
        parts += ["## Roles", roles, ""]

    projs = d.get("projects", [])
    if projs:
        parts.append("## Projects")
        for p in projs:
            dates = []
            if p.get("start_date"): dates.append(p["start_date"])
            if p.get("end_date"):   dates.append(p["end_date"])
            date_s = f" ({' — '.join(dates)})" if dates else ""
            parts.append(f"- **{p.get('title','')}** — _{p.get('role_title','')}_{date_s}")
            if p.get("description"):
                parts.append(f"  - {p['description']}")
        parts.append("")

    ach = d.get("achievements", [])
    if ach:
        parts.append("## Achievements")
        for a in ach:
            line = f"- **{a.get('title','')}**"
            if a.get("date"):
                line += f" ({a['date']})"
            parts.append(line)
            if a.get("description"):
                parts.append(f"  - {a['description']}")
        parts.append("")

    return "\n".join([x for x in parts if x is not None])


# ---------- JSON (Ajax) endpoints ----------

@require_POST
@csrf_exempt  # remove after wiring CSRF in JS
def ai_analyze_json(request):
    fp = _profile_from_session(request)
    if not fp:
        return JsonResponse({"ok": False, "error": "Not logged in as freelancer."}, status=400)

    data = _serialize_profile(fp)  # or: profile_to_json(fp)
    tips = analyze_profile_json(data) or {}
    # normalize shape
    suggestions = tips.get("suggestions", tips)
    return JsonResponse({"ok": True, "suggestions": suggestions})


@require_POST
@csrf_exempt  # remove after wiring CSRF in JS
def ai_resume_json(request):
    fp = _profile_from_session(request)
    if not fp:
        return JsonResponse({"ok": False, "error": "Not logged in as freelancer."}, status=400)

    data = _serialize_profile(fp)  # or: profile_to_json(fp)

    # Ensure we always extract a string markdown
    try:
        res = generate_resume_md(data)
        md  = res.get("markdown") if isinstance(res, dict) else str(res)
        if not md:
            md = _fallback_md(data)
        ok = bool(md)
    except Exception:
        ok = False
        md = _fallback_md(data)

    # keep for "preview" / PDF page
    request.session["ai_last_markdown"] = md
    request.session.modified = True

    return JsonResponse({"ok": ok, "markdown": md})


# ---------- Human pages ----------

def ai_resume_page(request):
    fp = _profile_from_session(request)
    if not fp:
        return HttpResponseBadRequest("Not logged in as freelancer.")

    data = _serialize_profile(fp)
    tips = (analyze_profile_json(data) or {}).get("suggestions", {})
    try:
        res = generate_resume_md(data)
        md  = res.get("markdown") if isinstance(res, dict) else str(res)
        if not md:
            md = _fallback_md(data)
    except Exception:
        md = _fallback_md(data)

    return render(request, "ai/resume.html", {"resume_md": md, "tips": tips})





def ai_resume_download_md(request):
    fp = _profile_from_session(request)
    if not fp:
        return HttpResponse("Not logged in", status=400)

    data = _serialize_profile(fp)
    try:
        res = generate_resume_md(data)
        md  = res.get("markdown") if isinstance(res, dict) else str(res)
        if not md:
            md = _fallback_md(data)
    except Exception:
        md = _fallback_md(data)

    filename = f"resume_{slugify(data.get('name') or 'freelancer')}.md"
    resp = HttpResponse(md, content_type="text/markdown; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def ai_resume_print(request):
    fp = _profile_from_session(request)
    if not fp:
        return HttpResponse("Not logged in", status=400)
    d = _serialize_profile(fp)  # <-- the dict with name, roles, skills, projects, achievements, links, etc.
    return render(request, "ai/resume_print.html", {"d": d})






def resume_builder(request):
    fp = _profile_from_session(request)
    if not fp:
        return HttpResponseBadRequest("Not logged in as freelancer.")

    if request.method == "POST":
        pform = ProfileForm(request.POST, instance=fp)
        proj_fs = ProjectFormSet(request.POST, instance=fp, prefix="proj")
        ach_fs  = AchievementFormSet(request.POST, instance=fp, prefix="ach")
        pub_fs  = PublicationFormSet(request.POST, instance=fp, prefix="pub")

        if pform.is_valid() and proj_fs.is_valid() and ach_fs.is_valid() and pub_fs.is_valid():
            pform.save()
            proj_fs.save()
            ach_fs.save()
            pub_fs.save()
            messages.success(request, "Saved!")
            # jump to print preview (or back to form)
            return redirect("ai:ai_resume_print")
        messages.error(request, "Please fix the errors below.")
    else:
        pform = ProfileForm(instance=fp)
        proj_fs = ProjectFormSet(instance=fp, prefix="proj")
        ach_fs  = AchievementFormSet(instance=fp, prefix="ach")
        pub_fs  = PublicationFormSet(instance=fp, prefix="pub")

    return render(request, "ai/resume_builder.html", {
        "pform": pform,
        "proj_fs": proj_fs,
        "ach_fs": ach_fs,
        "pub_fs": pub_fs,
    })





# ai_assist/views.py


# You already have these utilities:
# _profile_from_session, _first_attr, _serialize_profile, _fallback_md
# (keep them as-is)

def _prefill_from_profile(fp):
    """Create initial data dict for the form using the freelancer’s profile."""
    name  = _first_attr(fp, "full_name", default=None) or getattr(fp.freelancer, "name", "")
    email = _first_attr(fp, "contact_email", "email", default=None) or getattr(fp.freelancer, "email", "")

    # join skills/roles
    skills = ", ".join([fs.skill.name for fs in fp.freelancerskill_set.select_related("skill").all()])
    roles  = ", ".join([getattr(fr.role, "name", str(fr.role)) for fr in fp.freelancerrole_set.select_related("role").all()])

    init = {
        "name": name,
        "headline": getattr(fp, "headline", "") or "",
        "summary": getattr(fp, "summary", "") or getattr(fp, "bio", "") or "",
        "email": email,
        "phone": _first_attr(fp, "contact_phone", "phone", default="") or "",
        "city":  _first_attr(fp, "location_city", "city", default="") or "",
        "country": _first_attr(fp, "location_country", "country", default="") or "",
        "skills": skills,
        "roles": roles,
    }

    # Pre-fill up to 2 projects
    projs = list(fp.freelancerproject_set.all()[:2])
    if len(projs) >= 1:
        p = projs[0]
        init.update({
            "p1_title": _first_attr(p, "title", "name", default=""),
            "p1_role":  _first_attr(p, "role_title", "role", default=""),
            "p1_desc":  _first_attr(p, "description", "details", "summary", "about", default=""),
            "p1_start": getattr(p, "start_date", None),
            "p1_end":   getattr(p, "end_date", None),
            "p1_demo":  _first_attr(p, "demo_url", "live_demo", "demo", "link", default=""),
            "p1_repo":  _first_attr(p, "github_url", "repo_url", "repository", "repo", default=""),
        })
    if len(projs) >= 2:
        p = projs[1]
        init.update({
            "p2_title": _first_attr(p, "title", "name", default=""),
            "p2_role":  _first_attr(p, "role_title", "role", default=""),
            "p2_desc":  _first_attr(p, "description", "details", "summary", "about", default=""),
            "p2_start": getattr(p, "start_date", None),
            "p2_end":   getattr(p, "end_date", None),
            "p2_demo":  _first_attr(p, "demo_url", "live_demo", "demo", "link", default=""),
            "p2_repo":  _first_attr(p, "github_url", "repo_url", "repository", "repo", default=""),
        })
    return init

def _form_to_resume_data(cleaned):
    """Turn cleaned form data into the dict your resume template expects."""
    skills = [s.strip() for s in (cleaned.get("skills") or "").split(",") if s.strip()]
    roles  = [s.strip() for s in (cleaned.get("roles") or "").split(",") if s.strip()]

    projects = []
    for idx in (1, 2):
        title = cleaned.get(f"p{idx}_title") or ""
        role  = cleaned.get(f"p{idx}_role") or ""
        desc  = cleaned.get(f"p{idx}_desc") or ""
        if any([title, role, desc]):
            projects.append({
                "title": title,
                "role_title": role,
                "description": desc,
                "bullets": [ln.strip().lstrip("•*- ") for ln in desc.splitlines() if ln.strip()],  # derive bullets
                "start_date": cleaned.get(f"p{idx}_start"),
                "end_date":   cleaned.get(f"p{idx}_end"),
                "demo_url":   cleaned.get(f"p{idx}_demo"),
                "repo_url":   cleaned.get(f"p{idx}_repo"),
            })

    return {
        "name": cleaned["name"],
        "headline": cleaned.get("headline") or "",
        "summary": cleaned.get("summary") or "",
        "email": cleaned["email"],
        "phone": cleaned.get("phone") or "",
        "city":  cleaned.get("city")  or "",
        "country": cleaned.get("country") or "",
        "skills": skills,
        "roles": roles,
        "projects": projects,
        "achievements": [],  # can add later via another form
        "links": {},
    }


from datetime import date, datetime

def _jsonable(obj):
    """Recursively convert dates/datetimes to ISO strings so sessions/JSON can serialize."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    return obj
@require_http_methods(["GET", "POST"])
def resume_form(request):
    fp = _profile_from_session(request)
    if not fp:
        return HttpResponseBadRequest("Not logged in as freelancer.")

    if request.method == "GET":
        initial = _prefill_from_profile(fp)
        initial = _jsonable(initial)              # ensure no date objects in initial
        form = ResumeForm(initial=initial)
        return render(request, "ai/resume_form.html", {"form": form})

    # POST
    form = ResumeForm(request.POST)
    if not form.is_valid():
        return render(request, "ai/resume_form.html", {"form": form})

    raw_data = _form_to_resume_data(form.cleaned_data)
    data = _jsonable(raw_data)                    # <-- make safe for session
    request.session["ai_resume_data"] = data
    request.session.modified = True
    return redirect("ai:ai_resume_preview")

# ai_assist/views.py

def ai_resume_preview(request):
    """Render a clean, ATS-friendly HTML resume and show 'Download PDF'."""
    data = request.session.get("ai_resume_data")
    if not data:
        fp = _profile_from_session(request)
        if not fp:
            return HttpResponseBadRequest("No resume data.")
        data = _serialize_profile(fp)

    # Links can be in a nested dict or directly present
    links = (data.get("links") or {})
    # linkedin = links.get("linkedin") or data.get("linkedin_url")
    github   = links.get("github")   or data.get("github_url")

    context = {
        "d": data,  # original dict for name, phone, email, projects, etc.
        # unified, safe keys for the template:
        "about":        data.get("summary") or data.get("bio") or "",
        "achievements": data.get("achievements") or [],
        "publications": data.get("publications") or [],
        # "linkedin":     linkedin,
        "github":       github,
    }
    return render(request, "ai/resume_doc.html", context)




# def ai_resume_download_md(request):
#     """Optional: direct .md download of the current data."""
#     data = request.session.get("ai_resume_data")
#     if not data:
#         fp = _profile_from_session(request)
#         if not fp:
#             return HttpResponse("Not logged in", status=400)
#         data = _serialize_profile(fp)

#     # basic markdown using your fallback to avoid API calls
#     md = _fallback_md(data)
#     filename = f"resume_{slugify(data.get('name') or 'freelancer')}.md"
#     resp = HttpResponse(md, content_type="text/markdown; charset=utf-8")
#     resp["Content-Disposition"] = f'attachment; filename="{filename}"'
#     return resp



def _require_profile(request):
    # adapt to your existing session method
    from myapp.models import Freelancer, FreelancerProfile  # adjust import
    fid = request.session.get("freelancer_id")
    if not fid: 
        return None
    f = Freelancer.objects.filter(id=fid).first()
    if not f:
        return None
    profile, _ = FreelancerProfile.objects.get_or_create(freelancer=f)
    return profile

@login_required
@require_http_methods(["GET", "POST"])
def resume_analysis_view(request):
    profile = _require_profile(request)
    if not profile:
        return redirect("login")

    ctx = {"form": ResumeUploadForm(), "analyses": profile.resume_analyses.all()[:5]}
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            ctx["form"] = form
            return render(request, "ai/resume_form.html", ctx)

        text, ext = extract_text_from_file(form.cleaned_data["file"])
        suggestions = analyze_resume_text(text)

        ra = ResumeAnalysis.objects.create(
            profile=profile,
            file=form.cleaned_data["file"],
            extracted_text=text[:20000],  # store a slice
            score=suggestions["profile_strength"],
            report=suggestions,
        )
        ctx.update({"latest": ra, "analyses": profile.resume_analyses.all()[:5]})
        return render(request, "ai/resume_analyzer.html", {})

@login_required
@require_http_methods(["POST"])
def resume_analysis_json(request):
    profile = _require_profile(request)
    if not profile:
        return HttpResponseBadRequest("Not logged in")

    form = ResumeUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    text, _ = extract_text_from_file(form.cleaned_data["file"])
    base = analyze_resume_text(text)

    # Optionally blend your offline AI tips
    tips = analyze_profile_json({})["suggestions"]  # pass real DTO if you want
    base["ai_suggestions_like"].extend(tips.get("quick_wins", []))

    return JsonResponse({"ok": True, "report": base})


@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def ai_analyze_uploaded_resume(request):
    file = request.FILES.get("resume")
    if not file:
        return JsonResponse({"ok": False, "error": "No file uploaded."}, status=400)

    # ---- save temp file
    tmp_dir = os.path.join(settings.BASE_DIR, "tmp_uploads")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"_tmp_{request.user.id}_{slugify(file.name)}")
    with open(tmp_path, "wb") as w:
        for chunk in file.chunks():
            w.write(chunk)

    # ---- extract text
    try:
        from .utils_resume_text import extract_resume_text
        resume_text = extract_resume_text(tmp_path)
        print("Extracted characters:", len(resume_text))
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    if not (resume_text or "").strip():
        return JsonResponse({
            "ok": False,
            "error": "Could not read text. Try a DOCX/TXT or a PDF with selectable text."
        }, status=400)

    # ---- Gemini
    genai.configure(api_key=(settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")))
    model = genai.GenerativeModel("gemini-flash-latest")

    prompt = f"""
You are a resume coach. Analyze the resume and give short, concrete advice.

Return plain markdown like:

**Profile Strength:** 70/100
✅ Completed sections
⚠️ Missing sections
💬 Suggestions:
- ...
- ...

Resume:
\"\"\"{resume_text[:5000]}\"\"\"
"""
    try:
        resp = model.generate_content(prompt)
        return JsonResponse({"ok": True, "feedback": (resp.text or "").strip()})
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"AI error: {e}"}, status=500)