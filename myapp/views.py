from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Freelancer, FreelancerProfile
from .forms import FreelancerProfileForm
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.db import transaction
from .models import FreelancerProfile,Recruiter, RecruiterProfile,Job,Application
from .forms import (
    ProfileBasicsForm, ProfileContactForm,JobForm, JobSkillFormSet,
    RoleFormSet, SkillFormSet, LanguageFormSet,
    AchievementFormSet, PublicationFormSet, ProjectFormSet,RecruiterProfileForm,ApplicationForm
)

from django.db.models import Prefetch

from django.utils.http import urlencode
from django.db.models import Q


from django.shortcuts import render
from django.http import JsonResponse

def whoami(request):
    return JsonResponse({
        "session_key": request.session.session_key,
        "role": request.session.get("role"),
        "freelancer_id": request.session.get("freelancer_id"),
        "recruiter_id": request.session.get("recruiter_id"),
    })


def login_page(request):
    # role comes from ?role=recruiter or ?role=freelancer, default = freelancer
    role = (request.GET.get("role") or "freelancer").lower()
    if role not in ("freelancer", "recruiter"):
        role = "freelancer"
    return render(request, "login.html", {"role": role})

# ---- helper: require logged-in freelancer ----
def _require_freelancer(request):
    """Return (freelancer, profile) or redirect to login."""
    if request.session.get("role") != "freelancer" or not request.session.get("freelancer_id"):
        messages.warning(request, "Please login as a freelancer.")
        return None, None
    f = get_object_or_404(Freelancer, id=request.session["freelancer_id"])
    profile, _ = FreelancerProfile.objects.get_or_create(freelancer=f)
    return f, profile

# ========== AUTH (very simple session-based example) ==========
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Minimal example:
    - Accepts email + password fields from your login form.
    - On success sets session keys and redirects to freelancer dashboard.
    Replace with your real password check / hashing as needed.
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        # TODO: replace this with your real authentication
        try:
            freelancer = Freelancer.objects.get(email=email)
        except Freelancer.DoesNotExist:
            freelancer = None

        if freelancer and freelancer.password == password:  # <-- replace with proper hash check
            request.session["role"] = "freelancer"
            request.session["freelancer_id"] = freelancer.id
            messages.success(request, f"Welcome, {freelancer.name}!")
            return redirect("freelancer_dashboard")
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    return redirect("login")

# ========== PAGES ==========
def freelancer_dashboard(request):
    """Show ONLY the logged-in freelancer’s info, with Edit button."""
    freelancer, profile = _require_freelancer(request)
    if not freelancer:
        return redirect("login")
    return render(request, "freelancer_dashboard.html", {
        "freelancer": freelancer,
        "profile": profile,
    })

@require_http_methods(["GET", "POST"])
def freelancer_profile_edit(request):
    """Simple edit page for the logged-in freelancer’s profile."""
    freelancer, profile = _require_freelancer(request)
    if not freelancer:
        return redirect("login")

    if request.method == "POST":
        form = FreelancerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("freelancer_dashboard")
    else:
        form = FreelancerProfileForm(instance=profile)

    return render(request, "freelancer_profile_edit.html", {
        "freelancer": freelancer,
        "form": form,
    })
def freelancer_login_page(request):           # GET /login/
    return render(request, "login.html")

@require_http_methods(["POST"])               # POST /login/submit/
def freelancer_login(request):
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""

    try:
        freelancer = Freelancer.objects.get(email__iexact=email)
    except Freelancer.DoesNotExist:
        messages.error(request, "Invalid email or password.")
        return redirect("freelancer_login")

    # replace with your own check if you don’t hash passwords
    if hasattr(freelancer, "password") and not check_password(password, freelancer.password):
        messages.error(request, "Invalid email or password.")
        return redirect("freelancer_login")

    request.session["freelancer_id"] = freelancer.id   # <-- critical
    return redirect("freelancer_dashboard")

def logout_view(request):
    request.session.flush()   # clears all session data
    return redirect("login")  # or wherever you want to send them
