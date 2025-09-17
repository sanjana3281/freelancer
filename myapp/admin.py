from django.contrib import admin
from .models import Freelancer, Recruiter

@admin.register(Freelancer)
class FreelancerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")

@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ("id", "company_name", "contact_person", "email")
    search_fields = ("company_name", "contact_person", "email")


