from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from submit.models import Submission, SubmissionStatus
from problems.models import Problem


def index(request):
    """Home page - accessible to all users."""
    context = {}
    
    # Get some stats for the homepage
    context['total_problems'] = Problem.objects.filter(is_active=True).count()
    context['total_submissions'] = Submission.objects.count()
    
    return render(request, 'home/index.html', context)


@login_required
def dashboard(request):
    """User dashboard with personalized statistics."""
    user = request.user
    
    # User's submissions
    user_submissions = Submission.objects.filter(user=user)
    
    # Problems solved (unique problems with accepted submissions)
    solved_problems = user_submissions.filter(
        status=SubmissionStatus.ACCEPTED
    ).values('problem').distinct().count()
    
    # Total submissions
    total_submissions = user_submissions.count()
    
    # Success rate
    accepted_count = user_submissions.filter(status=SubmissionStatus.ACCEPTED).count()
    success_rate = round((accepted_count / total_submissions * 100), 1) if total_submissions > 0 else 0
    
    # Problems by difficulty
    easy_solved = user_submissions.filter(
        status=SubmissionStatus.ACCEPTED,
        problem__difficulty='easy'
    ).values('problem').distinct().count()
    
    medium_solved = user_submissions.filter(
        status=SubmissionStatus.ACCEPTED,
        problem__difficulty='medium'
    ).values('problem').distinct().count()
    
    hard_solved = user_submissions.filter(
        status=SubmissionStatus.ACCEPTED,
        problem__difficulty='hard'
    ).values('problem').distinct().count()
    
    # Total problems by difficulty
    easy_total = Problem.objects.filter(is_active=True, difficulty='easy').count()
    medium_total = Problem.objects.filter(is_active=True, difficulty='medium').count()
    hard_total = Problem.objects.filter(is_active=True, difficulty='hard').count()
    
    # Recent submissions
    recent_submissions = user_submissions.select_related('problem').order_by('-submitted_at')[:5]
    
    # Recommended problems (unsolved, starting with easy)
    solved_problem_ids = user_submissions.filter(
        status=SubmissionStatus.ACCEPTED
    ).values_list('problem_id', flat=True).distinct()
    
    recommended_problems = Problem.objects.filter(
        is_active=True
    ).exclude(
        id__in=solved_problem_ids
    ).order_by('difficulty', '?')[:3]
    
    context = {
        'solved_problems': solved_problems,
        'total_submissions': total_submissions,
        'success_rate': success_rate,
        'easy_solved': easy_solved,
        'easy_total': easy_total,
        'medium_solved': medium_solved,
        'medium_total': medium_total,
        'hard_solved': hard_solved,
        'hard_total': hard_total,
        'recent_submissions': recent_submissions,
        'recommended_problems': recommended_problems,
    }
    
    return render(request, 'home/dashboard.html', context)


@login_required
def profile(request):
    """User profile page with statistics and achievements."""
    user = request.user
    
    # User's submissions
    user_submissions = Submission.objects.filter(user=user)
    
    # Problems solved
    solved_problems = user_submissions.filter(
        status=SubmissionStatus.ACCEPTED
    ).values('problem').distinct().count()
    
    # Total submissions
    total_submissions = user_submissions.count()
    
    # Success rate
    accepted_count = user_submissions.filter(status=SubmissionStatus.ACCEPTED).count()
    success_rate = round((accepted_count / total_submissions * 100), 1) if total_submissions > 0 else 0
    
    # Recent activity
    recent_submissions = user_submissions.select_related('problem').order_by('-submitted_at')[:5]
    
    context = {
        'solved_problems': solved_problems,
        'total_submissions': total_submissions,
        'success_rate': success_rate,
        'recent_submissions': recent_submissions,
    }
    
    return render(request, 'home/profile.html', context)
