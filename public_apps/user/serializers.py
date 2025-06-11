from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from django_tenants.utils import get_tenant_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from public_apps.user.tokens import CustomerToken, MerchantToken

User = get_user_model()

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    user_permissions = PermissionSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField()
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'role',
            'schema_name',
            'store',
            'is_platform_admin',
            'password',
            'groups',
            'user_permissions',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'groups',
            'user_permissions',
        ]
        read_only_fields = ['id', 'is_platform_admin']
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
        password = validated_data.pop('password', None)

        # Get current tenant's schema_name
        from django_tenants.utils import get_current_schema_name
        schema_name = get_current_schema_name()
        validated_data['schema_name'] = schema_name
        # Ensure the schema_name is valid
        if not validated_data.get('schema_name'):
            raise serializers.ValidationError("Schema name is required")
        # Ensure the store is valid
        if validated_data.get('store') and not hasattr(validated_data['store'], 'id'):
            raise serializers.ValidationError("Invalid store")
        # Ensure the role is valid
        valid_roles = dict(User.ROLES).keys()
        if validated_data.get('role') not in valid_roles:
            raise serializers.ValidationError(f"Invalid role. Valid roles are: {', '.join(valid_roles)}")
        # Ensure the password meets complexity requirements
        if password:
            if len(password) < 8:
                raise serializers.ValidationError("Password must be at least 8 characters long")
            if not any(char.isdigit() for char in password):
                raise serializers.ValidationError("Password must contain at least one digit")
            if not any(char.isalpha() for char in password):
                raise serializers.ValidationError("Password must contain at least one letter")
        # Create the user instance without the password first
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='store_customer',
            schema_name=schema_name
        )
        if password:
            user.set_password(password)
        else:
            # If no password was provided mark as unusable
            user.set_unusable_password()

        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
    def validate_email(self, value):
        """Ensure email is unique and valid"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    def validate_username(self, value):
        """Ensure username is unique and valid"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    def validate(self, attrs):
        """Ensure that either email or username is provided"""
        if not attrs.get('email') and not attrs.get('username'):
            raise serializers.ValidationError("Either email or username must be provided")
        return attrs
    def to_representation(self, instance):
        """Customize the representation of the user object"""
        representation = super().to_representation(instance)
        representation['groups'] = GroupSerializer(instance.groups.all(), many=True).data
        representation['user_permissions'] = PermissionSerializer(instance.user_permissions.all(), many=True).data
        return representation
    def to_internal_value(self, data):
        """Customize the internal value conversion"""
        data['email'] = data.get('email', '').lower()
        return super().to_internal_value(data)
    def validate_role(self, value):
        """Ensure role is valid"""
        valid_roles = dict(User.ROLES).keys()
        if value not in valid_roles:
            raise serializers.ValidationError(f"Invalid role. Valid roles are: {', '.join(valid_roles)}")
        return value
    def validate_schema_name(self, value):
        """Ensure schema name follows PostgreSQL naming rules"""
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Schema name can only contain alphanumerics and underscores"
            )
        return value.lower()
    def validate_store(self, value):
        """Ensure store is valid"""
        if value and not hasattr(value, 'id'):
            raise serializers.ValidationError("Invalid store")
        return value
    def validate_password(self, value):
        """Ensure password meets complexity requirements"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Password must contain at least one letter")
        return value
    def validate_is_platform_admin(self, value):
        """Ensure is_platform_admin is a boolean"""
        if not isinstance(value, bool):
            raise serializers.ValidationError("is_platform_admin must be a boolean")
        return value
    def validate(self, attrs):
        """Ensure that either email or username is provided"""
        if not attrs.get('email') and not attrs.get('username'):
            raise serializers.ValidationError("Either email or username must be provided")
        return attrs
    
class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for customer registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
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
        user = User.objects.create_user(**validated_data)
        user.role = 'store_customer'
        tenant = get_tenant_model()
        if tenant:
            user.schema_name = tenant.schema_name
        user.save()
        return user

class CustomerTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token pair serializer for customers"""
    
    @classmethod
    def get_token(cls, user):
        if user.role not in ['store_customer', 'public_admin']:
            raise serializers.ValidationError(
                "Invalid role for customer authentication"
            )
        
        return CustomerToken.for_user(user)


    


