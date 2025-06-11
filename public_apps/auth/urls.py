# auth/urls.py
from django.urls import path
from .views import LoginView, SignupView, SocialAuthView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('social-login/', SocialAuthView.as_view(), name='social-login'),
]
