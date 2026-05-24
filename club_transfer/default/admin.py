from django.contrib import admin

from .models import User, Club, TransferApplication, ApprovalLog, SystemSettings, Student, Superviser


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'email')
    search_fields = ('name', 'username', 'email')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'class_number', 'role')
    search_fields = ('student_id', 'user__name')


@admin.register(Superviser)
class SuperviserAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'user', 'role')
    search_fields = ('teacher_id', 'user__name')


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('club_name', 'max_capacity', 'current_members', 'president', 'teacher')
    search_fields = ('club_name',)


@admin.register(TransferApplication)
class TransferApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'original_club', 'new_club', 'status', 'is_original_club_approved', 'created_at')
    list_filter = ('status', 'is_original_club_approved')


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'reviewer', 'action', 'created_at')
    list_filter = ('action',)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('transfer_start_date', 'transfer_end_date')
