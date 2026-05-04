"""
Management command to set up ERP groups and (optionally) clean up legacy
Django-only users.

Usage:
    python manage.py crear_usuarios

With MySQL auth enabled, Django users are **auto-created on first login**.
This command only ensures the three Django groups exist and removes any
leftover users that were created manually before the MySQL auth backend
was installed.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


# Legacy usernames from the old crear_usuarios command
_LEGACY_USERNAMES = {'dev_user', 'admin_user', 'operador'}


class Command(BaseCommand):
    help = (
        'Crea los grupos ERP y elimina usuarios legacy de Django. '
        'Los usuarios ahora se crean automáticamente al hacer login con '
        'credenciales de MySQL.'
    )

    def handle(self, *args, **options):
        # 1. Ensure Django groups exist
        for name in ('dev', 'admin', 'usuario'):
            group, created = Group.objects.get_or_create(name=name)
            status = self.style.SUCCESS('creado') if created else 'ya existe'
            self.stdout.write(f'  Grupo "{name}": {status}')

        # 2. Remove legacy Django-only users
        legacy = User.objects.filter(username__in=_LEGACY_USERNAMES)
        count = legacy.count()
        if count:
            legacy.delete()
            self.stdout.write(
                self.style.WARNING(
                    f'\n  Eliminados {count} usuario(s) legacy: '
                    f'{", ".join(_LEGACY_USERNAMES)}'
                )
            )
        else:
            self.stdout.write('\n  No se encontraron usuarios legacy.')

        self.stdout.write(
            self.style.SUCCESS(
                '\n¡Listo! Los usuarios ERP se crean automáticamente al '
                'hacer login con credenciales de MySQL.'
            )
        )
