import oscar.apps.partner.apps as apps


class PartnerConfig(apps.PartnerConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_apps.store.partner'
    label = 'partner'
    verbose_name = 'Store Partner Management'

    def ready(self):
        # Disable Oscar's receivers by not calling super()
        pass  # Remove Oscar's StockAlert signal handlers

