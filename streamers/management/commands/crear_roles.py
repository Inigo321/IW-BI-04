"""Crea los roles (grupos) del panel de administración y un usuario de prueba para cada uno.

Uso:
    python manage.py crear_roles
    python manage.py crear_roles --password OtraClave123

Se puede ejecutar varias veces: actualiza los grupos sin duplicar nada.
"""
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

from streamers.admin import GRUPO_ADMINISTRADORES

# Permisos por rol: modelo -> acciones permitidas (add, change, delete, view)
ROLES = {
    GRUPO_ADMINISTRADORES: {
        'descripcion': 'Control total del contenido, incluidos los seguidores y el borrado.',
        'usuario': 'admincontenido',
        'permisos': {
            'canal': ['add', 'change', 'delete', 'view'],
            'creador': ['add', 'change', 'delete', 'view'],
            'categoria': ['add', 'change', 'delete', 'view'],
            'plataforma': ['add', 'change', 'delete', 'view'],
        },
    },
    'Editores': {
        'descripcion': 'Crean y editan canales y creadores. No borran ni tocan los seguidores.',
        'usuario': 'editor',
        'permisos': {
            'canal': ['add', 'change', 'view'],
            'creador': ['add', 'change', 'view'],
            'categoria': ['view'],
            'plataforma': ['view'],
        },
    },
    'Revisores': {
        'descripcion': 'Solo pueden consultar el contenido.',
        'usuario': 'revisor',
        'permisos': {
            'canal': ['view'],
            'creador': ['view'],
            'categoria': ['view'],
            'plataforma': ['view'],
        },
    },
}


class Command(BaseCommand):
    help = 'Crea los grupos de administradores con sus permisos y un usuario de prueba por grupo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password', default='Streamers2026',
            help='Contraseña de los usuarios de prueba (por defecto: Streamers2026).',
        )
        parser.add_argument(
            '--sin-usuarios', action='store_true',
            help='Crea solo los grupos, sin usuarios de prueba.',
        )

    def handle(self, *args, **options):
        # Si la contraseña llega vacía (por ejemplo, una variable de entorno sin valor), se usa la de por defecto.
        options['password'] = options['password'] or 'Streamers2026'
        for nombre_grupo, rol in ROLES.items():
            grupo, _ = Group.objects.get_or_create(name=nombre_grupo)

            codenames = [
                f'{accion}_{modelo}'
                for modelo, acciones in rol['permisos'].items()
                for accion in acciones
            ]
            permisos = Permission.objects.filter(
                content_type__app_label='streamers', codename__in=codenames,
            )
            grupo.permissions.set(permisos)
            self.stdout.write(f'Grupo «{nombre_grupo}»: {permisos.count()} permisos. {rol["descripcion"]}')

            if options['sin_usuarios']:
                continue

            usuario, creado = User.objects.get_or_create(username=rol['usuario'])
            usuario.is_staff = True  # necesario para entrar al panel
            usuario.set_password(options['password'])
            usuario.save()
            usuario.groups.set([grupo])
            estado = 'creado' if creado else 'actualizado'
            self.stdout.write(f'    Usuario «{usuario.username}» {estado}.')

        if not options['sin_usuarios']:
            self.stdout.write(self.style.SUCCESS(
                f'Listo. Contraseña de los usuarios de prueba: {options["password"]}'
            ))
