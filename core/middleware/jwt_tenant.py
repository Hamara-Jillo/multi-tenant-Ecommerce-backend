from django.utils.deprecation import MiddlewareMixin
from django_tenants.utils import get_tenant_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

class JWTTenantMiddleware(MiddlewareMixin):
    """
    Middleware that processes JWT tokens for tenant-aware authentication.
    """
    
    def process_request(self, request):
        # Skip processing if this isn't an API request
        if not request.path.startswith('/api/'):
            return None
            
        # Initialize JWT authentication
        jwt_auth = JWTAuthentication()
        
        # Try to authenticate with JWT
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result is not None:
                user, token = auth_result
                
                # Set request.user to the authenticated user
                request.user = user
                
                # Store token payload for use in other middleware/views
                if token:
                    request.token_payload = token.payload
                    
                    # If there's schema information in the token, set it on the request
                    if 'schema_name' in token.payload:
                        request.tenant_from_jwt = token.payload['schema_name']
        except Exception:
            # If JWT authentication fails, continue without setting user
            pass
            
        return None