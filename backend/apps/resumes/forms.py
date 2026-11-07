from django import forms
from .models import Resume, ResumeEducation, ResumeExperience, ResumeProject


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            'title',
            'target_role',
            'full_name',
            'email',
            'phone',
            'location',
            'linkedin_url',
            'github_url',
            'portfolio_url',
            'professional_summary',
            'skills_raw',
            'template_style',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Engineer Resume'}),
            'target_role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Django Backend Engineer'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+880 17XX-XXXXXX'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dhaka, Bangladesh'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/username'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'professional_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Highlight your core expertise, career motivation, and academic grounding...'
            }),
            'skills_raw': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Python, Django, MySQL, Docker, REST APIs, Git, Problem Solving'
            }),
            'template_style': forms.Select(attrs={'class': 'form-select'}),
        }


class ResumeEducationForm(forms.ModelForm):
    class Meta:
        model = ResumeEducation
        fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'grade']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University / College'}),
            'degree': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Sc.'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Computer Science'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2020'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2024 or Present'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CGPA 3.85 / 4.00'}),
        }


class ResumeExperienceForm(forms.ModelForm):
    class Meta:
        model = ResumeExperience
        fields = ['company', 'position', 'location', 'start_date', 'end_date', 'description']
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dhaka, Bangladesh'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Jun 2023'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dec 2023 or Present'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter bullet points describing your impact and key duties...'
            }),
        }


class ResumeProjectForm(forms.ModelForm):
    class Meta:
        model = ResumeProject
        fields = ['title', 'tech_stack', 'live_link', 'github_link', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'}),
            'tech_stack': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, MySQL, Bootstrap'}),
            'live_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://myproject.live'}),
            'github_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/myrepo'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe problem solved, architecture, and measurable results...'
            }),
        }
