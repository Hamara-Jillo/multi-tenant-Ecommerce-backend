from django.apps import AppConfig


class MerchantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'public_apps.merchant'
    label = 'merchant'
    verbose_name = 'Merchant Management'