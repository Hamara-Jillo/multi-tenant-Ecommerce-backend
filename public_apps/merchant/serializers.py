
from django.db import connection
from rest_framework import serializers
from django_tenants.utils import schema_context, get_tenant_model
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from public_apps.user.tokens import MerchantToken, get_tokens_for_user
from .models import Merchant, Domain

tenant = get_tenant_model()

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary', 'ssl_enabled']

class MerchantSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, required=False)
    password = serializers.CharField(write_only=True, required=False)  # For admin user
    name = serializers.CharField(max_length=255)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(required=False)

    class Meta:
        model = Merchant
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'status']
        extra_kwargs = {
            'schema_name': {'required': False},
            'status': {'read_only': True}
        }

    def validate_schema_name(self, value):
        """Ensure schema name follows PostgreSQL naming rules"""
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Schema name can only contain alphanumerics and underscores"
            )
        return value.lower()

    def create(self, validated_data):
        """Handle merchant + schema creation and admin user setup"""
        domains_data = validated_data.pop('domains', [])
        password = validated_data.pop('password', None)

        # Auto-generate schema_name if not provided
        if not validated_data.get('schema_name'):
            validated_data['schema_name'] = validated_data['name'].lower().replace(' ', '_')

        merchant = Merchant.objects.create(**validated_data)

        # Create domains
        for domain_data in domains_data:
            Domain.objects.create(tenant=merchant, **domain_data)

        # Create admin user with password if provided
        if password:
            with schema_context(merchant.schema_name):
                User = get_user_model()
                User.objects.create_superuser(
                    email=merchant.contact_email,
                    password=password,
                    role='merchant_admin'
                )
        return merchant

class MerchantRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for merchant registration.
    Handles password validation and creation of merchant admin user.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = tenant
        fields = ('email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = tenant.objects.create_user(**validated_data)
        user.role = 'merchant_admin'
        schema_name = getattr(connection.tenant, 'schema_name', None)
        if schema_name:
            user.schema_name = schema_name
        user.save()
        return user

class MerchantTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer for obtaining merchant JWT tokens.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.")

        # Only allow merchant_admin or store_manager roles
        if getattr(user, 'role', None) not in ['merchant_admin', 'store_manager']:
            raise serializers.ValidationError("User does not have merchant access.")

        # Ensure user is in the correct tenant context
        tenant = getattr(connection, 'tenant', None)
        if tenant and getattr(user, 'schema_name', None) != getattr(tenant, 'schema_name', None):
            raise serializers.ValidationError("User does not belong to this tenant.")

        tokens = get_tokens_for_user(user, token_class=MerchantToken)
        return {
            'refresh': tokens['refresh'],
            'access': tokens['access'],
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
        }
