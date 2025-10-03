from django.contrib import admin
from .models import Freelancer, Recruiter


from .models import (                
    FreelancerProfile,
    Role, FreelancerRole,
    Skill, FreelancerSkill,
    Language, FreelancerLanguage,
    Achievement, Publication, FreelancerProject,
)

# ---------- Lookup models ----------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    search_fields = ("name",)

# ---------- Inlines bound to FreelancerProfile ----------
class FreelancerRoleInline(admin.TabularInline):
    model = FreelancerRole
    extra = 1
    autocomplete_fields = ("role",)
    # unique_together (freelancer, role) is enforced at DB; admin will show error on duplicate

class FreelancerSkillInline(admin.TabularInline):
    model = FreelancerSkill
    extra = 1
    autocomplete_fields = ("skill",)
    fields = ("skill", "level", "years")

class FreelancerLanguageInline(admin.TabularInline):
    model = FreelancerLanguage
    extra = 1
    autocomplete_fields = ("language",)
    fields = ("language", "proficiency")

class AchievementInline(admin.StackedInline):
    model = Achievement
    extra = 1

class PublicationInline(admin.StackedInline):
    model = Publication
    extra = 1

class FreelancerProjectInline(admin.StackedInline):
    model = FreelancerProject
    extra = 1
    fieldsets = (
        (None, {
            "fields": (
                "title", "role_title", "summary",
                "tech_stack", "demo_url", "repo_url",
                "start_date", "end_date", "impact_metrics",
            )
        }),
    )

# ---------- Profile admin with all inlines ----------
@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "freelancer", "headline", "location_city", "location_country",
        "years_experience", "updated_at",
    )
    search_fields = (
        "freelancer__name", "freelancer__email",
        "headline", "location_city", "location_country",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = [
        FreelancerRoleInline,
        FreelancerSkillInline,
        FreelancerLanguageInline,
        AchievementInline,
        PublicationInline,
        FreelancerProjectInline,
    ]
    fieldsets = (
        ("Identity", {
            "fields": ("freelancer", "headline", "bio", "profile_photo")
        }),
        ("Location & Work", {
            "fields": (
                "location_city", "location_country", "timezone",
                "years_experience", "hourly_rate",
                "work_modes", "work_authorization",
                "travel_ready",
            )
        }),
        ("Contact", {
            "fields": ("contact_phone", "contact_whatsapp", "contact_email")
        }),
        ("Links & Files", {
            "fields": ("resume_file", "github_url", "portfolio_link", "publications_link")
        }),
        ("Other", {
            "fields": ("preferred_industries_note", "avg_response_time_hours", "created_at", "updated_at")
        }),
    )

@admin.register(Freelancer)
class FreelancerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")

@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ("id", "company_name", "contact_person", "email")
    search_fields = ("company_name", "contact_person", "email")


