from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.urls import reverse

from submit.models import Submission, SubmissionTestResult, SubmissionStatus, LanguageChoice
from submit.services.executor import execute_submission
from problems.models import Problem


@login_required
def submit_solution(request, slug):
    """Handle code submission for a problem."""
    problem = get_object_or_404(Problem, slug=slug, is_active=True)
    
    if request.method == 'POST':
        language = request.POST.get('language')
        code = request.POST.get('code', '').strip()
        
        # Validate inputs
        if not language or language not in dict(LanguageChoice.choices):
            messages.error(request, 'Please select a valid programming language.')
            return redirect('problems:problem_detail', slug=slug)
        
        if not code:
            messages.error(request, 'Please provide your solution code.')
            return redirect('problems:problem_detail', slug=slug)
        
        # Create submission
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=language,
            code=code,
            status=SubmissionStatus.PENDING
        )
        
        # Execute the submission (synchronous for now, can be made async later)
        execute_submission(submission.id)
        
        # Redirect to result page
        return redirect('submit:submission_detail', pk=submission.id)
    
    return redirect('problems:problem_detail', slug=slug)


class SubmissionDetailView(LoginRequiredMixin, DetailView):
    """Display submission result with test case details."""
    model = Submission
    template_name = 'submit/result.html'
    context_object_name = 'submission'

    def get_queryset(self):
        # Users can only view their own submissions
        return Submission.objects.filter(user=self.request.user).select_related(
            'problem', 'user'
        ).prefetch_related('test_results__test_case')


class SubmissionHistoryView(LoginRequiredMixin, ListView):
    """Display user's submission history."""
    model = Submission
    template_name = 'submit/history.html'
    context_object_name = 'submissions'
    paginate_by = 20

    def get_queryset(self):
        queryset = Submission.objects.filter(
            user=self.request.user
        ).select_related('problem').order_by('-submitted_at')
        
        # Filter by problem
        problem_slug = self.request.GET.get('problem')
        if problem_slug:
            queryset = queryset.filter(problem__slug=problem_slug)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status in dict(SubmissionStatus.choices):
            queryset = queryset.filter(status=status)
        
        # Filter by language
        language = self.request.GET.get('language')
        if language and language in dict(LanguageChoice.choices):
            queryset = queryset.filter(language=language)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = SubmissionStatus.choices
        context['language_choices'] = LanguageChoice.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['current_language'] = self.request.GET.get('language', '')
        context['current_problem'] = self.request.GET.get('problem', '')
        
        # Get user's problems for filter dropdown
        context['user_problems'] = Problem.objects.filter(
            submissions__user=self.request.user
        ).distinct()
        
        return context


# Legacy view for backward compatibility
def submit(request):
    """Legacy submission view - redirects to problems list."""
    messages.info(request, 'Please select a problem to submit your solution.')
    return redirect('problems:problem_list')
