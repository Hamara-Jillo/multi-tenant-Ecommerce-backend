from django.db.models.signals import post_save
from django_tenants.utils import tenant_context
from oscar.apps.communication.utils import Dispatcher

from merchant_apps.store.order.models import Order

def send_order_confirmation_email(order):
    dispatcher = Dispatcher()
    dispatcher.dispatch_order_messages(order, 'order_placed')

def handle_order_placement(sender, instance, **kwargs):
    with tenant_context(instance.store.merchant):
        # Trigger tenant-specific post-order logic
        send_order_confirmation_email(instance)

post_save.connect(handle_order_placement, sender=Order)