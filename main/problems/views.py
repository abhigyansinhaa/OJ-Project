from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Prefetch
from .models import Problem, TestCase, Tag
from submit.models import Submission, SubmissionStatus


class ProblemListView(ListView):
    """List all active problems with filtering and user solve status."""
    model = Problem
    template_name = 'problems/problem_list.html'
    context_object_name = 'problems'
    paginate_by = 10

    def get_queryset(self):
        queryset = Problem.objects.filter(is_active=True).prefetch_related('tags')
        
        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty')
        if difficulty and difficulty in ['easy', 'medium', 'hard']:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filter by tag
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Filter by status (solved/attempted/unsolved)
        status = self.request.GET.get('status')
        if status and self.request.user.is_authenticated:
            user_submissions = Submission.objects.filter(user=self.request.user)
            solved_problem_ids = user_submissions.filter(
                status=SubmissionStatus.ACCEPTED
            ).values_list('problem_id', flat=True).distinct()
            attempted_problem_ids = user_submissions.values_list(
                'problem_id', flat=True
            ).distinct()
            
            if status == 'solved':
                queryset = queryset.filter(id__in=solved_problem_ids)
            elif status == 'attempted':
                queryset = queryset.filter(id__in=attempted_problem_ids).exclude(id__in=solved_problem_ids)
            elif status == 'unsolved':
                queryset = queryset.exclude(id__in=attempted_problem_ids)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = Tag.objects.all()
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Get user's solved and attempted problems
        if self.request.user.is_authenticated:
            user_submissions = Submission.objects.filter(user=self.request.user)
            context['solved_problem_ids'] = set(
                user_submissions.filter(status=SubmissionStatus.ACCEPTED)
                .values_list('problem_id', flat=True).distinct()
            )
            context['attempted_problem_ids'] = set(
                user_submissions.values_list('problem_id', flat=True).distinct()
            )
        else:
            context['solved_problem_ids'] = set()
            context['attempted_problem_ids'] = set()
        
        return context


class ProblemDetailView(DetailView):
    """Display problem details with sample test cases and submission form.
    
    Unauthenticated users can view problems but must log in to submit solutions.
    """
    model = Problem
    template_name = 'problems/problem_detail.html'
    context_object_name = 'problem'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Problem.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'test_cases',
                queryset=TestCase.objects.filter(is_sample=True).order_by('order'),
                to_attr='sample_test_cases'
            ),
            'tags'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem = self.get_object()
        
        # Get user's submissions for this problem
        if self.request.user.is_authenticated:
            all_user_submissions = Submission.objects.filter(
                user=self.request.user,
                problem=problem
            )
            # Check if solved before slicing
            context['is_solved'] = all_user_submissions.filter(
                status=SubmissionStatus.ACCEPTED
            ).exists()
            # Get recent submissions (sliced)
            context['user_submissions'] = all_user_submissions.order_by('-submitted_at')[:5]
        else:
            context['is_solved'] = False
            context['user_submissions'] = []
        
        # Language choices for the form
        from submit.models import LanguageChoice
        context['language_choices'] = LanguageChoice.choices
        
        return context
