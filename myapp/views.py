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
    Application,Role, Skill,Notification,
)
from django import forms
from .models import Review
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


@recruiter_required
def flow_recruiter_set_outcome(request, app_id, decision):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    app = get_object_or_404(Application.objects.select_related("job"), id=app_id, job__recruiter=rp)
    flow, _ = ApplicationFlow.objects.get_or_create(application=app)

    if decision not in ("hire", "reject"):
        messages.error(request, "Invalid outcome.")
        return redirect("job_applications", job_id=app.job.id)

    flow.set_outcome(hired=(decision == "hire"))
    flow.save()
    messages.success(request, f"Marked as {flow.stage.lower()}.")
    return redirect("job_applications", job_id=app.job.id)


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

@recruiter_required
def flow_recruiter_request_completion(request, app_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    app = get_object_or_404(Application.objects.select_related("job", "freelancer"), id=app_id, job__recruiter=rp)
    flow, _ = ApplicationFlow.objects.get_or_create(application=app)

    if flow.stage != "HIRED":
        messages.error(request, "You can request completion only after hiring.")
        return redirect("job_applications", job_id=app.job.id)

    flow.request_completion()
    flow.save()
    messages.success(request, "Asked the freelancer to confirm completion.")
    return redirect("job_applications", job_id=app.job.id)


@freelancer_required
def flow_freelancer_confirm_completion(request, app_id):
    fp = FreelancerProfile.objects.get(freelancer_id=request.session["freelancer_id"])
    app = get_object_or_404(Application.objects.select_related("flow", "job__recruiter"), id=app_id, freelancer=fp)
    flow = getattr(app, "flow", None)

    if not flow or flow.stage != "COMPLETION_REQUESTED":
        messages.error(request, "No completion request pending.")
        return redirect("freelancer_dashboard")

    if request.method == "POST":
        flow.confirm_completion()
        flow.save()
        messages.success(request, "Marked completed. Thanks!")
        return redirect("freelancer_dashboard")

    return render(request, "jobs/confirm_completion.html", {"app": app, "flow": flow})


# --- Review (recruiter -> freelancer) ---
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

@recruiter_required
def flow_recruiter_review(request, app_id):
    recruiter = Recruiter.objects.get(id=request.session["recruiter_id"])
    rp = getattr(recruiter, "profile", None)
    app = get_object_or_404(Application.objects.select_related("job", "freelancer", "flow"), id=app_id, job__recruiter=rp)
    flow = app.flow

    if not flow or flow.stage != "COMPLETED":
        messages.error(request, "You can review only after freelancer confirms completion.")
        return redirect("job_applications", job_id=app.job.id)

    if hasattr(app, "review_from_recruiter"):
        messages.info(request, "You already left a review.")
        return redirect("job_applications", job_id=app.job.id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.application = app
            r.reviewer = recruiter
            r.reviewee = app.freelancer  # FK to Freelancer on Application
            r.save()
            messages.success(request, "Review submitted.")
            return redirect("job_applications", job_id=app.job.id)
    else:
        form = ReviewForm()

    return render(request, "jobs/review_form.html", {"form": form, "app": app})




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