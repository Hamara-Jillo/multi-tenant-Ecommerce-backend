
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_tenants.utils import tenant_context, get_tenant_model 
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import (
    Store, BrandingSettings, BusinessSettings, PaymentSettings,
    ShippingZone, ShippingMethod, TaxSetting, Market, SEOSettings,StorePermission
)
from .serializers import (
    StoreSerializer, BrandingSettingsSerializer, BusinessSettingsSerializer,
    PaymentSettingsSerializer, ShippingZoneSerializer, ShippingMethodSerializer,
    TaxSettingSerializer, MarketSerializer, SEOSettingsSerializer,StorePermissionSerializer
)
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView


from rest_framework.exceptions import PermissionDenied
from .models import Store, StorePermission

class StoreContextMixin:
    """
    Mixin to add current shop to the context, now using StorePermission to enforce access.
    """
    def get_store(self, required_access_level='read'):
        """
        Get the current shop for the logged-in merchant, ensuring StorePermission.
        Default required access: 'read'. Use 'write' or 'admin' as appropriate.
        """
        request = getattr(self, 'request', None)
        merchant = getattr(request, 'tenant', None) if request else None

        if not merchant:
            raise PermissionDenied("Merchant context required.")

        # Find the store, checking StorePermission for this merchant and at least the required access level.
        # Adjust as needed if your store/user logic differs.
        try:
            # Looks for at least the required access; you can create a hierarchy if needed.
            valid_levels = ['admin', 'write', 'read']
            # Only access levels equal or higher than required_access_level count as valid
            req_index = valid_levels.index(required_access_level)
            allowed_levels = valid_levels[:req_index+1]

            # Find store IDs where this merchant has required permission
            permitted_store_ids = StorePermission.objects.filter(
                merchant=merchant,
                access_level__in=allowed_levels
            ).values_list('store_id', flat=True)

            store = Store.objects.filter(id__in=permitted_store_ids).order_by('-is_primary_store', 'name').first()
            if not store:
                raise PermissionDenied("No accessible shop found for current merchant.")
            return store
        except Store.DoesNotExist:
            raise PermissionDenied("No accessible shop found for current merchant.")

        
        
class StoreViewSet(viewsets.ModelViewSet, StoreContextMixin):
    serializer_class = StoreSerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        """Only show stores accessible to current merchant"""
        return Store.objects.filter(merchants=self.request.tenant)

    @action(detail=True, methods=['get'], url_path='products', url_name='products')
    def products(self, request, pk=None):
        """
        Retrieve all products for the given store in a tenant-aware manner.
        This action uses tenant_context to switch context to the store's schema.
        """
        store = self.get_object()  # current store instance
        merchant = request.tenant  # current merchant from tenant context

        # Get the tenant (store) model dynamically, similar to the snippet provided
        StoreModel = get_tenant_model()
        try:
            # Validate that the current merchant has access to this store
            store_instance = StoreModel.objects.get(slug=store.slug, merchants=merchant)
        except StoreModel.DoesNotExist:
            return Response({"detail": "Store not found for current merchant."}, status=404)

        # Switch to the store's tenant context to fetch products
        with tenant_context(store):
            # Adjust the Product import according to your project structure.
            # For example, if Product is defined in products.models, then:
            products_qs = Product.objects.all()
            # For simplicity, we'll return a list of product IDs and names.
            products_data = [{"id": product.id, "name": product.name} for product in products_qs]

        return Response(products_data)

class StoreAccessViewSet(viewsets.ModelViewSet):
    queryset = StorePermission.objects.all()
    serializer_class = StorePermissionSerializer

    def get_queryset(self):
        return super().get_queryset().filter(merchant=self.request.tenant)


class StoreDashboardAPIView(StoreContextMixin,APIView):
    """API view for the store dashboard."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        store = self.get_store()
        serializer = StoreSerializer(store)
        return Response(serializer.data)

class StoreSettingsAPIView(StoreContextMixin, UpdateAPIView):
    """API view for updating general store settings."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = StoreSerializer
    
    def get_object(self):
        return self.get_store()

class BrandingSettingsAPIView(StoreContextMixin, UpdateAPIView):
    """API view for updating store branding settings."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = BrandingSettingsSerializer
    
    def get_object(self):
        store = self.get_store()
        obj, created = BrandingSettings.objects.get_or_create(store=store)
        return obj

class BusinessSettingsAPIView(StoreContextMixin, UpdateAPIView):
    """API view for updating business operational settings."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = BusinessSettingsSerializer
    
    def get_object(self):
        store = self.get_store()
        obj, created = BusinessSettings.objects.get_or_create(store=store)
        return obj

class PaymentSettingsAPIView(StoreContextMixin, UpdateAPIView):
    """API view for updating payment gateway settings."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = PaymentSettingsSerializer
    
    def get_object(self):
        store = self.get_store()
        obj, created = PaymentSettings.objects.get_or_create(store=store)
        return obj

class ShippingZonesAPIView(StoreContextMixin, ListCreateAPIView):
    """API view for listing and creating shipping zones."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = ShippingZoneSerializer
    
    def get_queryset(self):
        store = self.get_store()
        return ShippingZone.objects.filter(store=store)
    
    def perform_create(self, serializer):
        store = self.get_store()
        serializer.save(store=store)

class ShippingZoneDetailAPIView(StoreContextMixin, RetrieveUpdateDestroyAPIView):
    """API view for managing a specific shipping zone."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = ShippingZoneSerializer
    
    def get_queryset(self):
        store = self.get_store()
        return ShippingZone.objects.filter(store=store)

class ShippingMethodsAPIView(StoreContextMixin, ListCreateAPIView):
    """API view for listing and creating shipping methods for a zone."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = ShippingMethodSerializer
    
    def get_queryset(self):
        store = self.get_store()
        zone_id = self.kwargs.get('zone_id')
        return ShippingMethod.objects.filter(shipping_zone__shop=store, shipping_zone_id=zone_id)
    
    def perform_create(self, serializer):
        zone = get_object_or_404(ShippingZone, id=self.kwargs.get('zone_id'), store=self.get_store())
        serializer.save(shipping_zone=zone)

class TaxSettingsAPIView(StoreContextMixin, ListCreateAPIView):
    """API view for managing tax settings across regions."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = TaxSettingSerializer
    
    def get_queryset(self):
        store = self.get_store()
        return TaxSetting.objects.filter(store=store)
    
    def perform_create(self, serializer):
        store = self.get_store()
        serializer.save(store=store)

class MarketsAPIView(StoreContextMixin, ListCreateAPIView):
    """API view for listing and creating markets."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = MarketSerializer
    
    def get_queryset(self):
        store = self.get_store()
        return Market.objects.filter(store=store)
    
    def perform_create(self, serializer):
        store = self.get_store()
        serializer.save(store=store)

class MarketDetailAPIView(StoreContextMixin, RetrieveUpdateDestroyAPIView):
    """API view for managing a specific market."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = MarketSerializer
    
    def get_queryset(self):
        store = self.get_store()
        return Market.objects.filter(store=store)

class SEOSettingsAPIView(StoreContextMixin, UpdateAPIView):
    """API view for updating SEO and marketing settings."""
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = SEOSettingsSerializer
    
    def get_object(self):
        store = self.get_store()
        obj, created = SEOSettings.objects.get_or_create(store=store)
        return obj
