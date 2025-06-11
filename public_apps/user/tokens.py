
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django_tenants.utils import get_tenant_model
from datetime import timedelta
from django.conf import settings
from django.db import connection

class TenantAwareTokenMixin:
    """
    Mixin to add tenant and user information to token payload.
    """
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        tenant = getattr(connection, 'tenant', None)

        # Add tenant info
        token['tenant_schema'] = str(getattr(tenant, 'schema_name', '')) if tenant else None
        token['role'] = getattr(user, 'role', None)
        token['email'] = getattr(user, 'email', None)

        # Add store info if applicable
        if hasattr(user, 'store') and user.store:
            token['store_id'] = user.store.id

        return token

class UserToken(TenantAwareTokenMixin, RefreshToken):
    """
    Token for customers, with tenant and user info.
    """
    token_type = 'customer'
    lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=60))

class MerchantToken(TenantAwareTokenMixin, RefreshToken):
    """
    Token for merchant users, with tenant and user info.
    """
    token_type = 'merchant'
    lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=60))

class GuestToken(RefreshToken):
    """
    Temporary token for guest users.
    """
    token_type = 'guest'
    lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=60))

    @classmethod
    def for_request(cls, request=None):
        token = cls()
        tenant = getattr(connection, 'tenant', None)

        token.payload.update({
            'is_guest': True,
            'tenant_schema': str(getattr(tenant, 'schema_name', '')) if tenant else None
        })

        return token

# Utility functions for compatibility with SimpleJWT serializers/views

def get_tokens_for_user(user, token_class=MerchantToken):
    """
    Returns a dict with refresh and access tokens for the given user.
    """
    refresh = token_class.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
