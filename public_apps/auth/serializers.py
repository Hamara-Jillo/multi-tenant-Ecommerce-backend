# public_apps/auth/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import secrets
from django.db import IntegrityError, transaction

from public_apps.merchant.models import Domain, Merchant, TenantMembership, TenantInvitation
from public_apps.user.tokens import TenantToken

User = get_user_model()

class UnifiedAuthenticationSerializer(TokenObtainPairSerializer):
    """
    Unified authentication that handles multi-tenant scenarios
    """
    
    def validate(self, attrs):
        # Standard email/password validation
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Authenticate user
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        
        # Get active tenant memberships
        memberships = user.memberships.filter(is_active=True).select_related('tenant')
        
        if not memberships.exists():
            raise serializers.ValidationError('User has no active tenant access')
        
        # Prepare response data
        data = {
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        # Handle multi-tenant scenario
        if memberships.count() > 1:
            data['requires_tenant_selection'] = True
            data['available_tenants'] = [
                {
                    'id': membership.tenant.id,
                    'name': membership.tenant.name,
                    'domain': membership.tenant.domain_url,
                    'role': membership.role,
                    'is_primary': user.primary_tenant_id == membership.tenant.id
                }
                for membership in memberships
            ]
        else:
            # Single tenant - generate tokens immediately
            membership = memberships.first()
            tenant = membership.tenant
            
            # Generate tenant-aware tokens
            token = TenantToken.for_user_and_tenant(user, tenant)
            
            data.update({
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
        
        return data


class TenantSelectionSerializer(serializers.Serializer):
    """
    Handle tenant selection for multi-tenant users
    """
    tenant_id = serializers.IntegerField()
    
    def validate_tenant_id(self, value):
        user = self.context['request'].user
        
        try:
            membership = user.memberships.get(
                tenant_id=value,
                is_active=True
            )
            return value
        except TenantMembership.DoesNotExist:
            raise serializers.ValidationError("Invalid tenant selection")
    
    def create(self, validated_data):
        user = self.context['request'].user
        tenant_id = validated_data['tenant_id']
        
        membership = user.memberships.get(
            tenant_id=tenant_id,
            is_active=True
        )
        
        tenant = membership.tenant
        
        # Generate tenant-specific tokens
        token = TenantToken.for_user_and_tenant(user, tenant)
        
        # Update primary tenant if user chooses
        if self.context['request'].data.get('set_as_primary'):
            user.primary_tenant = tenant
            user.save()
        
        return {
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
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration without tenant assignment
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


# class MerchantCreationSerializer(serializers.ModelSerializer):
#     """
#     Create merchant/tenant with user assignment
#     """
#     user_data = UserRegistrationSerializer(required=False)
    
#     class Meta:
#         model = Merchant
#         fields = [
#             'name', 'contact_email', 'contact_phone', 'timezone', 
#             'default_language', 'business_type', 'user_data'
#         ]
    
#     def create(self, validated_data):
#         user_data = validated_data.pop('user_data', None)
#         domains_data = validated_data.pop('domains', [])
#         request = self.context['request']

#         # Get or create user
#         if request.user.is_authenticated:
#             user = request.user
#         elif user_data:
#             user_serializer = UserRegistrationSerializer(data=user_data)
#             user_serializer.is_valid(raise_exception=True)
#             user = user_serializer.save()
#         else:
#             raise serializers.ValidationError("User data required for unauthenticated requests")

#         # Auto-generate schema_name if not provided
#         if 'schema_name' not in validated_data:
#             validated_data['schema_name'] = self._generate_schema_name(validated_data['name'])

#         try:
#             with transaction.atomic():
#                 # Create merchant
#                 merchant = Merchant.objects.create(**validated_data)

#                 # Create domains if provided
#                 for domain_data in domains_data:
#                     Domain.objects.create(tenant=merchant, **domain_data)

#                 # Create TenantMembership for the user
#                 TenantMembership.objects.create(
#                     user=user,
#                     tenant=merchant,
#                     role='merchant_admin',
#                     is_owner=True,
#                     is_active=True
#                 )

#                 # Set as primary tenant if user has no primary tenant
#                 if not user.primary_tenant:
#                     user.primary_tenant = merchant
#                     user.save()

#         except IntegrityError as e:
#             if 'unique constraint' in str(e):
#                 raise serializers.ValidationError("Merchant with this schema_name already exists.")
#             raise

#         return merchant  # <-- Only return the model instance!


class TenantInvitationSerializer(serializers.ModelSerializer):
    """
    Handle tenant invitations
    """
    class Meta:
        model = TenantInvitation
        fields = ['email', 'role']
    
    def create(self, validated_data):
        tenant = self.context['tenant']
        invited_by = self.context['request'].user
        
        # Check if user can invite
        if not tenant.can_add_user():
            raise serializers.ValidationError("Maximum user limit reached")
        
        # Generate token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=7)
        
        invitation = TenantInvitation.objects.create(
            tenant=tenant,
            invited_by=invited_by,
            token=token,
            expires_at=expires_at,
            **validated_data
        )
        
        # TODO: Send invitation email
        
        return invitation


class InvitationAcceptanceSerializer(serializers.Serializer):
    """
    Handle invitation acceptance
    """
    token = serializers.CharField()
    user_data = UserRegistrationSerializer(required=False)
    
    def validate_token(self, value):
        try:
            invitation = TenantInvitation.objects.get(token=value)
            if not invitation.is_valid():
                raise serializers.ValidationError("Invitation has expired or is invalid")
            return value
        except TenantInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token")
    
    def create(self, validated_data):
        token = validated_data['token']
        user_data = validated_data.get('user_data')
        request = self.context['request']
        
        invitation = TenantInvitation.objects.get(token=token)
        
        # Get or create user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Check if user exists
            try:
                user = User.objects.get(email=invitation.email)
                # User exists but not authenticated - they need to login first
                raise serializers.ValidationError({
                    'login_required': True,
                    'email': invitation.email,
                    'message': 'Please login to accept this invitation'
                })
            except User.DoesNotExist:
                # Create new user
                if not user_data:
                    raise serializers.ValidationError("User registration data required")
                
                user_serializer = UserRegistrationSerializer(data=user_data)
                user_serializer.is_valid(raise_exception=True)
                user = user_serializer.save()
        
        # Create membership
        membership = TenantMembership.objects.create(
            user=user,
            tenant=invitation.tenant,
            role=invitation.role,
            invited_by=invitation.invited_by,
            is_active=True,
            invitation_accepted_at=timezone.now()
        )
        
        # Update invitation
        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.save()
        
        # Set as primary if user has no primary tenant
        if not user.primary_tenant:
            user.primary_tenant = invitation.tenant
            user.save()
        
        return {
            'user': user,
            'membership': membership,
            'tenant': invitation.tenant
        }
    
class SocialAuthSerializer(serializers.Serializer):
    """
    Handle social authentication
    """
    email = serializers.EmailField()
    provider = serializers.CharField(max_length=50)
    provider_id = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)
    avatar_url = serializers.URLField(required=False)
    
    def create(self, validated_data):
        email = validated_data['email']
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'provider': validated_data['provider'],
                'provider_id': validated_data['provider_id'],
                'first_name': validated_data.get('first_name', ''),
                'last_name': validated_data.get('last_name', ''),
                'avatar_url': validated_data.get('avatar_url'),
                'username': email.split('@')[0],
            }
        )
        
        if created:
            user.set_unusable_password()
            user.save()
        
        # Get active tenant memberships
        memberships = user.memberships.filter(is_active=True).select_related('tenant')
        
        # Prepare response data
        data = {
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_new_user': created
        }
        
        if not memberships.exists():
            # User has no tenant access - they need to join or create one
            data['requires_onboarding'] = True
            data['message'] = 'Welcome! You can join an existing merchant or create your own.'
        elif memberships.count() > 1:
            # Multi-tenant scenario
            data['requires_tenant_selection'] = True
            data['available_tenants'] = [
                {
                    'id': membership.tenant.id,
                    'name': membership.tenant.name,
                    'domain': membership.tenant.domain_url,
                    'role': membership.role,
                    'is_primary': user.primary_tenant_id == membership.tenant.id
                }
                for membership in memberships
            ]
        else:
            # Single tenant - generate tokens immediately
            membership = memberships.first()
            tenant = membership.tenant
            
            token = TenantToken.for_user_and_tenant(user, tenant)
            
            data.update({
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
        
        return data


# Enhanced MerchantCreationSerializer
class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary', 'ssl_enabled']

class MerchantCreationSerializer(serializers.ModelSerializer):
    user_data = UserRegistrationSerializer(required=False)
    domains = DomainSerializer(many=True, required=False)

    class Meta:
        model = Merchant
        fields = [
            'name', 'contact_email', 'contact_phone', 'timezone', 
            'default_language', 'business_type', 'user_data', 'domains'
        ]
        extra_kwargs = {
            'schema_name': {'required': False}
        }

    def validate_schema_name(self, value):
        """Ensure schema name follows PostgreSQL naming rules"""
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Schema name can only contain alphanumerics and underscores"
            )
        return value.lower()

    def _generate_schema_name(self, name):
        """Generate a unique schema name based on the merchant name"""
        base_name = name.lower().replace(' ', '_')
        schema_name = base_name
        counter = 0
        original_schema = schema_name
        while Merchant.objects.filter(schema_name=schema_name).exists():
            counter += 1
            schema_name = f"{original_schema}_{counter}"
        return schema_name

    def create(self, validated_data):
        user_data = validated_data.pop('user_data', None)
        domains_data = validated_data.pop('domains', [])
        request = self.context['request']

        # Get or create user
        if request.user.is_authenticated:
            user = request.user
        elif user_data:
            user_serializer = UserRegistrationSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
        else:
            raise serializers.ValidationError("User data required for unauthenticated requests")

        # Auto-generate schema_name if not provided
        if 'schema_name' not in validated_data:
            validated_data['schema_name'] = self._generate_schema_name(validated_data['name'])

        try:
            with transaction.atomic():
                # Create merchant
                merchant = Merchant.objects.create(**validated_data)
                merchant._create_admin_user()  # Ensure admin user is created
                
                # Create domains if provided
                # for domain_data in domains_data:
                #     Domain.objects.create(tenant=merchant, **domain_data)

                # Create TenantMembership for the user
                TenantMembership.objects.create(
                    user=user,
                    tenant=merchant,
                    role='merchant_admin',
                    is_owner=True,
                    is_active=True
                )

                # Set as primary tenant if user has no primary tenant
                if not user.primary_tenant:
                    user.primary_tenant = merchant
                    user.save()

        except IntegrityError as e:
            if 'unique constraint' in str(e):
                raise serializers.ValidationError("Merchant with this schema_name already exists.")
            raise

        return merchant  