def freelancer_dashboard(request):
    # assume you store the freelancer_id in session after login
    freelancer_id = request.session.get("freelancer_id")
    if not freelancer_id:
        return redirect("login")

    profile = get_object_or_404(FreelancerProfile, freelancer_id=freelancer_id)

    context = {
        "freelancer": profile.freelancer,
        "profile": profile,
        "roles": profile.freelancerrole_set.select_related("role").all(),
        "skills": profile.freelancerskill_set.select_related("skill").all(),
        "langs": profile.freelancerlanguage_set.select_related("language").all(),
        "projects": profile.freelancerproject_set.all(),
        "achievements": profile.achievement_set.all(),
        "publications": profile.publication_set.all(),
    }
    return render(request, "freelancer_dashboard.html", context)





# this for the edit the form



def _get_profile(request):
    fid = request.session.get("freelancer_id")
    if not fid:
        return None
    return get_object_or_404(FreelancerProfile, freelancer_id=fid)

# myapp/views.py
def freelancer_profile_edit(request):
    profile = _get_profile(request)
    if not profile:
        return redirect("freelancer_login")

    if request.method == "POST":
        form = FreelancerProfileForm(request.POST, request.FILES, instance=profile)

        role_fs = RoleFormSet(request.POST, instance=profile, prefix="roles")
        skill_fs = SkillFormSet(request.POST, instance=profile, prefix="skills")
        lang_fs = LanguageFormSet(request.POST, instance=profile, prefix="langs")
        proj_fs = ProjectFormSet(request.POST, instance=profile, prefix="projects")
        ach_fs  = AchievementFormSet(request.POST, instance=profile, prefix="achs")
        pub_fs  = PublicationFormSet(request.POST, instance=profile, prefix="pubs")

        all_valid = (form.is_valid() and role_fs.is_valid() and skill_fs.is_valid() and
                     lang_fs.is_valid() and proj_fs.is_valid() and ach_fs.is_valid() and pub_fs.is_valid())

        if all_valid:
            with transaction.atomic():
                form.save()
                role_fs.save(); skill_fs.save(); lang_fs.save()
                proj_fs.save(); ach_fs.save(); pub_fs.save()
            messages.success(request, "Profile updated.")
            return redirect("freelancer_dashboard")
        else:
            messages.error(request, "Please fix the errors highlighted below and try again.")
    else:
        form = FreelancerProfileForm(instance=profile)
        role_fs = RoleFormSet(instance=profile, prefix="roles")
        skill_fs = SkillFormSet(instance=profile, prefix="skills")
        lang_fs = LanguageFormSet(instance=profile, prefix="langs")
        proj_fs = ProjectFormSet(instance=profile, prefix="projects")
        ach_fs  = AchievementFormSet(instance=profile, prefix="achs")
        pub_fs  = PublicationFormSet(instance=profile, prefix="pubs")

    return render(request, "freelancer_profile_edit.html", {
        "profile": profile,
        "form": form,
        "role_fs": role_fs, "skill_fs": skill_fs, "lang_fs": lang_fs,
        "proj_fs": proj_fs, "ach_fs": ach_fs, "pub_fs": pub_fs,
    })





#recuiter
def _require_recruiter(request):
    """
    Return (recruiter, profile) or redirect to login with a message.
    Assumes you set request.session['role'] = 'recruiter' and request.session['recruiter_id'] on login.
    """
    if request.session.get("role") != "recruiter" or not request.session.get("recruiter_id"):
        messages.warning(request, "Please login as a recruiter.")
        return None, None
    r = get_object_or_404(Recruiter, id=request.session["recruiter_id"])
    profile, _ = RecruiterProfile.objects.get_or_create(recruiter=r)
    return r, profile

@require_http_methods(["GET"])
def recruiter_profile_detail(request):
    r, profile = _require_recruiter(request)
    if not r:
        return redirect("login")
    return render(request, "recruiter_profile.html", {"recruiter": r, "profile": profile})

@require_http_methods(["GET", "POST"])
def recruiter_profile_edit(request):
    r, profile = _require_recruiter(request)
    if not r:
        return redirect("login")

    if request.method == "POST":
        form = RecruiterProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("recruiter_profile_detail")
    else:
        form = RecruiterProfileForm(instance=profile)

    return render(request, "recruiter_profile_edit.html", {"form": form, "recruiter": r})





