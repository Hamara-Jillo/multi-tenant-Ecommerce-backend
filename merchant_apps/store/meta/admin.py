from django.contrib import admin
from django.contrib.messages import success
from merchant_apps.store.catalogue.models import Product
from public_apps.merchant.models import Merchant
from .models import Store, StorePermission
import logging

logger = logging.getLogger(__name__)

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    fields = ('title', 'upc', 'description', 'is_public', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at') 

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    # list_display = ('name', 'slug', 'is_active')
    # search_fields = ('name', 'slug')
    # list_filter = ('is_active',)
    inlines = [ProductInline]
    list_display = ('name', 'slug', 'product_count', 'is_active')

    def product_count(self, obj):
        return obj.catalogue_products.count()
    product_count.short_description = "Products"

    def get_queryset(self, request):
        """Filter stores based on merchant permissions"""
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        if not request.tenant:
            return qs.prefetch_related('products', 'merchants')
        # Include stores through StorePermission
        merchant = request.tenant
        return qs.filter(storepermission__merchant=merchant).distinct().prefetch_related('products', 'merchants')

    def save_model(self, request, obj, form, change):
        """Handle store creation/update with automatic permission assignment"""
        super().save_model(request, obj, form, change)
        if not change:  # Only for new stores
            # Create store permission for the creating tenant
            merchant = request.tenant
            StorePermission.objects.get_or_create(
                store=obj,
                merchant=merchant,
            )
            logger.info(f"Created store permission for {merchant.name} on store {obj.name}")
            success(request, f"Store '{obj.name}' created successfully!")

    def has_view_permission(self, request, obj=None):
        """Control store visibility"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_platform_admin:
            return True
        if obj is None:
            return True  # Allow list view
        # Check store permission
        return StorePermission.objects.filter(
            store=obj,
            merchant=request.tenant
        ).exists()

    def has_change_permission(self, request, obj=None):
        """Control store editability"""
        if request.user.is_platform_admin:
            return True
        if obj is None:
            return True  # Allow displaying change list
        # Check store permission
        merchant = request.tenant

        return StorePermission.objects.filter(
            store=obj,
            merchant=merchant
        ).exists()

    def has_add_permission(self, request):
        """Allow tenant admins to add stores if tenant is set"""
        return request.user.is_authenticated and request.tenant is not None

    def has_delete_permission(self, request, obj=None):
        """Only platform admins can delete stores"""
        return request.user.is_platform_admin

    # def has_add_permission(self, request):
    #     return True  # Explicitly allow adding stores
        
    # def has_change_permission(self, request, obj=None):
    #     return True
        
    # def has_delete_permission(self, request, obj=None):
    #     return True