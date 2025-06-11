from oscar.apps.partner.abstract_models import (
    AbstractPartner, 
    AbstractStockRecord,
    AbstractStockAlert
    )
from django.db import models

class Partner(AbstractPartner):
    store = models.ForeignKey(
        'store_meta.Store', 
        on_delete=models.CASCADE,
        related_name='partners'
    )
    # Tenant-specific fields (e.g., custom commission rate)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)


class StockRecord(AbstractStockRecord):
    partner = models.ForeignKey(
        Partner, 
        on_delete=models.CASCADE,
        related_name='stockrecords'
    )
    product = models.ForeignKey(
        'catalogue.Product',  # Your forked Product model
        on_delete=models.CASCADE
    )

class StockAlert(AbstractStockAlert):
    # Add tenant/store relationship if needed
    store = models.ForeignKey('store_meta.Store', on_delete=models.CASCADE)

from oscar.apps.partner.models import *