#job
# def recruiter_required(view_fn):
#     def _wrapped(request, *args, **kwargs):
#         if request.session.get("role") != "recruiter" or not request.session.get("recruiter_id"):
#             return redirect("login_page")   # instead of "login"
#         return view_fn(request, *args, **kwargs)
#     return _wrapped

# @recruiter_required
# def job_create_view(request):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     if rp is None:
#         messages.error(request, "Please create your Recruiter Profile first.")
#         return redirect("create_profile")

#     if request.method == "POST":
#         form = JobForm(request.POST)
#         formset = JobSkillFormSet(request.POST)
#         if form.is_valid() and formset.is_valid():
#             job = form.save(commit=False)
#             job.recruiter = rp
#             job.save()

#             # attach formset to the saved job and save skills
#             formset.instance = job
#             # OPTIONAL validation: require at least one MUST_HAVE
#             musts = 0
#             for f in formset.forms:
#                 if f.cleaned_data.get("DELETE"):
#                     continue
#                 if f.cleaned_data.get("importance") == "MUST_HAVE":
#                     musts += 1
#             if musts == 0 and formset.total_form_count() > 0:
#                 # simple inline validation message
#                 messages.error(request, "Please add at least one Must-have skill.")
#                 # re-render with bound data
#                 return render(request, "jobs/job_form.html", {"form": form, "formset": formset})

#             formset.save()
#             messages.success(request, "Job posted successfully.")
#             return redirect("my_jobs")
#     else:
#         form = JobForm()
#         formset = JobSkillFormSet()

#     return render(request, "jobs/job_form.html", {"form": form, "formset": formset})


# @recruiter_required
# def my_jobs_view(request):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     jobs = Job.objects.filter(recruiter=rp).order_by("-posted_at")
#     return render(request, "jobs/my_jobs.html", {"jobs": jobs})

# # views.py
# from django.db.models import Q
# from django.shortcuts import render, redirect

# def jobs_list_view(request):
#     # If a recruiter visits the public list, send to "My Jobs"
#     if request.session.get("role") == "recruiter":
#         return redirect("my_jobs")

#     qs = (Job.objects
#             .filter(is_active=True)
#             .select_related("recruiter", "recruiter__recruiter")
#             .order_by("-posted_at"))

#     q = (request.GET.get("q") or "").strip()
#     if q:
#         qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

#     return render(request, "jobs/jobs_list.html", {"jobs": qs, "q": q})



# def job_detail_view(request, job_id):
#     job = Job.objects.get(id=job_id, is_active=True)
#     return render(request, "jobs/job_detail.html", {"job": job})

# @recruiter_required
# def job_toggle_active_view(request, job_id):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     job = Job.objects.get(id=job_id, recruiter=rp)  # ensures ownership
#     job.is_active = not job.is_active
#     job.save(update_fields=["is_active"])
#     return redirect("my_jobs")



# def recruiter_required(view_fn):
#     def _wrapped(request, *args, **kwargs):
#         if request.session.get("role") != "recruiter" or not request.session.get("recruiter_id"):
#             return redirect("login")
#         return view_fn(request, *args, **kwargs)
#     return _wrapped

# @recruiter_required
# def job_edit_view(request, job_id):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     if rp is None:
#         messages.error(request, "Please create your Recruiter Profile first.")
#         return redirect("create_profile")

#     job = get_object_or_404(Job, id=job_id, recruiter=rp)

#     if request.method == "POST":
#         form = JobForm(request.POST, instance=job)
#         formset = JobSkillFormSet(request.POST, instance=job)  # ← includes current skills
#         if form.is_valid() and formset.is_valid():
#             obj = form.save(commit=False)
#             obj.recruiter = rp
#             obj.save()

#             # optional: require ≥1 MUST_HAVE
#             musts = sum(
#                 1 for f in formset.forms
#                 if not f.cleaned_data.get("DELETE") and f.cleaned_data.get("importance") == "MUST_HAVE"
#             )
#             if musts == 0 and formset.total_form_count() > 0:
#                 messages.error(request, "Please add at least one Must-have skill.")
#                 return render(request, "jobs/job_form.html", {"form": form, "formset": formset, "mode": "edit"})

