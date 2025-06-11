from oscar.apps.shipping.abstract_models import (
    AbstractBase, 
    AbstractOrderAndItemCharges, 
    AbstractWeightBased, 
    AbstractWeightBand
)
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal as D
from oscar.core.prices import Price
from oscar.core.loading import get_class
from polymorphic.models import PolymorphicModel

Scale = get_class('shipping.scales', 'Scale')

class ShippingMethod(AbstractBase, PolymorphicModel):
    store = models.ForeignKey(
        'store_meta.Store', 
        on_delete=models.CASCADE,
        related_name='shipping_methods',
        verbose_name=_("Store")
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled")
    )
    
    class Meta(AbstractBase.Meta):
        unique_together = [('store', 'code')]
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def calculate(self, basket):
        """Base implementation to be overridden by subclasses"""
        raise NotImplementedError(_("Subclasses must implement calculate()"))

    def get_charge(self, basket):
        """Optional base implementation for charge calculation"""
        return self.calculate(basket)


class OrderAndItemCharges(ShippingMethod, AbstractOrderAndItemCharges):
    price_per_order = models.DecimalField(
        _("Price per order"), 
        decimal_places=2, 
        max_digits=12,
        default=D('0.00')
    )
    price_per_item = models.DecimalField(
        _("Price per item"), 
        decimal_places=2, 
        max_digits=12,
        default=D('0.00')
    )
    free_shipping_threshold = models.DecimalField(
        _("Free Shipping Threshold"), 
        decimal_places=2, 
        max_digits=12, 
        blank=True,
        null=True,
        help_text=_("Order total needed for free shipping")
    )

    def get_charge(self, basket):
        """Calculate shipping charge based on basket contents"""
        if self.free_shipping_applies(basket):
            return Price(currency=basket.currency, excl_tax=D('0.00'), incl_tax=D('0.00'))
        
        charge = self.price_per_order
        charge += sum(line.quantity * self.price_per_item 
                     for line in basket.lines.all() 
                     if line.product.is_shipping_required)
        return Price(currency=basket.currency, excl_tax=charge, incl_tax=charge)

    def free_shipping_applies(self, basket):
        """Check if free shipping threshold is met"""
        return (self.free_shipping_threshold is not None and 
                basket.total_incl_tax >= self.free_shipping_threshold)


class WeightBased(ShippingMethod, AbstractWeightBased):
    weight_attribute = 'weight'
    default_weight = models.DecimalField(
        _("Default Weight"), 
        decimal_places=3, 
        max_digits=12,
        default=D('0.000'),
        validators=[MinValueValidator(D('0.00'))],
        help_text=_("Default weight (kg) for products without weight attribute")
    )

    def calculate(self, basket):
        """Calculate shipping charge based on basket weight"""
        weight = self.weigh_basket(basket)
        return Price(
            currency=basket.currency,
            excl_tax=self.get_charge(weight),
            incl_tax=self.get_charge(weight)
        )

    def weigh_basket(self, basket):
        """Get total weight of basket with proper error handling"""
        try:
            scale = Scale(
                attribute_code=self.weight_attribute,
                default_weight=self.default_weight
            )
            return scale.weigh_basket(basket)
        except Exception as e:
            # Handle missing weight attributes
            return D('0.000')

    def get_charge(self, weight):
        """Calculate charge based on weight bands"""
        if not self.bands.exists():
            return D('0.00')
        
        weight = D(weight)
        top_band = self.top_band
        
        if weight <= top_band.upper_limit:
            return self.get_band_charge(weight)
        return self.calculate_oversize_charge(weight, top_band)

    def get_band_charge(self, weight):
        """Get charge for weight within band limits"""
        band = self.bands.filter(upper_limit__gte=weight).order_by('upper_limit').first()
        return band.charge if band else D('0.00')

    def calculate_oversize_charge(self, weight, top_band):
        """Calculate charge for weights exceeding top band"""
        quotient, remaining = divmod(weight, top_band.upper_limit)
        charge = quotient * top_band.charge
        
        if remaining:
            band = self.bands.filter(upper_limit__gte=remaining).order_by('upper_limit').first()
            charge += band.charge if band else D('0.00')
        return charge

    @property
    def top_band(self):
        """Safely get the highest weight band"""
        return self.bands.order_by('-upper_limit').first() or D('0.00')


class WeightBand(AbstractWeightBand):
    method = models.ForeignKey(
        WeightBased,
        on_delete=models.CASCADE,
        related_name='bands',
        verbose_name=_("Weight Based Method")
    )

    class Meta(AbstractWeightBand.Meta):
        ordering = ['upper_limit']
        verbose_name = _("Weight Band")
        verbose_name_plural = _("Weight Bands")

# Import remaining Oscar models after custom implementations
from oscar.apps.shipping.models import *