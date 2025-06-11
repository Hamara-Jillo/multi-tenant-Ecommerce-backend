from django import forms
from oscar.apps.checkout.forms import ShippingAddressForm as CoreShippingAddressForm
from oscar.apps.checkout.forms import ShippingMethodForm as CoreShippingMethodForm
from oscar.apps.checkout.forms import GatewayForm as CoreGatewayForm

from merchant_apps.store.meta.models import Store

class ShippingAddressForm(CoreShippingAddressForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant = kwargs.get('tenant')
        if tenant:
            permitted_stores = Store.objects.filter(storepermission__merchant=tenant)
            self.fields['store'] = forms.ModelChoiceField(queryset=permitted_stores, required=True)

class ShippingMethodForm(CoreShippingMethodForm):
    pass

class GatewayForm(CoreGatewayForm):
    pass 