from django.db import connection, models
from django.forms import ValidationError
from django_tenants.models import TenantMixin, DomainMixin
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from django.db.utils import DatabaseError
from django_tenants.utils import schema_context
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import logging
logger = logging.getLogger(__name__)


class Merchant(TenantMixin):
    # Core Identification
    name = models.CharField(
        _("merchant name"),
        max_length=255,
        help_text="Official business/organization name"
    )
    schema_name = models.CharField(
        max_length=63, 
        unique=True, 
        default='merchant_schema'
    )
    
    # Contact Information
    contact_email = models.EmailField(
        _("contact email"),
        unique=True,
        help_text="Primary contact email address"
    )
    contact_phone = PhoneNumberField(
        _("contact phone"),
        blank=True, 
        null=True, 
        region='US',
        help_text="Primary contact number with country code"
    )
    
    # Tenant Configuration
    timezone = models.CharField(
        _("timezone"),
        max_length=50,
        default="UTC",
        help_text="Preferred timezone"
    )
    default_language = models.CharField(
        _("language"),
        max_length=10,
        default="en",
        help_text="Preferred language code (ISO 639-1)"
    )

    domain_url = models.CharField(max_length=128, unique=True)
    custom_domain = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Custom domain (store.com)"
    )
   
    # Status Tracking
    ACCOUNT_STATUS = (
        ('unverified', _('Unverified')),
        ('active', _('Active')),
        ('suspended', _('Suspended')),
    )
    status = models.CharField(
        _("account status"),
        max_length=20,
        choices=ACCOUNT_STATUS,
        default='unverified'
    )
    
    ROLES = (
        ('public_admin', 'Public Admin'),
        ('merchant_admin', 'Merchant Admin'),
        ('store_manager', 'Store Manager'),
        ('store_customer', 'Store Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLES, default='merchant_admin')
    
    stores = models.ManyToManyField(
        'store_meta.Store', 
        through='store_meta.StorePermission',
        related_name='merchants',
        verbose_name=_("Managed Stores")
    )
    
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tenant Schema Configuration
    auto_create_schema = True
    auto_drop_schema = True
    auto_create_admin = models.BooleanField(
        default=True,
        help_text="Whether to automatically create admin user"
    )
    class Meta:
        app_label = 'merchant'
        verbose_name = _("Merchant")
        verbose_name_plural = _("Merchants")

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    @property
    def is_active(self):
        return self.status == 'active'

    def clean(self):
        if self.status == 'active' and not self.is_verified:
            raise ValidationError(_("Active accounts must be verified"))
        
    

    def delete(self, user=None, *args, **kwargs):
        """Enhanced delete method with security checks"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get current user from thread local storage
        current_user = getattr(connection, 'user', None)
        
        if current_user and not current_user.is_platform_admin:
            msg = f"Security Alert: Unauthorized deletion attempt of {self.name}"
            logger.warning(msg)
            raise PermissionDenied("Only platform administrators can delete merchants")

        logger.info(f"Initiating deletion of merchant {self.name}")
        try:
            # Delete domains first
            with transaction.atomic(): 
                self.domains.all().delete()
                # Drop schema
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{self.schema_name}" CASCADE')

                # Delete merchant record
                super().delete(*args, **kwargs)

                logger.info(f"Successfully deleted merchant {self.name}")
        except Exception as e:
            logger.error(f"Failed to delete merchant {self.name}: {str(e)}")
            raise


    def _create_admin_user(self):
        """Create a tenant admin user in the tenant's schema"""
        logger.debug(f"Creating admin user for merchant {self.name}")
        User = get_user_model()
        
        with schema_context(self.schema_name):
            # Generate a temporary password
            temp_password = User.objects.make_random_password()
            
            admin_user = User.objects.create_superuser(
                email=self.contact_email,
                password=temp_password,
                is_staff=True,
                is_superuser=True,
                role='merchant_admin',
            )
            print("Attempting to log admin user creation...")
            logger.info(
                f"""Created merchant admin user:
                Email: {admin_user.email}
                Temporary Password: {temp_password}
                Admin URL: http://{self.domain_url}/admin/
                """
            )
            return admin_user, temp_password

    def save(self, *args, **kwargs):
        with transaction.atomic():
            logger.debug(f"Saving merchant {self.name} with schema {self.schema_name}")
            is_new = not self.pk
            counter = 1
            
            if not self.domain_url:
                self.domain_url = f"{self.schema_name}.localhost"
                while Merchant.objects.filter(domain_url=self.domain_url).exists():
                    self.domain_url = f"{self.schema_name}{counter}.localhost"
                    counter += 1
                    
            self.clean()
            super().save(*args, **kwargs)

   
        # Create domain and admin user for new merchants
        if is_new:
            logger.debug(f"Creating domain for new merchant {self.name}")
            Domain.objects.get_or_create(
                domain=self.domain_url,
                tenant=self,
                defaults={
                    'is_primary': True,
                    'verified': True
                }
            )
            
            # Only create admin user if auto_create_admin is True
            if getattr(self, 'auto_create_admin', True):
                try:
                    self._create_admin_user()
                except DatabaseError as e:
                    logger.error(f"Error creating admin user: {str(e)}")
                    raise

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance) 

class Domain(DomainMixin):
    ssl_enabled = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    verification_method = models.CharField(
        max_length=20,
        choices=[
            ('dns', 'DNS Record'),
            ('file', 'File Upload'),
            ('meta', 'Meta Tag')
        ],
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name_plural = "Store Domains"
        
    def clean(self):
        if self.is_primary and self.tenant.domain_set.filter(is_primary=True).count() > 1:
            raise ValidationError(_("Primary domain already exists"))
        super().clean()




