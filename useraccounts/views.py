from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout

@login_required
def change_username(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Username changed successfully.')
            return redirect('profile')  # Replace 'profile' with the desired URL name or path for the user's profile page
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'change_username.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to update the session with the new password
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')  # Replace 'profile' with the desired URL name or path for the user's profile page
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'useraccounts/change_password.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # User is authenticated, redirect to a success page
                return redirect('home') 
            else:
                # Invalid credentials, display an error message
                error_message = 'Invalid username or password'
                return render(request, 'useraccounts/login.html', {'form': form, 'error_message': error_message})
    else:
        form = AuthenticationForm(request)
    return render(request, 'useraccounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

from .forms import RegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            form.save()
            # Registration successful, redirect to login page
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'useraccounts/registration.html', {'form': form})

@login_required
def confirm_users(request):
    if not request.user.is_superuser:
        return redirect('home')  # Redirect to the home page or any other appropriate page if the user is not a superuser

    users_to_confirm = User.objects.filter(is_staff=False, is_active=False)

    if request.method == 'POST':
        selected_users = request.POST.getlist('selected_users')

        for user_id in selected_users:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

        return redirect('home')  # Redirect to the home page or any other appropriate page after confirming users

    return render(request, 'useraccounts/confirm_users.html', {'users_to_confirm': users_to_confirm})

    