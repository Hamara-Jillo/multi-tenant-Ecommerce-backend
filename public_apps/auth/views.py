from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.db import transaction

from .serializers import (
    UnifiedAuthenticationSerializer,
    TenantSelectionSerializer,
    UserRegistrationSerializer,
    MerchantCreationSerializer,
    TenantInvitationSerializer,
    InvitationAcceptanceSerializer,
    SocialAuthSerializer
)
from public_apps.merchant.models import TenantMembership
from public_apps.user.tokens import TenantToken, get_tokens_for_user_and_tenant

User = get_user_model()


class UnifiedLoginView(TokenObtainPairView):
    """
    Unified login that handles both single and multi-tenant scenarios
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UnifiedAuthenticationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        memberships = user.memberships.filter(is_active=True)
    
        if not memberships.exists():
            # This is your current state
            return Response({
                'user_id': user.id,
                'email': user.email,
                'requires_onboarding': True,
                'message': 'Welcome! You need to create a merchant or join an existing one.',
                'available_actions': {
                    'create_merchant': '/api/auth/create-merchant/',
                    'accept_invitation': '/api/auth/accept-invitation/'
                }
            })


class TenantSelectionView(APIView):
    """
    Handle tenant selection for multi-tenant users
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TenantSelectionSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class SocialAuthView(APIView):
    """
    Handle social authentication (Google, GitHub, etc.)
    """
    
    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    User registration without tenant assignment
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        return Response({
            'user_id': user.id,
            'email': user.email,
            'message': 'Registration successful. You can join existing merchants or create your own.'
        }, status=status.HTTP_201_CREATED)


class CreateMerchantView(APIView):
    """
    Create merchant/tenant with user assignment
    """
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = MerchantCreationSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        merchant = serializer.save()
        
        # Get the user (either authenticated or newly created)
        user = request.user if request.user.is_authenticated else serializer.created_user
        
        # Generate tokens for the new merchant
        token = TenantToken.for_user_and_tenant(user, merchant)
        
        return Response({
            'merchant': {
                'id': merchant.id,
                'name': merchant.name,
                'domain': merchant.domain_url,
                'schema_name': merchant.schema_name
            },
            'access': str(token.access_token),
            'refresh': str(token),
            'redirect_url': f"https://{merchant.domain_url}/dashboard/"
        }, status=status.HTTP_201_CREATED)


class InviteUserView(APIView):
    """
    Invite user to tenant
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, tenant_id):
        # Get tenant from user's memberships
        try:
            membership = request.user.memberships.get(
                tenant_id=tenant_id,
                is_active=True
            )
            tenant = membership.tenant
        except TenantMembership.DoesNotExist:
            return Response(
                {'error': 'You do not have access to this tenant'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user can invite (admin or owner)
        if membership.role not in ['merchant_admin'] and not membership.is_owner:
            return Response(
                {'error': 'You do not have permission to invite users'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TenantInvitationSerializer(
            data=request.data,
            context={'request': request, 'tenant': tenant}
        )
        serializer.is_valid(raise_exception=True)
        
        invitation = serializer.save()
        
        return Response({
            'invitation_id': invitation.id,
            'email': invitation.email,
            'role': invitation.role,
            'expires_at': invitation.expires_at,
            'invitation_url': f"https://{tenant.domain_url}/invite/{invitation.token}/"
        }, status=status.HTTP_201_CREATED)


class AcceptInvitationView(APIView):
    """
    Accept tenant invitation
    """
    
    def post(self, request):
        serializer = InvitationAcceptanceSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        result = serializer.save()
        user = result['user']
        tenant = result['tenant']
        
        # Generate tokens
        token = TenantToken.for_user_and_tenant(user, tenant)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'domain': tenant.domain_url,
                'schema_name': tenant.schema_name
            },
            'role': result['membership'].role,
            'access': str(token.access_token),
            'refresh': str(token),
            'redirect_url': f"https://{tenant.domain_url}/dashboard/"
        }, status=status.HTTP_200_OK)


class UserTenantsView(APIView):
    """
    Get user's accessible tenants
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        memberships = request.user.memberships.filter(
            is_active=True
        ).select_related('tenant')
        
        tenants = []
        for membership in memberships:
            tenant = membership.tenant
            tenants.append({
                'id': tenant.id,
                'name': tenant.name,
                'domain': tenant.domain_url,
                'schema_name': tenant.schema_name,
                'role': membership.role,
                'is_owner': membership.is_owner,
                'is_primary': request.user.primary_tenant_id == tenant.id,
                'dashboard_url': f"https://{tenant.domain_url}/dashboard/"
            })
        
        return Response({
            'tenants': tenants,
            'count': len(tenants)
        })


class SwitchTenantView(APIView):
    """
    Switch to a different tenant
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        tenant_id = request.data.get('tenant_id')
        
        if not tenant_id:
            return Response(
                {'error': 'tenant_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            membership = request.user.memberships.get(
                tenant_id=tenant_id,
                is_active=True
            )
            tenant = membership.tenant
        except TenantMembership.DoesNotExist:
            return Response(
                {'error': 'You do not have access to this tenant'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate new tokens for the selected tenant
        token = TenantToken.for_user_and_tenant(request.user, tenant)
        
        # Optionally update primary tenant
        if request.data.get('set_as_primary', False):
            request.user.primary_tenant = tenant
            request.user.save()
        
        return Response({
            'access': str(token.access_token),
            'refresh': str(token),
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'domain': tenant.domain_url,
                'schema_name': tenant.schema_name,
                'role': membership.role
            },
            'redirect_url': f"https://{tenant.domain_url}/dashboard/"
        })





