from django.urls import path
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('attendance/create/', views.create_attendance_session, name='create_attendance'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/verify/', views.verify_attendance, name='verify_attendance'),
    path('create-session/', views.create_attendance_session, name='create_session'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin/add-course/', views.add_course, name='add_course'),
    path('make-announcement/', views.make_announcement, name='make_announcement'),

    

]


