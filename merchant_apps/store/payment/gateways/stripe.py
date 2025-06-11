from django_tenants.utils import get_tenant

def get_stripe_api_key():
    tenant = get_tenant()
    return tenant.stripe_secret_key  # Store keys in Tenant model