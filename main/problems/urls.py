from django.urls import path
from .views import ProblemListView, ProblemDetailView

app_name = 'problems'

urlpatterns = [
    path('', ProblemListView.as_view(), name='problem_list'),
    path('<slug:slug>/', ProblemDetailView.as_view(), name='problem_detail'),
]



