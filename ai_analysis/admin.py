from django.contrib import admin
from .models import ImageAnalysis, GeminiUsageStats


@admin.register(ImageAnalysis)
class ImageAnalysisAdmin(admin.ModelAdmin):
    """Admin para ImageAnalysis"""
    list_display = ('user', 'status', 'image_format', 'image_size', 
                   'gemini_cost_usd', 'processing_time_seconds', 'created_at')
    list_filter = ('status', 'image_format', 'created_at')
    search_fields = ('user__email', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'processing_time_seconds')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Imagen', {
            'fields': ('image_size', 'image_format')
        }),
        ('Estado', {
            'fields': ('status', 'error_message')
        }),
        ('Gemini API', {
            'fields': ('gemini_request_tokens', 'gemini_response_tokens', 'gemini_cost_usd'),
            'classes': ('collapse',)
        }),
        ('Respuesta IA', {
            'fields': ('raw_ai_response',),
            'classes': ('collapse',)
        }),
        ('Tiempos', {
            'fields': ('processing_time_seconds', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeminiUsageStats)
class GeminiUsageStatsAdmin(admin.ModelAdmin):
    """Admin para GeminiUsageStats"""
    list_display = ('user', 'date', 'total_requests', 'successful_analyses', 
                   'failed_analyses', 'success_rate', 'total_cost_usd', 'average_cost_per_request')
    list_filter = ('date', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('success_rate', 'average_cost_per_request', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Usuario y Fecha', {
            'fields': ('user', 'date')
        }),
        ('Estadísticas de Requests', {
            'fields': ('total_requests', 'successful_analyses', 'failed_analyses', 'success_rate')
        }),
        ('Tokens y Costos', {
            'fields': ('total_input_tokens', 'total_output_tokens', 'total_cost_usd', 'average_cost_per_request')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')