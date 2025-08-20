from django.shortcuts import render
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User

# Create your views here.
def user_register(request):
    if request.method=='POST':
        username=request.POST.get['username']
        pass1=request.POST.get['pass1']
        pass2=request.POST.get['pass2']
        
        if User.objects.filter(username=username).exists():
            messages.error(request,"Username already taken..Try again!!")
            return redirect('accounts:user_register')
        
        if pass1!=pass2:
            messages.error(request,"Both passwords don't match..Try again!!")
            return redirect('accounts:user_register')
        
        user=User.objects.create_user(username=username,password=pass2)
        user.save()
        
        messages.success(request,'Account created successfully')
        return redirect('accounts:user_login')
    return render(request,'accounts/register.html')

def user_login(request):
    if request.method=='POST':
        username=request.POST.get['username']
        password=request.POST.get['password']
        
        user=authenticate(username='username',password='password')
        if user is not None:
            login(request,user)
            return redirect('app:home')
        else:
            messages.error(request,"Invalid Credentials..Try again!!")
            return redirect('accounts:user_login')
        
    return render(request,'accounts/login.html')

def user_logout(request):
    logout(request)
    