from oscar.apps.checkout.views import (
    IndexView as CoreIndexView,
    ShippingAddressView as CoreShippingAddressView,
    ShippingMethodView as CoreShippingMethodView,
    PaymentMethodView as CorePaymentMethodView,
    PaymentDetailsView as CorePaymentDetailsView,
    ThankYouView as CoreThankYouView,
    
)

from oscar.core.loading import get_class, get_classes, get_model
from django_tenants.utils import get_tenant, tenant_context
from merchant_apps.store.checkout.forms import ShippingAddressForm
from merchant_apps.store.meta.models import Store
from merchant_apps.store.shipping.models import OrderAndItemCharges
CoreCheckoutSessionMixin = get_class("checkout.session", "CheckoutSessionMixin")
CoreOrderPlacementMixin = get_class("checkout.views", "OrderPlacementMixin")
from merchant_apps.store.payment.models import Source

import logging

logger = logging.getLogger(__name__)



class IndexView(CoreIndexView):
    pass


class CheckoutSessionMixin(CoreCheckoutSessionMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_tenant()
        if tenant:
            context['tenant'] = tenant
            # Ensure session data is scoped to tenant
            self.checkout_session.set_namespace(f"checkout_{tenant.schema_name}")
        return context

    def get_store(self):
        """Retrieve the current tenant's store from session or fallback."""
        tenant = get_tenant()
        store_id = self.request.session.get(f"store_id_{tenant.schema_name}")
        if store_id:
            try:
                return Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                logger.warning(f"Store ID {store_id} not found for tenant {tenant.schema_name}")
        # Fallback to first permitted store
        permitted_stores = Store.objects.filter(storepermission__merchant=tenant)
        return permitted_stores.first() if permitted_stores.exists() else None

class ShippingAddressView(CheckoutSessionMixin,CoreShippingAddressView):
    form_class = ShippingAddressForm
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.get_store()
        if store:
            context['store'] = store
        return context

    def form_valid(self, form):
        store = self.get_store()
        if store:
            self.request.session[f"store_id_{get_tenant().schema_name}"] = store.id
        return super().form_valid(form)
    def get_store(self):
        store_id = self.request.session.get(f"store_id_{get_tenant().schema_name}")
        if store_id:
            return Store.objects.get(id=store_id)
        return None
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = get_tenant()
        return kwargs

class ShippingMethodView(CheckoutSessionMixin,CoreShippingMethodView):
    def get_available_shipping_methods(self):
        """Filter shipping methods by tenant’s store."""
        store = self.get_store()
        if store:
            # Assuming shipping methods are linked to stores; adjust as needed
            return OrderAndItemCharges.objects.filter(store=store)
        return super().get_available_shipping_methods()

class PaymentMethodView(CorePaymentMethodView):
    pass

class PaymentDetailsView(CheckoutSessionMixin,CorePaymentDetailsView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.get_store()
        if store:
            context['store'] = store
            # Filter payment methods by store (customize based on your payment setup)
            context['payment_methods'] = self.get_payment_methods(store)
        return context

    def get_payment_methods(self, store):
        # Placeholder; implement based on your payment gateway integration
        return ["Credit Card", "PayPal"]  # Example

    def get_shipping_methods(self, user, basket, shipping_addr=None):
        with tenant_context(self.request.tenant):
            return super().get_shipping_methods(user, basket, shipping_addr)

    def handle_payment(self, order_number, total, **kwargs):
        with tenant_context(self.request.tenant):
            return super().handle_payment(order_number, total, **kwargs)

class ThankYouView(CoreThankYouView):
    pass

class UserAddressUpdateView():
    pass 


class OrderPlacementView(CoreOrderPlacementMixin, CheckoutSessionMixin):
    def place_order(self, order_form, shipping_method, shipping_address):
        store = self.get_store()
        if store:
            order = super().place_order(order_form, shipping_method, shipping_address)
            order.store = store  # Assuming Order model has a store field from forked order app
            order.save()
            logger.info(f"Order {order.number} placed for store {store.name} in tenant {get_tenant().schema_name}")
            return order
        raise ValueError("No store associated with checkout.")