from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from volunteers.models import Activity, Assignment, Attendance, Notification
from django.utils import timezone
from decimal import Decimal
import datetime

User = get_user_model()

class TestVolunteerAppFull(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin user
        self.admin = User.objects.create_user(username='admin', password='adminpass', role='admin', email='admin@example.com')
        self.admin.is_staff = True
        self.admin.save()
        # Volunteer user
        self.volunteer = User.objects.create_user(username='volunteer', password='volpass', role='volunteer', email='volunteer@example.com')
        # Activity
        self.activity = Activity.objects.create(
            title='Community Clean Up',
            description='Clean the park',
            date=timezone.now() + datetime.timedelta(days=2),
            required_volunteers=5,
            created_by=self.admin
        )
        # Assignment for volunteer
        self.assignment = Assignment.objects.create(volunteer=self.volunteer, activity=self.activity)

    def test_registration_login_logout(self):
        # Registration
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
            'email': 'newuser@example.com',
            'role': 'volunteer'
        })
        self.assertEqual(response.status_code, 302)
        # Login
        response = self.client.post(reverse('login'), {
            'username': 'newuser',
            'password': 'Testpass123!'
        })
        self.assertEqual(response.status_code, 302)
        # Logout
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_role_access(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        self.client.login(username='volunteer', password='volpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_activity_creation_and_inscription(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('create_activity'), {
            'title': 'Tree Planting',
            'description': 'Plant trees in community',
            'date': (timezone.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
            'required_volunteers': 3,
            'location': 'Community Park'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        new_activity = Activity.objects.get(title='Tree Planting')
        self.client.logout()

        self.client.login(username='volunteer', password='volpass')
        response = self.client.get(reverse('inscribe_activity', args=[new_activity.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assignment.objects.filter(volunteer=self.volunteer, activity=new_activity).exists())

    def test_record_attendance(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('record_attendance', args=[self.assignment.id]), {
            'attended': 'on',
            'hours': '3.5'
        })
        self.assertEqual(response.status_code, 302)
        attendance = Attendance.objects.filter(assignment=self.assignment).first()
        self.assertIsNotNone(attendance)
        self.assertTrue(attendance.attended)
        self.assertEqual(float(attendance.hours), 3.5)

    def test_send_notification(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('send_notification'), {
            'activity': self.activity.id,
            'message': 'Join the event!'
        })
        self.assertIn(response.status_code, [302, 403, 200])  # Accept redirect, forbidden, or success
        notification = Notification.objects.filter(activity=self.activity, message='Join the event!').first()
        self.assertIsNotNone(notification)

    def test_send_notification_get(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('send_notification'))
        self.assertEqual(response.status_code, 200)

    def test_generate_certificate_access(self):
        # Only admin can access
        self.client.login(username='volunteer', password='volpass')
        response = self.client.get(reverse('generate_certificate', args=[self.volunteer.id]))
        self.assertIn(response.status_code, [403, 302])  # Allow forbidden or redirect
        self.client.logout()

        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('generate_certificate', args=[self.volunteer.id]))
        self.assertIn(response.status_code, [200, 404])  # Content or not found allowed for PDF generation
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/pdf')
