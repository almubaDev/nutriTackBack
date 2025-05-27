from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import UserProfile, FitnessGoal, NutritionTargets
from .serializers import (
    UserProfileSerializer, 
    FitnessGoalSerializer, 
    NutritionTargetsSerializer,
    NutritionTargetsCreateSerializer
)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vista para ver y actualizar el perfil nutricional del usuario"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class FitnessGoalListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear objetivos fitness"""
    serializer_class = FitnessGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FitnessGoal.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Desactivar objetivos anteriores
        FitnessGoal.objects.filter(user=self.request.user).update(is_active=False)
        # Crear nuevo objetivo activo
        serializer.save(user=self.request.user, is_active=True)


class ActiveFitnessGoalView(generics.RetrieveAPIView):
    """Vista para obtener el objetivo fitness activo"""
    serializer_class = FitnessGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        try:
            return FitnessGoal.objects.get(user=self.request.user, is_active=True)
        except FitnessGoal.DoesNotExist:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({'detail': 'No hay objetivo fitness activo'}, 
                          status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NutritionTargetsView(generics.RetrieveAPIView):
    """Vista para obtener las metas nutricionales de una fecha específica"""
    serializer_class = NutritionTargetsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        date = self.request.query_params.get('date', timezone.now().date())
        try:
            return NutritionTargets.objects.get(user=self.request.user, date=date)
        except NutritionTargets.DoesNotExist:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({'detail': 'No hay metas nutricionales para esta fecha'}, 
                          status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_nutrition_targets(request):
    """Endpoint para calcular y crear metas nutricionales"""
    serializer = NutritionTargetsCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        targets = serializer.save()
        response_serializer = NutritionTargetsSerializer(targets)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_targets(request):
    """Endpoint para obtener las metas nutricionales de hoy"""
    today = timezone.now().date()
    try:
        targets = NutritionTargets.objects.get(user=request.user, date=today)
        serializer = NutritionTargetsSerializer(targets)
        return Response(serializer.data)
    except NutritionTargets.DoesNotExist:
        return Response({'detail': 'No hay metas nutricionales para hoy'}, 
                       status=status.HTTP_404_NOT_FOUND)