from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'public_apps.auth'
    label = 'authentication'
    verbose_name = 'Auth Management'