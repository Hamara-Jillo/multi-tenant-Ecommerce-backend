from django.contrib import admin
from oscar.apps.basket.admin import *  

from merchant_apps.store.meta.models import Store, StorePermission
from .models import Basket as StoreBasket

class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'store', 'owner', 'status', 'num_lines')
    list_filter = ('store', 'status')

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


# admin.site.register(StoreBasket, BasketAdmin)


















