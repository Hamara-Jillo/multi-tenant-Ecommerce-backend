from django.contrib import admin
from django.db import connection
from django_tenants.admin import TenantAdminMixin

from public_apps.user.admin import UserAdmin
from public_apps.user.models import User
from .models import Domain, Merchant
from merchant_apps.store.meta.models import StorePermission
from django.contrib.messages import success
from django.shortcuts import redirect
import logging
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


@admin.register(Merchant)
class MerchantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_filter = ('status', 'created_at')
    list_display = ('name', 'schema_name', 'domain_url', 'status')
    search_fields = ('name', 'schema_name', 'domain_url')
    actions = None

    # def get_stores(self, obj):
    #     """Display stores for this merchant with count"""
    #     stores = obj.stores.all()
    #     if not stores:
    #         return "No stores"
        
    #     store_names = ", ".join([store.name for store in stores])
    #     return f"{store_names}"
    # get_stores.short_description = 'Stores'
    

    def changelist_view(self, request, extra_context=None):
        """Redirect tenant admins to their own detail view, allow platform admins to see the list."""
        if not request.user.is_platform_admin:
            if not request.tenant:
                logger.error(f"User {request.user.email} has no tenant assigned")
                raise PermissionDenied("No tenant associated with user")
            logger.debug(f"Redirecting {request.user.email} to merchant {request.tenant.id}")
            return redirect('admin:public_app_merchant_change', request.tenant.id)
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        """Filter queryset to tenant’s own merchant for non-platform admins."""
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            return qs.filter(id=request.tenant.id)
        return qs

    def has_view_permission(self, request, obj=None):
        """Allow view access only to platform admins or the tenant’s own merchant."""
        if request.user.is_platform_admin:
            return True
        if obj and obj.id == request.tenant.id:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """Restrict changes to platform admins only."""
        return request.user.is_platform_admin
    
    def has_add_permission(self, request):
        """Restrict additions to platform admins only."""
        return request.user.is_platform_admin

    def get_form(self, request, obj=None, **kwargs):
        """Remove dangerous fields for non-platform admins"""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_platform_admin:
            form.base_fields.pop('schema_name', None)
            form.base_fields.pop('domain_url', None)
        return form

    def has_module_permission(self, request):
        """Control visibility of merchant module"""
        if not request.user.is_authenticated:
            return False
        # Only show module to platform admins and users with tenants
        return request.user.is_authenticated and (
            request.user.is_platform_admin or
            request.tenant is not None
        )

    def get_list_display(self, request):
        """Customize displayed fields based on user"""
        if request.user.is_platform_admin:
            return self.list_display
        # Regular users see limited fields
        return ('name', 'domain_url', 'status')


    def has_delete_permission(self, request, obj=None):
        """Only platform admins can delete merchants"""
        return request.user.is_platform_admin

    def delete_model(self, request, obj):
        """Handle single deletion with strict permission check"""
        if not request.user.is_platform_admin:
            logger.warning(f"Unauthorized deletion attempt of merchant {obj.name} by {request.user.email}")
            raise PermissionDenied("Only platform admins can delete merchants")
            
        try:
            logger.debug(f"Platform admin {request.user.email} attempting to delete merchant {obj.name}")
            
            # Delete store permissions first
            StorePermission.objects.filter(merchant=obj).delete()
            
            # Delete domains
            Domain.objects.filter(tenant=obj).delete()
            
            # Drop schema
            schema_name = obj.schema_name
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            
            # Finally delete the merchant
            obj.delete()
            
            logger.info(f"Successfully deleted merchant {obj.name}")
            success(request, f"Successfully deleted merchant {obj.name}")
        except Exception as e:
            logger.error(f"Error deleting merchant {obj.name}: {str(e)}")
            raise

    def get_actions(self, request):
        """Remove actions for tenant admins."""
        actions = super().get_actions(request)
        if not request.user.is_platform_admin and 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_selected(self, request, queryset):
        """Override delete_selected to enforce platform admin check"""
        if not request.user.is_platform_admin:
            msg = f"Security Alert: User {request.user.email} attempted bulk deletion of merchants"
            logger.warning(msg)
            self.message_user(request, "Only platform administrators can delete merchants", level='ERROR')
            return

        for obj in queryset:
            try:
                obj.delete()
                logger.info(f"Successfully deleted merchant {obj.name}")
            except Exception as e:
                logger.error(f"Failed to delete merchant {obj.name}: {str(e)}")
                self.message_user(request, f"Error deleting {obj.name}: {str(e)}", level='ERROR')
                return

        self.message_user(request, f"Successfully deleted {len(queryset)} merchants")
    delete_selected.short_description = "Delete selected merchants"


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Only for new merchants
            success(request, 
                f"""Merchant created successfully!
                Admin URL: http://{obj.domain_url}/admin/
                Admin Email: {obj.contact_email}
                Check the logs for the temporary password.
                """
            )
    def changelist_view(self, request, extra_context=None):
        """Override changelist view to enforce tenant isolation"""
        if not request.user.is_platform_admin:
            # Redirect to detail view for regular users
            try:
                return self.change_view(
                    request, 
                    str(request.tenant.id), 
                    extra_context=extra_context
                )
            except (AttributeError, Merchant.DoesNotExist):
                raise PermissionDenied("You don't have access to view merchants")
        return super().changelist_view(request, extra_context)

    def get_model_perms(self, request):
        """Control model permissions in admin index"""
        perms = super().get_model_perms(request)
        if not request.user.is_platform_admin:
            # Regular users can only view their own merchant
            perms['add'] = False
            perms['delete'] = False
            perms['change'] = False
        return perms

    def get_urls(self):
        """Override URLs to prevent list view access for regular users"""
        urls = super().get_urls()
        if not hasattr(self.model, '_meta'):
            return urls
            
        from django.urls import path
        from functools import update_wrapper
        
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        return [
            path('', wrap(self.changelist_view), name='%s_%s_changelist' % info),
        ] + urls

        
    
