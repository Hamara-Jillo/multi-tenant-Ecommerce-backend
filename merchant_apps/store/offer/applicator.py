from oscar.apps.offer.applicator import Applicator as BaseApplicator
from .models import ConditionalOffer 

class Applicator(BaseApplicator):
    def get_offers(self, basket, user=None):
        offers = super().get_offers(basket, user)
        if basket.store:
            offers = offers.filter(store=basket.store)
        return offers