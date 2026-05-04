from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Only store MySQL credentials when MySQLAuthBackend authenticated the user.
            # Django superusers go through ModelBackend and their password doesn't work in MySQL.
            if request.session.get('_auth_user_backend') == 'accounts.mysql_auth_backend.MySQLAuthBackend':
                request.session['mysql_user'] = username
                request.session['mysql_password'] = password
            next_url = request.GET.get('next', '/')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = '/'
            return redirect(next_url)
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')
