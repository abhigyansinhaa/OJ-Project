from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tag(models.Model):
    """Category/topic tags for problems (e.g., Arrays, Strings, DP)."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Problem(models.Model):
    """A programming problem with metadata and test cases."""
    
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(help_text="Problem statement in Markdown")
    input_format = models.TextField(blank=True, help_text="Description of input format")
    output_format = models.TextField(blank=True, help_text="Description of output format")
    constraints = models.TextField(blank=True, help_text="Problem constraints")
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.EASY
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='problems')
    time_limit = models.FloatField(default=2.0, help_text="Time limit in seconds")
    memory_limit = models.IntegerField(default=256, help_text="Memory limit in MB")
    
    # Statistics
    solve_count = models.PositiveIntegerField(default=0)
    attempt_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['difficulty', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

    @property
    def acceptance_rate(self):
        if self.attempt_count == 0:
            return 0
        return round((self.solve_count / self.attempt_count) * 100, 1)


class TestCase(models.Model):
    """Input/output test case for a problem."""
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='test_cases'
    )
    input_data = models.TextField(help_text="Test input")
    expected_output = models.TextField(help_text="Expected output")
    is_sample = models.BooleanField(
        default=False,
        help_text="Sample test cases are shown to users"
    )
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(
        blank=True,
        help_text="Explanation for sample test cases"
    )

    class Meta:
        ordering = ['problem', 'order']

    def __str__(self):
        case_type = "Sample" if self.is_sample else "Hidden"
        return f"{self.problem.title} - {case_type} Case {self.order}"
