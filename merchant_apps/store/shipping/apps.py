import oscar.apps.shipping.apps as apps


class ShippingConfig(apps.ShippingConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_apps.store.shipping'
    label = 'shipping'
    verbose_name = 'Store Shipping Management'

    def ready(self):
        # Disable Oscar’s signals if needed
        pass