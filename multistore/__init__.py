# project/__init__.py
from django_tenants import utils

# Override default tenant app name
utils.DEFAULT_TENANT_APP_LABEL = 'merchant'