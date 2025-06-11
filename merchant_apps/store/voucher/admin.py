from django.contrib import admin
from django.utils.translation import gettext_lazy as _
# Import only the models you need from Oscar
# from oscar.apps.voucher.models import Voucher, VoucherApplication
from oscar.core.loading import get_model
Voucher = get_model('voucher', 'Voucher')
VoucherApplication = get_model('voucher', 'VoucherApplication')
from merchant_apps.store.meta.models import StorePermission
from .models import (
    Voucher as StoreVoucher, VoucherOffer, VoucherSet,
    VoucherApplication as StoreVoucherApplication, VoucherGroup
)

class VoucherOfferInline(admin.TabularInline):
    model = VoucherOffer
    extra = 1
    raw_id_fields = ('offer',)
    verbose_name = _("Linked Offer")
    fk_name = 'voucher'  # Refers to the FK in VoucherOffer (correct)

class VoucherGroupInline(admin.TabularInline):
    model = VoucherGroup
    extra = 1
    fk_name = 'main_voucher'  # Refers to the FK in VoucherGroup (correct)
    verbose_name = _("Linked Voucher")
    raw_id_fields = ('linked_voucher',)

# Rename custom VoucherAdmin to avoid collision with Oscar's VoucherAdmin
class StoreVoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'store_field', 'usage', 'start_datetime', 'end_datetime')
    list_filter = ('store', 'usage', 'start_datetime', 'end_datetime')  # 'store' is correct
    search_fields = ('code', 'store__name')
    raw_id_fields = ('store',)  # 'store' is a FK in StoreVoucher
    inlines = [VoucherOfferInline, VoucherGroupInline]

    def store_field(self, obj):
        return obj.store.name
    store_field.short_description = _("Store")

class VoucherSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'store_field', 'count', 'offer')
    list_filter = ('store',)
    raw_id_fields = ('store', 'offer')
    search_fields = ('name', 'store__name')

class VoucherApplicationAdmin(admin.ModelAdmin):
    list_display = ('voucher', 'order', 'user', 'date_created')
    list_filter = ('date_created',)
    raw_id_fields = ('voucher', 'order', 'user')

class VoucherGroupAdmin(admin.ModelAdmin):
    list_display = ('main_voucher', 'linked_voucher')
    raw_id_fields = ('main_voucher', 'linked_voucher')

# Unregister Oscar's original Voucher and VoucherApplication models
# (Use direct import to avoid overwriting your custom admin classes)
# admin.site.unregister(Voucher)
# admin.site.unregister(VoucherApplication)

# Register custom models using the renamed admin class
admin.site.register(StoreVoucher, StoreVoucherAdmin)
admin.site.register(StoreVoucherApplication, VoucherApplicationAdmin)
admin.site.register(VoucherGroup, VoucherGroupAdmin)