#             formset.save()
#             messages.success(request, "Job updated.")
#             return redirect("my_jobs")
#     else:
#         form = JobForm(instance=job)
#         formset = JobSkillFormSet(instance=job)  # ← pre-fills existing skills

#     return render(request, "jobs/job_form.html", {"form": form, "formset": formset, "mode": "edit"})


# # ---------- LIST (public / freelancer) ----------
# def jobs_list_view(request):
#     qs = Job.objects.filter(is_active=True).select_related("recruiter", "recruiter__recruiter").order_by("-posted_at")

#     # simple filters (optional)
#     q = request.GET.get("q", "").strip()
#     if q:
#         qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)

#     return render(request, "jobs/jobs_list.html", {"jobs": qs})

# # ---------- DETAIL (public / freelancer) ----------
# def job_detail_view(request, job_id):
#     job = get_object_or_404(Job.objects.select_related("recruiter", "recruiter__recruiter"), id=job_id)
#     applied = False
#     if request.session.get("role") == "freelancer" and request.session.get("freelancer_id"):
#         try:
#             fp = FreelancerProfile.objects.get(freelancer_id=request.session["freelancer_id"])
#             applied = Application.objects.filter(job=job, freelancer=fp).exists()
#         except FreelancerProfile.DoesNotExist:
#             applied = False

#     return render(request, "jobs/job_detail.html", {"job": job, "applied": applied})

# # ---------- APPLY (freelancer only) ----------
# def freelancer_required(view_fn):
#     def _wrapped(request, *args, **kwargs):
#         if request.session.get("role") != "freelancer" or not request.session.get("freelancer_id"):
#             messages.error(request, "Please login as a freelancer to apply.")
#             return redirect("login")
#         return view_fn(request, *args, **kwargs)
#     return _wrapped

# @freelancer_required
# def job_apply_view(request, job_id):
#     job = get_object_or_404(Job, id=job_id, is_active=True)

#     # require freelancer profile
#     fid = request.session["freelancer_id"]
#     freelancer = get_object_or_404(Freelancer, id=fid)
#     try:
#         fp = freelancer.profile
#     except FreelancerProfile.DoesNotExist:
#         messages.error(request, "Please complete your Freelancer Profile before applying.")
#         return redirect(f"{reverse('freelancer_profile_create')}?{urlencode({'step': '1'})}")

#     # block duplicate applications
#     if Application.objects.filter(job=job, freelancer=fp).exists():
#         messages.info(request, "You already applied to this job.")
#         return redirect("job_detail", job_id=job.id)

#     if request.method == "POST":
#         form = ApplicationForm(request.POST, request.FILES)
#         if form.is_valid():
#             app = form.save(commit=False)
#             app.job = job
#             app.freelancer = fp
#             app.save()

#             # email recruiter
#             _email_recruiter_new_application(app, request)
#             messages.success(request, "Application submitted!")
#             return redirect("job_detail", job_id=job.id)
#     else:
#         form = ApplicationForm()

#     return render(request, "jobs/job_apply.html", {"job": job, "form": form})


# @recruiter_required
# def my_jobs_view(request):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     jobs = Job.objects.filter(recruiter=rp).order_by("-posted_at")
#     return render(request, "jobs/my_jobs.html", {"jobs": jobs})

# views.py


# --- decorators --------------------------------------------------------------

def recruiter_required(view_fn):
    def _wrapped(request, *args, **kwargs):
        if request.session.get("role") != "recruiter" or not request.session.get("recruiter_id"):
            messages.error(request, "Please login as a recruiter.")
            return redirect("login_page")
        return view_fn(request, *args, **kwargs)
    return _wrapped

def freelancer_required(view_fn):
    def _wrapped(request, *args, **kwargs):
        if request.session.get("role") != "freelancer" or not request.session.get("freelancer_id"):
            messages.error(request, "Please login as a freelancer to apply.")
            return redirect("login_page")
        return view_fn(request, *args, **kwargs)
    return _wrapped

