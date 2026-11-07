from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Education, Experience, UserSkill


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class UserSkillInline(admin.TabularInline):
    model = UserSkill
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password', 'is_staff', 'is_active'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    inlines = [UserProfileInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'city', 'country', 'target_career', 'updated_at')
    search_fields = ('user__email', 'headline', 'target_career')
    inlines = [EducationInline, ExperienceInline, UserSkillInline]


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'profile', 'category', 'proficiency')
    list_filter = ('category', 'proficiency')
    search_fields = ('skill_name', 'profile__user__email')
