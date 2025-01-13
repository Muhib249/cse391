from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'teacher']  # Include only the fields you want to display in the form
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Code'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }
