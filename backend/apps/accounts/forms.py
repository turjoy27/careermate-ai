from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, UserProfile, Education, Experience, UserSkill


class UserRegistrationForm(forms.ModelForm):
    """Registration form supporting Student and Job Seeker roles."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter strong password (min 8 characters)',
            'autocomplete': 'new-password'
        }),
        min_length=8,
        help_text='Must be at least 8 characters long.'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter password',
            'autocomplete': 'new-password'
        }),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tanvir'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hossain'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Email-based authentication form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').strip().lower()
        password = cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise ValidationError('Invalid email or password. Please try again.')
            elif not self.user_cache.is_active:
                raise ValidationError('This account is currently deactivated.')
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class UserProfileForm(forms.ModelForm):
    """Profile editing form."""
    class Meta:
        model = UserProfile
        fields = [
            'headline',
            'phone',
            'city',
            'country',
            'summary',
            'target_career',
            'linkedin_url',
            'github_url',
            'portfolio_url',
        ]
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Final Year CSE Student | Aspiring Backend Developer'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+880 17XX-XXXXXX'
            }),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dhaka'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bangladesh'}),
            'target_career': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Python Backend Developer, Data Analyst'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief summary of your background, career aspirations, and key strengths...'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourportfolio.dev'
            }),
        }


class EducationForm(forms.ModelForm):
    """Form to add or edit education entries."""
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'is_current', 'grade']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BUET, Dhaka University'}),
            'degree': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Sc. in CSE'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'isCurrentEducation'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CGPA 3.80 / 4.00'}),
        }


class UserSkillForm(forms.ModelForm):
    """Form to add a skill with category and proficiency."""
    class Meta:
        model = UserSkill
        fields = ['skill_name', 'category', 'proficiency']
        widgets = {
            'skill_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Docker, SQL'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'proficiency': forms.Select(attrs={'class': 'form-select'}),
        }
