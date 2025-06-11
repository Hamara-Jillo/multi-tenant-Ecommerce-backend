from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

class MerchantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            user = getattr(request, 'user', None)
            tenant = getattr(request, 'tenant', None)

            if not user.is_authenticated:
                return self.get_response(request)
            
            if not tenant:
                logger.error("No tenant found in request")
                raise PermissionDenied("Tenant context is required")
            
            if not user.is_platform_admin:
                # Get user's merchant from schema_name
                from public_apps.merchant.models import Merchant
                try:
                    user_merchant = Merchant.objects.get(id=request.tenant)
                except Merchant.DoesNotExist:
                    logger.error(f"User {user.email} has invalid schema_name: {user.schema_name}")
                    raise PermissionDenied("Invalid tenant association")
                
                if tenant != user_merchant:
                    logger.critical(f"User {user.email} tried accessing {tenant.name} admin")
                    raise PermissionDenied("Tenant mismatch detected")
        return self.get_response(request)
    
     