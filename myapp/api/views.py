from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.utils import IntegrityError
from myapp.models import  Recruiter
from .serializers import RecruiterSerializer
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, mixins, status,generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .permissions import IsRecruiter, IsOwnerRecruiterProfile
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from myapp.models import Recruiter

from myapp.models import (
    FreelancerProfile, Freelancer,  # your base models
    FreelancerRole, FreelancerSkill, FreelancerLanguage,
    Achievement, Publication, FreelancerProject,Recruiter, RecruiterProfile
)
from .serializers import (
    FreelancerProfileSerializer,
    FreelancerRoleSerializer, FreelancerSkillSerializer, FreelancerLanguageSerializer,
    AchievementSerializer, PublicationSerializer, FreelancerProjectSerializer,RecruiterProfileSerializer
)
from django.urls import reverse


#
def _set_session_role(request, role, **ids):
    # clear opposite role ids so the header/nav isn’t confused
    request.session.pop("freelancer_id", None)
    request.session.pop("recruiter_id", None)
    request.session["role"] = role
    for k, v in ids.items():
        request.session[k] = v
    request.session.modified = True

def _password_ok(instance, raw_password):
    """
    Works whether you saved a hashed password (make_password) or a plain one.
    Prefer hashing in production.
    """
    stored = getattr(instance, "password", "") or ""
    return check_password(raw_password, stored) or stored == raw_password




# --------- FREELANCERS ----------
@api_view(['GET'])
def freelancers_list(request):
    qs = Freelancer.objects.all().order_by('id')
    return Response(FreelancerSerializer(qs, many=True).data)

@api_view(['POST'])
def freelancers_register(request):
    ser = FreelancerSerializer(data=request.data)
    if ser.is_valid():
        try:
            obj = ser.save()
            return Response(FreelancerSerializer(obj).data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"detail": "Email already exists."}, status=400)
    return Response(ser.errors, status=400)

# --------- RECRUITERS ----------
@api_view(['GET'])
def recruiters_list(request):
    qs = Recruiter.objects.all().order_by('id')
    return Response(RecruiterSerializer(qs, many=True).data)

@api_view(['POST'])
def recruiters_register(request):
    ser = RecruiterSerializer(data=request.data)
    if ser.is_valid():
        try:
            obj = ser.save()
            return Response(RecruiterSerializer(obj).data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"detail": "Email already exists."}, status=400)
    return Response(ser.errors, status=400)


# ---------- FREELANCERS LOGIN ----------
@api_view(['POST'])
def freelancers_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"detail": "Email and password required"}, status=400)

    try:
        freelancer = Freelancer.objects.get(email=email)
    except Freelancer.DoesNotExist:
        return Response({"detail": "Invalid email or password"}, status=400)

    if check_password(password, freelancer.password_hash):
        return Response({
            "id": freelancer.id,
            "name": freelancer.name,
            "email": freelancer.email,
            "role": "freelancer"
        })
    else:
        return Response({"detail": "Invalid email or password"}, status=400)


# ---------- RECRUITERS LOGIN ----------
@api_view(['POST'])
def recruiters_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"detail": "Email and password required"}, status=400)

    try:
        recruiter = Recruiter.objects.get(email=email)
    except Recruiter.DoesNotExist:
        return Response({"detail": "Invalid email or password"}, status=400)

    if check_password(password, recruiter.password_hash):
        return Response({
            "id": recruiter.id,
            "company_name": recruiter.company_name,
            "contact_person": recruiter.contact_person,
            "email": recruiter.email,
            "role": "recruiter"
        })
    else:
        return Response({"detail": "Invalid email or password"}, status=400)



def _get_or_create_profile_for_user(user):
    """
    Assumes Freelancer has OneToOne to auth.User as `user`.
    If your login uses sessions without auth.User, adapt accordingly.
    """
    freelancer = Freelancer.objects.get(user=user)
    profile, _ = FreelancerProfile.objects.get_or_create(freelancer=freelancer)
    return profile

# ---- Profile endpoints for the current logged-in freelancer ----

