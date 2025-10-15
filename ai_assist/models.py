from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class ResumeAnalysis(models.Model):
    # Link to your existing profile model; change the import/path as needed
    from myapp.models import FreelancerProfile  # adjust to your actual app
    profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name="resume_analyses")

    file = models.FileField(upload_to="resumes/")
    extracted_text = models.TextField(blank=True)
    score = models.PositiveIntegerField(default=0)
    report = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

