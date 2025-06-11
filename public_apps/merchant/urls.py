# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MerchantTokenView
from .views import MerchantProfileView, MerchantSignupView, LogoutView


urlpatterns = [
    path('merchant/token/', MerchantTokenView.as_view(), name='merchant-token'),
    path('merchant/signup/', MerchantSignupView.as_view(), name='merchant-signup'),
    path('merchant/profile/', MerchantProfileView.as_view(), name='merchant-profile'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),

    # path('merchant/activate/', MerchantActivateView.as_view(), name='merchant-activate'),
    # path('merchant/suspend/', MerchantSuspendView.as_view(), name='merchant-suspend'),
    # path('merchant/deactivate/', MerchantDeactivateView.as_view(), name='merchant-deactivate'),
    # path('merchant/delete/', MerchantDeleteView.as_view(), name='merchant-delete'),
    # path('merchant/restore/', MerchantRestoreView.as_view(), name='merchant-restore'),
    # path('merchant/verify/', MerchantVerifyView.as_view(), name='merchant-verify'),
    # path('merchant/verify/<str:token>/', MerchantVerifyView.as_view(), name='merchant-verify-token'),
    # path('merchant/verify/<str:token>/<str:email>/', MerchantVerifyView.as_view(), name='merchant-verify-token-email'),
    # path('merchant/verify/<str:token>/<str:email>/<str:password>/', MerchantVerifyView.as_view(), name='merchant-verify-token-email-password'),
    # path('merchant/verify/<str:token>/<str:email>/<str:password>/<str:store_name>/', MerchantVerifyView.as_view(), name='merchant-verify-token-email-password-store'),
]