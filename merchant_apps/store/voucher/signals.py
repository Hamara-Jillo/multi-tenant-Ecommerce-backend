from oscar.core.loading import get_model
from django.db.models.signals import post_save

Voucher = get_model('voucher', 'Voucher')  

def custom_voucher_handler(sender, instance, **kwargs):
    
    pass

post_save.connect(custom_voucher_handler, sender=Voucher)