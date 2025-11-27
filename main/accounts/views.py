from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, CustomAuthenticationForm


class UserRegisterView(CreateView):
    """User registration view using Django's class-based views."""
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:user_login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please log in.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class UserLoginView(LoginView):
    """User login view using Django's built-in LoginView."""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home:dashboard')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    """User logout view using Django's built-in LogoutView."""
    next_page = reverse_lazy('accounts:user_login')
    http_method_names = ['get', 'post', 'options']  # Allow GET requests

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for logout."""
        return self.post(request, *args, **kwargs)


# Function-based views for backward compatibility (deprecated)
def user_register(request):
    """Redirect to class-based view."""
    return UserRegisterView.as_view()(request)


def user_login(request):
    """Redirect to class-based view."""
    return UserLoginView.as_view()(request)


def user_logout(request):
    """Redirect to class-based view."""
    return UserLogoutView.as_view()(request)
