from rest_framework import viewsets, permissions, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_tenants.utils import get_tenant_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from public_apps.merchant.serializers import MerchantTokenObtainPairSerializer
from .models import Merchant
from .serializers import MerchantRegistrationSerializer, MerchantSerializer

from rest_framework_simplejwt.views import TokenObtainPairView

Merchant = get_tenant_model()



class MerchantViewSet(viewsets.ModelViewSet):
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAdminUser]  # Platform admins only

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Custom endpoint to activate merchant"""
        merchant = self.get_object()
        merchant.status = 'active'
        merchant.save()
        return Response({'status': 'activated'})

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Custom endpoint to suspend merchant"""
        merchant = self.get_object()
        merchant.status = 'suspended'
        merchant.save()
        return Response({'status': 'suspended'})

    def perform_destroy(self, instance):
        """Override delete to use our custom model method"""
        instance.delete(user=self.request.user)

class MerchantProfileView(APIView):
    """API endpoint for retrieving and updating merchant profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.tenant
        serializer = MerchantSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        serializer = MerchantSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class MerchantSignupView(APIView):
    """
    API view for merchant signup (creates a new tenant)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request) -> Response:
        """
        Handle GET request to retrieve the signup form.
        """
        return Response(
            {
                "message": "Merchant signup form",
                "fields": ["name", "contact_email", "password"],
            },
            status=status.HTTP_200_OK,
        )
    def post(self, request):
        serializer = MerchantRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            merchant = serializer.save()
            
            # Return success response with tenant domain
            return Response({
                'message': 'Merchant created successfully',
                'domain': merchant.domain_url,
                'email': merchant.contact_email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MerchantTokenView(TokenObtainPairView):
    """API endpoint for merchant token acquisition"""
    serializer_class = MerchantTokenObtainPairSerializer



class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
      