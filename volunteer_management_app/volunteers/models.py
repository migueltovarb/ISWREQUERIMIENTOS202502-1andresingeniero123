from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('volunteer', 'Volunteer'),
        ('admin', 'Administrator'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='volunteer')
    document_id = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)
    areas_of_interest = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

class Activity(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    required_volunteers = models.PositiveIntegerField()
    profile_needed = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})

    def __str__(self):
        return self.title

class Assignment(models.Model):
    volunteer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'volunteer'}, related_name='assignments')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('assigned', 'Assigned'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='assigned')

    class Meta:
        unique_together = ('volunteer', 'activity')

class Attendance(models.Model):
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    recipients = models.ManyToManyField(CustomUser, limit_choices_to={'role': 'volunteer'})

    def __str__(self):
        return f'Notification for {self.activity.title} at {self.created_at.strftime("%Y-%m-%d %H:%M")}'
