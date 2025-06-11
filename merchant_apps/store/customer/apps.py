import oscar.apps.customer.apps as apps


class CustomerConfig(apps.CustomerConfig):
    name = 'merchant_apps.store.customer'
    label = 'customer'
    verbose_name = 'Store Customer Management'

    def ready(self):
        from . import receivers  # For signal handling (optional)
        super().ready()