class MerchantAdminSite(admin.AdminSite):
    site_header = 'Multistore Administration'
    site_title = 'Multistore Admin'
    index_title = 'Administration'

    def has_permission(self, request):
        """Enhanced permission check"""
        # First check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Basic staff permission check
        if not request.user.is_active or not request.user.is_staff:
            logger.debug(f"User {request.user.email} failed basic permission check")
            return False

        # Platform admins always have access
        if request.user.is_platform_admin:
            logger.debug(f"Platform admin {request.user.email} granted access")
            return True

        # For regular users, check tenant context
        if not hasattr(request, 'tenant'):
            logger.warning("No tenant in request context")
            return False

        # Regular users must have a tenant
        if not request.tenant:
            logger.warning(f"User {request.user.email} has no tenant assigned")
            return False

        # Regular users can only access their own tenant's admin
        has_access = request.tenant.schema_name == request.tenant.schema_name
        logger.debug(
            f"User {request.user.email} accessing {request.tenant.schema_name} "
            f"admin: {'granted' if has_access else 'denied'}"
        )
        return has_access

    def get_app_list(self, request):
        app_list = super().get_app_list(request)

        if request.user.is_authenticated and not request.user.is_platform_admin:
            filtered_apps = []
            for app in app_list:
                filtered_models = []
                
                if app['app_label'] == 'catalogue':
                    # Include catalogue models for merchants
                    filtered_models = app['models']
                    # Set permissions
                    for model in filtered_models:
                        model['perms'].update({
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        })
                elif app['app_label'] == 'store_meta':
                    # Include store management models
                    filtered_models = app['models']
                
                if filtered_models:
                    app['models'] = filtered_models
                    filtered_apps.append(app)
            
            return filtered_apps
        
        return app_list




@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary', 'verified')
    list_filter = ('is_primary', 'verified')
    search_fields = ('domain',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        if request.user.is_platform_admin:
            return qs
        return qs.filter(tenant=request.tenant)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tenant":
            if not request.user.is_platform_admin:
                kwargs["queryset"] = Merchant.objects.filter(id=request.tenant.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

class PlatformAdminSite(admin.AdminSite):
    site_header = 'Platform Administration'
    site_title = 'Platform Admin'
    index_title = 'Platform Management'

    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_platform_admin

# Create platform admin instance
platform_admin = PlatformAdminSite(name='platform_admin')

# Register models only for platform admin
platform_admin.register(Merchant, MerchantAdmin)
platform_admin.register(Domain, DomainAdmin)
platform_admin.register(User, UserAdmin)

