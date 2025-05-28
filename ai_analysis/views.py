# ai_analysis/views.py
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
from .gemini_client import GeminiClient


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
        
        # Usar Gemini real
        gemini_client = GeminiClient()
        ai_result = gemini_client.analyze_food_image(image_data, image_format)
        
        processing_time = time.time() - start_time
        
        if ai_result['success']:
            # Actualizar análisis con resultados exitosos
            analysis.status = 'completed'
            analysis.processing_time_seconds = processing_time
            analysis.raw_ai_response = ai_result.get('raw_response')
            analysis.gemini_request_tokens = ai_result.get('input_tokens', 0)
            analysis.gemini_response_tokens = ai_result.get('output_tokens', 0)
            analysis.gemini_cost_usd = ai_result.get('cost_usd', 0)
            analysis.save()
            
            food_data = ai_result['food_data']
            
            # Crear ScannedFood si se identificó el alimento
            if (food_data.get('food_name') and 
                food_data['food_name'] != 'No identificado' and 
                food_data.get('confidence') != 'bajo'):
                
                # Preparar datos para ScannedFood
                nutrition_serving = food_data.get('nutrition_per_serving', {})
                nutrition_100g = food_data.get('nutrition_per_100g', {})
                
                scanned_food_data = {
                    'ai_identified_name': food_data['food_name'],
                    'serving_size': food_data.get('serving_size', ''),
                    'calories_per_serving': nutrition_serving.get('calories'),
                    'protein_per_serving': nutrition_serving.get('protein_g'),
                    'carbs_per_serving': nutrition_serving.get('carbs_g'),
                    'fat_per_serving': nutrition_serving.get('fat_g'),
                    'calories_per_100g': nutrition_100g.get('calories'),
                    'protein_per_100g': nutrition_100g.get('protein_g'),
                    'carbs_per_100g': nutrition_100g.get('carbs_g'),
                    'fat_per_100g': nutrition_100g.get('fat_g'),
                    'raw_ai_response': ai_result
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
                else:
                    # Si hay error en el serializer, aún devolvemos el análisis
                    update_usage_stats(user, analysis, success=True)
                    return Response({
                        'analysis': ImageAnalysisSerializer(analysis).data,
                        'message': 'Alimento identificado pero con problemas en los datos nutricionales',
                        'food_data': food_data
                    }, status=status.HTTP_200_OK)
            else:
                # No se pudo identificar el alimento
                analysis.status = 'failed'
                analysis.error_message = food_data.get('error', 'No se pudo identificar el alimento')
                analysis.save()
                
                update_usage_stats(user, analysis, success=False)
                
                return Response({
                    'analysis': ImageAnalysisSerializer(analysis).data,
                    'message': 'No se pudo identificar el alimento en la imagen'
                }, status=status.HTTP_200_OK)
        else:
            # Error en el análisis de Gemini
            analysis.status = 'error'
            analysis.error_message = ai_result.get('error', 'Error en el análisis de IA')
            analysis.processing_time_seconds = processing_time
            analysis.save()
            
            update_usage_stats(user, analysis, success=False)
            
            return Response({
                'analysis': ImageAnalysisSerializer(analysis).data,
                'error': 'Error en el análisis de la imagen'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        # Manejar errores generales
        analysis.status = 'error'
        analysis.error_message = str(e)
        analysis.processing_time_seconds = time.time() - start_time if 'start_time' in locals() else 0
        analysis.save()
        
        update_usage_stats(user, analysis, success=False)
        
        return Response({
            'analysis': ImageAnalysisSerializer(analysis).data,
            'error': f'Error inesperado: {str(e)}'
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