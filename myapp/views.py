from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Freelancer, FreelancerProfile
from .forms import FreelancerProfileForm
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.db import transaction
from .models import FreelancerProfile,Recruiter, RecruiterProfile,Job,Application,ApplicationFlow
from .forms import (
    ProfileBasicsForm, ProfileContactForm,JobForm, JobSkillFormSet,
    RoleFormSet, SkillFormSet, LanguageFormSet,
    AchievementFormSet, PublicationFormSet, ProjectFormSet,RecruiterProfileForm,ApplicationForm
)
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from django.db.models import Prefetch
from django.utils.http import urlencode
from django.db.models import Q
from django.http import JsonResponse
from .models import (
    Freelancer, FreelancerProfile,
    FreelancerProject, Achievement, Publication,
    Application,Role, Skill,Notification,Job,
)
from django import forms

from datetime import timedelta
from django.db.models import Q, F
from django.db.models import Count as DjCount

from .models import Job
def whoami(request):
    return JsonResponse({
        "session_key": request.session.session_key,
        "role": request.session.get("role"),
        "freelancer_id": request.session.get("freelancer_id"),
        "recruiter_id": request.session.get("recruiter_id"),
    })


def login_page(request):
    role = (request.GET.get("role") or "freelancer").lower()
    if role not in ("freelancer", "recruiter"):
        role = "freelancer"
    return render(request, "login.html", {"role": role})

def _require_freelancer(request):
    """Return (freelancer, profile) or redirect to login."""
    if request.session.get("role") != "freelancer" or not request.session.get("freelancer_id"):
        messages.warning(request, "Please login as a freelancer.")
        return None, None
    f = get_object_or_404(Freelancer, id=request.session["freelancer_id"])
    profile, _ = FreelancerProfile.objects.get_or_create(freelancer=f)
    return f, profile

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        try:
            freelancer = Freelancer.objects.get(email=email)
        except Freelancer.DoesNotExist:
            freelancer = None

        if freelancer and freelancer.password == password: 
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
def freelancer_login_page(request):           
    return render(request, "login.html")

@require_http_methods(["POST"])               
def freelancer_login(request):
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""

    try:
        freelancer = Freelancer.objects.get(email__iexact=email)
    except Freelancer.DoesNotExist:
        messages.error(request, "Invalid email or password.")
        return redirect("freelancer_login")

    if hasattr(freelancer, "password") and not check_password(password, freelancer.password):
        messages.error(request, "Invalid email or password.")
        return redirect("freelancer_login")

    request.session["freelancer_id"] = freelancer.id   
    return redirect("freelancer_dashboard")

def logout_view(request):
    request.session.flush()  
    return redirect("login")  
def freelancer_dashboard(request):
    
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



@recruiter_required
def my_jobs_view(request):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)

    jobs = list(Job.objects.filter(recruiter=rp).order_by("-posted_at"))

    for j in jobs:
        try:
            j.apps_count = j.applications.count()      
        except AttributeError:
            j.apps_count = j.application_set.count()    

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


def jobs_list_view(request):
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




# def jobs_list_view(request):
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


