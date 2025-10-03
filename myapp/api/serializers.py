from rest_framework import serializers
from myapp.models import (
    FreelancerProfile, Role, FreelancerRole,
    Skill, FreelancerSkill,
    Language, FreelancerLanguage,
    Achievement, Publication, FreelancerProject,
    Freelancer,RecruiterProfile, Recruiter,
)
from django.contrib.auth.hashers import make_password
from datetime import datetime

class FreelancerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Freelancer
        fields = ['id', 'name', 'email', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        pwd = validated_data.pop('password')
        obj = Freelancer(**validated_data)
        obj.password_hash = make_password(pwd)
        obj.save()
        return obj

class RecruiterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Recruiter
        fields = ['id', 'company_name', 'contact_person', 'email', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        pwd = validated_data.pop('password')
        obj = Recruiter(**validated_data)
        obj.password_hash = make_password(pwd)
        obj.save()
        return obj
    





class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "name"]


class FreelancerRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Role.objects.all(), source="role"
    )
    class Meta:
        model = FreelancerRole
        fields = ["id", "role", "role_id"]

class FreelancerSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Skill.objects.all(), source="skill"
    )
    class Meta:
        model = FreelancerSkill
        fields = ["id", "skill", "skill_id", "level", "years"]

class FreelancerLanguageSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)
    language_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Language.objects.all(), source="language"
    )
    class Meta:
        model = FreelancerLanguage
        fields = ["id", "language", "language_id", "proficiency"]

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["id", "title", "description", "date"]

class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = ["id", "title", "link", "description", "date"]

class FreelancerProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreelancerProject
        fields = [
            "id", "title", "role_title", "summary", "tech_stack",
            "demo_url", "repo_url", "start_date", "end_date", "impact_metrics"
        ]

# --- Profile serializer ---

class FreelancerProfileSerializer(serializers.ModelSerializer):
    roles = FreelancerRoleSerializer(source="freelancerrole_set", many=True, read_only=True)
    skills = FreelancerSkillSerializer(source="freelancerskill_set", many=True, read_only=True)
    languages = FreelancerLanguageSerializer(source="freelancerlanguage_set", many=True, read_only=True)
    achievements = AchievementSerializer(source="achievement_set", many=True, read_only=True)
    publications = PublicationSerializer(source="publication_set", many=True, read_only=True)
    projects = FreelancerProjectSerializer(source="freelancerproject_set", many=True, read_only=True)

    class Meta:
        model = FreelancerProfile
        fields = [
            "id", "headline", "bio", "profile_photo",
            "location_city", "location_country", "timezone",
            "years_experience", "hourly_rate",
            "work_modes", "work_authorization",
            "resume_file", "github_url",
            "preferred_industries_note", "travel_ready",
            "contact_phone", "contact_whatsapp", "contact_email",
            "publications_link", "portfolio_link",
            "avg_response_time_hours",
            "created_at", "updated_at",
            "roles", "skills", "languages", "achievements", "publications", "projects",
        ]
        read_only_fields = ["created_at", "updated_at", "avg_response_time_hours"]






#recuiter
from rest_framework import serializers
from myapp.models import Recruiter, RecruiterProfile

class RecruiterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = ["id", "company_name", "email", "contact_name"]

class RecruiterProfileSerializer(serializers.ModelSerializer):
    recruiter = RecruiterSerializer(read_only=True)

    class Meta:
        model = RecruiterProfile
        fields = [
            "recruiter",
            "company_website", "industry", "about_company",
            "founded_year", "headquarters_city", "headquarters_country",
            "contact_email_alt", "contact_phone", "linkedin_url",
            "logo",
            "last_active_at", "created_at", "updated_at",
            "jobs_posted_count", "active_jobs",
        ]
        read_only_fields = ["last_active_at", "created_at", "updated_at",
                            "jobs_posted_count", "active_jobs"]
