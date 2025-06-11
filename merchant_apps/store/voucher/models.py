from django.conf import settings
from oscar.apps.voucher.abstract_models import (
    AbstractVoucher, 
    AbstractVoucherSet,
    AbstractVoucherApplication
    )
from oscar.core.loading import get_model
from django.db import models
from merchant_apps.store.meta.models import Store


# OscarVoucher = get_model('voucher', 'Voucher') 
class VoucherOffer(models.Model):
    voucher = models.ForeignKey(
        'voucher.Voucher',
        on_delete=models.CASCADE,
        related_name='store_voucher_offers'
    )
    offer = models.ForeignKey(
        'offer.ConditionalOffer',
        on_delete=models.CASCADE,
        related_name='store_voucher_offers'
    )
    class Meta:
        app_label = 'voucher'
        unique_together = ('voucher', 'offer')




class VoucherSet(AbstractVoucherSet):
    # Override the store field to use a unique reverse accessor name.
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='store_voucher_sets',
        verbose_name='Store'
    )
    offer = models.ForeignKey(
        'offer.ConditionalOffer',
        on_delete=models.CASCADE,
        related_name='store_voucher_sets',
        # Add this line to resolve the missing relationship
        verbose_name='Offer'  # Add proper verbose name
    )

    class Meta(AbstractVoucherSet.Meta):
        app_label = 'voucher'
        unique_together = ('name', 'store')

class VoucherApplication(AbstractVoucherApplication):
    voucher = models.ForeignKey(
        'voucher.Voucher',
        on_delete=models.CASCADE,
        related_name='store_applications'
    )
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='store_voucher_apps'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store_voucher_apps'
    )
    
    class Meta:
        app_label = 'voucher'

class VoucherGroup(models.Model):
    main_voucher = models.ForeignKey(
        'voucher.Voucher',
        on_delete=models.CASCADE,
        related_name='store_main_groups'
    )
    linked_voucher = models.ForeignKey(
        'voucher.Voucher',
        on_delete=models.CASCADE,
        related_name='store_linked_groups'
    )
    
    class Meta:
        app_label = 'voucher'
        unique_together = ('main_voucher', 'linked_voucher')

class Voucher(AbstractVoucher):
    """Store-specific voucher model"""
    # Override the store field to use a unique reverse accessor name.
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='store_vouchers',
        verbose_name='Store'
    )
    offers = models.ManyToManyField(
        'offer.ConditionalOffer',
        through="voucher.VoucherOffer",
        related_name='store_vouchers'
    )

    applications = models.ManyToManyField(
        'order.Order',
        through=VoucherApplication,
        related_name='store_voucher_set',
        verbose_name='Applications'
    )
    voucher_set = models.ManyToManyField(
        'self',
        through='voucher.VoucherGroup',
        symmetrical=False,
        related_name='store_voucher_groups',
        blank=True
    )



    def __str__(self):
        return self.code

    class Meta(AbstractVoucher.Meta):
        unique_together = ('code', 'store')
        app_label = 'voucher'
# from oscar.apps.voucher.models import *
