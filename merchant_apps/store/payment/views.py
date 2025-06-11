# Override Oscar’s PaymentDetailsView
from oscar.apps.checkout.views import PaymentDetailsView

from merchant_apps.store.payment.models import Source

class TenantPaymentDetailsView(PaymentDetailsView):
    def handle_payment(self, order_number, total, **kwargs):
        source = Source.objects.create(
            store=self.request.store,
            currency=total.currency,
            amount_allocated=total.incl_tax
        )
        # Process payment using tenant-specific gateway