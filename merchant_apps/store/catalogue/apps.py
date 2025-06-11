from oscar.apps.catalogue.apps import CatalogueConfig as BaseCatalogueConfig

class CatalogueConfig(BaseCatalogueConfig):
    name = 'merchant_apps.store.catalogue'
    label = 'catalogue'
    verbose_name = 'Store Catalogue' 
    
    def ready(self):
        super().ready()
        from . import models
    
    def has_module_permission(self, request):
        """Control visibility of the entire catalogue app in admin"""
        return request.user.is_authenticated  # Or add tenant-specific checks