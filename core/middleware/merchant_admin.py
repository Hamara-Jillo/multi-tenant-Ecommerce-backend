import logging
from django.core.exceptions import PermissionDenied
# from django.contrib.auth.middleware import AuthenticationMiddleware

logger = logging.getLogger(__name__)

class MerchantAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            logger.debug(f"Admin request to {request.path}")
            
            if not hasattr(request, 'tenant'):
                logger.error("No tenant found in request")
                raise PermissionDenied("Tenant admin requires tenant context")
            
            # Check if authentication middleware has run
            if not hasattr(request, 'user'):
                logger.debug("Authentication middleware hasn't run yet")
                return self.get_response(request)
                
            # Allow anonymous users (will be handled by admin login)
            if not request.user.is_authenticated:
                logger.debug("Anonymous user accessing admin")
                return self.get_response(request)
                
            # Allow platform admins to access everything
            if getattr(request.user, 'is_platform_admin', False):
                logger.debug(f"Platform admin {request.user.email} accessing admin")
                return self.get_response(request)
                
            # Check tenant access
            user_tenant_id = getattr(request.tenant, 'id', None)
            if not user_tenant_id or request.tenant.id != user_tenant_id:
                logger.warning(
                    f"User {request.user.email} attempted to access "
                    f"tenant {request.tenant.name}'s admin"
                )
                raise PermissionDenied("You can only access your own tenant's admin")
                
        return self.get_response(request)