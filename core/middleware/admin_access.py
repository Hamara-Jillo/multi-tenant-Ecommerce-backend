from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        merchant = request.tenant  # Merchant instance

        # Block tenant access to platform admin
        if request.path.startswith('/platform/') and merchant.schema_name != 'public':  # Use schema_name instead
            logger.warning(f"Merchant {merchant.name} attempted to access platform admin")
            raise PermissionDenied("Platform admin is only accessible from public schema")

        # Block public schema access to tenant admin
        if request.path.startswith('/admin/') and merchant.schema_name == 'public':
            logger.warning("Public schema attempted to access merchant admin")
            raise PermissionDenied("Merchant admin is only accessible from merchant schemas")

        return self.get_response(request)