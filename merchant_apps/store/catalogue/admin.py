from oscar.apps.catalogue.admin import (
    Product,
    ProductClass,
    Category,
    ProductAttributeValue,
    ProductImage,
    ProductRecommendation,
    AttributeOption,
    AttributeOptionGroup,
    ProductCategory,
    Option
)

from django.contrib import admin
from django_tenants.utils import tenant_context

from merchant_apps.store.meta.models import Store, StorePermission
from .models import (
    Product as StoreProduct, 
    ProductClass as StoreProductClass, 
    Category as StoreCategory, 
    ProductAttributeValue as StoreProductAttributeValue, 
    ProductImage as StoreProductImage, 
    ProductRecommendation as StoreProductRecommendation,
    AttributeOption as StoreAttributeOption, 
    AttributeOptionGroup as StoreAttributeOptionGroup, 
    ProductCategory as StoreProductCategory, 
    Option as StoreOption
    )
# @admin.register(StoreProduct)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'upc', 'store', 'created_at', 'updated_at']
    list_filter = ['store', 'created_at']
    search_fields = ['title', 'upc']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            return qs.filter(store__merchant=request.tenant)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store" and not request.user.is_platform_admin:
            kwargs["queryset"] = Store.objects.filter(merchant=request.tenant)

        if db_field.name == "product_class":
            kwargs["queryset"] = StoreProductClass.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.store and hasattr(request, 'tenant'):
            # If no store is set, try to get the first store of the tenant
            store = Store.objects.filter(merchant=request.tenant).first()
            if store:
                obj.store = store
        super().save_model(request, obj, form, change)

class ProductClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'requires_shipping', 'track_stock')
    
    def has_add_permission(self, request):
        """Allow platform admins AND merchants to add product classes"""
        return request.user.is_authenticated  # Or request.user.is_merchant_admin
    
class MerchantProductClassAdmin(ProductClassAdmin):
    def get_queryset(self, request):
        """Restrict product classes to the tenant's schema"""
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            return qs.filter(store=request.tenant.default_store)
        return qs

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'slug')
    list_filter = ('store',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            permitted_stores = StorePermission.objects.filter(
                merchant=request.tenant
            ).values_list('store_id', flat=True)
            return qs.filter(store_id__in=permitted_stores)
        return qs

# --------------------------
# Product Attribute Values
# --------------------------
# @admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value_boolean')
    list_filter = ('attribute',)
    search_fields = ('product__title', 'attribute__name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            permitted_stores = StorePermission.objects.filter(
                merchant=request.tenant
            ).values_list('store', flat=True)
            return qs.filter(product__store__in=permitted_stores)
        return qs

# --------------------------
# Product Images
# --------------------------
# @admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'display_order')
    list_filter = ('product__store',)
    raw_id_fields = ('product',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            return qs.filter(product__store__merchant=request.tenant)
        return qs

# --------------------------
# Product Recommendations
# --------------------------
# @admin.register(ProductRecommendation)
class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ('primary', 'recommendation', 'ranking')
    raw_id_fields = ('primary', 'recommendation')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['primary', 'recommendation']:
            kwargs["queryset"] = Product.objects.filter(
                store__storepermission__merchant=request.tenant
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# --------------------------
# Attribute Options
# --------------------------
class AttributeOptionInline(admin.TabularInline):
    model = StoreAttributeOption
    extra = 1

# @admin.register(AttributeOptionGroup)
class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'option_summary')
    inlines = [AttributeOptionInline]
    
    def option_summary(self, obj):
        return ", ".join([option.option for option in obj.options.all()])
    option_summary.short_description = 'Options'

# @admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    list_display = ('group', 'option')
    list_filter = ('group',)
    search_fields = ('option',)

# --------------------------
# Product Categories
# --------------------------
# @admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'category')
    list_filter = ('category__store',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.filter(
                store__storepermission__merchant=request.tenant
            )
        elif db_field.name == "category":
            kwargs["queryset"] = StoreCategory.objects.filter(
                store__storepermission__merchant=request.tenant
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# --------------------------
# Options (Tenant-aware)
# --------------------------
# @admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'type', 'required')
    list_filter = ('store', 'type')
    search_fields = ('name', 'store__name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            return qs.filter(store__storepermission__merchant=request.tenant)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store":
            kwargs["queryset"] = Store.objects.filter(
                storepermission__merchant=request.tenant
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.store_id and not request.user.is_platform_admin:
            obj.store = request.tenant.default_store
        super().save_model(request, obj, form, change)




admin.site.unregister(Product)  
admin.site.unregister(ProductClass) 
admin.site.unregister(Category) 

admin.site.unregister(ProductAttributeValue)  
admin.site.unregister(ProductImage) 
# admin.site.unregister(ProductRecommendation) 

# admin.site.unregister(AttributeOption)  
admin.site.unregister(AttributeOptionGroup) 
admin.site.unregister(ProductCategory) 
admin.site.unregister(Option) 


admin.site.register(StoreProduct, ProductAdmin)
admin.site.register(StoreProductClass, ProductClassAdmin)
admin.site.register(StoreCategory, CategoryAdmin)

admin.site.register(StoreProductAttributeValue, ProductAttributeValueAdmin)  
admin.site.register(StoreProductImage, ProductImageAdmin) 
admin.site.register(StoreProductRecommendation, ProductRecommendationAdmin) 

admin.site.register(StoreAttributeOption, AttributeOptionAdmin)  
admin.site.register(StoreAttributeOptionGroup, AttributeOptionGroupAdmin) 
admin.site.register(StoreProductCategory, ProductCategoryAdmin) 
admin.site.register(StoreOption, OptionAdmin) 

