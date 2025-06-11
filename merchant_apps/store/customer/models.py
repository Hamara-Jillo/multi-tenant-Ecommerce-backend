from django.db import OperationalError, ProgrammingError, models
from django.conf import settings
from django.dispatch import receiver
from django.apps import apps
from oscar.apps.customer.abstract_models import AbstractUser
from django.db.models.signals import post_save

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_customer(sender, instance=None, created=False, **kwargs):
    
    # Only run if the Customer model/table exists
    try:
        Customer = apps.get_model('customer', 'Customer')
        if instance.role == 'store_customer':
            customer, created = Customer.objects.get_or_create(user=instance)
            if not created:
                customer.save()
    except (ProgrammingError, OperationalError):
        # Table does not exist yet
        pass

class Customer(AbstractUser):
    # Link to your existing User model (not a proxy)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store_customer',
        null=True,
        blank=True,
        help_text="Link to the user model"
    )

    @property
    def email(self):
        return self.user.email if self.user else self.guest_email
    
    
    class Meta:
        app_label = 'customer'

# Import Oscar’s post-abstract models AFTER defining your Customer
from oscar.apps.customer.models import *
