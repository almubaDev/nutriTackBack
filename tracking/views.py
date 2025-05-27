from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import DailyLog, LoggedFoodItem
from .serializers import (
    DailyLogSerializer,
    LoggedFoodItemSerializer,
    LoggedFoodItemCreateSerializer,
    QuickLogFoodSerializer
)


class DailyLogListView(generics.ListAPIView):
    """Vista para listar registros diarios del usuario"""
    serializer_class = DailyLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DailyLog.objects.filter(user=self.request.user).order_by('-date')


class DailyLogDetailView(generics.RetrieveAPIView):
    """Vista para ver un registro diario específico"""
    serializer_class = DailyLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DailyLog.objects.filter(user=self.request.user)


class LoggedFoodItemListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear alimentos registrados"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LoggedFoodItemCreateSerializer
        return LoggedFoodItemSerializer
    
    def get_queryset(self):
        daily_log_id = self.kwargs.get('daily_log_id')
        if daily_log_id:
            daily_log = get_object_or_404(DailyLog, id=daily_log_id, user=self.request.user)
            return LoggedFoodItem.objects.filter(daily_log=daily_log).order_by('-logged_at')
        return LoggedFoodItem.objects.none()
    
    def perform_create(self, serializer):
        daily_log_id = self.kwargs.get('daily_log_id')
        daily_log = get_object_or_404(DailyLog, id=daily_log_id, user=self.request.user)
        serializer.save(daily_log=daily_log)


class LoggedFoodItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar alimentos registrados"""
    serializer_class = LoggedFoodItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LoggedFoodItem.objects.filter(daily_log__user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LoggedFoodItemCreateSerializer
        return LoggedFoodItemSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def today_log(request):
    """Endpoint para obtener o crear el registro de hoy"""
    today = timezone.now().date()
    daily_log, created = DailyLog.objects.get_or_create(
        user=request.user,
        date=today
    )
    
    if request.method == 'GET':
        serializer = DailyLogSerializer(daily_log)
        return Response(serializer.data)
    
    # Si es POST, podría ser para resetear el día
    if request.method == 'POST' and request.data.get('action') == 'reset':
        daily_log.food_items.all().delete()
        daily_log.calculate_totals()
        serializer = DailyLogSerializer(daily_log)
        return Response(serializer.data)
    
    return Response({'error': 'Acción no válida'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_log_food(request):
    """Endpoint para registrar comida rápidamente"""
    serializer = QuickLogFoodSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        logged_item = serializer.save()
        response_serializer = LoggedFoodItemSerializer(logged_item)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_log_by_date(request):
    """Endpoint para obtener registro diario por fecha"""
    date_str = request.query_params.get('date')
    if not date_str:
        return Response({'error': 'Parámetro date es requerido'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Formato de fecha inválido (YYYY-MM-DD)'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        daily_log = DailyLog.objects.get(user=request.user, date=date)
        serializer = DailyLogSerializer(daily_log)
        return Response(serializer.data)
    except DailyLog.DoesNotExist:
        return Response({'error': 'No hay registro para esta fecha'}, 
                       status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_summary(request):
    """Endpoint para obtener resumen nutricional del usuario"""
    # Últimos 7 días
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=6)
    
    logs = DailyLog.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Calcular promedios
    if logs.exists():
        total_days = logs.count()
        avg_calories = sum(log.total_calories for log in logs) / total_days
        avg_protein = sum(log.total_protein for log in logs) / total_days
        avg_carbs = sum(log.total_carbs for log in logs) / total_days
        avg_fat = sum(log.total_fat for log in logs) / total_days
    else:
        avg_calories = avg_protein = avg_carbs = avg_fat = 0
    
    return Response({
        'period': f'{start_date} - {end_date}',
        'days_logged': logs.count(),
        'averages': {
            'calories': round(avg_calories, 1),
            'protein': round(avg_protein, 1),
            'carbs': round(avg_carbs, 1),
            'fat': round(avg_fat, 1),
        },
        'daily_logs': DailyLogSerializer(logs, many=True).data
    })