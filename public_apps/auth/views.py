# views/auth.py
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
User = get_user_model()
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)

        # Determine primary tenant or list accessible tenants
        primary = user.primary_tenant
        if not primary:
            tenants = user.get_accessible_tenants()
            primary = tenants.first() if tenants.exists() else None

        return Response({
            'token': token.key,
            'user': {
                'email': user.email,
                'id': user.id,
                'is_platform_admin': user.is_platform_admin,
                'primary_tenant': {
                    'id': primary.id,
                    'name': primary.name,
                    'schema_name': primary.schema_name,
                    'domain_url': primary.domain_url
                } if primary else None,
            }
        })

class LogoutView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
    

class SignupView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'Email already registered'}, status=400)

        user = User.objects.create_user(email=email, password=password)
        token = Token.objects.create(user=user)

        return Response({
            'token': token.key,
            'user': {'email': user.email, 'id': user.id}
        }, status=201)
    

class UserProfileView(APIView):
    def get(self, request):
        user = request.user
        return Response({
            'email': user.email,
            'id': user.id,
            'is_platform_admin': user.is_platform_admin,
            'primary_tenant': {
                'id': user.primary_tenant.id,
                'name': user.primary_tenant.name,
                'schema_name': user.primary_tenant.schema_name,
                'domain_url': user.primary_tenant.domain_url
            } if user.primary_tenant else None,
        })
    

class SocialAuthView(APIView):
    def post(self, request):
        email = request.data.get('email')
        provider = request.data.get('provider')  # 'google', 'github', etc.
        provider_id = request.data.get('provider_id')
        avatar_url = request.data.get('avatar_url')

        user, created = User.objects.get_or_create(email=email, defaults={
            'provider': provider,
            'provider_id': provider_id,
            'avatar_url': avatar_url,
            'username': email.split('@')[0],
        })

        if created:
            user.set_unusable_password()
            user.save()

        token, _ = Token.objects.get_or_create(user=user)

        primary = user.primary_tenant or user.get_accessible_tenants().first()

        return Response({
            'token': token.key,
            'user': {
                'email': user.email,
                'id': user.id,
                'is_platform_admin': user.is_platform_admin,
                'primary_tenant': {
                    'id': primary.id,
                    'name': primary.name,
                    'schema_name': primary.schema_name,
                    'domain_url': primary.domain_url
                } if primary else None,
            }
        })
