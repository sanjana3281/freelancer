from django.urls import path
from . import views
from .views import MyRecruiterProfileView


app_name = 'api' 

urlpatterns = [
    # freelancers
    path('freelancers/', views.freelancers_list, name='freelancers-list'),
    path('freelancers/register', views.freelancers_register, name='freelancers-register'),
    path('freelancers/login', views.freelancers_login),
    # recruiters
    path('recruiters/', views.recruiters_list, name='recruiters-list'),
    path('recruiters/register', views.recruiters_register, name='recruiters-register'),
    path("recruiter/login/", views.recruiters_login, name="recruiter_login"),
    path("recruiter/login/submit/", views.recruiter_login_submit, name="recruiter_login_submit"),
    path("freelancer/login/submit/", views.freelancer_login_submit, name="freelancer_login_submit"),
    path("recruiter/profile/", MyRecruiterProfileView.as_view(), name="api_my_recruiter_profile"),

]
