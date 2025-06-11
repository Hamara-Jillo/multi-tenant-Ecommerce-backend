from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from django.core.validators import URLValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
    

class Store(models.Model):
    """
    Base Store model for multi-tenant e-commerce, inspired by Shopify.
    Contains general store information and settings.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_("Store Name"),
        help_text=_("Official name of the store"),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _("A store with this name already exists."),
            'blank': _("Store name cannot be blank."),
            'null': _("Store name cannot be null.")
        },
        null=False,
        blank=False,
       
        default='My Store'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("Store Slug"),
        help_text=_("URL-friendly identifier")
    )
    
    
    
    auto_create_schema = True
    auto_drop_schema = True
    auto_create_admin = models.BooleanField(
        default=True,
        help_text=_("Automatically create admin user for this store")
    )

    legal_business_name = models.CharField(_('Legal Business Name'), max_length=255, 
                                         blank=True)
    primary_domain = models.CharField(_('Primary Domain'), max_length=255, 
                                    validators=[URLValidator()], blank=True)
    contact_email = models.EmailField(_('Contact Email'), blank=True)
    contact_phone = models.CharField(_('Contact Phone'), max_length=20, blank=True)
    
    # Address info
    address_line1 = models.CharField(_('Address Line 1'), max_length=255, blank=True)
    address_line2 = models.CharField(_('Address Line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    state_province = models.CharField(_('State/Province'), max_length=100, blank=True)
    postal_code = models.CharField(_('Postal/Zip Code'), max_length=20, blank=True)
    country = CountryField(_('Country'), blank=True)
    
    # Store settings
    timezone = models.CharField(_('Timezone'), max_length=50, 
                              default='UTC')
    default_currency = models.CharField(_('Default Currency'), max_length=3, 
                                      default='USD')
    weight_unit = models.CharField(_('Weight Unit'), max_length=10, 
                                 choices=[('kg', 'Kilograms (kg)'), 
                                         ('lb', 'Pounds (lb)')], 
                                 default='kg')
    dimension_unit = models.CharField(_('Dimension Unit'), max_length=10, 
                                    choices=[('cm', 'Centimeters (cm)'), 
                                            ('in', 'Inches (in)')], 
                                    default='cm')
    order_id_prefix = models.CharField(_('Order ID Prefix'), max_length=10, 
                                     blank=True)
    
    # Store status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Status")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    password_protected = models.BooleanField(_('Password Protected'), default=False)
    store_password = models.CharField(_('Store Password'), max_length=100, blank=True)
    
    # Organization related
    is_primary_store = models.BooleanField(_('Is Primary Store'), default=False)
    organization_id = models.CharField(_('Organization ID'), max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        app_label = 'store_meta'
        db_table = 'store_meta_store'
        ordering = ['name']
        verbose_name = _("Store")
        verbose_name_plural = _("Stores")
    def save(self, *args, **kwargs):
        """Custom save method to ensure slug is a valid identifier"""
        if self.is_primary_store:
            Store.objects.filter(
                merchant=self.merchant, 
                is_primary_store=True
            ).exclude(pk=self.pk).update(is_primary_store=False)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def clean(self):
        """Ensure slug follows tenant naming rules"""
        if not self.slug.isidentifier():
            raise ValidationError(_("Slug must be a valid identifier (letters, numbers, underscores)"))


class StorePermission(models.Model):
    merchant = models.ForeignKey('merchant.Merchant', db_index=True, blank=True, on_delete=models.CASCADE, verbose_name=_("Merchant"))
    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name=_("Store"))
    created_at = models.DateTimeField(auto_now_add=True)
    access_level = models.CharField(
        max_length=20,
        choices=[
            ('read', _("Read Only")),
            ('write', _("Read/Write")),
            ('admin', _("Full Admin"))
        ],
        default='read'
    )

    class Meta:
        db_table = 'store_meta_storepermission'
        unique_together = ('merchant', 'store')
        verbose_name = _('Store Access Permission')
        verbose_name_plural = _('Store Access Permissions')

    def __str__(self):
        return f"{self.merchant} - {self.store.name}"

    def clean(self):
        from django_tenants.utils import get_tenant_model
        TenantModel = get_tenant_model()
        if not TenantModel.objects.filter(id=self.merchant).exists():
            raise ValidationError(_("Invalid merchant"))


class BrandingSettings(models.Model):
    """
    Branding and theming settings for the store.
    """
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='branding')
    
    # Logo and icon
    logo = models.ImageField(_('Logo'), upload_to='shop_logos/', blank=True, null=True)
    logo_alt_text = models.CharField(_('Logo Alt Text'), max_length=100, blank=True)
    favicon = models.ImageField(_('Favicon'), upload_to='shop_favicons/', blank=True, null=True)
    
    # Theme settings
    theme_id = models.CharField(_('Theme ID'), max_length=100, blank=True)
    
    # Color schemes
    primary_color = models.CharField(_('Primary Color'), max_length=7, default='#000000')
    secondary_color = models.CharField(_('Secondary Color'), max_length=7, default='#ffffff')
    accent_color = models.CharField(_('Accent Color'), max_length=7, default='#0000ff')
    text_color = models.CharField(_('Text Color'), max_length=7, default='#000000')
    background_color = models.CharField(_('Background Color'), max_length=7, default='#ffffff')
    button_color = models.CharField(_('Button Color'), max_length=7, default='#0000ff')
    
    # Typography
    heading_font = models.CharField(_('Heading Font'), max_length=50, default='Helvetica')
    body_font = models.CharField(_('Body Font'), max_length=50, default='Arial')
    base_font_size = models.PositiveSmallIntegerField(_('Base Font Size'), default=16)
    
    # Layout settings
    header_layout = models.CharField(_('Header Layout'), max_length=50, 
                                   choices=[('centered', 'Centered'), 
                                           ('left_aligned', 'Left Aligned')], 
                                   default='centered')
    sticky_header = models.BooleanField(_('Sticky Header'), default=False)
    
    # Content
    announcement_bar_text = models.CharField(_('Announcement Bar Text'), max_length=255, blank=True)
    brand_headline = models.CharField(_('Brand Headline'), max_length=255, blank=True)
    brand_description = models.TextField(_('Brand Description'), blank=True)
    
    # Social media
    facebook_url = models.URLField(_('Facebook URL'), blank=True)
    instagram_url = models.URLField(_('Instagram URL'), blank=True)
    twitter_url = models.URLField(_('Twitter URL'), blank=True)
    youtube_url = models.URLField(_('YouTube URL'), blank=True)
    tiktok_url = models.URLField(_('TikTok URL'), blank=True)
    
    # Footer
    copyright_text = models.CharField(_('Copyright Text'), max_length=255, blank=True)
    footer_show_newsletter = models.BooleanField(_('Show Newsletter in Footer'), default=True)
    
    # Custom CSS
    custom_css = models.TextField(_('Custom CSS'), blank=True)
    
    class Meta:
        verbose_name = _('Branding Settings')
        verbose_name_plural = _('Branding Settings')
    
    def __str__(self):
        return f"{self.store.name} Branding"


class BusinessSettings(models.Model):
    """
    Business operational parameters and policies.
    """
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='business_settings')
    
    # Tax settings
    tax_number = models.CharField(_('Tax Registration Number'), max_length=50, blank=True)
    include_tax_in_prices = models.BooleanField(_('Include Tax in Prices'), default=False)
    charge_tax_on_shipping = models.BooleanField(_('Charge Tax on Shipping'), default=False)
    
    # Order and payment settings
    payment_capture_mode = models.CharField(
        _('Payment Capture Mode'),
        max_length=20,
        choices=[('auto', 'Automatic'), ('manual', 'Manual')],
        default='auto'
    )
    auto_fulfill_orders = models.BooleanField(_('Auto-Fulfill Orders'), default=False)
    auto_archive_orders = models.BooleanField(_('Auto-Archive Orders'), default=False)
    
    # Fulfillment settings
    fulfillment_origin_address = models.CharField(_('Fulfillment Origin Address'), max_length=255, blank=True)
    
    # Customer settings
    customer_accounts_required = models.BooleanField(_('Customer Accounts Required'), default=False)
    notification_email = models.EmailField(_('Notification Email'), blank=True)
    
    # Marketing
    default_marketing_opt_in = models.BooleanField(_('Default Marketing Opt-in'), default=False)
    
    # Analytics and tracking
    google_analytics_id = models.CharField(_('Google Analytics ID'), max_length=50, blank=True)
    facebook_pixel_id = models.CharField(_('Facebook Pixel ID'), max_length=50, blank=True)
    
    # Policies
    refund_policy = models.TextField(_('Refund Policy'), blank=True)
    privacy_policy = models.TextField(_('Privacy Policy'), blank=True)
    terms_of_service = models.TextField(_('Terms of Service'), blank=True)
    
    class Meta:
        verbose_name = _('Business Settings')
        verbose_name_plural = _('Business Settings')
    
    def __str__(self):
        return f"{self.store.name} Business Settings"


class PaymentSettings(models.Model):
    """
    Configuration of payment gateways and options.
    """
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='payment_settings')
    
    # Payment gateway settings
    stripe_enabled = models.BooleanField(_('Stripe Enabled'), default=False)
    stripe_api_key = models.CharField(_('Stripe API Key'), max_length=255, blank=True)
    stripe_public_key = models.CharField(_('Stripe Public Key'), max_length=255, blank=True)
    
    paypal_enabled = models.BooleanField(_('PayPal Enabled'), default=False)
    paypal_client_id = models.CharField(_('PayPal Client ID'), max_length=255, blank=True)
    paypal_secret = models.CharField(_('PayPal Secret'), max_length=255, blank=True)
    
    # Payment methods
    allow_credit_cards = models.BooleanField(_('Allow Credit Cards'), default=True)
    accepted_card_brands = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=list,
        verbose_name=_('Accepted Card Brands')
    )
    
    apple_pay_enabled = models.BooleanField(_('Apple Pay Enabled'), default=False)
    google_pay_enabled = models.BooleanField(_('Google Pay Enabled'), default=False)
    
    # Manual payment methods
    bank_transfer_enabled = models.BooleanField(_('Bank Transfer Enabled'), default=False)
    bank_transfer_instructions = models.TextField(_('Bank Transfer Instructions'), blank=True)
    
    cash_on_delivery_enabled = models.BooleanField(_('Cash on Delivery Enabled'), default=False)
    cash_on_delivery_instructions = models.TextField(_('Cash on Delivery Instructions'), blank=True)
    
    # Payment options
    multi_currency_enabled = models.BooleanField(_('Multi-Currency Support'), default=False)
    installments_enabled = models.BooleanField(_('Installments Enabled'), default=False)
    
    # Fraud prevention
    fraud_prevention_enabled = models.BooleanField(_('Fraud Prevention Enabled'), default=False)
    cvv_required = models.BooleanField(_('CVV Required'), default=True)
    
    class Meta:
        verbose_name = _('Payment Settings')
        verbose_name_plural = _('Payment Settings')
    
    def __str__(self):
        return f"{self.store.name} Payment Settings"


class ShippingZone(models.Model):
    """
    Defines a shipping zone (region/country) with its own shipping methods.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='shipping_zones')
    name = models.CharField(_('Zone Name'), max_length=100)
    countries = ArrayField(
        models.CharField(max_length=2),
        verbose_name=_('Countries')
    )
    is_default = models.BooleanField(_('Is Default Zone'), default=False)
    
    class Meta:
        verbose_name = _('Shipping Zone')
        verbose_name_plural = _('Shipping Zones')
    
    def __str__(self):
        return f"{self.name} ({self.store.name})"


