from oscar.apps.offer.admin import (
ConditionalOffer,
Condition,
Range,
Benefit,
)
from django.contrib import admin
from .models import Benefit as StoreBenefit,Condition as StoreCondition,ConditionalOffer as StoreConditionalOffer,Range as StoreRange
from merchant_apps.store.meta.models import Store, StorePermission

# @admin.register(ConditionalOffer)
class ConditionalOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'offer_type', 'start_datetime', 'end_datetime')
    list_filter = ('store', 'offer_type')
    search_fields = ('name', 'store__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:  # Platform admins see all offers
            return qs
        permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
        return qs.filter(store__in=permitted_stores)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store":
            permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
            kwargs["queryset"] = Store.objects.filter(id__in=permitted_stores)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

# @admin.register(Range)
class RangeAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'includes_all_products')
    list_filter = ('store',)
    search_fields = ('name', 'store__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
        return qs.filter(store__in=permitted_stores)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store":
            permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
            kwargs["queryset"] = Store.objects.filter(id__in=permitted_stores)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('store', 'type', 'value')
    list_filter = ('store', 'type')
    search_fields = ('store__name', 'type', 'value')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
        return qs.filter(store__in=permitted_stores)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store":
            permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
            kwargs["queryset"] = Store.objects.filter(id__in=permitted_stores)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

class BenefitAdmin(admin.ModelAdmin):
    list_display = ('store', 'type', 'value')
    list_filter = ('store', 'type')
    search_fields = ('store__name', 'type', 'value')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
        return qs.filter(store__in=permitted_stores)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store":
            permitted_stores = StorePermission.objects.filter(merchant=request.tenant).values_list('store', flat=True)
            kwargs["queryset"] = Store.objects.filter(id__in=permitted_stores)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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


admin.site.unregister(ConditionalOffer)
admin.site.unregister(Condition)
admin.site.unregister(Range)
admin.site.unregister(Benefit)
admin.site.register(StoreConditionalOffer, ConditionalOfferAdmin)
admin.site.register(StoreRange, RangeAdmin)
admin.site.register(StoreCondition, ConditionAdmin)
admin.site.register(StoreBenefit, BenefitAdmin)