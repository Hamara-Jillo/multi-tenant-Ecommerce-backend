from django_tenants.utils import schema_context
from merchant_apps.store.meta.models import Store  # Import the function

class NestedTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Resolve parent tenant from domain
        merchant = request.tenant
        
        # Resolve child tenant from header
        store_schema = request.headers.get('X-Store-Schema')
        
        with schema_context(merchant.schema_name):
            try:
                store = Store.objects.get(schema_name=store_schema)
                request.tenant = store  # Now operating in merchant_schema.store_schema
            except Store.DoesNotExist:
                request.tenant = merchant

        response = self.get_response(request)
        return response