from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    StoreViewSet, 
    StoreAccessViewSet,
    StoreDashboardAPIView,
    StoreSettingsAPIView,
    BrandingSettingsAPIView,
    BusinessSettingsAPIView,
    PaymentSettingsAPIView,
    ShippingZonesAPIView,
    ShippingZoneDetailAPIView,
    TaxSettingsAPIView,
    MarketsAPIView,
    MarketDetailAPIView,
    SEOSettingsAPIView,
)

# Set up the router for viewsets
router = DefaultRouter()
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'store-permissions', StoreAccessViewSet, basename='store-permissions')

# Define the app name
app_name = 'store'

# Define URL patterns
urlpatterns = [
    # Include router URLs for store and store-permissions viewsets
    path('api/', include(router.urls)),
    
    # API endpoints for store management
    path('api/dashboard/', StoreDashboardAPIView.as_view(), name='dashboard'),
    path('api/settings/', StoreSettingsAPIView.as_view(), name='settings'),
    path('api/branding/', BrandingSettingsAPIView.as_view(), name='branding'),
    path('api/business/', BusinessSettingsAPIView.as_view(), name='business'),
    path('api/payments/', PaymentSettingsAPIView.as_view(), name='payments'),
    path('api/shipping/', ShippingZonesAPIView.as_view(), name='shipping'),
    path('api/shipping/<int:pk>/', ShippingZoneDetailAPIView.as_view(), name='shipping_zone_detail'),
    path('api/taxes/', TaxSettingsAPIView.as_view(), name='taxes'),
    path('api/markets/', MarketsAPIView.as_view(), name='markets'),
    path('api/markets/<int:pk>/', MarketDetailAPIView.as_view(), name='market_detail'),
    path('api/seo/', SEOSettingsAPIView.as_view(), name='seo'),
]