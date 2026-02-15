
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import encrypt_password

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    force_password_change = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()

class GolfCourse(models.Model):
    LOGIC_CHOICES = [
        ('foreup', 'ForeUp Software'),
        ('foreup_new', 'ForeUp New Layout'),
        ('cps', 'CPS Golf (Capital Hills/Old Post)'),
        ('frear', 'Frear Park Custom'),
        ('schenectady', 'Schenectady Muni'),
    ]
    
    name = models.CharField(max_length=100)
    url = models.URLField()
    logic_type = models.CharField(max_length=20, choices=LOGIC_CHOICES)
    public_btn_xpath = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class UserCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(GolfCourse, on_delete=models.CASCADE)
    course_email = models.EmailField()
    encrypted_password = models.CharField(max_length=500)

    def set_password(self, raw_password):
        self.encrypted_password = encrypt_password(raw_password)

    class Meta:
        unique_together = ('user', 'course')

class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(GolfCourse, on_delete=models.CASCADE)
    
    desired_date = models.DateField()
    earliest_time = models.TimeField()
    latest_time = models.TimeField()
    players = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])
    
    execution_time = models.DateTimeField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    result_log = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course} - {self.desired_date} ({self.status})"
