from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.utils import IntegrityError
from myapp.models import Freelancer, Recruiter
from .serializers import FreelancerSerializer, RecruiterSerializer
from django.contrib.auth.hashers import check_password
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
