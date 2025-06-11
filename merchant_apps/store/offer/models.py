from oscar.apps.offer.abstract_models import (
    AbstractCondition, 
    AbstractBenefit,
    AbstractRange,
    AbstractConditionalOffer,
    AbstractRangeProduct
)
from django.db import models
from merchant_apps.store.meta.models import Store
from django.utils.translation import gettext_lazy as _ 


class ConditionalOfferCombination(models.Model):
    """
    Explicit through model for ConditionalOffer.combinations
    """
    primary = models.ForeignKey(
        'offer.ConditionalOffer',
        on_delete=models.CASCADE,
        related_name='primary_combinations'
    )
    secondary = models.ForeignKey(
        'offer.ConditionalOffer',
        on_delete=models.CASCADE,
        related_name='secondary_combinations'
    )

    class Meta:
        unique_together = ('primary', 'secondary')
        app_label = 'offer' 
        verbose_name = 'Conditional Offer Combination'
        verbose_name_plural = 'Conditional Offer Combinations'

class ConditionalOffer(AbstractConditionalOffer):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='offers',  # Unique related_name
        verbose_name='Store'
    )
    benefit = models.ForeignKey(
        'offer.Benefit',
        related_name='store_conditional_offers',  # Unique name
        on_delete=models.CASCADE
    )
    condition = models.ForeignKey(
        'offer.Condition',
        related_name='store_conditional_offers',  # Unique name
        on_delete=models.CASCADE
    )
    combinations = models.ManyToManyField(
        'self',
        through=ConditionalOfferCombination,  # Use explicit through model
        symmetrical=False,
        verbose_name=_("Combinations"),
        help_text=_("Select other offers to combine with this one")
    )

class RangeProduct(AbstractRangeProduct):
    class Meta:
        app_label = 'offer'


class Range(AbstractRange):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='ranges',
        verbose_name='Store'
    )
    included_products = models.ManyToManyField(
        'catalogue.Product',
        through=RangeProduct,  # Use the custom through model
        related_name='included_in_ranges',
        blank=True
    )
    excluded_products = models.ManyToManyField(
        'catalogue.Product',
        related_name='excluded_from_ranges',
        blank=True
    )



class Condition(AbstractCondition):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='conditions'
    )

class Benefit(AbstractBenefit):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='benefits'
    )

# Import Oscar’s abstract models after defining your overrides
from oscar.apps.offer.models import *