from django.urls import path
from . import views

app_name = 'api' 

urlpatterns = [
    # freelancers
    path('freelancers/', views.freelancers_list, name='freelancers-list'),
    path('freelancers/register', views.freelancers_register, name='freelancers-register'),
    path('freelancers/login', views.freelancers_login),
    # recruiters
    path('recruiters/', views.recruiters_list, name='recruiters-list'),
    path('recruiters/register', views.recruiters_register, name='recruiters-register'),
    path('recruiters/login', views.recruiters_login),
]
