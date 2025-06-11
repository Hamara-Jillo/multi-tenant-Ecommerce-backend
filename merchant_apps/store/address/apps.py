import oscar.apps.address.apps as apps


class AddressConfig(apps.AddressConfig):
    name = 'merchant_apps.store.address'
    label = 'address'
    verbose_name = 'Store Address Management'
    swappable = 'OSCAR_ADDRESS_MODEL'
    def ready(self):
        super().ready()
        from . import signals  # Import signals to ensure they are registered
        # You can also import models or other components if needed
    # def get_models(self, include_auto_created=False, include_swapped=False):
    #     # Include all models (or specify explicitly)
    #     return super().get_models(include_auto_created, include_swapped)
