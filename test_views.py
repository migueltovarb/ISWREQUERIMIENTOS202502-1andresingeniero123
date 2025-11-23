from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from volunteer_management_app.volunteers.models import Activity, Assignment, Attendance
from django.utils import timezone
import datetime

User = get_user_model()

class VolunteerAppTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create admin user
        self.admin_user = User.objects.create_user(username='adminuser', password='adminpass', role='admin', email='admin@example.com')
        self.admin_user.is_staff = True
        self.admin_user.save()

        # Create volunteer user
        self.volunteer_user = User.objects.create_user(username='volunteeruser', password='volunteerpass', role='volunteer', email='volunteer@example.com')

        # Create an activity by admin
        self.activity = Activity.objects.create(
            title='Test Activity',
            description='Description',
            date=timezone.now() + datetime.timedelta(days=1),
            created_by=self.admin_user
        )

        # Assign volunteer to activity
        self.assignment = Assignment.objects.create(volunteer=self.volunteer_user, activity=self.activity)

    def test_registration_and_login(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'strongPassword123',
            'password2': 'strongPassword123',
            'email': 'newuser@example.com',
            'role': 'volunteer'
        })
        self.assertEqual(response.status_code, 302)

        login_response = self.client.post(reverse('login'), {
            'username': 'newuser',
            'password': 'strongPassword123',
        })
        self.assertEqual(login_response.status_code, 302)

    def test_dashboard_access(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        self.client.login(username='volunteeruser', password='volunteerpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_inscribe_activity(self):
        self.client.login(username='volunteeruser', password='volunteerpass')
        response = self.client.get(reverse('inscribe_activity', args=[self.activity.id]))
        self.assertEqual(response.status_code, 302)

    def test_generate_certificate(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.get(reverse('generate_certificate', args=[self.volunteer_user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_record_attendance(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.post(reverse('record_attendance', args=[self.assignment.id]), {
            'attended': 'on',
            'hours': '4'
        })
        self.assertEqual(response.status_code, 302)
