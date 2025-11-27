from django.contrib import admin
from .models import Submission, SubmissionTestResult, CodeSubmission


class SubmissionTestResultInline(admin.TabularInline):
    model = SubmissionTestResult
    extra = 0
    readonly_fields = ['test_case', 'status', 'actual_output', 'runtime_ms', 'memory_kb', 'error_message']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'problem', 'language', 'status', 'tests_passed', 'tests_total', 'runtime_ms', 'submitted_at']
    list_filter = ['status', 'language', 'problem']
    search_fields = ['user__username', 'problem__title']
    readonly_fields = ['user', 'problem', 'language', 'code', 'status', 'runtime_ms', 'memory_kb', 
                       'error_message', 'tests_passed', 'tests_total', 'submitted_at', 'judged_at']
    inlines = [SubmissionTestResultInline]
    date_hierarchy = 'submitted_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SubmissionTestResult)
class SubmissionTestResultAdmin(admin.ModelAdmin):
    list_display = ['submission', 'test_case', 'status', 'runtime_ms']
    list_filter = ['status']
    readonly_fields = ['submission', 'test_case', 'status', 'actual_output', 'runtime_ms', 'memory_kb', 'error_message']


# Legacy model admin
@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'timestamp']
    list_filter = ['language']
    readonly_fields = ['language', 'code', 'input_data', 'output_data', 'timestamp']