# --- recruiter: create / list mine / toggle / edit --------------------------

@recruiter_required
def job_create_view(request):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    if rp is None:
        messages.error(request, "Please create your Recruiter Profile first.")
        return redirect("recruiter_profile_edit")   # <-- make sure this name exists

    if request.method == "POST":
        form = JobForm(request.POST)
        formset = JobSkillFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            job = form.save(commit=False)
            job.recruiter = rp
            job.save()

            formset.instance = job

            # optional: require at least one MUST_HAVE
            musts = sum(
                1 for f in formset.forms
                if not f.cleaned_data.get("DELETE") and f.cleaned_data.get("importance") == "MUST_HAVE"
            )
            if musts == 0 and formset.total_form_count() > 0:
                messages.error(request, "Please add at least one Must-have skill.")
                return render(request, "jobs/job_form.html", {"form": form, "formset": formset})

            formset.save()
            messages.success(request, "Job posted successfully.")
            return redirect("my_jobs")
    else:
        form = JobForm()
        formset = JobSkillFormSet()

    return render(request, "jobs/job_form.html", {"form": form, "formset": formset})


# @recruiter_required
# def my_jobs_view(request):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     jobs = Job.objects.filter(recruiter=rp).order_by("-posted_at")
#     return render(request, "jobs/my_jobs.html", {"jobs": jobs})
# myapp/views.py
@recruiter_required
def my_jobs_view(request):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)

    # make it a list so we can add attributes on each object
    jobs = list(Job.objects.filter(recruiter=rp).order_by("-posted_at"))

    # attach a safe applicants count regardless of related_name
    for j in jobs:
        try:
            j.apps_count = j.applications.count()       # if you set related_name="applications"
        except AttributeError:
            j.apps_count = j.application_set.count()    # Django’s default reverse name

    return render(request, "jobs/my_jobs.html", {"jobs": jobs})


@recruiter_required
def job_toggle_active_view(request, job_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    job = get_object_or_404(Job, id=job_id, recruiter=rp)
    job.is_active = not job.is_active
    job.save(update_fields=["is_active"])
    return redirect("my_jobs")



@recruiter_required
def job_edit_view(request, job_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    if rp is None:
        messages.error(request, "Please create your Recruiter Profile first.")
        return redirect("recruiter_profile_edit")

    job = get_object_or_404(Job, id=job_id, recruiter=rp)

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        formset = JobSkillFormSet(request.POST, instance=job)
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.recruiter = rp
            obj.save()

            musts = sum(
                1 for f in formset.forms
                if not f.cleaned_data.get("DELETE") and f.cleaned_data.get("importance") == "MUST_HAVE"
            )
            if musts == 0 and formset.total_form_count() > 0:
                messages.error(request, "Please add at least one Must-have skill.")
                return render(request, "jobs/job_form.html", {"form": form, "formset": formset, "mode": "edit"})

            formset.save()
            messages.success(request, "Job updated.")
            return redirect("my_jobs")
    else:
        form = JobForm(instance=job)
        formset = JobSkillFormSet(instance=job)

    return render(request, "jobs/job_form.html", {"form": form, "formset": formset, "mode": "edit"})

# --- public / freelancer: list all & detail ---------------------------------

def jobs_list_view(request):
    # keep recruiters in their area
    if request.session.get("role") == "recruiter":
        return redirect("my_jobs")

    qs = (Job.objects
            .filter(is_active=True)
            .select_related("recruiter", "recruiter__recruiter")
            .order_by("-posted_at"))

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    return render(request, "jobs/jobs_list.html", {"jobs": qs, "q": q})




# ---- PUBLIC / FREELANCER: LIST ALL JOBS ----
def jobs_list_view(request):
    # Keep recruiters in their own area
    if request.session.get("role") == "recruiter":
        return redirect("my_jobs")

    qs = (Job.objects
            .filter(is_active=True)  # show ALL active jobs
            .select_related("recruiter", "recruiter__recruiter")
            .order_by("-posted_at"))

    q = (request.GET.get("q") or "").strip()
    if q:
        # IMPORTANT: use Q(...) instead of union (|) of QuerySets
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    return render(request, "jobs/jobs_list.html", {"jobs": qs, "q": q})


# ---- PUBLIC / FREELANCER: JOB DETAIL WITH CLEAR FLAGS ----
def job_detail_view(request, job_id):
    job = get_object_or_404(
        Job.objects.select_related("recruiter", "recruiter__recruiter"),
        id=job_id
    )

    # compute flags for the template
    is_freelancer = (request.session.get("role") == "freelancer" and
                     bool(request.session.get("freelancer_id")))
    applied = False
    can_apply = False
    why_cant_apply = None  # "closed" | "applied" | "no_profile" | "not_logged_in"

    if not job.is_active:
        why_cant_apply = "closed"
    elif is_freelancer:
        fid = request.session["freelancer_id"]
        try:
            fp = FreelancerProfile.objects.get(freelancer_id=fid)
        except FreelancerProfile.DoesNotExist:
            why_cant_apply = "no_profile"
        else:
            applied = Application.objects.filter(job=job, freelancer=fp).exists()
            if applied:
                why_cant_apply = "applied"
            else:
                can_apply = True
    else:
        why_cant_apply = "not_logged_in"

    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "applied": applied,
            "can_apply": can_apply,
            "is_freelancer": bool(is_freelancer),
            "why_cant_apply": why_cant_apply,
        },
    )

