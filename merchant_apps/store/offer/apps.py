# apps.py
from oscar.apps.offer.apps import OfferConfig as OscarOfferConfig
from django.utils.module_loading import import_string

class OfferConfig(OscarOfferConfig):
    name = 'merchant_apps.store.offer'
    label = 'offer'  # Avoid conflict with Oscar's 'offer' label
    verbose_name = 'Store Offers'

    def ready(self):
        from .models import (
            ConditionalOffer, Range, Benefit, Condition
        )
        super().ready()
        # Dynamically override Oscar's OfferApplications
        from oscar.apps.offer import results as oscar_results
        from .results import OfferApplications
        oscar_results.OfferApplications = OfferApplications