
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import qrcode
from io import BytesIO
from django.core.files import File
import datetime
import secrets




from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType


def default_expiry_time():
    return datetime.now() + timedelta(minutes=2)

@receiver(post_migrate)
def create_school_admin_group(sender, **kwargs):
    # Check if group exists
    group, created = Group.objects.get_or_create(name='School Admin')

    # Assign permissions to the group
    if created:
        content_types = [
            ContentType.objects.get_for_model(Course),
            ContentType.objects.get_for_model(Student),
            ContentType.objects.get_for_model(Teacher),
        ]

        # Assign relevant permissions to the group
        for content_type in content_types:
            permissions = Permission.objects.filter(content_type=content_type)
            group.permissions.add(*permissions)


class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.IntegerField()

    def __str__(self):
        return self.user.username
    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username
class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    students = models.ManyToManyField(Student, blank=True, related_name='courses')
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )  # Teacher can be assigned later

    def __str__(self):
        return f"{self.name} ({self.code})"


    
from datetime import datetime, timedelta

class AttendanceSession(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    secret_key = models.CharField(max_length=100, blank=True)
    expiry_time = models.DateTimeField(default=default_expiry_time)
    is_active = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius = models.IntegerField(default=50)  # Acceptable range in meters
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)  # Change to ImageField
    

    def generate_qr_data(self):
        # Generate a unique session key
        self.secret_key = secrets.token_urlsafe(32)
        self.save()  # Save the session with the secret key
        return f"{self.id}:{self.secret_key}"


class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_valid = models.BooleanField(default=False)

    class Meta:
        unique_together = ['session', 'student']
        
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    for_students = models.BooleanField(default=True)  # Specifies if it's for students

    def __str__(self):
        return self.title


class Query(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

class QueryResponse(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='responses')
    response = models.TextField()
    responded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Calendar(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    for_course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['date']

