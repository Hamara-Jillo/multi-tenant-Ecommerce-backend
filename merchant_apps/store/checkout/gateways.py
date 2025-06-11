from oscar.apps.payment import bankcards
from oscar.apps.payment import gateways

class TenantPaymentGateway:
    
    def __init__(self, store):
        self.store = store
        self.config = store.payment_config
        
    def authorize(self, amount, card):
        if self.config.get('use_sandbox'):
            return self._mock_authorization()
        # Use tenant-specific API credentials
        return gateways.real_payment_processor(
            api_key=self.config['api_key'],
            amount=amount,
            card=card
        )