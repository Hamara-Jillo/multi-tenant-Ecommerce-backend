from django.db import models
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = getattr(connection, 'tenant', None)
        
        if tenant:
            logger.debug(f"Filtering queryset for tenant {tenant.name}")
            
            # Filter through StorePermission for Store model
            if self.model.__name__ == 'Store':
                return qs.filter(storepermission__merchant=tenant).distinct()
                
            # Direct tenant field for other models
            if hasattr(self.model, 'tenant'):
                return qs.filter(tenant=tenant)
                
        return qs.none()