def job_detail_view(request, job_id):
    job = get_object_or_404(
        Job.objects.select_related("recruiter", "recruiter__recruiter"),
        id=job_id
    )

    is_freelancer = (request.session.get("role") == "freelancer" and
                     bool(request.session.get("freelancer_id")))
    applied = False
    can_apply = False
    why_cant_apply = None 

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
@recruiter_required
def job_applications_view(request, job_id):
    r = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = r.profile
    job = get_object_or_404(Job, id=job_id, recruiter=rp)
    apps = (Application.objects
              .filter(job=job)
              .select_related("freelancer__freelancer"))
    return render(request, "jobs/job_applications.html", {
        "job": job,
        "applications": apps,   # <-- name matches template
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
        id=app_id, job__recruiter=rp,   
    )

    return render(request, "jobs/job_application_detail.html", {
        "app": app,
    })



@recruiter_required
def recruiter_view_freelancer_profile(request, profile_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    fp = get_object_or_404(FreelancerProfile, id=profile_id)

    job = None
    job_id = request.GET.get("job")
    if job_id:
        job = get_object_or_404(Job, id=job_id, recruiter=rp)

    return render(request, "jobs/recruiter_view_freelancer_profile.html", {"fp": fp, "job": job})








#commuication




def _parse_when(when_str: str):
   
    when_str = (when_str or "").strip().replace("T", " ")
    return timezone.make_aware(datetime.strptime(when_str, "%Y-%m-%d %H:%M"))


@recruiter_required
def flow_recruiter_shortlist(request, app_id):
    from django.utils import timezone
    app = get_object_or_404(
        Application.objects.select_related("job__recruiter"),
        id=app_id,
        job__recruiter__recruiter_id=request.session["recruiter_id"],
    )
    flow, created = ApplicationFlow.objects.get_or_create(
        application=app,
        defaults={
            "stage": "SHORTLISTED",
            "shortlist_expires_at": timezone.now() + timezone.timedelta(hours=72),
        },
    )
    if not created and flow.stage != "SHORTLISTED":
        flow.stage = "SHORTLISTED"
        flow.shortlist_expires_at = timezone.now() + timezone.timedelta(hours=72)
        flow.save(update_fields=["stage", "shortlist_expires_at"])
    messages.success(request, "Candidate shortlisted.")
    return redirect("job_applications", job_id=app.job.id)



@recruiter_required
def flow_recruiter_schedule_interview(request, app_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    app = get_object_or_404(Application.objects.select_related("job"), id=app_id, job__recruiter=rp)
    flow, _ = ApplicationFlow.objects.get_or_create(application=app)

    if flow.stage not in ("SHORTLISTED_ACCEPTED", "INTERVIEW"):
        messages.error(request, "Interview can be scheduled only after candidate accepts.")
        return redirect("job_applications", job_id=app.job.id)

    if request.method == "POST":
        when = _parse_when(request.POST.get("when"))
        link = (request.POST.get("link") or "").strip()
        msg  = (request.POST.get("message") or "").strip()

        flow.schedule_interview(when, link, msg)
        flow.save()
        messages.success(request, "Interview scheduled.")
        return redirect("job_applications", job_id=app.job.id)

    return render(request, "jobs/schedule_interview.html", {"app": app, "flow": flow})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.db import transaction
from .models import Application, ApplicationFlow, Contract, RecruiterProfile
@recruiter_required
# def flow_recruiter_set_outcome(request, app_id, decision):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     app = get_object_or_404(Application.objects.select_related("job"), id=app_id, job__recruiter=rp)
#     flow, _ = ApplicationFlow.objects.get_or_create(application=app)

#     if decision not in ("hire", "reject"):
#         messages.error(request, "Invalid outcome.")
#         return redirect("job_applications", job_id=app.job.id)

#     flow.set_outcome(hired=(decision == "hire"))
#     flow.save()
#     messages.success(request, f"Marked as {flow.stage.lower()}.")
#     return redirect("job_applications", job_id=app.job.id)
# myapp/views.py


# def flow_recruiter_set_outcome(request, app_id, decision):
#     """
#     Finalize an application's outcome as HIRED or REJECTED.

#     - Only the job's recruiter (from session) can set the outcome.
#     - Only accepts POST.
#     - Idempotent for already-final states.
#     - On HIRED, ensures a Contract anchor exists for reviews/completion.
#     """
#     if request.method != "POST":
#         return HttpResponseNotAllowed(["POST"])

#     # --- Authz: recruiter must be in session and own the job ---
#     rid = request.session.get("recruiter_id")
#     if not rid:
#         messages.error(request, "Please log in as a recruiter.")
#         return redirect("login_page")  # adjust to your login route

#     # Pull the application that belongs to this recruiter
#     app = get_object_or_404(
#         Application.objects.select_related("job", "job__recruiter", "flow"),
#         id=app_id,
#         job__recruiter__id=rid,
#     )

#     # Ensure there is a flow row
#     flow, _ = ApplicationFlow.objects.get_or_create(application=app)

#     # --- Normalize and validate decision ---
#     decision = (decision or "").strip().lower()
#     if decision not in {"hire", "reject"}:
#         messages.error(request, "Invalid decision. Use 'hire' or 'reject'.")
#         return redirect("application_detail", app_id=app.id)

#     # --- Prevent changing after finalization ---
#     if flow.stage in {"HIRED", "REJECTED"}:
#         messages.info(request, f"Already finalized as {flow.stage}.")
#         return redirect("application_detail", app_id=app.id)

#     # (Optional) Enforce allowed-from stages for hire/reject:
#     # e.g., you may want to only allow HIRED from INTERVIEW or SHORTLISTED_ACCEPTED.
#     # allowed_from_hire = {"INTERVIEW", "SHORTLISTED_ACCEPTED", "SHORTLISTED"}
#     # allowed_from_reject = {"SUBMITTED", "SHORTLISTED", "SHORTLISTED_ACCEPTED", "INTERVIEW"}
#     # if decision == "hire" and flow.stage not in allowed_from_hire:
#     #     messages.error(request, "You can only mark HIRED after interview/acceptance.")
#     #     return redirect("application_detail", app_id=app.id)

#     with transaction.atomic():
#         if decision == "hire":
#             flow.set_outcome(True)  # sets stage=HIRED, outcome_at=now
#             flow.save(update_fields=["stage", "outcome_at"])
#             # Ensure a Contract exists (anchor for review + completion)
#             Contract.objects.get_or_create(application=app)
#             messages.success(request, "Marked as HIRED. You can now leave a review.")
#         else:
#             flow.set_outcome(False)  # sets stage=REJECTED, outcome_at=now
#             flow.save(update_fields=["stage", "outcome_at"])
#             messages.info(request, "Marked as REJECTED.")

#     return redirect("application_detail", app_id=app.id)



@freelancer_required
def flow_freelancer_respond(request, app_id, decision):
    fp = FreelancerProfile.objects.get(freelancer_id=request.session["freelancer_id"])
    app = get_object_or_404(Application, id=app_id, freelancer=fp)
    flow, _ = ApplicationFlow.objects.get_or_create(application=app)

    flow.mark_expired_if_needed()
    if flow.stage == "SHORTLIST_EXPIRED":
        messages.error(request, "This shortlist has expired.")
        return redirect("freelancer_dashboard")

    if flow.stage != "SHORTLISTED":
        messages.error(request, "This application is not awaiting your response.")
        return redirect("freelancer_dashboard")

    if decision == "accept":
        flow.accepted()
        flow.save()
        messages.success(request, "Thanks! The recruiter will schedule an interview.")
    elif decision == "decline":
        flow.declined()
        flow.save()
        messages.info(request, "You declined this shortlist.")
    else:
        messages.error(request, "Invalid decision.")

    return redirect("freelancer_dashboard")




@freelancer_required
def freelancer_dashboard(request):
    fid = request.session.get("freelancer_id")
    freelancer = get_object_or_404(Freelancer, id=fid)

    profile, _ = FreelancerProfile.objects.get_or_create(freelancer=freelancer)

    fp = (
        FreelancerProfile.objects
        .filter(pk=profile.pk)
        .select_related("freelancer")
        .prefetch_related(
            # change names here if you set related_name on your FKs
            Prefetch("freelancerproject_set", queryset=FreelancerProject.objects.order_by("-id")),
            Prefetch("achievement_set", queryset=Achievement.objects.order_by("-id")),
            Prefetch("publication_set", queryset=Publication.objects.order_by("-id")),
        )
        .first()
    )

    my_apps = (
        Application.objects
        .filter(freelancer=fp)
        .select_related("job", "job__recruiter", "flow")   
        .order_by("-created_at")
    )

    context = {
        "freelancer": freelancer,
        "profile": fp,  
        "projects": list(fp.freelancerproject_set.all()),
        "achievements": list(fp.achievement_set.all()),
        "publications": list(fp.publication_set.all()),
        "my_apps": my_apps,
    }
    return render(request, "freelancer_dashboard.html", context)




#

# @recruiter_required
# def flow_recruiter_request_completion(request, app_id):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     app = get_object_or_404(Application.objects.select_related("job", "freelancer"), id=app_id, job__recruiter=rp)
#     flow, _ = ApplicationFlow.objects.get_or_create(application=app)

#     if flow.stage != "HIRED":
#         messages.error(request, "You can request completion only after hiring.")
#         return redirect("job_applications", job_id=app.job.id)

#     flow.request_completion()
#     flow.save()
#     messages.success(request, "Asked the freelancer to confirm completion.")
#     return redirect("job_applications", job_id=app.job.id)


# @freelancer_required
# def flow_freelancer_confirm_completion(request, app_id):
#     fp = FreelancerProfile.objects.get(freelancer_id=request.session["freelancer_id"])
#     app = get_object_or_404(Application.objects.select_related("flow", "job__recruiter"), id=app_id, freelancer=fp)
#     flow = getattr(app, "flow", None)

#     if not flow or flow.stage != "COMPLETION_REQUESTED":
#         messages.error(request, "No completion request pending.")
#         return redirect("freelancer_dashboard")

#     if request.method == "POST":
#         flow.confirm_completion()
#         flow.save()
#         messages.success(request, "Marked completed. Thanks!")
#         return redirect("freelancer_dashboard")

#     return render(request, "jobs/confirm_completion.html", {"app": app, "flow": flow})


# # --- Review (recruiter -> freelancer) ---
# class ReviewForm(forms.ModelForm):
#     class Meta:
#         model = Review
#         fields = ["rating", "comment"]

# @recruiter_required
# def flow_recruiter_review(request, app_id):
#     recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
#     rp = getattr(recruiter, "profile", None)
#     app = get_object_or_404(Application.objects.select_related("job", "freelancer", "flow"), id=app_id, job__recruiter=rp)
#     flow = app.flow

#     if not flow or flow.stage != "COMPLETED":
#         messages.error(request, "You can review only after freelancer confirms completion.")
#         return redirect("job_applications", job_id=app.job.id)

#     if hasattr(app, "review_from_recruiter"):
#         messages.info(request, "You already left a review.")
#         return redirect("job_applications", job_id=app.job.id)

#     if request.method == "POST":
#         form = ReviewForm(request.POST)
#         if form.is_valid():
#             r = form.save(commit=False)
#             r.application = app
#             r.reviewer = recruiter
#             r.reviewee = app.freelancer  # FK to Freelancer on Application
#             r.save()
#             messages.success(request, "Review submitted.")
#             return redirect("job_applications", job_id=app.job.id)
#     else:
#         form = ReviewForm()

#     return render(request, "jobs/review_form.html", {"form": form, "app": app})
#reveiw and contact
# myapp/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Application, Contract, FreelancerReview, RecruiterProfile
from .forms import ReviewForm


def _get_recruiter_profile_from_session(request):
    rid = request.session.get("recruiter_id")
    if not rid:
        return None
    # Your session stores the base Recruiter.id, so fetch the profile by recruiter_id
    try:
        return RecruiterProfile.objects.select_related("recruiter").get(recruiter_id=rid)
    except RecruiterProfile.DoesNotExist:
        # If you ever store the profile id directly, this fallback helps
        try:
            return RecruiterProfile.objects.select_related("recruiter").get(id=rid)
        except RecruiterProfile.DoesNotExist:
            return None
def flow_recruiter_set_outcome(request, app_id, decision):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    rp = _get_recruiter_profile_from_session(request)
    if rp is None:
        messages.error(request, "Please log in as a recruiter.")
        return redirect("login_page")

    # IMPORTANT: filter by the *profile* object, not by the base Recruiter id
    app = get_object_or_404(
        Application.objects.select_related("job", "flow"),
        id=app_id,
        job__recruiter=rp,
    )

    flow, _ = ApplicationFlow.objects.get_or_create(application=app)
    decision = (decision or "").lower().strip()
    if decision not in {"hire", "reject"}:
        messages.error(request, "Invalid decision.")
        return redirect("job_application_detail", app_id=app.id)

    if flow.stage in {"HIRED", "REJECTED"}:
        messages.info(request, f"Already finalized as {flow.stage}.")
        return redirect("job_application_detail", app_id=app.id)

    with transaction.atomic():
        if decision == "hire":
            flow.set_outcome(True)
            flow.save(update_fields=["stage", "outcome_at"])
            Contract.objects.get_or_create(application=app)
            messages.success(request, "Marked as HIRED. You can now leave a review.")
        else:
            flow.set_outcome(False)
            flow.save(update_fields=["stage", "outcome_at"])
            messages.info(request, "Marked as REJECTED.")

    return redirect("job_application_detail", app_id=app.id)


def application_review_create(request, app_id):
    rp = _get_recruiter_profile_from_session(request)

    # ⬇️ NOTE: 'freelancer' (no '__profile') because Application.freelancer is already a FreelancerProfile FK
    app = get_object_or_404(
        Application.objects.select_related("job", "freelancer", "flow"),
        id=app_id,
        job__recruiter=rp,
    )
    flow = app.flow
    if not flow or flow.stage != "HIRED":
        messages.error(request, "You can review only after hiring.")
        return redirect("application_detail", app_id=app.id)

    contract, _ = Contract.objects.get_or_create(application=app)
    if hasattr(contract, "review"):
        messages.info(request, "Review already exists—use Edit.")
        return redirect("application_review_edit", app_id=app.id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.contract = contract
            review.recruiter = rp
            review.freelancer = app.freelancer   # ⬅️ use the profile directly
            review.save()

            if form.cleaned_data.get("is_completed"):
                contract.mark_completed(form.cleaned_data.get("completion_notes", ""))
            else:
                contract.completion_notes = form.cleaned_data.get("completion_notes", "")
            contract.save()

            messages.success(request, "Review submitted. Thank you!")
            return redirect("job_application_detail", app_id=app.id)
    else:
        form = ReviewForm()

    return render(request, "applications/review_form.html", {"application": app, "form": form})


def application_review_edit(request, app_id):
    rp = _get_recruiter_profile_from_session(request)

    app = get_object_or_404(
        Application.objects.select_related("job", "freelancer", "flow"),
        id=app_id,
        job__recruiter=rp,
    )
    contract = get_object_or_404(Contract, application=app)
    review = get_object_or_404(FreelancerReview, contract=contract, recruiter=rp)

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get("is_completed"):
                contract.mark_completed(form.cleaned_data.get("completion_notes", ""))
            else:
                contract.is_completed = False
                contract.completed_at = None
                contract.completion_notes = form.cleaned_data.get("completion_notes", "")
            contract.save()

            messages.success(request, "Review updated.")
            return redirect("job_application_detail", app_id=app.id)
    else:
        form = ReviewForm(
            instance=review,
            initial={
                "is_completed": contract.is_completed,
                "completion_notes": contract.completion_notes,
            },
        )

    return render(request, "applications/review_form.html", {"application": app, "form": form, "is_edit": True})





#add job and skill


@login_required
@require_POST
def ajax_create_role(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Missing name"}, status=400)

    existing = Role.objects.filter(name__iexact=name).first()
    if existing:
        # 409 = Conflict (duplicate)
        return JsonResponse(
            {"error": "Already exists", "id": existing.id, "name": existing.name},
            status=409
        )

    obj = Role.objects.create(name=name)
    return JsonResponse({"id": obj.id, "name": obj.name}, status=201)


@login_required
@require_POST
def ajax_create_skill(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Missing name"}, status=400)

    existing = Skill.objects.filter(name__iexact=name).first()
    if existing:
        return JsonResponse(
            {"error": "Already exists", "id": existing.id, "name": existing.name},
            status=409
        )

    obj = Skill.objects.create(name=name)
    return JsonResponse({"id": obj.id, "name": obj.name}, status=201)



#for email and notification 
def notifications_list(request):
    fid = request.session.get("freelancer_id")
    fr = get_object_or_404(Freelancer, id=fid)
    notifications = fr.notifications.all().order_by("-created_at")
    return render(request, "notifications/list.html", {"notifications": notifications})

def notification_open(request, pk):
    fid = request.session.get("freelancer_id")
    fr = get_object_or_404(Freelancer, id=fid)
    n = get_object_or_404(Notification, id=pk, freelancer=fr)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])
    # fallback to jobs list if url missing
    return redirect(n.url or "jobs_list")

def notification_mark_read(request, pk):
    fid = request.session.get("freelancer_id")
    fr = get_object_or_404(Freelancer, id=fid)
    n = get_object_or_404(Notification, pk=pk, freelancer=fr)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect(n.url or "notifications_list")


def toggle_job_email_notifications(request):
    fid = request.session.get("freelancer_id")
    f = get_object_or_404(Freelancer, id=fid)
    f.profile.email_notifications = not f.profile.email_notifications
    f.profile.save(update_fields=["email_notifications"])
    return redirect(request.GET.get("next") or "freelancer_profile_edit")


def notifications_mark_all_read(request):
    fid = request.session.get("freelancer_id")
    fr = get_object_or_404(Freelancer, id=fid)
    from .models import Notification
    Notification.objects.filter(freelancer=fr, is_read=False).update(is_read=True)
    return redirect("notifications_list")



#fliter


from datetime import timedelta
from django.db.models import Q, F, Count as DjCount
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Job, Skill  # <-- make sure Skill is imported

# Role buckets for title matching
ROLE_BUCKETS = {
    "DATA_ANALYST":   ["data analyst", "analytics"],
    "DATA_SCIENTIST": ["data scientist", "ml", "machine learning"],
    "BACKEND_DEV":    ["backend", "back-end", "django", "node", "spring", "api"],
    "FRONTEND_DEV":   ["frontend", "front-end", "react", "angular", "vue"],
    "FULLSTACK_DEV":  ["full stack", "full-stack"],
    "DEVOPS":         ["devops", "sre", "site reliability"],
    "ML_ENGINEER":    ["ml engineer", "ai engineer"],
    "MOBILE_DEV":     ["android", "ios", "flutter", "react native"],
    "UI_UX":          ["ui/ux", "ux designer", "ui designer", "product designer"],
    "QA_TESTER":      ["qa", "tester", "test engineer", "quality assurance"],
}

def _filter_by_role(qs, role_key: str):
    kws = ROLE_BUCKETS.get(role_key, [])
    if not kws:
        return qs.none()
    cond = Q()
    for kw in kws:
        cond |= Q(title__icontains=kw)
    return qs.filter(cond)

def jobs_list_view(request):
    # recruiters see their own area
    if request.session.get("role") == "recruiter":
        return redirect("my_jobs")

    qs = (Job.objects
            .filter(is_active=True)
            .select_related("recruiter", "recruiter__recruiter")
            .prefetch_related("skills_required")
            .order_by("-posted_at"))

    # -------- read inputs --------
    q         = (request.GET.get("q") or "").strip()

    # SKILLS: checkboxes + free-text "skill_custom" (comma separated OK)
    skills = [s.strip() for s in request.GET.getlist("skills") if s and s.strip()]
    skill_custom_raw = (request.GET.get("skill_custom") or "").strip()
    if skill_custom_raw:
        for part in skill_custom_raw.split(","):
            part = part.strip()
            if part:
                skills.append(part)
    # dedupe case-insensitively
    seen = set()
    skills = [s for s in skills if not (s.lower() in seen or seen.add(s.lower()))]

    exp_min   = (request.GET.get("exp_min") or "").strip()
    exp_max   = (request.GET.get("exp_max") or "").strip()
    bmin      = (request.GET.get("budget_min") or "").strip()
    bmax      = (request.GET.get("budget_max") or "").strip()
    currency  = (request.GET.get("currency") or "").strip()
    remote    = (request.GET.get("remote") or "").strip()
    city      = (request.GET.get("city") or "").strip()
    country   = (request.GET.get("country") or "").strip()
    posted    = (request.GET.get("posted") or "").strip()
    job_type  = (request.GET.get("job_type") or "").strip()
    role      = (request.GET.get("role") or "").strip()
    sort      = (request.GET.get("sort") or "new").strip()

    # -------- apply filters --------
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(recruiter__recruiter__company_name__icontains=q) |
            Q(location_city__icontains=q) |
            Q(location_country__icontains=q)
        )

    if role:
        qs = _filter_by_role(qs, role)

    if skills:
        cond = Q()
        for term in skills:
            cond |= Q(skills_required__name__iexact=term) | Q(skills_required__name__icontains=term)
        qs = qs.filter(cond).distinct()

    if exp_min:
        qs = qs.filter(experience_required__icontains=exp_min)
    if exp_max:
        qs = qs.filter(experience_required__icontains=exp_max)

    try:
        if bmin:
            qs = qs.filter(salary_min__gte=float(bmin))
        if bmax:
            qs = qs.filter(salary_max__lte=float(bmax))
    except ValueError:
        pass

    if currency:
        qs = qs.filter(currency__iexact=currency)
    if remote:
        qs = qs.filter(work_mode__iexact=remote)
    if city:
        qs = qs.filter(location_city__icontains=city)
    if country:
        qs = qs.filter(location_country__icontains=country)

    posted_map = {"1d": 1, "7d": 7, "30d": 30}
    if posted in posted_map:
        qs = qs.filter(posted_at__gte=timezone.now() - timedelta(days=posted_map[posted]))

    if job_type:
        qs = qs.filter(job_type__iexact=job_type)

    # sorting
    if sort == "budget_desc":
        qs = qs.order_by(F("salary_max").desc(nulls_last=True), "-posted_at")
    elif sort == "salary_low":
        qs = qs.order_by(F("salary_min").asc(nulls_last=True), "-posted_at")
    elif sort == "closing":
        qs = qs.order_by("application_deadline", "-posted_at")
    else:
        qs = qs.order_by("-posted_at")

    # -------- facets --------
    facet_base = Job.objects.filter(is_active=True)
    if q:
        facet_base = facet_base.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(recruiter__recruiter__company_name__icontains=q) |
            Q(location_city__icontains=q) |
            Q(location_country__icontains=q)
        )
    if skills:
        # mirror skills logic for facet base
        cond = Q()
        for term in skills:
            cond |= Q(skills_required__name__iexact=term) | Q(skills_required__name__icontains=term)
        facet_base = facet_base.filter(cond).distinct()
    if posted in posted_map:
        facet_base = facet_base.filter(posted_at__gte=timezone.now() - timedelta(days=posted_map[posted]))
    try:
        if bmin:
            facet_base = facet_base.filter(salary_min__gte=float(bmin))
        if bmax:
            facet_base = facet_base.filter(salary_max__lte=float(bmax))
    except ValueError:
        pass

    facet_workplace = {r["work_mode"]: r["n"] for r in facet_base.values("work_mode").annotate(n=DjCount("id"))}
    facet_jobtype   = {r["job_type"]: r["n"]   for r in facet_base.values("job_type").annotate(n=DjCount("id"))}
    facet_role      = {}
    for key, kws in ROLE_BUCKETS.items():
        c = 0
        for kw in kws:
            c += facet_base.filter(title__icontains=kw).count()
        facet_role[key] = c

    # -------- options for template loops --------
    WORK_MODES  = Job.WORK_MODES
    JOB_TYPES   = Job.JOB_TYPES
    POSTED_OPTS = [("1d", "Last 24h"), ("7d", "Last 7 days"), ("30d", "Last 30 days")]
    ROLE_LABELS = [
        ("DATA_ANALYST", "Data Analyst"),
        ("DATA_SCIENTIST", "Data Scientist"),
        ("BACKEND_DEV", "Backend Developer"),
        ("FRONTEND_DEV", "Frontend Developer"),
        ("FULLSTACK_DEV", "Full-Stack Developer"),
        ("DEVOPS", "DevOps / SRE"),
        ("ML_ENGINEER", "ML Engineer"),
        ("MOBILE_DEV", "Mobile Developer"),
        ("UI_UX", "UI/UX Designer"),
        ("QA_TESTER", "QA / Test Engineer"),
    ]

    # popular skills from DB (fallback to a small list)
    try:
        POPULAR_SKILLS = list(
            Skill.objects.filter(jobs__is_active=True)
            .annotate(n=DjCount("jobs"))
            .order_by("-n", "name")
            .values_list("name", flat=True)[:20]
        )
        if not POPULAR_SKILLS:
            POPULAR_SKILLS = ["Python", "Django", "SQL", "React", "AWS", "Azure", "Flask"]
    except Exception:
        POPULAR_SKILLS = ["Python", "Django", "SQL", "React", "AWS", "Azure", "Flask"]

    CURRENCIES = ["INR", "USD", "EUR"]

    # -------- build context ONCE (no context.update) --------
    context = {
        "jobs": qs,
        "facet": {"workplace": facet_workplace, "jobtype": facet_jobtype, "role": facet_role},
        "WORK_MODES": WORK_MODES,
        "JOB_TYPES": JOB_TYPES,
        "POSTED_OPTS": POSTED_OPTS,
        "ROLE_LABELS": ROLE_LABELS,
        "POPULAR_SKILLS": POPULAR_SKILLS,
        "CURRENCIES": CURRENCIES,
        "selected_skills": skills,
    }
    return render(request, "jobs/jobs_list.html", context)
