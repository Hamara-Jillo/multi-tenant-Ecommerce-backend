from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager

from public_apps.merchant.models import Merchant

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_platform_admin', True)

        if not extra_fields['is_staff'] or not extra_fields['is_superuser']:
            raise ValueError('Superuser must have is_staff=True and is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('merchant_admin', 'Merchant Admin'),
        ('store_manager', 'Store Manager'),
        ('store_staff', 'Store Staff'),
        ('accountant', 'Accountant'),
        ('customer_service', 'Customer Service'),
        ('store_customer', 'Store Customer'),
        ('public_admin', 'Platform Admin'),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='store_customer')
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(unique=True)
    is_platform_admin = models.BooleanField(default=False)

    # Social authentication fields
    avatar_url = models.URLField(blank=True, null=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    provider_id = models.CharField(max_length=100, blank=True, null=True)

    # User preferences
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")

    # Multi-tenant relationships
    tenant_memberships = models.ManyToManyField(
        'merchant.Merchant',
        through='merchant.TenantMembership',
        through_fields=('user', 'tenant'),
        related_name='users'
    )

    primary_tenant = models.ForeignKey(
        'merchant.Merchant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_users',
        help_text="User's default tenant for quick access"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_tenant_role(self, tenant):
        """Get user's role in a specific tenant"""
        return self.tenantmembership_set.filter(tenant=tenant, is_active=True).values_list('role', flat=True).first()

    def can_access_tenant(self, tenant):
        """Check if user has access to a tenant"""
        return self.tenantmembership_set.filter(tenant=tenant, is_active=True).exists()

    def get_accessible_tenants(self):
        """Get all tenants the user has access to"""
        return Merchant.objects.filter(memberships__user=self, memberships__is_active=True).distinct()

    def is_merchant_admin(self):
        """Check if the user is a merchant admin in any tenant"""
        return self.tenantmembership_set.filter(role='merchant_admin', is_active=True).exists()

    def get_primary_schema_name(self):
        """Return the schema_name of the user's primary tenant, if set"""
        return self.primary_tenant.schema_name if self.primary_tenant else None
    
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this customer belongs to.',
        related_name='+',
        related_query_name='+'
        )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this customer.',
        related_name='+',
        related_query_name='+'
    )

