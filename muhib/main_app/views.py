from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    User, UserProfile, Student, Teacher, 
    AttendanceSession, AttendanceRecord, 
    Announcement, Query, QueryResponse, Calendar,
    Course
)
from .utils import verify_attendance
from datetime import datetime
from django.utils import timezone
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CourseForm
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name']  # Include the fields you want to expose
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Code'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}),
        }


@login_required
@user_passes_test(lambda u: u.groups.filter(name='School Admin').exists())
def admin_dashboard(request):
    # Retrieve data for rendering
    teachers = Teacher.objects.all()
    courses = Course.objects.all()
    students = Student.objects.all()

    # Handle form submission
    if request.method == 'POST':
        course_id = request.POST.get('course')
        teacher_id = request.POST.get('teacher')
        student_id = request.POST.get('student')

        message = None  # Default message for feedback

        # Validate and update teacher assignment
        if course_id and teacher_id:
            try:
                course = Course.objects.get(id=course_id)
                teacher = Teacher.objects.get(id=teacher_id)
                course.teacher = teacher  # Assign teacher to course
                course.save()
                message = "Teacher assigned successfully."
            except (Course.DoesNotExist, Teacher.DoesNotExist):
                message = "Invalid course or teacher."

        # Validate and update student assignment
        if course_id and student_id:
            try:
                course = Course.objects.get(id=course_id)
                student = Student.objects.get(id=student_id)
                course.students.add(student)  # Add student to course
                message = "Student assigned successfully."
            except (Course.DoesNotExist, Student.DoesNotExist):
                message = "Invalid course or student."
            except AttributeError as e:
                message = str(e)

        # Render the page with feedback
        return render(
            request,
            'main_app/admin_dashboard.html',
            {
                'teachers': teachers,
                'courses': courses,
                'students': students,
                'message': message,  # Pass feedback message to the template
            },
        )

    # Initial GET request - render the page
    return render(request, 'main_app/admin_dashboard.html', {
        'teachers': teachers,
        'courses': courses,
        'students': students,
    })



def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            try:
                if user.groups.filter(name='School Admin').exists():
                    login(request, user)
                    return redirect('main_app:admin_dashboard')
                else:
                    return render(request, 'main_app/admin_login.html', {'error': 'You are not authorized as an admin.'})
            except:
                return render(request, 'main_app/admin_login.html', {'error': 'An error occurred. Contact the system administrator.'})
        else:
            return render(request, 'main_app/admin_login.html', {'error': 'Invalid username or password.'})
    return render(request, 'main_app/admin_login.html')

def is_school_admin(user):
    return user.groups.filter(name='School Admin').exists()

@login_required
@user_passes_test(is_school_admin)
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_app:admin_dashboard')
    else:
        form = CourseForm()
    return render(request, 'main_app/add_course.html', {'form': form})





def home(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'student'):
            return redirect('main_app:student_dashboard')
        elif hasattr(request.user, 'teacher'):
            return redirect('main_app:teacher_dashboard')
    return render(request, 'main_app/home.html')

