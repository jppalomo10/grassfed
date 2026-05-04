def user_group(request):
    """Exposes the current user's primary ERP group to all templates."""
    group = None
    if request.user.is_authenticated:
        for g in ('dev', 'admin', 'usuario'):
            if request.user.groups.filter(name=g).exists():
                group = g
                break
    return {'user_group': group}
