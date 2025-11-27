from django.urls import path
from submit.views import submit_solution, SubmissionDetailView, SubmissionHistoryView, submit

app_name = 'submit'

urlpatterns = [
    path('', submit, name='submit'),  # Legacy
    path('problem/<slug:slug>/', submit_solution, name='submit_solution'),
    path('result/<int:pk>/', SubmissionDetailView.as_view(), name='submission_detail'),
    path('history/', SubmissionHistoryView.as_view(), name='submission_history'),
]
