from django.apps import AppConfig


class StoreMetaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_apps.store.meta'
    label = 'store_meta'
    verbose_name = 'Store Management'
