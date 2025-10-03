from django.db import models

# Create your models here.


class Freelancer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    

    def __str__(self):
        return self.name

class Recruiter(models.Model):
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.company_name} ({self.contact_person})"

class FreelancerProfile(models.Model):
    WORK_MODES = [
        ("REMOTE", "Remote"),
        ("HYBRID", "Hybrid"),
        ("ONSITE", "Onsite"),
    ]

    WORK_AUTH = [
        ("INDIA_ONLY", "India Only"),
        ("GLOBAL_REMOTE", "Global Remote"),
        ("SPECIFIC_COUNTRIES", "Specific Countries"),
    ]

    freelancer = models.OneToOneField(Freelancer, on_delete=models.CASCADE, related_name="profile")
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True, max_length=2000)
    location_city = models.CharField(max_length=80, blank=True)
    location_country = models.CharField(max_length=80, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    hourly_rate = models.CharField(max_length=32, blank=True, null=True)
    work_modes = models.CharField(max_length=10, choices=WORK_MODES, default="REMOTE")
    work_authorization = models.CharField(max_length=30, choices=WORK_AUTH, default="GLOBAL_REMOTE")
    resume_file = models.FileField(upload_to="resumes/", blank=True, null=True)
    github_url = models.URLField(blank=True)
    preferred_industries_note = models.TextField(blank=True)   
    travel_ready = models.BooleanField(default=False)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_whatsapp = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)

    avg_response_time_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    publications_link = models.URLField(blank=True)  
    portfolio_link = models.URLField(blank=True)    
    profile_photo = models.ImageField(upload_to="freelancer_photos/", blank=True, null=True)


    def __str__(self):
        return f"FreelancerProfile for {self.freelancer.name}"




class Role(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

class FreelancerRole(models.Model):
    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("freelancer", "role")

    def __str__(self):
        return f"{self.freelancer.freelancer.name} - {self.role.name}"


class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

class FreelancerSkill(models.Model):
    LEVELS = [
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("ADVANCED", "Advanced"),
        ("EXPERT", "Expert"),
    ]

    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVELS)
    years = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("freelancer", "skill")

    def __str__(self):
        return f"{self.freelancer.freelancer.name} - {self.skill.name} ({self.level})"



class Language(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

class FreelancerLanguage(models.Model):
    PROFICIENCY = [
        ("BASIC", "Basic"),
        ("CONVERSATIONAL", "Conversational"),
        ("FLUENT", "Fluent"),
        ("NATIVE", "Native"),
    ]

    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY)

    class Meta:
        unique_together = ("freelancer", "language")

    def __str__(self):
        return f"{self.freelancer.freelancer.name} - {self.language.name} ({self.proficiency})"



class Achievement(models.Model):
    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.freelancer.freelancer.name} - {self.title}"


class Publication(models.Model):
    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    link = models.URLField(blank=True)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
         return f"{self.freelancer.freelancer.name} - {self.title}"



class FreelancerProject(models.Model):
    freelancer = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    role_title = models.CharField(max_length=120, blank=True)
    summary = models.TextField(blank=True)
    tech_stack = models.CharField(max_length=255, blank=True)  # simple comma-separated list
    demo_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    impact_metrics = models.TextField(blank=True)

    def __str__(self):
        return f"{self.freelancer.freelancer.name} - {self.title}"

class ProjectMedia(models.Model):
    project = models.ForeignKey(FreelancerProject, on_delete=models.CASCADE, related_name="media")
    image = models.ImageField(upload_to="project_media/")
    caption = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"Media for {self.project.title}"







#recuiter
class RecruiterProfile(models.Model):
    INDUSTRY_CHOICES = [
        ("IT", "IT / Software"),
        ("HEALTHCARE", "Healthcare"),
        ("EDUCATION", "Education"),
        ("FINTECH", "FinTech"),
        ("RETAIL", "Retail"),
        ("OTHER", "Other"),
    ]

    recruiter = models.OneToOneField(Recruiter, on_delete=models.CASCADE, related_name="profile")

    company_website = models.URLField(blank=True)
    industry = models.CharField(max_length=40, choices=INDUSTRY_CHOICES, blank=True)
    about_company = models.TextField(blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    headquarters_city = models.CharField(max_length=100, blank=True)
    headquarters_country = models.CharField(max_length=100, blank=True)

    contact_email_alt = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)

    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)

    
    last_active_at = models.DateTimeField(null=True, blank=True)  # keep on this model

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RecruiterProfile for {self.recruiter.company_name}"

    
    @property
    def jobs_posted_count(self):
        
        return getattr(self, "_jobs_posted_stub", 0)  

    @property
    def active_jobs(self): 
        return getattr(self, "_active_jobs_stub", 0) 





#job 
class Job(models.Model):
    JOB_TYPES = [
        ("FULLTIME", "Full-time"),
        ("PARTTIME", "Part-time"),
        ("CONTRACT", "Contract"),
        ("INTERNSHIP", "Internship"),
    ]

    WORK_MODES = [
        ("REMOTE", "Remote"),
        ("HYBRID", "Hybrid"),
        ("ONSITE", "Onsite"),
    ]

   
    title = models.CharField(max_length=200)
    description = models.TextField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default="FULLTIME")
    work_mode = models.CharField(max_length=10, choices=WORK_MODES, default="ONSITE")
    location_city = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)

   
    skills_required = models.ManyToManyField("Skill", through="JobSkill", related_name="jobs")   
    experience_required = models.CharField(max_length=20, blank=True)  # e.g., "2–5"
    education_required = models.CharField(max_length=120, blank=True)


    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="INR")

    
    recruiter = models.ForeignKey("RecruiterProfile", on_delete=models.CASCADE, related_name="jobs")
    application_deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.recruiter.recruiter.company_name}"


class JobSkill(models.Model):
    IMPORTANCE = [
        ("MUST_HAVE", "Must-have"),
        ("NICE_TO_HAVE", "Nice to have"),
    ]
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="job_skills")
    skill = models.ForeignKey("Skill", on_delete=models.CASCADE)
    importance = models.CharField(max_length=12, choices=IMPORTANCE, default="MUST_HAVE")

    class Meta:
        unique_together = ("job", "skill")   # prevent duplicates

    def __str__(self):
        return f"{self.job.title} - {self.skill.name} ({self.importance})"




#application

from django.db import models
from django.utils import timezone

class Application(models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="applications")
    freelancer = models.ForeignKey("FreelancerProfile", on_delete=models.CASCADE, related_name="applications")

    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to="applications/resumes/", blank=True, null=True)

    # ← Make these optional so we don't need defaults when adding columns
    portfolio_url = models.URLField(blank=True, null=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    availability_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application: {self.freelancer} → {self.job}"

