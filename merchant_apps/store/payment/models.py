# merchant_apps/store/payment/models.py
from oscar.apps.payment.abstract_models import (
    AbstractTransaction, AbstractSource, AbstractSourceType
)
from merchant_apps.store.order.models import Order
from django.db import models

class SourceType(AbstractSourceType):
    # Optional: Add tenant-specific configuration (e.g., store-specific payment methods)
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='payment_source_types',
        null=True  # Allow global source types (e.g., "Visa") to exist
    )

class Source(AbstractSource):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='payment_sources',
        null=True
    )

class Transaction(AbstractTransaction):
    # Link transactions to the tenant’s store via Source
    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

# Import remaining Oscar models (e.g., Bankcard)
from oscar.apps.payment.models import *





















