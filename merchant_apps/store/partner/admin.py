from oscar.apps.partner.admin import  *  
from .models import Partner as StorePartner, StockRecord as StoreStockRecord, StockAlert as StoreStockAlert
from merchant_apps.store.meta.models import StorePermission, Store

class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'commission_rate')
    list_filter = ('store',)

    def get_queryset(self, request):
        """Show only Partners in stores that the merchant has access to"""
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        # Get stores that the merchant has access to through StorePermission
        accessible_stores = StorePermission.objects.filter(
            merchant=request.tenant
        ).values_list('store', flat=True)
        return qs.filter(store__in=accessible_stores)

# @admin.register(StockRecord)
class StockRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'partner', 'partner_sku', 'price_currency', 'price', 'num_in_stock')
    list_filter = ('partner', 'price_currency')
    search_fields = ('partner_sku', 'product__title')
    raw_id_fields = ('product',)

    def get_queryset(self, request):
        """Show only StockRecords for products in stores the merchant has access to"""
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        # Get stores that the merchant has access to
        accessible_stores = StorePermission.objects.filter(
            merchant=request.tenant
        ).values_list('store', flat=True)
        return qs.filter(partner__store__in=accessible_stores)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter partner choices to only show partners from accessible stores"""
        if db_field.name == "partner" and not request.user.is_platform_admin:
            accessible_stores = StorePermission.objects.filter(
                merchant=request.tenant
            ).values_list('store', flat=True)
            kwargs["queryset"] = StorePartner.objects.filter(store__in=accessible_stores)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# @admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('stockrecord', 'status', 'threshold', 'date_created', 'store')
    list_filter = ('status', 'date_created', 'store')
    readonly_fields = ('date_created',)

    def get_queryset(self, request):
        """Show only StockAlerts for stores the merchant has access to"""
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        # Get stores that the merchant has access to
        accessible_stores = StorePermission.objects.filter(
            merchant=request.tenant
        ).values_list('store', flat=True)
        return qs.filter(store__in=accessible_stores)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter store choices to only show accessible stores"""
        if db_field.name == "store" and not request.user.is_platform_admin:
            accessible_stores = StorePermission.objects.filter(
                merchant=request.tenant
            ).values_list('store', flat=True)
            kwargs["queryset"] = Store.objects.filter(id__in=accessible_stores)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.unregister(Partner) 
admin.site.unregister(StockRecord) 

admin.site.register(StorePartner, PartnerAdmin)
admin.site.register(StoreStockRecord, StockRecordAdmin)
admin.site.register(StoreStockAlert, StockAlertAdmin)


