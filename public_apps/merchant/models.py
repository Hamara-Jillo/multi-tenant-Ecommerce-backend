from django.db import connection, models, transaction
from django.forms import ValidationError
from django_tenants.models import TenantMixin, DomainMixin
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from django.db.utils import DatabaseError
from django_tenants.utils import schema_context
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)


class TenantMembership(models.Model):
    """Junction table for User-Tenant relationships with roles"""

    ROLES = (
        ('merchant_admin', 'Merchant Admin'),
        ('store_manager', 'Store Manager'),
        ('store_staff', 'Store Staff'),
        ('accountant', 'Accountant'),
        ('customer_service', 'Customer Service'),
    )

    PERMISSION_LEVELS = (
        ('full', 'Full Access'),
        ('limited', 'Limited Access'),
        ('read_only', 'Read Only'),
    )

    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='memberships')
    tenant = models.ForeignKey('merchant.Merchant', on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLES)
    permission_level = models.CharField(max_length=20, choices=PERMISSION_LEVELS, default='full')
    is_active = models.BooleanField(default=True)
    is_owner = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey('user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_invitations')
    invitation_token = models.CharField(max_length=100, blank=True, null=True)
    invitation_sent_at = models.DateTimeField(null=True, blank=True)
    invitation_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'tenant']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"

    def clean(self):
        if self.is_owner:
            existing_owners = TenantMembership.objects.filter(tenant=self.tenant, is_owner=True).exclude(pk=self.pk)
            if existing_owners.exists():
                raise ValidationError(_("Only one owner is allowed per tenant"))


class TenantInvitation(models.Model):
    """Handles pending invitations to tenants."""

    email = models.EmailField()
    tenant = models.ForeignKey('merchant.Merchant', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=TenantMembership.ROLES)
    invited_by = models.ForeignKey('user.User', on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ['email', 'tenant']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email', 'status']),
        ]

    @property
    def is_valid(self):
        from django.utils import timezone
        return self.status == 'pending' and self.expires_at > timezone.now()


class Merchant(TenantMixin):
    name = models.CharField(_('merchant name'), max_length=255, help_text="Official business/organization name")
    schema_name = models.CharField(max_length=63, unique=True, default='merchant_schema')
    contact_email = models.EmailField(_('contact email'), unique=True, help_text="Primary contact email address")
    contact_phone = PhoneNumberField(_('contact phone'), blank=True, null=True, region='US')
    timezone = models.CharField(_('timezone'), max_length=50, default="UTC")
    default_language = models.CharField(_('language'), max_length=10, default="en")
    domain_url = models.CharField(max_length=128, unique=True)
    custom_domain = models.CharField(max_length=255, blank=True, null=True)

    ACCOUNT_STATUS = (
        ('unverified', _('Unverified')),
        ('active', _('Active')),
        ('suspended', _('Suspended')),
    )
    status = models.CharField(_('account status'), max_length=20, choices=ACCOUNT_STATUS, default='unverified')

    ROLES = (
        ('public_admin', 'Public Admin'),
        ('merchant_admin', 'Merchant Admin'),
        ('store_manager', 'Store Manager'),
        ('store_customer', 'Store Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLES, default='merchant_admin')

    business_type = models.CharField(max_length=50, choices=[
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('service', 'Service'),
        ('digital', 'Digital Products'),
        ('subscription', 'Subscription'),
    ], blank=True)

    plan_type = models.CharField(max_length=20, choices=[
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ], default='free')

    allow_user_registration = models.BooleanField(default=True)
    require_invitation = models.BooleanField(default=False)
    max_users = models.IntegerField(default=5)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stores = models.ManyToManyField('store_meta.Store', through='store_meta.StorePermission', related_name='merchants')

    auto_create_schema = True
    auto_drop_schema = True
    auto_create_admin = models.BooleanField(default=True)

    class Meta:
        app_label = 'merchant'
        verbose_name = _('Merchant')
        verbose_name_plural = _('Merchants')

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    @property
    def is_active(self):
        return self.status == 'active'

    def get_owner(self):
        try:
            return self.memberships.get(is_owner=True).user
        except TenantMembership.DoesNotExist:
            return None

    def get_user_count(self):
        return self.memberships.filter(is_active=True).count()

    def can_add_user(self):
        return self.get_user_count() < self.max_users

    def add_user(self, user, role='store_staff', invited_by=None):
        if not self.can_add_user():
            raise ValidationError("Maximum user limit reached")

        membership, created = TenantMembership.objects.get_or_create(
            user=user,
            tenant=self,
            defaults={'role': role, 'invited_by': invited_by, 'is_active': True}
        )

        if not created and not membership.is_active:
            membership.is_active = True
            membership.save()

        if not user.primary_tenant:
            user.primary_tenant = self
            user.save()

        return membership

    def clean(self):
        if self.status == 'active' and not self.is_verified:
            raise ValidationError(_("Active accounts must be verified"))

    def delete(self, user=None, *args, **kwargs):
        current_user = getattr(connection, 'user', None)
        if current_user and not current_user.is_platform_admin:
            logger.warning("Unauthorized merchant deletion attempt by %s", current_user.email)
            raise PermissionDenied("Only platform administrators can delete merchants")

        logger.info("Initiating deletion of merchant %s", self.name)
        try:
            with transaction.atomic():
                self.domains.all().delete()
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{self.schema_name}" CASCADE')
                super().delete(*args, **kwargs)
                logger.info("Successfully deleted merchant %s", self.name)
        except Exception as e:
            logger.error("Failed to delete merchant %s: %s", self.name, str(e))
            raise

    def _create_admin_user(self):
        logger.debug("Creating admin user for merchant %s", self.name)
        User = get_user_model()
        with schema_context(self.schema_name):
            temp_password = User.objects.make_random_password()
            admin_user = User.objects.create_superuser(
                email=self.contact_email,
                password=temp_password,
                is_staff=True,
                is_superuser=True,
                role='merchant_admin'
            )
            logger.info("Created admin user for %s: %s", self.name, admin_user.email)
            return admin_user, temp_password

    def save(self, *args, **kwargs):
        with transaction.atomic():
            logger.debug("Saving merchant %s", self.name)
            is_new = not self.pk
            counter = 1

            if not self.domain_url:
                self.domain_url = f"{self.schema_name}.localhost"
                while Merchant.objects.filter(domain_url=self.domain_url).exists():
                    self.domain_url = f"{self.schema_name}{counter}.localhost"
                    counter += 1

            self.clean()
            super().save(*args, **kwargs)

        if is_new:
            self.get_or_create_domain()
            if self.auto_create_admin:
                try:
                    self._create_admin_user()
                except DatabaseError as e:
                    logger.error("Error creating admin user: %s", str(e))
                    raise

    def get_or_create_domain(self):
        Domain.objects.get_or_create(
            domain=self.domain_url,
            tenant=self,
            defaults={'is_primary': True, 'verified': True}
        )


class Domain(DomainMixin):
    ssl_enabled = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    verification_method = models.CharField(
        max_length=20,
        choices=[('dns', 'DNS Record'), ('file', 'File Upload'), ('meta', 'Meta Tag')],
        null=True,
        blank=True
    )

    class Meta:
        verbose_name_plural = "Store Domains"

    def clean(self):
        if self.is_primary and self.tenant.domain_set.filter(is_primary=True).count() > 1:
            raise ValidationError(_("Primary domain already exists"))
        super().clean()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance)
