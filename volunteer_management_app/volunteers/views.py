from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from .models import CustomUser, Activity, Assignment, Attendance
from .forms import CustomUserCreationForm, ActivityForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

def home(request):
    activities = Activity.objects.filter(date__gte=timezone.now()).order_by('date')
    return render(request, 'volunteers/home.html', {'activities': activities})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'volunteers/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'volunteers/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'admin':
        activities = Activity.objects.filter(created_by=user)
        assignments = Assignment.objects.filter(activity__created_by=user)
    else:
        assignments = Assignment.objects.filter(volunteer=user)
        activities = Activity.objects.all()
    return render(request, 'volunteers/dashboard.html', {
        'activities': activities,
        'assignments': assignments,
    })

@login_required
def create_activity(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.created_by = request.user
            activity.save()
            messages.success(request, 'Activity created successfully.')
            return redirect('dashboard')
    else:
        form = ActivityForm()
    return render(request, 'volunteers/create_activity.html', {'form': form})

@login_required
def inscribe_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if request.user.role != 'volunteer':
        return redirect('dashboard')
    assignment, created = Assignment.objects.get_or_create(volunteer=request.user, activity=activity)
    if created:
        messages.success(request, 'Inscribed successfully.')
        # Send email notification
        send_mail(
            'Inscription Confirmation',
            f'You have been inscribed in {activity.title}.',
            'noreply@example.com',
            [request.user.email],
        )
    else:
        messages.info(request, 'Already inscribed.')
    return redirect('dashboard')

@login_required
def record_attendance(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if request.user.role != 'admin' or assignment.activity.created_by != request.user:
        return redirect('dashboard')
    if request.method == 'POST':
        attended = request.POST.get('attended') == 'on'
        hours = request.POST.get('hours', 0)
        Attendance.objects.create(assignment=assignment, attended=attended, hours=hours)
        messages.success(request, 'Attendance recorded.')
        return redirect('dashboard')
    return render(request, 'volunteers/record_attendance.html', {'assignment': assignment})
