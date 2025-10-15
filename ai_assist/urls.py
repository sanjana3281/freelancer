# ai_assist/urls.py
from django.urls import path
from . import views
from . import views_chat
app_name = "ai"  # <- add this so you can reverse with 'ai:...'

urlpatterns = [
    # path("analyze.json",        views.ai_analyze_json,     name="ai_analyze_profile"),
    path("resume.json",         views.ai_resume_json,      name="ai_generate_resume"),  # <-- UNCOMMENTED
    # Human page (GET) – useful to test and copy the markdown
    path("resume/",             views.ai_resume_page,      name="ai_resume_page"),
    path("resume/download-md/", views.ai_resume_download_md, name="ai_resume_download_md"),
    # path("resume/print/",       views.ai_resume_print,       name="ai_resume_print"),
    path("resume/builder/", views.resume_builder,    name="resume_builder"),
    path("resume/print/",   views.ai_resume_print,   name="ai_resume_print"),
    path("resume/form/", views.resume_form, name="resume_form"),
    path("resume/preview/", views.ai_resume_preview,  name="ai_resume_preview"),
    # path("resume/analysis/", views.resume_analysis_view, name="resume_analysis"),
    # path("resume/analysis.json", views.resume_analysis_json, name="resume_analysis_json"),      # GET page
    # path("resume/analyze-profile/", views.ai_analyze_profile, name="ai_analyze_profile"),  # POST ajax
    # path("resume/generate-resume/", views.ai_generate_resume, name="ai_generate_resume"),  # POST ajax
    # path("resume/preview/", views.ai_resume_preview, name="ai_resume_preview"),  
    path("resume/chat/", views_chat.resume_chat_page, name="resume_chat"),
    path("resume/chat/reply/", views_chat.resume_chat_reply, name="resume_chat_reply"),
    path("resume/analysis/", views_chat.resume_analysis, name="resume_analysis"),
    path("resume/upload-analysis/", views.ai_analyze_uploaded_resume, name="ai_analyze_uploaded_resume"),

]

