# from oscar.apps.shipping.admin import * 
from django.contrib import admin
from oscar.apps.shipping.admin import (
    OrderChargesAdmin as CoreOrderChargesAdmin,
    WeightBasedAdmin as CoreWeightBasedAdmin,
    WeightBandInline as CoreWeightBandInline,
    WeightBand
)
from oscar.core.loading import get_model

from core.filters.simple_list_filter import EnabledFilter, StoreFilter
from .models import (
    ShippingMethod, 
    OrderAndItemCharges as StoreOrderAndItemCharges, 
    WeightBased as StoreWeightBased, 
    WeightBand as StoreWeightBand
    )

from merchant_apps.store.meta.models import StorePermission
from merchant_apps.store.partner.models import Partner as StorePartner
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


OrderAndItemCharges = get_model('shipping', 'OrderAndItemCharges')
WeightBased = get_model('shipping', 'WeightBased')

class WeightBandInline(CoreWeightBandInline):
    model = StoreWeightBand
    extra = 1

# class ShippingMethodAdmin(admin.ModelAdmin):
#     list_display = ('name', 'code', 'store', 'get_type')
#     list_filter = ('store',)
#     search_fields = ('name', 'code')

#     def get_type(self, obj):
#         if isinstance(obj, OrderAndItemCharges):
#             return "Order and Item Charges"
#         elif isinstance(obj, WeightBased):
#             return "Weight Based"
#         return "Unknown"
#     get_type.short_description = "Type"

class ShippingMethodChildAdmin(PolymorphicChildModelAdmin):
    base_model = ShippingMethod
    list_display = ('name', 'code', 'store', 'enabled')
    list_filter = ('store', 'enabled')
    search_fields = ('name', 'code')

class OrderAndItemChargesAdmin(PolymorphicChildModelAdmin):
    base_model = ShippingMethod
    list_display = ('name', 'code', 'parent_store', 'parent_enabled', 'price_per_order', 'price_per_item', 'free_shipping_threshold')
    list_filter = (StoreFilter, EnabledFilter)
    search_fields = ('name', 'code')

    def parent_store(self, obj):
        return obj.shippingmethod_ptr.store
    parent_store.short_description = "Store"

    def parent_enabled(self, obj):
        return obj.shippingmethod_ptr.enabled
    parent_enabled.short_description = "Enabled"

class WeightBasedAdmin(PolymorphicChildModelAdmin):
    base_model = ShippingMethod
    list_display = ('name', 'code', 'parent_store', 'parent_enabled', 'default_weight')
    list_filter = (StoreFilter, EnabledFilter)
    search_fields = ('name', 'code')
    
    def parent_store(self, obj):
        return obj.shippingmethod_ptr.store
    parent_store.short_description = "Store"

    def parent_enabled(self, obj):
        return obj.shippingmethod_ptr.enabled
    parent_enabled.short_description = "Enabled"



class ShippingMethodParentAdmin(PolymorphicParentModelAdmin):
    base_model = ShippingMethod
    child_models = (StoreOrderAndItemCharges, StoreWeightBased)
    list_display = ('name', 'code', 'parent_store', 'parent_enabled', 'polymorphic_ctype')
    list_filter = ()  # or use custom filters if needed

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only call non_polymorphic() if it exists
        if hasattr(qs, 'non_polymorphic'):
            return qs.non_polymorphic()
        if not request.user.is_platform_admin:
            return qs.filter(store__merchant=request.tenant)
        return qs

    def parent_store(self, obj):
        return obj.get_real_instance().shippingmethod_ptr.store
    parent_store.short_description = "Store"

    def parent_enabled(self, obj):
        return obj.get_real_instance().shippingmethod_ptr.enabled
    parent_enabled.short_description = "Enabled"

    def polymorphic_ctype(self, obj):
        return obj.get_real_instance_class().__name__
    polymorphic_ctype.short_description = "Type"



# class OrderAndItemChargesAdmin(CoreOrderChargesAdmin):
#     list_display = ('name', 'code', 'price_per_order', 'price_per_item', 'free_shipping_threshold')
#     list_filter = ('countries',)
    
#     def get_queryset(self, request):
#         """Filter stores based on merchant permissions"""
#         qs = super().get_queryset(request)
#         if request.user.is_platform_admin:
#             return qs
    
# class WeightBasedAdmin(CoreWeightBasedAdmin):
#     list_display = ('name', 'code', 'default_weight')
#     list_filter = ('countries',)

#     def get_queryset(self, request):
#         """Filter stores based on merchant permissions"""
#         qs = super().get_queryset(request)
#         if request.user.is_platform_admin:
#             return qs

admin.site.unregister(OrderAndItemCharges)
admin.site.unregister(WeightBased)
admin.site.register(ShippingMethod, ShippingMethodParentAdmin)
admin.site.register(StoreOrderAndItemCharges, OrderAndItemChargesAdmin)
admin.site.register(StoreWeightBased, WeightBasedAdmin)