# --- apply (freelancer only) -------------------------------------------------

def freelancer_required(view_fn):
    def _wrapped(request, *args, **kwargs):
        if request.session.get("role") != "freelancer" or not request.session.get("freelancer_id"):
            messages.error(request, "Please login as a freelancer to apply.")
            return redirect("login_page")
        return view_fn(request, *args, **kwargs)
    return _wrapped

@freelancer_required
def job_apply_view(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)

    fid = request.session["freelancer_id"]
    freelancer = get_object_or_404(Freelancer, id=fid)
    try:
        fp = freelancer.profile
    except FreelancerProfile.DoesNotExist:
        messages.error(request, "Please complete your Freelancer Profile before applying.")
        return redirect(f"{reverse('freelancer_profile_create')}?{urlencode({'step': '1'})}")

    # Block duplicates at UI layer (DB also blocks via unique_together)
    if Application.objects.filter(job=job, freelancer=fp).exists():
        messages.info(request, "You already applied to this job.")
        return redirect("job_detail", job_id=job.id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            app.freelancer = fp
            app.save()
            messages.success(request, "Application submitted!")
            return redirect("job_detail", job_id=job.id)
    else:
        form = ApplicationForm()

    return render(request, "jobs/job_apply.html", {"job": job, "form": form})






#for recuiter
# ---------- APPLICANTS LIST (for one job) ----------
@recruiter_required
def job_applications_view(request, job_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)

    # only allow if the job belongs to this recruiter profile
    job = get_object_or_404(
        Job.objects.select_related("recruiter", "recruiter__recruiter"),
        id=job_id, recruiter=rp
    )

    apps = (
        Application.objects
        .filter(job=job)
        .select_related("freelancer", "freelancer__freelancer")   # profile + base user
        .order_by("-created_at")
    )

    return render(request, "jobs/job_applications.html", {
        "job": job,
        "apps": apps,
    })


# ---------- ONE APPLICATION DETAIL ----------
@recruiter_required
def job_application_detail_view(request, app_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)

    app = get_object_or_404(
        Application.objects.select_related(
            "job", "job__recruiter", "freelancer", "freelancer__freelancer"
        ),
        id=app_id, job__recruiter=rp,   # ensures ownership
    )

    return render(request, "jobs/job_application_detail.html", {
        "app": app,
    })


# ---------- (Optional) SIMPLE PUBLIC VIEW OF A FREELANCER PROFILE ----------
@recruiter_required
def recruiter_view_freelancer_profile(request, profile_id):
    fp = get_object_or_404(
        FreelancerProfile.objects.select_related("freelancer"),
        id=profile_id
    )
    return render(request, "jobs/recruiter_view_freelancer_profile.html", {"fp": fp})

