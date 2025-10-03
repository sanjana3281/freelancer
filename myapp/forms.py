from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import (
    FreelancerProfile, FreelancerRole, Role,
    FreelancerSkill, Skill,
    FreelancerLanguage, Language,
    Achievement, Publication, FreelancerProject,RecruiterProfile,
    Job, Skill, JobSkill,Application

)

class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = [
            "headline", "bio","profile_photo",
            "location_city", "location_country", "timezone",
            "years_experience", "hourly_rate",
            "work_modes", "work_authorization",
            "resume_file", "github_url",
            "preferred_industries_note", "travel_ready",
            "contact_phone", "contact_whatsapp", "contact_email",
            "publications_link", "portfolio_link",
        ]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in [
            "work_authorization", "hourly_rate", "resume_file", "github_url",
            "preferred_industries_note", "contact_phone", "contact_whatsapp",
            "contact_email", "publications_link", "portfolio_link", "profile_photo"
        ]:
            if name in self.fields:
                self.fields[name].required = False
        if "work_modes" in self.fields and not self.fields["work_modes"].initial:
            self.fields["work_modes"].initial = getattr(self.instance, "work_modes", None) or "REMOTE"
        if "work_authorization" in self.fields and not self.fields["work_authorization"].initial:
            self.fields["work_authorization"].initial = getattr(self.instance, "work_authorization", None) or "GLOBAL_REMOTE"

class FreelancerRoleForm(forms.ModelForm):
    class Meta:
        model = FreelancerRole
        fields = ["role"]

class FreelancerSkillForm(forms.ModelForm):
    class Meta:
        model = FreelancerSkill
        fields = ["skill", "level", "years"]

class FreelancerLanguageForm(forms.ModelForm):
    class Meta:
        model = FreelancerLanguage
        fields = ["language", "proficiency"]

class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ["title", "description", "date"]

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ["title", "link", "description", "date"]

class FreelancerProjectForm(forms.ModelForm):
    class Meta:
        model = FreelancerProject
        fields = [
            "title", "role_title", "summary", "tech_stack",
            "demo_url", "repo_url", "start_date", "end_date", "impact_metrics",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "demo_url": forms.URLInput(),
            "repo_url": forms.URLInput(),
        }

class ProjectsBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        field_names = [
            "title", "role_title", "summary", "tech_stack",
            "demo_url", "repo_url", "start_date", "end_date", "impact_metrics",
        ]
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            is_blank = all(
                not form.cleaned_data.get(name) for name in field_names
            )
            if is_blank:
                form.cleaned_data["DELETE"] = True
class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ["title", "description", "date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ["title", "link", "description", "date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "link": forms.URLInput(),                 # better URL validation
            "date": forms.DateInput(attrs={"type": "date"}),
        }

class AchievementsBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        fields = ["title", "description", "date"]
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            # If ALL fields are empty -> mark as DELETE (ignored on save)
            if all(not form.cleaned_data.get(f) for f in fields):
                form.cleaned_data["DELETE"] = True

class PublicationsBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        fields = ["title", "link", "description", "date"]
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            if all(not form.cleaned_data.get(f) for f in fields):
                form.cleaned_data["DELETE"] = True


RoleFormSet       = inlineformset_factory(FreelancerProfile, FreelancerRole, form=FreelancerRoleForm, extra=0, can_delete=True)
SkillFormSet      = inlineformset_factory(FreelancerProfile, FreelancerSkill, form=FreelancerSkillForm, extra=0, can_delete=True)
LanguageFormSet   = inlineformset_factory(FreelancerProfile, FreelancerLanguage, form=FreelancerLanguageForm, extra=0, can_delete=True)
ProjectFormSet    = inlineformset_factory(FreelancerProfile, FreelancerProject, form=FreelancerProjectForm, formset=ProjectsBaseFormSet, extra=1, can_delete=True)
AchievementFormSet = inlineformset_factory(
    FreelancerProfile,
    Achievement,
    form=AchievementForm,
    formset=AchievementsBaseFormSet,
    extra=1,                
    can_delete=True,
)

PublicationFormSet = inlineformset_factory(
    FreelancerProfile,
    Publication,
    form=PublicationForm,
    formset=PublicationsBaseFormSet,
    extra=1,
    can_delete=True,
)






class ProfileBasicsForm(forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = [
            "headline", "bio", "profile_photo",
            "location_country", "location_city", "timezone",
            "years_experience", "hourly_rate",
            "work_modes", "work_authorization", "travel_ready",
        ]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

class ProfileContactForm(forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = [
            "github_url", "portfolio_link", "publications_link",
            "contact_email", "contact_phone", "contact_whatsapp",
            "resume_file",
        ]




 
class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = [
            "company_website", "industry", "about_company",
            "founded_year", "headquarters_city", "headquarters_country",
            "contact_email_alt", "contact_phone", "linkedin_url",
            "logo",
        ]




class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title", "description",
            "job_type", "work_mode",
            "location_city", "location_country",
            "experience_required", "education_required",
            "salary_min", "salary_max", "currency",
            "application_deadline",
        ]
        widgets = {
            "skills_required": forms.SelectMultiple(attrs={"size": 8}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    
    def clean(self):
        cleaned = super().clean()
        work_mode = cleaned.get("work_mode")
        city = cleaned.get("location_city")
        country = cleaned.get("location_country")
        salary_min = cleaned.get("salary_min")
        salary_max = cleaned.get("salary_max")

       
        if work_mode in ("ONSITE", "HYBRID"):
            if not city or not country:
                self.add_error("location_city", "City is required for onsite/hybrid roles.")
                self.add_error("location_country", "Country is required for onsite/hybrid roles.")

       
        if salary_min and salary_max and salary_min > salary_max:
            self.add_error("salary_max", "Max salary must be greater than or equal to Min salary.")

        return cleaned

class JobSkillForm(forms.ModelForm):
    class Meta:
        model = JobSkill
        fields = ["skill", "importance"]

JobSkillFormSet = inlineformset_factory(
    parent_model=Job,
    model=JobSkill,
    form=JobSkillForm,
    extra=3,
    can_delete=True,
)


#application



class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter", "resume", "portfolio_url", "expected_salary", "availability_date"]
        widgets = {
            "cover_letter": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "Write a short cover letter..."
            }),
            "availability_date": forms.DateInput(attrs={"type": "date"}),
            "portfolio_url": forms.URLInput(attrs={"placeholder": "https://..."}),
            "expected_salary": forms.NumberInput(attrs={"step": "0.01", "placeholder": "e.g. 600000"}),
        }
        help_texts = {
            "resume": "PDF/DOC up to ~5MB",
        }


