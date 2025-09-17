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