# Authentication Views
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import UserProfile, Student, Teacher

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        user_type = request.POST.get('user_type')
        
        if password1 != password2:
            return render(request, 'main_app/register.html', 
                        {'error': 'Passwords do not match'})
            
        try:
            # Create base user
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password1
            )
            
            # Check if UserProfile exists, if not create one
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.create(
                    user=user,
                    user_type=user_type,
                    phone_number=request.POST.get('phone_number')
                )
            
            # Create specific profile based on user type
            if user_type == 'student':
                student_id = request.POST.get('id_number')
                if Student.objects.filter(student_id=student_id).exists():
                    return render(request, 'main_app/register.html', 
                                {'error': 'Student ID already exists'})
                Student.objects.create(
                    user=user,
                    student_id=student_id,
                    department=request.POST.get('department'),
                    semester=request.POST.get('semester')
                )
                redirect_url = 'main_app:student_dashboard'
            
            elif user_type == 'teacher':
                teacher_id = request.POST.get('tid_number')
                if Teacher.objects.filter(teacher_id=teacher_id).exists():
                    return render(request, 'main_app/register.html', 
                                {'error': 'Teacher ID already exists'})
                Teacher.objects.create(
                    user=user,
                    teacher_id=teacher_id,
                    department=request.POST.get('department'),
                    designation=request.POST.get('designation')
                )
                redirect_url = 'main_app:teacher_dashboard'
            
            login(request, user)
            return redirect(redirect_url)
            
        except Exception as e:
            return render(request, 'main_app/register.html', 
                        {'error': str(e)})
    
    return render(request, 'main_app/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if user.userprofile.user_type == 'student':
                return render(request, 'main_app/student_dashboard.html')
            elif user.userprofile.user_type == 'teacher':
                return redirect('/teacher')
            else:
                return redirect('admin_dashboard')
    return render(request, 'main_app/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('main_app:home')
@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('main_app:home')

    teacher = request.user.teacher

    # Debugging: Log the teacher
    print(f"Logged-in teacher: {teacher.user.username}")

    # Fetch courses assigned to the teacher
    courses = Course.objects.filter(teacher=teacher)

    # Debugging: Log courses
    print(f"Courses assigned to teacher {teacher.user.username}: {courses}")

    active_sessions = AttendanceSession.objects.filter(
        teacher=teacher,
        is_active=True,
        expiry_time__gt=timezone.now()
    )

    latest_session = AttendanceSession.objects.filter(teacher=teacher).order_by('-id').first()
    qr_image_url = latest_session.qr_code.url if latest_session and latest_session.qr_code else None

    return render(request, 'main_app/teacher_dashboard.html', {
        'courses': courses,
        'active_sessions': active_sessions,
        'qr_image_url': qr_image_url,
        'session_id': latest_session.id if latest_session else None,
    })








@login_required
def student_dashboard(request):
    student = request.user.student
    attendance_records = AttendanceRecord.objects.filter(student=student)
    active_sessions = AttendanceSession.objects.filter(
        is_active=True,
        expiry_time__gt=timezone.now(),
    )
    announcements = Announcement.objects.filter(for_students=True).order_by('-created_at')  # Get latest announcements

    context = {
        'attendance_records': attendance_records,
        'active_sessions': active_sessions,
        'announcements': announcements,
    }
    return render(request, 'main_app/student_dashboard.html', context)





# @login_required
# def student_dashboard(request):
#     student = request.user.student

#     # Fetch attendance records for the student
#     attendance_records = AttendanceRecord.objects.filter(student=student)

#     # Fetch active sessions for courses the student is enrolled in
#     active_sessions = AttendanceSession.objects.filter(
#         course__students=student,
#         is_active=True,
#         expiry_time__gt=timezone.now()
#     )

#     # Get the latest active session
#     latest_session = active_sessions.order_by('-id').first()
#     qr_image_url = latest_session.qr_code.url if latest_session and latest_session.qr_code else None

#     context = {
#         'attendance_records': attendance_records,
#         'active_sessions': active_sessions,
#         'qr_image_url': qr_image_url,
#     }
#     return render(request, 'main_app/student_dashboard.html', context)


@login_required
def mark_attendance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = data.get('session_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        session = get_object_or_404(AttendanceSession, id=session_id)
        
        if not session.is_active or session.expiry_time < timezone.now():
            return JsonResponse({'status': 'error', 'message': 'Session expired'})
            
        AttendanceRecord.objects.create(
            session=session,
            student=request.user.student,
            latitude=latitude,
            longitude=longitude,
            is_valid=True
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def calculate_attendance(records):
    total = records.count()
    if total == 0:
        return 0
    present = records.filter(is_present=True).count()
    return (present / total) * 100
# Attendance Views
from datetime import datetime, timedelta


@login_required
@csrf_exempt
def create_attendance_session(request):
    if request.method == 'POST':
        teacher = request.user.teacher
        course_id = request.POST.get('course_id')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        radius = request.POST.get('radius', 50)  # Default radius is 50 meters

        # Create an attendance session
        session = AttendanceSession.objects.create(
            course_id=course_id,
            teacher=teacher,
            latitude=latitude,
            longitude=longitude,
            radius=radius
        )

        # Generate QR data
        qr_data = session.generate_qr_data()

        # Generate QR Code image
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        # Save QR code image
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        session.qr_code.save(f"session_{session.id}.png", ContentFile(buffer.read()), save=True)
        return redirect('main_app:teacher_dashboard')

        # return JsonResponse({
        #     'status': 'success',
        #     'session_id': session.id,
        #     'qr_data': qr_data,
        #     'qr_image_url': session.qr_code.url  # URL to access the saved QR image
        # })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def make_announcement(request):
    if request.method == 'POST':
        teacher = request.user.teacher
        title = request.POST.get('title')
        content = request.POST.get('content')

        # Save the announcement
        Announcement.objects.create(
            title=title,
            content=content,
            created_by=teacher,
            for_students=True  # Announcements are meant for students
        )
        return redirect('main_app:teacher_dashboard')





@login_required
@csrf_exempt
def mark_attendance(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        student = request.user.student
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
            is_valid, message = verify_attendance(session, latitude, longitude)
            
            if is_valid:
                AttendanceRecord.objects.create(
                    session=session,
                    student=student,
                    latitude=latitude,
                    longitude=longitude,
                    is_valid=True
                )
                return JsonResponse({'status': 'success'})
            
            return JsonResponse({'status': 'error', 'message': message})
            
        except AttendanceSession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid session'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
