from django.conf import settings
from oscar.apps.order.abstract_models import (
    AbstractOrder, AbstractLine, AbstractLinePrice, AbstractLineAttribute,
    AbstractOrderNote, AbstractShippingEvent, AbstractOrderStatusChange,
    AbstractCommunicationEvent, AbstractPaymentEvent, AbstractPaymentEventType,
    AbstractOrderDiscount
)
# from merchant_apps.store.voucher.models import Voucher as StoreVoucher
from django.db import models

class Order(AbstractOrder):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True
    )

    voucher = models.ForeignKey(
        settings.OSCAR_VOUCHER_MODEL,  # Dynamic reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta(AbstractOrder.Meta):
        unique_together = [('store', 'number')]
        permissions = [
            ("multi_store_order", "Can access orders across stores")
        ]
class Line(AbstractLine):
    stockrecord = models.ForeignKey(
        'partner.StockRecord',
        on_delete=models.CASCADE,
        related_name='order_lines',
        verbose_name="Stock record"
    )

class LinePrice(AbstractLinePrice):
    pass

class LineAttribute(AbstractLineAttribute):
    pass

class OrderNote(AbstractOrderNote):
    pass

class ShippingEvent(AbstractShippingEvent):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        null=True
    )

class OrderStatusChange(AbstractOrderStatusChange):
    pass

class CommunicationEvent(AbstractCommunicationEvent):
    pass

class PaymentEvent(AbstractPaymentEvent):
    pass

class PaymentEventType(AbstractPaymentEventType):
    pass

# class PaymentEventQuantity(AbstractPaymentEventQuantity):
#     pass



class OrderDiscount(AbstractOrderDiscount):
    pass

from oscar.apps.order.models import *