class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _get_or_create_profile_for_user(request.user)
        return Response(FreelancerProfileSerializer(profile).data)

    def post(self, request):
        # create/update in one place; ensures OneToOne is set
        profile = _get_or_create_profile_for_user(request.user)
        ser = FreelancerProfileSerializer(profile, data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = _get_or_create_profile_for_user(request.user)
        ser = FreelancerProfileSerializer(profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

# ---- Child collections (auto-bound to your profile). 
# They are list/create/update/delete but always scoped to the owner. ----

class _OwnedByProfileQuerysetMixin:
    permission_classes = [IsAuthenticated]

    def get_profile(self):
        return _get_or_create_profile_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(freelancer=self.get_profile())

    def get_queryset(self):
        # Each concrete class sets its model via queryset attr
        return self.queryset.filter(freelancer=self.get_profile())

class MyRolesViewSet(_OwnedByProfileQuerysetMixin, viewsets.ModelViewSet):
    queryset = FreelancerRole.objects.all().select_related("role", "freelancer")
    serializer_class = FreelancerRoleSerializer

class MySkillsViewSet(_OwnedByProfileQuerysetMixin, viewsets.ModelViewSet):
    queryset = FreelancerSkill.objects.all().select_related("skill", "freelancer")
    serializer_class = FreelancerSkillSerializer

class MyLanguagesViewSet(_OwnedByProfileQuerysetMixin, viewsets.ModelViewSet):
    queryset = FreelancerLanguage.objects.all().select_related("language", "freelancer")
    serializer_class = FreelancerLanguageSerializer

class MyAchievementsViewSet(_OwnedByProfileQuerysetMixin, viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class MyPublicationsViewSet(_OwnedByProfileQuerysetMixin, viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer

class MyProjectsViewSet(_OwnedByProfileQuerysetMixin, viewsets.ModelViewSet):
    queryset = FreelancerProject.objects.all()
    serializer_class = FreelancerProjectSerializer




#recuiter

class MyRecruiterProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/recruiter/profile/     -> fetch my profile (auto-creates if absent)
    PUT/PATCH /api/recruiter/profile/ -> update my profile
    """
    serializer_class = RecruiterProfileSerializer
    permission_classes = [IsRecruiter, IsOwnerRecruiterProfile]
    parser_classes = [MultiPartParser, FormParser]  # for 'logo' upload

    def get_object(self):
        # Identify the logged-in recruiter
        recruiter_id = self.request.session.get("recruiter_id")
        recruiter = get_object_or_404(Recruiter, id=recruiter_id)

        # Get or create profile
        profile, _ = RecruiterProfile.objects.get_or_create(recruiter=recruiter)
        # object-level permission check:
        self.check_object_permissions(self.request, profile)
        return profile

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        # Optionally touch last_active_at
        return Response(self.get_serializer(obj).data)

    


PW_FIELDS = ("password_hash", "password", "passward", "pwd", "passwd")
HASH_PREFIXES = ("pbkdf2_", "argon2", "bcrypt", "scrypt")

def _get_pw(instance):
    for name in PW_FIELDS:
        if hasattr(instance, name):
            val = getattr(instance, name) or ""
            if val:
                return val
    return ""

def _pw_ok(raw, stored):
    if not stored:
        return False
    if stored.startswith(HASH_PREFIXES):
        return check_password(raw, stored)
    return raw == stored

def freelancer_login_submit(request):
    if request.method != "POST":
        return redirect("login_page")

    email = (request.POST.get("email") or "").strip()
    pw = request.POST.get("password") or ""

    f = Freelancer.objects.filter(email__iexact=email).first()
    if not f:
        messages.error(request, "No freelancer account found for that email.")
        return redirect(f"{reverse('login_page')}?role=freelancer")

    if not _pw_ok(pw, _get_pw(f)):
        messages.error(request, "Invalid email or password.")
        return redirect(f"{reverse('login_page')}?role=freelancer")

    # set session
    request.session.pop("recruiter_id", None)
    request.session["role"] = "freelancer"
    request.session["freelancer_id"] = f.id
    request.session.modified = True

    return redirect("freelancer_dashboard")

def recruiter_login_submit(request):
    if request.method != "POST":
        return redirect("login_page")

    email = (request.POST.get("email") or "").strip()
    pw = request.POST.get("password") or ""

    r = Recruiter.objects.filter(email__iexact=email).first()
    if not r:
        messages.error(request, "No recruiter account found for that email.")
        return redirect(f"{reverse('login_page')}?role=recruiter")

    if not _pw_ok(pw, _get_pw(r)):
        messages.error(request, "Invalid email or password.")
        return redirect(f"{reverse('login_page')}?role=recruiter")

    # set session
    request.session.pop("freelancer_id", None)
    request.session["role"] = "recruiter"
    request.session["recruiter_id"] = r.id
    request.session.modified = True

    return redirect("recruiter_profile_detail")


