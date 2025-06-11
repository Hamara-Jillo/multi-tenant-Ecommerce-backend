from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    CustomerTokenObtainPairSerializer,
    CustomerRegistrationSerializer,
    UserSerializer
)
from .tokens import GuestToken

User = get_user_model()

class CustomerTokenView(TokenObtainPairView):
    """API endpoint for customer token acquisition"""
    serializer_class = CustomerTokenObtainPairSerializer


class CustomerRegistrationView(APIView):
    """API endpoint for customer registration"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Set role and schema
            user.role = 'store_customer'
            tenant = request.tenant
            if tenant:
                user.schema_name = tenant.schema_name
            user.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class MerchantRegistrationView(APIView):
#     """API endpoint for merchant admin registration"""
#     permission_classes = [permissions.AllowAny]
    
#     def post(self, request):
#         serializer = MerchantRegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
            
#             # Set role and schema
#             user.role = 'merchant_admin'
#             tenant = request.tenant
#             if tenant:
#                 user.schema_name = tenant.schema_name
#             user.save()
            
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerProfileView(APIView):
    """API endpoint for retrieving and updating customer profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        serializer = CustomerRegistrationSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class MerchantProfileView(APIView):
#     """API endpoint for retrieving and updating merchant profile"""
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         user = request.user
#         serializer = MerchantRegistrationSerializer(user)
#         return Response(serializer.data)
    
#     def put(self, request):
#         user = request.user
#         serializer = MerchantRegistrationSerializer(user, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GuestTokenView(APIView):
    """API endpoint for guest token acquisition"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = GuestToken.for_request(request)
        return Response({
            'access': str(token),
            'token_type': 'Bearer',
            'is_guest': True
        })