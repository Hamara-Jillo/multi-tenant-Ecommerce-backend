# merchant_apps/store/checkout/rules.py
from oscar.apps.checkout import rules

class StoreCheckoutRules(rules.Core):
    
    def skip_unless_basket_requires_shipping(self, request):
        """Override shipping check based on store settings"""
        if not request.store.requires_shipping:
            return None
        return super().skip_unless_basket_requires_shipping(request)