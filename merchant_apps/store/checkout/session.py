from oscar.apps.checkout import session as core_session

class TenantCheckoutSessionData(core_session.CheckoutSessionData):
    
    def _get_store_key(self, key):
        return f"store_{self.request.store.id}_{key}"

    def use_store_shipping_method(self, method_code):
        key = self._get_store_key('shipping_method_code')
        self._set(key, method_code)

    def get_store_shipping_method(self):
        key = self._get_store_key('shipping_method_code')
        return self._get(key)