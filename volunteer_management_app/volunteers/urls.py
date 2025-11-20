from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create_activity/', views.create_activity, name='create_activity'),
    path('inscribe/<int:activity_id>/', views.inscribe_activity, name='inscribe_activity'),
    path('record_attendance/<int:assignment_id>/', views.record_attendance, name='record_attendance'),
]
