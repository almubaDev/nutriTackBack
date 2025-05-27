from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import User


class CustomRegisterSerializer(RegisterSerializer):
    """Serializer personalizado para registro"""
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    
    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer para datos del usuario"""
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_email_verified', 
                 'date_joined', 'created_at', 'updated_at')
        read_only_fields = ('id', 'is_email_verified', 'date_joined', 
                          'created_at', 'updated_at')


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar datos del usuario"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name')