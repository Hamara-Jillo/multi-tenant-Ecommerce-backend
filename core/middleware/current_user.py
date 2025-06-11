# current_user.py
from threading import local
from django_tenants.utils import get_tenant_model
from django.core.exceptions import PermissionDenied

_thread_locals = local()

class CurrentMerchantUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user and tenant in thread-local storage
        _thread_locals.user = request.user
        _thread_locals.tenant = self._resolve_tenant(request)
        
        response = self.get_response(request)
        
        # Cleanup after response
        del _thread_locals.user
        del _thread_locals.tenant
        
        return response

    def _resolve_tenant(self, request):
        """Extract tenant from header or JWT claim"""
        tenant_schema = request.headers.get('X-Tenant-ID') or \
                       request.auth.get('tenant_id') if hasattr(request, 'auth') else None
        
        if tenant_schema:
            TenantModel = get_tenant_model()
            try:
                return TenantModel.objects.get(schema_name=tenant_schema)
            except TenantModel.DoesNotExist:
                if request.user.is_platform_admin:
                    return None  # Allow platform admins to work without tenant context
                raise PermissionDenied("Invalid tenant schema")
        return None

def get_current_user():
    """Retrieve current user from thread locals"""
    return getattr(_thread_locals, 'user', None)

def get_current_tenant():
    """Retrieve current tenant from thread locals"""
    return getattr(_thread_locals, 'tenant', None)