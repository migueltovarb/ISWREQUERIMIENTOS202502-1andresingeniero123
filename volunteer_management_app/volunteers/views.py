from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from .models import CustomUser, Activity, Assignment, Attendance, Notification
from .forms import CustomUserCreationForm, ActivityForm, CustomAuthenticationForm, NotificationForm
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import logging
from django.http import HttpResponseForbidden, HttpResponse, Http404
from django.db.models import Sum
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import FileResponse
import io
from django.template.loader import render_to_string
import tempfile
import os
from django.contrib.auth.decorators import login_required, user_passes_test

logger = logging.getLogger(__name__)

@login_required
def send_notification(request):
    logger.debug(f"send_notification accessed by user: {request.user.username} with role: {getattr(request.user, 'role', None)} and method: {request.method}")
    if request.user.role.lower() != 'admin':
        logger.warning(f"Access denied to send_notification for user: {request.user.username} with role: {request.user.role}")
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.save()
            # Get volunteers assigned to the activity
            volunteers = CustomUser.objects.filter(role='volunteer', assignments__activity=notification.activity).distinct()
            notification.recipients.set(volunteers)
            # Send email notifications
            subject = f'Notificación para la actividad: {notification.activity.title}'
            message = notification.message
            from_email = 'noreply@example.com'
            recipient_list = [v.email for v in volunteers if v.email]
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'Notificación enviada exitosamente.')
            except BadHeaderError:
                messages.error(request, 'Error al enviar el correo electrónico debido a un encabezado inválido. Por favor, revise el mensaje por posibles caracteres inválidos.')
                logger.error('BadHeaderError al enviar correo en send_notification.')
            except Exception as e:
                messages.error(request, f'Error al enviar el correo electrónico: {str(e)}')
                logger.error(f'Error al enviar correo en send_notification: {str(e)}')
            return redirect('send_notification')
        else:
            logger.error(f"Form invalid in send_notification for user: {request.user.username}. Errors: {form.errors}")
    else:
        form = NotificationForm()
    return render(request, 'volunteers/send_notification.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.username.lower() == 'andres')
def volunteer_activity_history(request):
    # Get attendance records with related assignment, volunteer, and activity details
    attendance_records = Attendance.objects.select_related(
        'assignment__volunteer',
        'assignment__activity'
    ).order_by('-recorded_at')

    context = {
        'attendance_records': attendance_records,
    }
    return render(request, 'volunteers/volunteer_activity_history.html', context)

@login_required
def admin_volunteer_list(request):
    if not request.user.role.lower() == 'admin':
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    volunteers = CustomUser.objects.filter(role__iexact='volunteer')
    return render(request, 'volunteers/admin_volunteer_list.html', {'volunteers': volunteers})

@login_required
def admin_volunteer_dashboard(request):
    if not request.user.role.lower() == 'admin':
        return HttpResponseForbidden("No tienes permiso para ver esta página.")

    # Aggregate total hours per volunteer
    volunteers_hours = (
        CustomUser.objects.filter(role__iexact='volunteer')
        .annotate(total_hours=Sum('assignments__attendance__hours'))
        .order_by('-total_hours')
    )

    selected_volunteer_id = request.GET.get('volunteer_id')
    selected_volunteer = None
    if selected_volunteer_id:
        try:
            selected_volunteer = CustomUser.objects.get(id=selected_volunteer_id, role__iexact='volunteer')
        except CustomUser.DoesNotExist:
            selected_volunteer = None

    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.save()
            # Set recipients to selected volunteers related to the notification's activity
            volunteers = CustomUser.objects.filter(role='volunteer', assignments__activity=notification.activity).distinct()
            notification.recipients.set(volunteers)
            subject = f'Notificación para la actividad: {notification.activity.title}'
            message = notification.message
            from_email = 'noreply@example.com'
            recipient_list = [v.email for v in volunteers if v.email]
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'Notificación enviada exitosamente.')
            except BadHeaderError:
                messages.error(request, 'Error al enviar el correo electrónico debido a un encabezado inválido. Por favor, revise el mensaje para caracteres inválidos.')
                logger.error('BadHeaderError al enviar correo en admin_volunteer_dashboard.')
            except Exception as e:
                messages.error(request, f'Error al enviar el correo electrónico: {str(e)}')
                logger.error(f'Error al enviar correo en admin_volunteer_dashboard: {str(e)}')
            return redirect('admin_volunteer_dashboard')
    else:
        form = NotificationForm()

    context = {
        'volunteers_hours': volunteers_hours,
        'form': form,
        'selected_volunteer': selected_volunteer,
    }
    return render(request, 'volunteers/admin_volunteer_dashboard.html', context)

@login_required
def admin_volunteer_profile(request, volunteer_id):
    if not request.user.role.lower() == 'admin':
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    try:
        volunteer = CustomUser.objects.get(id=volunteer_id, role__iexact='volunteer')
    except CustomUser.DoesNotExist:
        raise Http404("Voluntario no encontrado.")
    return render(request, 'volunteers/admin_volunteer_profile.html', {'volunteer': volunteer})

@login_required
def admin_certificate_eligibility(request):
    user_role = getattr(request.user, 'role', '').strip().lower()
    if user_role != 'admin':
        logging.warning(f"Access denied to admin_certificate_eligibility for user {request.user.username} with role '{user_role}'")
        return HttpResponseForbidden("No tienes permiso para ver esta página.")

    # Aggregate total hours by volunteer with 2 hours threshold
    min_hours = 2
    volunteers_hours = (
        CustomUser.objects.filter(role__iexact='volunteer')
        .annotate(total_hours=Sum('assignments__attendance__hours'))
        .filter(total_hours__gte=min_hours)
        .order_by('-total_hours')
    )

    context = {
        'volunteers_hours': volunteers_hours,
        'min_hours_required': min_hours,
    }
    return render(request, 'volunteers/admin_certificate_eligibility.html', context)

