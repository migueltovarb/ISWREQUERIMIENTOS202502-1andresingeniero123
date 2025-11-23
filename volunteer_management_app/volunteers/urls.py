from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/volunteers/', views.admin_volunteer_dashboard, name='admin_volunteer_dashboard'),
    path('create_activity/', views.create_activity, name='create_activity'),
    path('inscribe/<int:activity_id>/', views.inscribe_activity, name='inscribe_activity'),
    path('record_attendance/<int:assignment_id>/', views.record_attendance, name='record_attendance'),
    path('activity-history/', views.volunteer_activity_history, name='volunteer_activity_history'),
    path('admin/volunteers/list/', views.admin_volunteer_list, name='admin_volunteer_list'),
    path('admin/volunteer/<int:volunteer_id>/', views.admin_volunteer_profile, name='admin_volunteer_profile'),
    path('admin/certificates/', views.admin_certificate_eligibility, name='admin_certificate_eligibility'),
    path('admin/certificate/<int:volunteer_id>/', views.generate_certificate, name='generate_certificate'),
    path('admin/send_notification/', views.send_notification, name='send_notification'),
]
