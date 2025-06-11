import oscar.apps.checkout.apps as apps


class CheckoutConfig(apps.CheckoutConfig):
    name = 'merchant_apps.store.checkout'
    label = 'checkout'
    verbose_name = 'Store Checkout Process'

    def ready(self):
        from . import views
        self.index_view = views.IndexView
        self.shipping_address_view = views.ShippingAddressView
        self.shipping_method_view = views.ShippingMethodView
        self.payment_method_view = views.PaymentMethodView
        self.payment_details_view = views.PaymentDetailsView
        self.thank_you_view = views.ThankYouView
        self.user_address_update_view = views.UserAddressUpdateView