@login_required
def generate_certificate(request, volunteer_id):
    logger.debug(f"generate_certificate accessed by user: {request.user.username} with role: {getattr(request.user, 'role', None)} for volunteer_id: {volunteer_id}")
    if not request.user.role.lower() == 'admin':
        logger.warning(f"Access denied to generate_certificate for user: {request.user.username} with role: {request.user.role}")
        return HttpResponseForbidden("No tienes permiso para generar certificados.")
    try:
        volunteer = CustomUser.objects.get(id=volunteer_id, role__iexact='volunteer')
    except CustomUser.DoesNotExist:
        logger.error(f"Volunteer with id {volunteer_id} not found in generate_certificate.")
        return HttpResponse("Voluntario no encontrado.", status=404)

    try:
        total_hours = (
            Attendance.objects.filter(assignment__volunteer=volunteer, attended=True)
            .aggregate(total_hours=Sum('hours'))
            .get('total_hours') or 0
        )
    except Exception as e:
        logger.error(f"Error calculating total hours for volunteer {volunteer_id}: {e}")
        return HttpResponse(f"Error al calcular horas: {str(e)}", status=500)

    # Create PDF using ReportLab
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width / 2.0, height - 100, "Certificado de Voluntariado")

    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2.0, height - 150, f"Este certificado se otorga a {volunteer.get_full_name() or volunteer.username}")

    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2.0, height - 180, f"Por haber completado {total_hours} horas de voluntariado.")

    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2.0, height - 210, "Gracias por tu valiosa contribución y compromiso.")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename=f"certificate_{volunteer.username}.pdf")

def home(request):
    activities = Activity.objects.filter(date__gte=timezone.now()).order_by('date')
    assigned_activity_ids = []
    if request.user.is_authenticated:
        assigned_activity_ids = list(request.user.assignments.values_list('activity_id', flat=True))
    return render(request, 'volunteers/home.html', {'activities': activities, 'assigned_activity_ids': assigned_activity_ids})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro exitoso.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'volunteers/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None and user.is_active:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Cuenta inactiva o inválida.')
                logger.warning(f"Inactive or invalid account login attempt for username: {request.POST.get('username')}")
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            logger.warning(f"Login failed for username: {request.POST.get('username')} with errors: {form.errors.as_json()}")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'volunteers/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    assigned_activity_ids = list(user.assignments.values_list('activity_id', flat=True))
    if user.role.lower() == 'admin':
        activities = Activity.objects.filter(created_by=user)
        assignments = Assignment.objects.filter(activity__created_by=user)
    else:
        assignments = Assignment.objects.filter(volunteer=user)
        activities = Activity.objects.all()
    return render(request, 'volunteers/dashboard.html', {
        'activities': activities,
        'assignments': assignments,
        'assigned_activity_ids': assigned_activity_ids,
    })

@login_required
def create_activity(request):
    if request.user.role.lower() != 'admin':
        return redirect('dashboard')
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.created_by = request.user
            try:
                activity.save()
                messages.success(request, 'Actividad creada exitosamente.')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, 'Error al crear la actividad: ' + str(e))
                logger.error(f'Error saving activity: {e}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ActivityForm()
    return render(request, 'volunteers/create_activity.html', {'form': form})

@login_required
def inscribe_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if request.user.role.lower() != 'volunteer':
        return redirect('dashboard')
    try:
        assignment, created = Assignment.objects.get_or_create(volunteer=request.user, activity=activity)
        if created:
            messages.success(request, 'Inscrito exitosamente.')
            # Send email notification with error handling
            try:
                send_mail(
                    'Confirmación de Inscripción',
                    f'Has sido inscrito en {activity.title}.',
                    'noreply@example.com',
                    [request.user.email],
                )
            except BadHeaderError:
                messages.error(request, 'Se produjo un error al enviar el correo electrónico.')
                logger.error('BadHeaderError occurred while sending email for inscribe_activity.')
            except Exception as e:
                messages.error(request, 'No se pudo enviar el correo electrónico: ' + str(e))
                logger.error(f'Error sending email: {e}')
        else:
            messages.info(request, 'Ya inscrito.')
    except Exception as e:
        messages.error(request, 'Error al inscribirse: ' + str(e))
        logger.error(f'Error in inscribe_activity: {e}')
    return redirect('dashboard')

@login_required
def record_attendance(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if request.user.role.lower() != 'admin' or assignment.activity.created_by != request.user:
        return redirect('dashboard')
    if request.method == 'POST':
        if Attendance.objects.filter(assignment=assignment).exists():
            messages.info(request, 'Asistencia ya registrada.')
            return redirect('dashboard')
        attended = request.POST.get('attended') == 'on'
        hours_input = request.POST.get('hours', '0')
        try:
            hours = Decimal(hours_input)
            if hours < 0:
                raise InvalidOperation("Horas no pueden ser negativas.")
        except (InvalidOperation, ValueError) as e:
            messages.error(request, 'Entrada inválida para horas: ' + str(e))
            return render(request, 'volunteers/record_attendance.html', {'assignment': assignment})
        try:
            Attendance.objects.create(assignment=assignment, attended=attended, hours=hours)
            messages.success(request, 'Asistencia registrada.')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, 'Error al registrar asistencia: ' + str(e))
            logger.error(f'Error in record_attendance: {e}')
    return render(request, 'volunteers/record_attendance.html', {'assignment': assignment})
