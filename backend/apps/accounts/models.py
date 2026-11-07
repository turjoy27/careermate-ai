from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Primary User model using email as unique identifier."""

    ROLE_CHOICES = (
        ('student', 'University Student'),
        ('jobseeker', 'Job Seeker / Fresh Graduate'),
        ('admin', 'Platform Administrator'),
    )

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.email


class UserProfile(models.Model):
    """Detailed profile data for career assistance."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    headline = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=100, blank=True, default='Dhaka')
    country = models.CharField(max_length=100, blank=True, default='Bangladesh')
    summary = models.TextField(blank=True)
    target_career = models.CharField(max_length=200, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.email}'s Profile"


class Education(models.Model):
    """Academic background records."""

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    grade = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Education'
        verbose_name_plural = 'Educations'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class Experience(models.Model):
    """Work and internship experience records."""

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Experience'
        verbose_name_plural = 'Experiences'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} at {self.company}"


class UserSkill(models.Model):
    """Skills categorized for AI matching and gap analysis."""

    CATEGORY_CHOICES = (
        ('technical', 'Technical Skill'),
        ('soft', 'Soft Skill'),
        ('tool', 'Tool / Framework'),
        ('language', 'Language'),
    )

    PROFICIENCY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    )

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='technical')
    proficiency = models.CharField(max_length=30, choices=PROFICIENCY_CHOICES, default='intermediate')

    class Meta:
        verbose_name = 'User Skill'
        verbose_name_plural = 'User Skills'
        unique_together = ('profile', 'skill_name')

    def __str__(self):
        return f"{self.skill_name} ({self.proficiency})"
