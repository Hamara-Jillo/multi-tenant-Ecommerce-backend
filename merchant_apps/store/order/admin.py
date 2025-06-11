from oscar.apps.order.admin import *  # noqa
from django.contrib import admin
from oscar.apps.order.admin import OrderAdmin as CoreOrderAdmin

from merchant_apps.store.meta.models import StorePermission
from .models import Order as StoreOrder

class OrderAdmin(CoreOrderAdmin):
    list_display = ('number', 'store', 'total_incl_tax', 'status', 'date_placed')
    list_filter = ('store', 'status')
    search_fields = ('number', 'store__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
        return qs.filter(store__in=permitted_stores)

    def has_add_permission(self, request):
        return request.user.is_platform_admin or request.tenant is not None

    def has_change_permission(self, request, obj=None):
        if request.user.is_platform_admin:
            return True
        if obj and StorePermission.objects.filter(merchant=request.tenant, store=obj.store).exists():
            return True
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.is_platform_admin:
            return True
        if obj and StorePermission.objects.filter(merchant=request.tenant, store=obj.store).exists():
            return True
        return False

admin.site.unregister(Order)  # Unregister Oscar’s default
admin.site.register(StoreOrder, OrderAdmin)