class ShippingMethod(models.Model):
    """
    Shipping method within a shipping zone.
    """
    shipping_zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name='shipping_methods')
    name = models.CharField(_('Method Name'), max_length=100)
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2)
    
    METHOD_TYPE_CHOICES = [
        ('flat', 'Flat Rate'),
        ('weight', 'Weight Based'),
        ('price', 'Price Based'),
        ('carrier', 'Carrier Calculated'),
    ]
    method_type = models.CharField(_('Method Type'), max_length=20, choices=METHOD_TYPE_CHOICES)
    
    min_order_price = models.DecimalField(_('Minimum Order Price'), max_digits=10, decimal_places=2, null=True, blank=True)
    max_order_price = models.DecimalField(_('Maximum Order Price'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    min_weight = models.DecimalField(_('Minimum Weight'), max_digits=10, decimal_places=2, null=True, blank=True)
    max_weight = models.DecimalField(_('Maximum Weight'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    carrier_name = models.CharField(_('Carrier Name'), max_length=100, blank=True)
    carrier_account_id = models.CharField(_('Carrier Account ID'), max_length=100, blank=True)
    
    delivery_estimate_min = models.PositiveSmallIntegerField(_('Delivery Est. Min Days'), null=True, blank=True)
    delivery_estimate_max = models.PositiveSmallIntegerField(_('Delivery Est. Max Days'), null=True, blank=True)
    
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    class Meta:
        verbose_name = _('Shipping Method')
        verbose_name_plural = _('Shipping Methods')
    
    def __str__(self):
        return f"{self.name} ({self.shipping_zone.name})"


class TaxSetting(models.Model):
    """
    Tax settings for specific regions.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='tax_settings')
    country = CountryField(_('Country'))
    state_province = models.CharField(_('State/Province'), max_length=100, blank=True)
    tax_registration_number = models.CharField(_('Tax Registration Number'), max_length=100, blank=True)
    tax_rate = models.DecimalField(_('Tax Rate'), max_digits=5, decimal_places=2, help_text=_('Percentage'))
    
    # Tax override for specific product types or categories
    product_type_overrides = models.JSONField(_('Product Type Tax Overrides'), default=dict, blank=True)
    
    # Automatic tax calculation service
    use_automatic_tax = models.BooleanField(_('Use Automatic Tax Calculation'), default=False)
    tax_provider = models.CharField(_('Tax Provider'), max_length=50, blank=True, 
                                  choices=[('avalara', 'Avalara'), ('taxjar', 'TaxJar')])
    
    class Meta:
        verbose_name = _('Tax Setting')
        verbose_name_plural = _('Tax Settings')
        unique_together = ('store', 'country', 'state_province')
    
    def __str__(self):
        if self.state_province:
            return f"{self.store.name} - {self.country.name} - {self.state_province}"
        return f"{self.store.name} - {self.country.name}"


class Market(models.Model):
    """
    Markets for international sales (groups of countries with specific settings).
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='markets')
    name = models.CharField(_('Market Name'), max_length=100)
    countries = ArrayField(
        models.CharField(max_length=2),
        verbose_name=_('Countries')
    )
    base_currency = models.CharField(_('Base Currency'), max_length=3)
    enabled_currencies = ArrayField(
        models.CharField(max_length=3),
        verbose_name=_('Enabled Currencies'),
        blank=True,
        default=list
    )
    enabled_languages = ArrayField(
        models.CharField(max_length=10),
        verbose_name=_('Enabled Languages'),
        blank=True,
        default=list
    )
    
    # Price adjustments
    price_adjustment_type = models.CharField(
        _('Price Adjustment Type'),
        max_length=20,
        choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        blank=True
    )
    price_adjustment_value = models.DecimalField(
        _('Price Adjustment Value'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Domains
    domain = models.CharField(_('Market Domain'), max_length=255, blank=True)
    
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    class Meta:
        verbose_name = _('Market')
        verbose_name_plural = _('Markets')
    
    def __str__(self):
        return f"{self.name} ({self.store.name})"


class SEOSettings(models.Model):
    """
    SEO and marketing-related settings.
    """
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='seo_settings')
    
    homepage_title = models.CharField(_('Homepage Title'), max_length=255, blank=True)
    homepage_meta_description = models.TextField(_('Homepage Meta Description'), blank=True)
    social_sharing_image = models.ImageField(_('Social Sharing Image'), upload_to='seo_images/', blank=True, null=True)
    
    robots_txt = models.TextField(_('Robots.txt Content'), blank=True)
    custom_head_scripts = models.TextField(_('Custom Head Scripts'), blank=True)
    
    enable_sitemap = models.BooleanField(_('Enable Sitemap'), default=True)
    
    class Meta:
        verbose_name = _('SEO Settings')
        verbose_name_plural = _('SEO Settings')
    
    def __str__(self):
        return f"{self.store.name} SEO Settings"


# Connect to Oscar models as needed
# from django.apps import apps

# try:
#     Product = apps.get_model('catalogue', 'Product')
    
class StoreProduct(models.Model):
        """
        Maps products to shops in a multi-tenant environment.
        """
        store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='shop_products')
        product = models.ForeignKey('catalogue.Product', on_delete=models.CASCADE, related_name='shop_products')
        is_active = models.BooleanField(_('Is Active'), default=True)
        sort_order = models.PositiveIntegerField(_('Sort Order'), default=0)
        
        # Market-specific pricing overrides could go here
        
        class Meta:
            verbose_name = _('Store Product')
            verbose_name_plural = _('Store Products')
            unique_together = ('store', 'product')
        
        def __str__(self):
            return f"{self.product.title} - {self.store.name}"
# except ImportError:
#     pass  # Oscar not available