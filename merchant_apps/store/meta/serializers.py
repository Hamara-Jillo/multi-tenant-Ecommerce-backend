
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Store, StorePermission
from .models import (
    Store, StorePermission, BrandingSettings, BusinessSettings, PaymentSettings,
    ShippingZone, ShippingMethod, TaxSetting, Market, SEOSettings, StoreProduct
)

class StorePermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the StorePermission model.
    """
    class Meta:
        model = StorePermission
        fields = ['id', 'merchant', 'store', 'created_at', 'access_level']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        # Additional validations can be added here if needed.
        return attrs


class StoreSerializer(serializers.ModelSerializer):
    """
    Serializer for the Store (meta) model.
    
    Includes extensive permission checks:
      - On creation: verifies that the user has permission to create a store.
      - On update: verifies that the user has permission to modify store details.
      - For termination (i.e., disabling a store): uses an extra write-only "terminate" flag and requires termination permission.
    
    Also includes a nested list of permissions related to the store.
    """
    # Nested permissions read-only field: provides a list of associated permissions.
    permissions = StorePermissionSerializer(source="storepermission_set", many=True, read_only=True)
    # Extra flag to indicate that this request is to terminate the store.
    terminate = serializers.BooleanField(write_only=True, required=False)
    country = serializers.CharField(source='country.code', read_only=True)
    class Meta:
        model = Store
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'store_password': {'write_only': True},  # Ensure password is not exposed in responses
        }


    def validate(self, attrs):
        """
        Check permissions based on the type of operation:
          - Creation: user must have 'store_meta.add_store'
          - Update (non termination changes): user must have 'store_meta.change_store'
          - Termination: ensure the terminate flag can only be used by users with termination rights.
        """
        request = self.context.get('request', None)
        if request:
            # When creating a store
            if self.instance is None:
                if not request.user.has_perm("store_meta.add_store"):
                    raise serializers.ValidationError(_("User does not have permission to create a store."))
            else:
                # For updates affecting fields other than termination flag.
                if not request.user.has_perm("store_meta.change_store"):
                    raise serializers.ValidationError(_("User does not have permission to change store details."))

                # If termination flag is provided, check termination permission.
                if attrs.get('terminate', False):
                    if not request.user.has_perm("store_meta.terminate_store"):
                        raise serializers.ValidationError(_("User does not have permission to terminate the store."))
        else:
            raise serializers.ValidationError(_("Request context is required for permission checks."))
        return attrs
    
    def validate_slug(self, value):
        """
        Custom validation to ensure the slug is a valid identifier.
        """
        if not value.isidentifier():
            raise serializers.ValidationError("Slug must be a valid identifier (letters, numbers, underscores)")
        return value

    def create(self, validated_data):
        # Remove the 'terminate' field if accidentally sent during creation
        validated_data.pop('terminate', None)
        store = super().create(validated_data)
        # Automatically add admin-level StorePermission for the creating merchant/user
        request = self.context.get('request', None)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Assumes the related merchant is request.user for the access table
            from .models import StorePermission
            StorePermission.objects.create(
                merchant=request.tenant,
                store=store,
                access_level='admin'
            )
        return store


    def update(self, instance, validated_data):
        # Check if termination is requested.
        terminate = validated_data.pop('terminate', False)
        if terminate:
            # Termination is interpreted as deactivating the store.
            instance.is_active = False
        # Update other fields normally.
        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        # Ensure is_active is included in the response
        representation = super().to_representation(instance)
        representation['is_active'] = instance.is_active
        return representation
    

class BrandingSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the BrandingSettings model.
    Handles branding and theming settings for the store.
    """
    class Meta:
        model = BrandingSettings
        fields = '__all__'

class BusinessSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the BusinessSettings model.
    Handles business operational parameters and policies.
    """
    class Meta:
        model = BusinessSettings
        fields = '__all__'

class PaymentSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the PaymentSettings model.
    Configures payment gateways and options, with sensitive fields hidden in responses.
    """
    class Meta:
        model = PaymentSettings
        fields = '__all__'
        extra_kwargs = {
            'stripe_api_key': {'write_only': True},
            'stripe_public_key': {'write_only': True},
            'paypal_client_id': {'write_only': True},
            'paypal_secret': {'write_only': True},
        }

class ShippingMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for the ShippingMethod model.
    Represents shipping methods within a shipping zone.
    """
    class Meta:
        model = ShippingMethod
        fields = '__all__'

class ShippingZoneSerializer(serializers.ModelSerializer):
    """
    Serializer for the ShippingZone model.
    Defines shipping zones with nested shipping methods.
    """
    shipping_methods = ShippingMethodSerializer(many=True, read_only=True)

    class Meta:
        model = ShippingZone
        fields = '__all__'

class TaxSettingSerializer(serializers.ModelSerializer):
    """
    Serializer for the TaxSetting model.
    Manages tax settings for specific regions.
    """
    class Meta:
        model = TaxSetting
        fields = '__all__'

class MarketSerializer(serializers.ModelSerializer):
    """
    Serializer for the Market model.
    Defines markets for international sales with specific settings.
    """
    class Meta:
        model = Market
        fields = '__all__'

class SEOSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the SEOSettings model.
    Handles SEO and marketing-related settings.
    """
    class Meta:
        model = SEOSettings
        fields = '__all__'

class StoreProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the StoreProduct model.
    Maps products to stores with additional product details.
    """
    product_title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = StoreProduct
        fields = ['id', 'store', 'product', 'product_title', 'is_active', 'sort_order']