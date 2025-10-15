# ai_assist/forms.py
from django import forms
from django.forms import inlineformset_factory
from myapp.models import FreelancerProfile, FreelancerProject, Achievement, Publication

class ProfileForm(forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = [
            "headline",
            "summary",            # ← use summary here
            "contact_phone",
            "contact_email",
            "location_city",
            "location_country",
            "linkedin_url",
            "github_url",
            "portfolio_link",
        ]
        labels = {
            "summary": "Summary",
            "contact_phone": "Phone",
            "contact_email": "Email",
            "location_city": "City",
            "location_country": "Country",
            "portfolio_link": "Portfolio URL",
        }
        widgets = {
            "summary": forms.Textarea(
                attrs={"rows": 4, "placeholder": "2–4 lines that sell your impact."}
            ),
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = FreelancerProject
        fields = ["title", "role_title", "start_date", "end_date", "summary", "demo_url", "repo_url"]
        labels = {"summary": "Description", "repo_url": "Repository URL"}
        widgets = {"summary": forms.Textarea(attrs={"rows": 3})}

class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ["title", "description", "date"]

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ["title", "description", "link", "date"]

ProjectFormSet     = inlineformset_factory(FreelancerProfile, FreelancerProject, form=ProjectForm,     extra=1, can_delete=True)
AchievementFormSet = inlineformset_factory(FreelancerProfile, Achievement,      form=AchievementForm, extra=1, can_delete=True)
PublicationFormSet = inlineformset_factory(FreelancerProfile, Publication,      form=PublicationForm, extra=1, can_delete=True)




class ResumeForm(forms.Form):
    # Basics
    name     = forms.CharField(label="Full name")
    headline = forms.CharField(label="Headline", required=False)
    summary  = forms.CharField(label="Professional Summary", widget=forms.Textarea(attrs={"rows":4}), required=False)

    # Contact
    email   = forms.EmailField()
    phone   = forms.CharField(required=False)
    city    = forms.CharField(required=False)
    country = forms.CharField(required=False)

    # Keywords
    skills = forms.CharField(
        label="Top skills (comma-separated)",
        widget=forms.Textarea(attrs={"rows":2}),
        required=False
    )
    roles  = forms.CharField(
        label="Target roles / titles (comma-separated)",
        widget=forms.Textarea(attrs={"rows":2}),
        required=False
    )

    # Project 1
    p1_title = forms.CharField(label="Project 1 — Title", required=False)
    p1_role  = forms.CharField(label="Project 1 — Your role", required=False)
    p1_desc  = forms.CharField(label="Project 1 — Description / bullets", widget=forms.Textarea(attrs={"rows":4}), required=False)
    p1_start = forms.DateField(label="Project 1 — Start (YYYY-MM-DD)", required=False, input_formats=["%Y-%m-%d"])
    p1_end   = forms.DateField(label="Project 1 — End (YYYY-MM-DD)", required=False, input_formats=["%Y-%m-%d"])
    p1_demo  = forms.URLField(label="Project 1 — Demo URL", required=False)
    p1_repo  = forms.URLField(label="Project 1 — Repo URL", required=False)

    # Project 2
    p2_title = forms.CharField(label="Project 2 — Title", required=False)
    p2_role  = forms.CharField(label="Project 2 — Your role", required=False)
    p2_desc  = forms.CharField(label="Project 2 — Description / bullets", widget=forms.Textarea(attrs={"rows":4}), required=False)
    p2_start = forms.DateField(label="Project 2 — Start (YYYY-MM-DD)", required=False, input_formats=["%Y-%m-%d"])
    p2_end   = forms.DateField(label="Project 2 — End (YYYY-MM-DD)", required=False, input_formats=["%Y-%m-%d"])
    p2_demo  = forms.URLField(label="Project 2 — Demo URL", required=False)
    p2_repo  = forms.URLField(label="Project 2 — Repo URL", required=False)





class ResumeUploadForm(forms.Form):
    file = forms.FileField(
        help_text="Upload PDF, DOCX, or TXT",
        widget=forms.ClearableFileInput(attrs={"accept":".pdf,.docx,.txt"})
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        ok = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}
        if f.content_type not in ok and not f.name.lower().endswith((".pdf",".docx",".txt")):
            raise forms.ValidationError("Only PDF, DOCX, or TXT files are allowed.")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Max size 5 MB.")
        return f
