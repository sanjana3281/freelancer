from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from myapp.models import Freelancer, Recruiter

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
