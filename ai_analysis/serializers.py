from rest_framework import serializers
from .models import ImageAnalysis, GeminiUsageStats


class ImageAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para ImageAnalysis"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ImageAnalysis
        fields = ('id', 'user_email', 'image_size', 'image_format', 'status', 'status_display',
                 'gemini_request_tokens', 'gemini_response_tokens', 'gemini_cost_usd',
                 'error_message', 'processing_time_seconds', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user_email', 'created_at', 'updated_at')


class ImageAnalysisCreateSerializer(serializers.Serializer):
    """Serializer para crear análisis de imagen"""
    image_data = serializers.CharField(
        help_text="Imagen en base64 (sin el prefijo data:image/...)"
    )
    image_format = serializers.CharField(
        max_length=10, 
        default='jpeg',
        help_text="Formato de la imagen: jpeg, png, etc."
    )
    
    def validate_image_data(self, value):
        """Validar que la imagen base64 sea válida"""
        try:
            import base64
            decoded = base64.b64decode(value)
            if len(decoded) == 0:
                raise serializers.ValidationError("Imagen base64 vacía")
            if len(decoded) > 10 * 1024 * 1024:  # 10MB máximo
                raise serializers.ValidationError("Imagen demasiado grande (máximo 10MB)")
        except Exception as e:
            raise serializers.ValidationError(f"Imagen base64 inválida: {str(e)}")
        return value


class GeminiUsageStatsSerializer(serializers.ModelSerializer):
    """Serializer para GeminiUsageStats"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    success_rate = serializers.ReadOnlyField()
    average_cost_per_request = serializers.ReadOnlyField()
    
    class Meta:
        model = GeminiUsageStats
        fields = ('id', 'user_email', 'date', 'total_requests', 'total_input_tokens',
                 'total_output_tokens', 'total_cost_usd', 'successful_analyses',
                 'failed_analyses', 'success_rate', 'average_cost_per_request',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'user_email', 'success_rate', 'average_cost_per_request',
                          'created_at', 'updated_at')


class UserStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del usuario"""
    total_analyses = serializers.IntegerField()
    successful_analyses = serializers.IntegerField()
    failed_analyses = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=6)
    average_cost_per_analysis = serializers.DecimalField(max_digits=8, decimal_places=6)
    last_analysis_date = serializers.DateTimeField()
    analyses_this_month = serializers.IntegerField()
    cost_this_month = serializers.DecimalField(max_digits=10, decimal_places=6)