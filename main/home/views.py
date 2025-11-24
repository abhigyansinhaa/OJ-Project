from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
def index(request):
    return render(request,'home/index.html')

@login_required
def dashboard(request):
    return render(request, 'home/dashboard.html')

@login_required
def problems(request):
    return render(request, 'home/problems.html')

@login_required
def profile(request):
    return render(request, 'home/profile.html')