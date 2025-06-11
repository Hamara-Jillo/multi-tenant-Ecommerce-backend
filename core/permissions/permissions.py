from rest_framework import permissions

class IsPlatformAdmin(permissions.BasePermission):
    """
    Permission check for platform administrators only.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'public_admin'

class IsMerchantAdmin(permissions.BasePermission):
    """
    Permission check for merchant administrators only.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'merchant_admin'

class IsStoreManager(permissions.BasePermission):
    """
    Permission check for store managers only.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'store_manager'

class IsCustomer(permissions.BasePermission):
    """
    Permission check for store customers.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'store_customer'

class IsTenantMember(permissions.BasePermission):
    """
    Permission check for users belonging to the current tenant.
    """
    def has_permission(self, request, view):
        from django_tenants.utils import get_current_schema_name
        current_schema = get_current_schema_name()
        
        # Check if user's schema matches current schema or is a platform admin
        return (
            request.user.is_authenticated and 
            (request.user.schema_name == current_schema or request.user.role == 'public_admin')
        )

class IsStoreStaff(permissions.BasePermission):
    """
    Permission check for staff of a specific store.
    """
    def has_permission(self, request, view):
        # Basic authentication check
        if not request.user.is_authenticated:
            return False
            
        # Platform admins and merchant admins always have access
        if request.user.role in ['public_admin', 'merchant_admin']:
            return True
            
        # For store managers, check if they're assigned to the store
        # This would need store_id from URL or request parameter
        store_id = view.kwargs.get('store_id')
        
        if not store_id:
            return False
            
        return (
            request.user.role == 'store_manager' and
            request.user.store and request.user.store.id == int(store_id)
        )