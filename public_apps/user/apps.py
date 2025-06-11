from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'public_apps.user'
    label = 'user'
    verbose_name = 'User Management'
