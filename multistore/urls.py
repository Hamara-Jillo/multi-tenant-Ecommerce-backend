"""
URL configuration for multistore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.apps import apps
from django.urls import  include, path
from merchant_apps.store.catalogue.admin import (
    ProductAdmin as StoreProductAdmin , 
    ProductClassAdmin as StoreProductClassAdmin , 
    CategoryAdmin as StoreCategoryAdmin,
    ProductAttributeValueAdmin, OptionAdmin,
    AttributeOptionGroupAdmin, AttributeOptionAdmin
    )
from merchant_apps.store.offer.admin import ConditionAdmin, ConditionalOfferAdmin, RangeAdmin
from merchant_apps.store.offer.models import Condition as StoreCondition, ConditionalOffer as StoreConditionalOffer, Range as StoreRange
from merchant_apps.store.partner.admin import (
    PartnerAdmin,
    StockRecordAdmin,
    StockAlertAdmin
    ) 
from merchant_apps.store.partner.models import (
    Partner as StorePartner,
    StockRecord as StoreStockRecord,
    StockAlert as StoreStockAlert
    )

from merchant_apps.store.catalogue.models import (
    Product as StoreProduct, 
    ProductClass as StoreProductClass, 
    Category as StoreCategory,   
    ProductAttributeValue, Option,
    AttributeOptionGroup, AttributeOption 
    )
from merchant_apps.store.basket.models import (
    Basket as StoreBasket,
)
from merchant_apps.store.basket.admin import (
    BasketAdmin,
)

from merchant_apps.store.order.models import (
    Order as StoreOrder
)

from merchant_apps.store.order.admin import (
    OrderAdmin
)

from merchant_apps.store.payment.models import (
    SourceType as StoreSourceType,
    Source as StoreSource,
    Transaction as StoreTranscation
)

from merchant_apps.store.payment.admin import (
    SourceAdmin,
    TransactionAdmin,
    SourceTypeAdmin
)
from merchant_apps.store.shipping.admin import (
    OrderAndItemChargesAdmin,
    WeightBasedAdmin,
    ShippingMethodParentAdmin
)

from merchant_apps.store.shipping.models import (
    ShippingMethod,
    OrderAndItemCharges,
    WeightBased,
    WeightBand
)
from merchant_apps.store.voucher.models import (
    Voucher as StoreVoucher,
    VoucherOffer as StoreVoucherOffer,
    VoucherSet as StoreVoucherSet,
    VoucherApplication as StoreVoucherApplication
)

from merchant_apps.store.voucher.admin import (
   VoucherGroupAdmin,
   StoreVoucherAdmin,  
    VoucherSetAdmin,
    VoucherApplicationAdmin,
    VoucherGroup
)

from public_apps.merchant.admin import MerchantAdminSite, PlatformAdminSite


from public_apps.merchant.models import Merchant
from public_apps.user.models import User
from merchant_apps.store.meta.models import Store
from public_apps.merchant.admin import MerchantAdmin
from public_apps.user.admin import UserAdmin
from merchant_apps.store.meta.admin import StoreAdmin
from rest_framework.authtoken import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# from rest_framework_swagger.views import get_swagger_view
# from django.conf.urls import url
# schema_view = get_swagger_view(title='Pastebin API')
store_admin = MerchantAdminSite(name='tenant_admin')
platform_admin = PlatformAdminSite(name='platform_admin')

platform_admin.register(Merchant, MerchantAdmin)
platform_admin.register(User, UserAdmin)
store_admin.register(Store, StoreAdmin)
store_admin.register(StoreProduct, StoreProductAdmin)  
store_admin.register(StoreProductClass,StoreProductClassAdmin)
store_admin.register(StoreCategory, StoreCategoryAdmin)
store_admin.register(ProductAttributeValue, ProductAttributeValueAdmin)
store_admin.register(Option, OptionAdmin)
store_admin.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
store_admin.register(AttributeOption, AttributeOptionAdmin)
store_admin.register(StorePartner, PartnerAdmin)
store_admin.register(StoreStockRecord, StockRecordAdmin)
store_admin.register(StoreStockAlert, StockAlertAdmin)
store_admin.register(StoreBasket, BasketAdmin)
store_admin.register(StoreOrder, OrderAdmin)
store_admin.register(StoreSource, SourceAdmin)
store_admin.register(StoreTranscation, TransactionAdmin)
store_admin.register(StoreSourceType, SourceTypeAdmin)
store_admin.register(ShippingMethod, ShippingMethodParentAdmin)
store_admin.register(OrderAndItemCharges, OrderAndItemChargesAdmin)
store_admin.register(WeightBased, WeightBasedAdmin)
store_admin.register(StoreConditionalOffer, ConditionalOfferAdmin)
store_admin.register(StoreRange,RangeAdmin)
store_admin.register(StoreCondition,ConditionAdmin)
store_admin.register(StoreVoucher,StoreVoucherAdmin)
store_admin.register(StoreVoucherApplication,VoucherApplicationAdmin)
store_admin.register(VoucherGroup, VoucherGroupAdmin)






urlpatterns = [
     # Platform admin (public schema only)
    path('platform/', platform_admin.urls),
    # Tenant admin (tenant schemas)
    path('admin/', store_admin.urls),
    # url(r'^$', schema_view),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', views.obtain_auth_token),
    # API endpoints for merchants
    # path('accounts/', include('public_apps.merchant.urls')),

    # API endpoints for user operations
    path('api/auth/', include('public_apps.auth.urls')),
    # # API endpoints for store operations
    path('store/', include('merchant_apps.store.meta.urls')),
    # API endpoints for Merchant operations
    # path('api/merchants/', include('public_apps.merchant.urls')),


    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # # API endpoints for checkout operations
    # path('checkout/', include('merchant_apps.store.checkout.urls')),
    # # API endpoints for voucher operations
    # path('voucher/', include('merchant_apps.store.voucher.urls')),
    # # API endpoints for basket operations
    # path('basket/', include('merchant_apps.store.basket.urls')),
    # # API endpoints for order operations
    # path('order/', include('merchant_apps.store.order.urls')),
    # # API endpoints for payment operations
    # path('payment/', include('merchant_apps.store.payment.urls')),
    # # API endpoints for shipping operations
    # path('shipping/', include('merchant_apps.store.shipping.urls')),
    # # API endpoints for catalogue operations
    # path('catalogue/', include('merchant_apps.store.catalogue.urls')),
    # # API endpoints for partner operations
    # path('partner/', include('merchant_apps.store.partner.urls')),
    # # API endpoints for offer operations
    # path('offer/', include('merchant_apps.store.offer.urls')),
    # # API endpoints for meta operations
    # path('meta/', include('merchant_apps.store.meta.urls')),
    # # API endpoints for notifications
    # path('notifications/', include('public_apps.notifications.urls')),
    # # API endpoints for analytics
    # path('analytics/', include('merchant_apps.store.analytics.urls')),  
    # The Django admin is not officially supported; expect breakage.
    # Nonetheless, it's often useful for debugging.

    # path('', include(apps.get_app_config('oscar').urls[0])),
]
