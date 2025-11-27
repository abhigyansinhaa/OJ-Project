from django.contrib import admin
from .models import Problem, TestCase, Tag


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1
    fields = ['order', 'is_sample', 'input_data', 'expected_output', 'explanation']
    ordering = ['order']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'problem_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def problem_count(self, obj):
        return obj.problems.count()
    problem_count.short_description = 'Problems'


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'time_limit', 'solve_count', 'attempt_count', 'is_active', 'created_at']
    list_filter = ['difficulty', 'is_active', 'tags']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    inlines = [TestCaseInline]
    readonly_fields = ['solve_count', 'attempt_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'difficulty', 'tags', 'is_active')
        }),
        ('Problem Statement', {
            'fields': ('description', 'input_format', 'output_format', 'constraints')
        }),
        ('Limits', {
            'fields': ('time_limit', 'memory_limit')
        }),
        ('Statistics', {
            'fields': ('solve_count', 'attempt_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['problem', 'order', 'is_sample']
    list_filter = ['problem', 'is_sample']
    search_fields = ['problem__title']
    ordering = ['problem', 'order']
