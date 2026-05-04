from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render


def role_required(*group_names):
    """
    Restrict a view to users who belong to at least one of the given groups.
    Unauthenticated users are redirected to the login page.
    Authenticated users without the required group see a 403 page.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(
                render(request, 'errors/403.html', status=403).content
            )
        return wrapper
    return decorator
