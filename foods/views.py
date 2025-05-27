from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Food, ScannedFood
from .serializers import (
    FoodSerializer, 
    FoodCreateSerializer,
    ScannedFoodSerializer, 
    ScannedFoodCreateSerializer,
    FoodSearchSerializer
)


class FoodListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear alimentos"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FoodCreateSerializer
        return FoodSerializer
    
    def get_queryset(self):
        return Food.objects.filter(is_verified=True).order_by('name')


class FoodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar alimentos"""
    queryset = Food.objects.all()
    serializer_class = FoodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FoodCreateSerializer
        return FoodSerializer


class ScannedFoodListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear alimentos escaneados"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ScannedFoodCreateSerializer
        return ScannedFoodSerializer
    
    def get_queryset(self):
        return ScannedFood.objects.filter(user=self.request.user).order_by('-created_at')


class ScannedFoodDetailView(generics.RetrieveDestroyAPIView):
    """Vista para ver y eliminar alimentos escaneados"""
    serializer_class = ScannedFoodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ScannedFood.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_foods(request):
    """Endpoint para buscar alimentos"""
    serializer = FoodSearchSerializer(data=request.data)
    if serializer.is_valid():
        query = serializer.validated_data['query']
        limit = serializer.validated_data['limit']
        
        # Buscar en alimentos verificados
        foods = Food.objects.filter(
            Q(name__icontains=query) | Q(brand__icontains=query),
            is_verified=True
        ).order_by('name')[:limit]
        
        food_serializer = FoodSerializer(foods, many=True)
        return Response({
            'foods': food_serializer.data,
            'count': len(food_serializer.data)
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_scanned_foods(request):
    """Endpoint para obtener alimentos escaneados del usuario"""
    limit = request.query_params.get('limit', 20)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 20
    
    scanned_foods = ScannedFood.objects.filter(
        user=request.user
    ).order_by('-created_at')[:limit]
    
    serializer = ScannedFoodSerializer(scanned_foods, many=True)
    return Response({
        'scanned_foods': serializer.data,
        'count': len(serializer.data)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_scanned_to_food(request, scanned_id):
    """Convertir un alimento escaneado en un alimento de la base de datos"""
    try:
        scanned_food = ScannedFood.objects.get(id=scanned_id, user=request.user)
    except ScannedFood.DoesNotExist:
        return Response({'error': 'Alimento escaneado no encontrado'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Crear alimento en la base de datos
    food_data = {
        'name': scanned_food.ai_identified_name,
        'calories_per_100g': scanned_food.calories_per_100g or 0,
        'protein_per_100g': scanned_food.protein_per_100g or 0,
        'carbs_per_100g': scanned_food.carbs_per_100g or 0,
        'fat_per_100g': scanned_food.fat_per_100g or 0,
    }
    
    serializer = FoodCreateSerializer(data=food_data, context={'request': request})
    if serializer.is_valid():
        food = serializer.save()
        return Response(FoodSerializer(food).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)