from django.urls import path
from . import views
from myapp import views as app_views


urlpatterns = [

    # Freelancer-only pages
    path("login/", views.login_page, name="login_page"),
    path("freelancer/dashboard/", views.freelancer_dashboard, name="freelancer_dashboard"),
    
    path("login/submit/", views.freelancer_login, name="freelancer_login_submit"), # POST
    path("freelancer/dashboard/", views.freelancer_dashboard, name="freelancer_dashboard"),
    path("freelancer/profile/edit/", views.freelancer_profile_edit, name="freelancer_profile_edit"),
    path("recruiter/profile/", app_views.recruiter_profile_detail, name="recruiter_profile_detail"),
    path("recruiter/profile/edit/", app_views.recruiter_profile_edit, name="recruiter_profile_edit"),
    # recruiter job CRUD
    path("recruiter/jobs/new/", views.job_create_view, name="job_create"),
    path("recruiter/jobs/", views.my_jobs_view, name="my_jobs"),
    path("recruiter/jobs/<int:job_id>/edit/", views.job_edit_view, name="job_edit"),
    path("recruiter/jobs/<int:job_id>/toggle/", views.job_toggle_active_view, name="job_toggle_active"),

    # public/freelancer
    path("jobs/", views.jobs_list_view, name="jobs_list"),
    path("jobs/<int:job_id>/", views.job_detail_view, name="job_detail"),
    path("jobs/<int:job_id>/apply/", views.job_apply_view, name="job_apply"),
    path("whoami/", views.whoami, name="whoami"),
    path("logout/", views.logout_view, name="logout"),
    

    path("recruiter/jobs/<int:job_id>/applications/",
         views.job_applications_view, name="job_applications"),
    path("recruiter/applications/<int:app_id>/",
         views.job_application_detail_view, name="job_application_detail"),
    path("recruiter/freelancers/<int:profile_id>/",
         views.recruiter_view_freelancer_profile, name="recruiter_view_freelancer_profile"),


    #communication
    path("recruiter/jobs/<int:job_id>/shortlist/<int:profile_id>/",
         views.flow_recruiter_shortlist, name="flow_recruiter_shortlist"),
    path("recruiter/applications/<int:app_id>/interview/",
         views.flow_recruiter_schedule_interview, name="flow_recruiter_schedule_interview"),
    path("recruiter/applications/<int:app_id>/outcome/<str:decision>/",
         views.flow_recruiter_set_outcome, name="flow_recruiter_set_outcome"),  # decision = hire|reject

    # Freelancer
    path("freelancer/applications/<int:app_id>/respond/<str:decision>/",
         views.flow_freelancer_respond, name="flow_freelancer_respond"),  # decision = accept|decline

    path("flow/shortlist/<int:app_id>/", views.flow_recruiter_shortlist, name="flow_recruiter_shortlist"),
    path("flow/schedule/<int:app_id>/", views.flow_recruiter_schedule_interview, name="flow_recruiter_schedule_interview"),
    path("flow/outcome/<int:app_id>/<str:decision>/", views.flow_recruiter_set_outcome, name="flow_recruiter_set_outcome"),

    #for email and notifications
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),
    path("settings/job-email-toggle/", views.toggle_job_email_notifications, name="toggle_job_email_notifications"),
    path("notifications/mark-all-read/", views.notifications_mark_all_read, name="notifications_mark_all_read"),
    path("notifications/<int:pk>/open/", views.notification_open, name="notification_open"),


]


    



