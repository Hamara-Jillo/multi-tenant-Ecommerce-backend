# results.py
from oscar.apps.offer.results import (
    OfferApplications as OscarOfferApplications,
    BasketDiscount as OscarBasketDiscount)

class OfferApplications(OscarOfferApplications):
    def __init__(self, request):
        super().__init__()
        self.store = getattr(request, 'store', None)  # Get store from request

class BasketDiscount(OscarBasketDiscount):
    def __init__(self, *args, **kwargs):
        self.store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)