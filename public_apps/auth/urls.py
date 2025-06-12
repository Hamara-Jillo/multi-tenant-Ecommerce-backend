from django.urls import path
from .views import (
    UnifiedLoginView,
    TenantSelectionView,
    SocialAuthView,
    RegisterView,
    CreateMerchantView,
    InviteUserView,
    AcceptInvitationView,
    UserTenantsView,
    SwitchTenantView
)

urlpatterns = [
    # Authentication
    path('login/', UnifiedLoginView.as_view(), name='unified_login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('social-auth/', SocialAuthView.as_view(), name='social_auth'),
    
    # Tenant management
    path('select-tenant/', TenantSelectionView.as_view(), name='select_tenant'),
    path('switch-tenant/', SwitchTenantView.as_view(), name='switch_tenant'),
    path('user-tenants/', UserTenantsView.as_view(), name='user_tenants'),
    
    # Merchant management
    path('create-merchant/', CreateMerchantView.as_view(), name='create_merchant'),
    
    # Invitations
    path('invite/<int:tenant_id>/', InviteUserView.as_view(), name='invite_user'),
    path('accept-invitation/', AcceptInvitationView.as_view(), name='accept_invitation'),
]