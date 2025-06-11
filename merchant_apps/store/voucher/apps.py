import oscar.apps.voucher.apps as apps


class VoucherConfig(apps.VoucherConfig):
    name = 'merchant_apps.store.voucher'
    label = 'voucher'
    verbose_name = 'Store Voucher'
    swappable = 'OSCAR_VOUCHER_MODEL' 
    def ready(self):
        super().ready()
        from . import signals  
    def get_models(self, include_auto_created=False, include_swapped=False):
        # Include all models (or specify explicitly)
        return super().get_models(include_auto_created, include_swapped)
