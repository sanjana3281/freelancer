# resume_ai/urls.py
from django.urls import path
from .views import resume_suggest_view

app_name = "resume_ai"
urlpatterns = [ path("suggest/", resume_suggest_view, name="suggest") ]
