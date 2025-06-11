# public_apps/user/tokens.py
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django_tenants.utils import get_tenant_model, schema_context
from datetime import timedelta
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class TenantAwareTokenMixin:
    """
    Enhanced mixin for tenant-aware tokens
    """
    @classmethod
    def for_user_and_tenant(cls, user, tenant):
        """
        Create token for specific user and tenant combination
        """
        token = cls()
        
        # Standard user info
        token.payload.update({
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
        
        # Tenant-specific info
        if tenant:
            try:
                membership = user.tenantmembership_set.get(tenant=tenant, is_active=True)
                token.payload.update({
                    'tenant_id': tenant.id,
                    'tenant_schema': tenant.schema_name,
                    'tenant_name': tenant.name,
                    'tenant_domain': tenant.domain_url,
                    'role': membership.role,
                    'permission_level': membership.permission_level,
                    'is_owner': membership.is_owner,
                })
            except Exception as e:
                logger.warning(f"Could not get membership for user {user.id} in tenant {tenant.id}: {e}")
        
        return token
    
    @classmethod
    def for_user(cls, user):
        """
        Create token for user with their primary tenant
        """
        tenant = user.primary_tenant
        return cls.for_user_and_tenant(user, tenant)

    def get_user_and_tenant(self):
        """
        Get user and tenant objects from token payload
        """
        try:
            user_id = self.payload.get('user_id')
            tenant_id = self.payload.get('tenant_id')
            
            user = User.objects.get(id=user_id) if user_id else None
            tenant = get_tenant_model().objects.get(id=tenant_id) if tenant_id else None
            
            return user, tenant
        except Exception as e:
            logger.warning(f"Could not retrieve user/tenant from token: {e}")
            return None, None
    
    def validate_tenant_access(self):
        """
        Validate that the user still has access to the tenant
        """
        user, tenant = self.get_user_and_tenant()
        
        if not user or not tenant:
            raise TokenError("Invalid token payload")
        
        if not user.can_access_tenant(tenant):
            raise TokenError("User no longer has access to this tenant")
        
        return True


class UniversalToken(TenantAwareTokenMixin, RefreshToken):
    """
    Universal token that can be used across the platform
    """
    token_type = 'universal'
    lifetime = settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))


class TenantToken(TenantAwareTokenMixin, RefreshToken):
    """
    Tenant-specific token with extended payload
    """
    token_type = 'tenant'
    lifetime = settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))


class MerchantToken(TenantToken):
    """
    Token specifically for merchant users
    """
    token_type = 'merchant'
    
    @classmethod
    def for_user_and_tenant(cls, user, tenant):
        token = super().for_user_and_tenant(user, tenant)
        
        # Add merchant-specific claims
        token.payload.update({
            'is_merchant': True,
            'merchant_plan': tenant.plan_type if tenant else None,
        })
        
        return token


class CustomerToken(TenantToken):
    """
    Token for customer users
    """
    token_type = 'customer'
    
    @classmethod
    def for_user_and_tenant(cls, user, tenant):
        token = super().for_user_and_tenant(user, tenant)
        
        # Add customer-specific claims
        token.payload.update({
            'is_customer': True,
        })
        
        # Add store info if applicable
        if hasattr(user, 'store') and user.store:
            token.payload['store_id'] = user.store.id
        
        return token


class GuestToken(RefreshToken):
    """
    Token for guest users (anonymous shopping)
    """
    token_type = 'guest'
    lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(hours=24))
    
    @classmethod
    def for_tenant(cls, tenant):
        """
        Create guest token for a specific tenant
        """
        token = cls()
        
        if tenant:
            token.payload.update({
                'is_guest': True,
                'tenant_id': tenant.id,
                'tenant_schema': tenant.schema_name,
                'tenant_domain': tenant.domain_url,
            })
        
        return token


class SwitchTenantToken(RefreshToken):
    """
    Temporary token for tenant switching
    """
    token_type = 'switch'
    lifetime = timedelta(minutes=5)  # Short-lived
    
    @classmethod
    def for_switch(cls, user, from_tenant, to_tenant):
        """
        Create token for tenant switching
        """
        token = cls()
        
        token.payload.update({
            'user_id': user.id,
            'from_tenant_id': from_tenant.id if from_tenant else None,
            'to_tenant_id': to_tenant.id,
            'is_switch_token': True,
        })
        
        return token


# Enhanced utility functions
def get_tokens_for_user_and_tenant(user, tenant, token_class=TenantToken):
    """
    Get refresh and access tokens for user and tenant
    """
    refresh = token_class.for_user_and_tenant(user, tenant)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'token_type': 'Bearer',
    }


def get_universal_tokens_for_user(user):
    """
    Get universal tokens that work across all user's tenants
    """
    refresh = UniversalToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'token_type': 'Bearer',
    }


def switch_tenant_context(token, new_tenant_id):
    """
    Switch tenant context for a token
    """
    user, current_tenant = token.get_user_and_tenant()
    
    if not user:
        raise TokenError("Invalid token")
    
    # Get new tenant
    try:
        new_tenant = get_tenant_model().objects.get(id=new_tenant_id)
    except:
        raise TokenError("Invalid tenant")
    
    # Check access
    if not user.can_access_tenant(new_tenant):
        raise TokenError("User doesn't have access to this tenant")
    
    # Create new token for the new tenant
    new_token = token.__class__.for_user_and_tenant(user, new_tenant)
    
    return {
        'refresh': str(new_token),
        'access': str(new_token.access_token),
        'tenant_switched': True,
    }


# Token validation middleware helper
def validate_token_tenant_access(token):
    """
    Validate that token's tenant access is still valid
    """
    try:
        if hasattr(token, 'validate_tenant_access'):
            return token.validate_tenant_access()
        return True
    except TokenError:
        return False


# Custom token serializer for DRF
class TenantAwareTokenSerializer:
    """
    Serializer for tenant-aware tokens
    """
    def __init__(self, token):
        self.token = token
    
    def to_dict(self):
        user, tenant = self.token.get_user_and_tenant()
        
        data = {
            'access': str(self.token.access_token),
            'refresh': str(self.token),
            'token_type': 'Bearer',
            'expires_in': self.token.access_token.lifetime.total_seconds(),
        }
        
        if user:
            data['user'] = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        
        if tenant:
            data['tenant'] = {
                'id': tenant.id,
                'name': tenant.name,
                'domain': tenant.domain_url,
                'schema': tenant.schema_name,
            }
        
        return data