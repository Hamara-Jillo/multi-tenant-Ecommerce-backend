from oscar.apps.address.abstract_models import( 
    AbstractCountry, 
    AbstractShippingAddress, 
    AbstractUserAddress
    )
from django.db import models
from django.utils.translation import gettext_lazy as _
class ShippingAddress(AbstractShippingAddress):
    store = models.ForeignKey('store_meta.Store', on_delete=models.CASCADE)
    country = models.ForeignKey(
        'address.Country',
        on_delete=models.CASCADE,
        related_name='store_address_shipping',  # Unique name
        verbose_name=_("Country")
    )

    class Meta(AbstractShippingAddress.Meta):
        app_label = 'address'  

class UserAddress(AbstractUserAddress):
    schema_name = models.CharField(max_length=63, blank=True)  # Tenant schema identifier
    store = models.ForeignKey('store_meta.Store', on_delete=models.CASCADE,  null=True, blank=True, related_name='store_user_addresses')
    country = models.ForeignKey(
        'address.Country',
        on_delete=models.CASCADE,
        related_name='store_address_user',  # Unique name
        verbose_name=_("Country")
    )

    class Meta(AbstractUserAddress.Meta):
        app_label = 'address'  # Avoid conflicts with Oscar's default

class Country(AbstractCountry):
    class Meta(AbstractCountry.Meta):
        app_label = 'address'

from oscar.apps.address.models import *  