from django.db import models
from django.contrib.auth.models import User


class SubmissionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    ACCEPTED = 'accepted', 'Accepted'
    WRONG_ANSWER = 'wrong_answer', 'Wrong Answer'
    TIME_LIMIT_EXCEEDED = 'tle', 'Time Limit Exceeded'
    RUNTIME_ERROR = 'rte', 'Runtime Error'
    COMPILATION_ERROR = 'ce', 'Compilation Error'
    MEMORY_LIMIT_EXCEEDED = 'mle', 'Memory Limit Exceeded'


class LanguageChoice(models.TextChoices):
    PYTHON = 'py', 'Python'
    CPP = 'cpp', 'C++'
    C = 'c', 'C'
    JAVA = 'java', 'Java'


class Submission(models.Model):
    """A code submission for a problem by a user."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    problem = models.ForeignKey(
        'problems.Problem',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    language = models.CharField(
        max_length=10,
        choices=LanguageChoice.choices
    )
    code = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING
    )
    
    # Execution results
    runtime_ms = models.IntegerField(null=True, blank=True)
    memory_kb = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Test case results
    tests_passed = models.PositiveIntegerField(default=0)
    tests_total = models.PositiveIntegerField(default=0)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    judged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} ({self.get_status_display()})"

    @property
    def is_accepted(self):
        return self.status == SubmissionStatus.ACCEPTED


class SubmissionTestResult(models.Model):
    """Result of running a submission against a single test case."""
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='test_results'
    )
    test_case = models.ForeignKey(
        'problems.TestCase',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices
    )
    actual_output = models.TextField(blank=True)
    runtime_ms = models.IntegerField(null=True, blank=True)
    memory_kb = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['test_case__order']

    def __str__(self):
        return f"{self.submission} - Test {self.test_case.order}: {self.get_status_display()}"


# Keep legacy model for backward compatibility during migration
class CodeSubmission(models.Model):
    """Legacy model - will be deprecated."""
    language = models.CharField(max_length=100)
    code = models.TextField()
    input_data = models.TextField(null=True, blank=True)
    output_data = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Legacy Code Submission"
