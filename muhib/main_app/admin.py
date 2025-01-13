from django.contrib import admin

# Register your models here.
from .models import UserProfile, Student, Teacher, Course, AttendanceSession
admin.site.register(UserProfile)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Course)
admin.site.register(AttendanceSession)
