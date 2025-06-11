# public_apps/user/backends.py
from django_tenants.utils import get_tenant_model
from django.contrib.auth import get_user_model

class TenantAwareAuthBackend:
    def authenticate(self, request, email=None, password=None, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                # Set tenant schema for the session
                if user.schema_name:
                    request.tenant = get_tenant_model().objects.get(schema_name=user.schema_name)
                return user
        except User.DoesNotExist:
            return None