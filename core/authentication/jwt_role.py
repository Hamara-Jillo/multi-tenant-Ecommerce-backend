# core/authentication.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django_tenants.utils import get_tenant
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
User = get_user_model()

def jwt_user_authentication_rule(user):
    """
    Custom user authentication rule for SimpleJWT.
    """
    # You can add custom checks here, e.g. user.is_active, user.role, etc.
    return True  # Continue with authentication

class TenantAwareJWTAuthentication(JWTAuthentication):
    """
    Custom authentication that's aware of the current tenant context
    """
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        tenant = get_tenant()
        
        # For merchant admins and store managers, verify they belong to this tenant
        if user.role in ['merchant_admin', 'store_manager']:
            if user.schema_name != tenant.schema_name:
                return None  # Deny access to this tenant
        
        return user

class TenantAwareAuthBackend(ModelBackend):
    """
    Backend that verifies a user's schema matches the current tenant
    for merchant_admin and store_manager roles
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # Try to fetch the user
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        # Validate password
        if user.check_password(password):
            tenant = get_tenant()
            
            # Platform admins can access any tenant
            if user.is_platform_admin:
                return user
                
            # Merchant admins and store managers must belong to current tenant
            if user.role in ['merchant_admin', 'store_manager']:
                if user.schema_name != tenant.schema_name:
                    return None  # Wrong tenant
            
            return user
        return None
    
class TenantAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        tenant = get_tenant()
        if tenant:
            token['tenant_schema'] = tenant.schema_name
            if hasattr(user, 'store') and user.store:
                token['store_id'] = user.store.id
        return token