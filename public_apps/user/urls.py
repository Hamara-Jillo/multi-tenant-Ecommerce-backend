from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .tokens import UserToken
from .views import (UserTokenView, GuestTokenView, 
    UserProfileView, UserRegistrationView
)
         
urlpatterns = [
    # JWT endpoints
    path('token/', UserToken, name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User registration endpoints
    path('users/token/', UserTokenView.as_view(), name='user_token_obtain_pair'),
    path('users/register/', UserRegistrationView.as_view(), name='user_register'),
    path('users/profile/', UserProfileView.as_view(), name='user_profile'),
    path('users/guest-token/', GuestTokenView.as_view(), name='guest_token'),
    
]