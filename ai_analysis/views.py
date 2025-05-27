from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
import time
import base64
from .models import ImageAnalysis, GeminiUsageStats
from .serializers import (
    ImageAnalysisSerializer,
    ImageAnalysisCreateSerializer,
    GeminiUsageStatsSerializer,
    UserStatsSerializer
)
from foods.models import ScannedFood
from foods.serializers import ScannedFoodCreateSerializer


class ImageAnalysisListView(generics.ListAPIView):
    """Vista para listar análisis de imágenes del usuario"""
    serializer_class = ImageAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ImageAnalysis.objects.filter(user=self.request.user).order_by('-created_at')


class ImageAnalysisDetailView(generics.RetrieveAPIView):
    """Vista para ver detalles de un análisis específico"""
    serializer_class = ImageAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ImageAnalysis.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_food_image(request):
    """Endpoint para analizar imagen de comida con IA"""
    serializer = ImageAnalysisCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    image_data = serializer.validated_data['image_data']
    image_format = serializer.validated_data['image_format']
    
    # Crear registro de análisis
    analysis = ImageAnalysis.objects.create(
        user=user,
        image_size=len(base64.b64decode(image_data)),
        image_format=image_format,
        status='processing'
    )
    
    try:
        start_time = time.time()
        
        # TODO: Aquí iría la integración real con Gemini
        # Por ahora simulamos la respuesta
        ai_response = simulate_gemini_analysis(image_data)
        
        processing_time = time.time() - start_time
        
        # Actualizar análisis con resultados
        analysis.status = 'completed'
        analysis.processing_time_seconds = processing_time
        analysis.raw_ai_response = ai_response
        analysis.gemini_request_tokens = ai_response.get('request_tokens', 0)
        analysis.gemini_response_tokens = ai_response.get('response_tokens', 0)
        analysis.gemini_cost_usd = ai_response.get('cost_usd', 0)
        analysis.save()
        
        # Crear ScannedFood si el análisis fue exitoso
        if ai_response.get('food_name') and ai_response['food_name'] != 'No identificado':
            scanned_food_data = {
                'ai_identified_name': ai_response['food_name'],
                'serving_size': ai_response.get('serving_size', ''),
                'calories_per_serving': ai_response.get('calories_per_serving'),
                'protein_per_serving': ai_response.get('protein_per_serving'),
                'carbs_per_serving': ai_response.get('carbs_per_serving'),
                'fat_per_serving': ai_response.get('fat_per_serving'),
                'calories_per_100g': ai_response.get('calories_per_100g'),
                'protein_per_100g': ai_response.get('protein_per_100g'),
                'carbs_per_100g': ai_response.get('carbs_per_100g'),
                'fat_per_100g': ai_response.get('fat_per_100g'),
                'raw_ai_response': ai_response
            }
            
            scanned_serializer = ScannedFoodCreateSerializer(
                data=scanned_food_data,
                context={'request': request}
            )
            if scanned_serializer.is_valid():
                scanned_food = scanned_serializer.save()
                
                # Actualizar estadísticas de uso
                update_usage_stats(user, analysis, success=True)
                
                return Response({
                    'analysis': ImageAnalysisSerializer(analysis).data,
                    'scanned_food': scanned_serializer.data,
                    'message': 'Análisis completado exitosamente'
                }, status=status.HTTP_201_CREATED)
        
        # Si llegamos aquí, el análisis no fue exitoso
        analysis.status = 'failed'
        analysis.error_message = 'No se pudo identificar el alimento'
        analysis.save()
        
        update_usage_stats(user, analysis, success=False)
        
        return Response({
            'analysis': ImageAnalysisSerializer(analysis).data,
            'message': 'No se pudo identificar el alimento en la imagen'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Manejar errores
        analysis.status = 'error'
        analysis.error_message = str(e)
        analysis.processing_time_seconds = time.time() - start_time
        analysis.save()
        
        update_usage_stats(user, analysis, success=False)
        
        return Response({
            'analysis': ImageAnalysisSerializer(analysis).data,
            'error': 'Error en el análisis de la imagen'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Endpoint para obtener estadísticas del usuario"""
    user = request.user
    
    # Estadísticas generales
    analyses = ImageAnalysis.objects.filter(user=user)
    total_analyses = analyses.count()
    successful_analyses = analyses.filter(status='completed').count()
    failed_analyses = analyses.filter(status__in=['failed', 'error']).count()
    
    success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
    
    # Costos
    total_cost = analyses.aggregate(Sum('gemini_cost_usd'))['gemini_cost_usd__sum'] or 0
    avg_cost = total_cost / total_analyses if total_analyses > 0 else 0
    
    # Estadísticas del mes actual
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_analyses = analyses.filter(created_at__gte=current_month)
    analyses_this_month = monthly_analyses.count()
    cost_this_month = monthly_analyses.aggregate(Sum('gemini_cost_usd'))['gemini_cost_usd__sum'] or 0
    
    # Última fecha de análisis
    last_analysis = analyses.order_by('-created_at').first()
    last_analysis_date = last_analysis.created_at if last_analysis else None
    
    stats_data = {
        'total_analyses': total_analyses,
        'successful_analyses': successful_analyses,
        'failed_analyses': failed_analyses,
        'success_rate': round(success_rate, 2),
        'total_cost': total_cost,
        'average_cost_per_analysis': round(avg_cost, 6),
        'last_analysis_date': last_analysis_date,
        'analyses_this_month': analyses_this_month,
        'cost_this_month': cost_this_month,
    }
    
    serializer = UserStatsSerializer(stats_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usage_stats_by_date(request):
    """Endpoint para obtener estadísticas por fecha"""
    user = request.user
    days = int(request.query_params.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    stats = GeminiUsageStats.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    serializer = GeminiUsageStatsSerializer(stats, many=True)
    return Response({
        'period': f'{start_date} - {end_date}',
        'stats': serializer.data
    })


def simulate_gemini_analysis(image_data):
    """Función temporal para simular respuesta de Gemini"""
    # TODO: Reemplazar con integración real de Gemini
    import random
    
    foods = [
        {
            'food_name': 'Manzana Roja',
            'serving_size': '1 manzana mediana (150g)',
            'calories_per_serving': 80,
            'protein_per_serving': 0.3,
            'carbs_per_serving': 21,
            'fat_per_serving': 0.2,
            'calories_per_100g': 52,
            'protein_per_100g': 0.2,
            'carbs_per_100g': 14,
            'fat_per_100g': 0.1,
        },
        {
            'food_name': 'Pan Integral',
            'serving_size': '1 rebanada (30g)',
            'calories_per_serving': 80,
            'protein_per_serving': 3.5,
            'carbs_per_serving': 14,
            'fat_per_serving': 1.2,
            'calories_per_100g': 265,
            'protein_per_100g': 12,
            'carbs_per_100g': 47,
            'fat_per_100g': 4,
        }
    ]
    
    selected_food = random.choice(foods)
    selected_food.update({
        'request_tokens': random.randint(1500, 2000),
        'response_tokens': random.randint(200, 400),
        'cost_usd': random.uniform(0.001, 0.003),
    })
    
    return selected_food


def update_usage_stats(user, analysis, success=True):
    """Actualizar estadísticas de uso diarias"""
    today = timezone.now().date()
    
    stats, created = GeminiUsageStats.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'total_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost_usd': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
        }
    )
    
    # Actualizar estadísticas
    stats.total_requests += 1
    stats.total_input_tokens += analysis.gemini_request_tokens or 0
    stats.total_output_tokens += analysis.gemini_response_tokens or 0
    stats.total_cost_usd += analysis.gemini_cost_usd or 0
    
    if success:
        stats.successful_analyses += 1
    else:
        stats.failed_analyses += 1
    
    stats.save()