import oscar.apps.payment.apps as apps


class PaymentConfig(apps.PaymentConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_apps.store.payment'
    label = 'payment'
    verbose_name = 'Store Payment Management'

    def ready(self):
        # Disable Oscar’s signals if they conflict with tenancy
        pass
