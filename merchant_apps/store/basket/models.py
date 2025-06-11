from django.db import models
from oscar.apps.basket.abstract_models import (
    AbstractBasket, AbstractLine, AbstractLineAttribute
)
from merchant_apps.store.offer.models import ConditionalOffer
from merchant_apps.store.offer.results import OfferApplications

class Basket(AbstractBasket):
    store = models.ForeignKey(
        'store_meta.Store', 
        on_delete=models.CASCADE,
        related_name='baskets'
    )

class Line(AbstractLine):
    stockrecord = models.ForeignKey(
        'partner.StockRecord',
        on_delete=models.CASCADE,
        related_name='basket_lines',
        verbose_name="Stock record"
    )

class LineAttribute(AbstractLineAttribute):
    pass

