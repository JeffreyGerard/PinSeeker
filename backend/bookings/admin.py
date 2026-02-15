
from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import GolfCourse, UserCredential, BookingRequest, UserProfile
from .utils import encrypt_password

# --- Inline Profile for User Admin ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend User Admin to show Profile
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# --- Custom Form for Credentials ---
class UserCredentialForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput, 
        required=False, 
        help_text="Enter a new password to update credentials. Leave blank to keep current."
    )
    
    class Meta:
        model = UserCredential
        fields = ['user', 'course', 'course_email', 'password']

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_password = self.cleaned_data.get('password')
        if raw_password:
            instance.encrypted_password = encrypt_password(raw_password)
        if commit:
            instance.save()
        return instance

# --- Admin Registrations ---

@admin.register(GolfCourse)
class GolfCourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'logic_type', 'url')
    search_fields = ('name',)

@admin.register(UserCredential)
class UserCredentialAdmin(admin.ModelAdmin):
    form = UserCredentialForm
    list_display = ('user', 'course', 'course_email')
    list_filter = ('course',)
    search_fields = ('user__username', 'course_email')
    readonly_fields = ('encrypted_password',) 

@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'desired_date', 'status', 'created_at')
    list_filter = ('status', 'course', 'desired_date')
    search_fields = ('user__username', 'course__name')
