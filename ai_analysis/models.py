from django.db import models
from django.conf import settings


class ImageAnalysis(models.Model):
    """Registro de análisis de imágenes por IA"""
    
    ANALYSIS_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    
    # Metadatos de la imagen (NO almacenamos la imagen)
    image_size = models.IntegerField('Tamaño de imagen (bytes)', null=True, blank=True)
    image_format = models.CharField('Formato de imagen', max_length=10, null=True, blank=True)
    
    # Request/Response de Gemini
    gemini_request_tokens = models.IntegerField('Tokens de request', null=True, blank=True)
    gemini_response_tokens = models.IntegerField('Tokens de response', null=True, blank=True)
    gemini_cost_usd = models.DecimalField(
        'Costo en USD',
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Status del análisis
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=ANALYSIS_STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField('Mensaje de error', blank=True)
    
    # Respuesta cruda de IA (para debugging)
    raw_ai_response = models.JSONField('Respuesta cruda de IA', null=True, blank=True)
    
    # Tiempo de procesamiento
    processing_time_seconds = models.FloatField('Tiempo de procesamiento (s)', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Análisis de {self.user.email} - {self.status} ({self.created_at})"
    
    class Meta:
        db_table = 'ai_analysis_imageanalysis'
        verbose_name = 'Análisis de Imagen'
        verbose_name_plural = 'Análisis de Imágenes'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]


class GeminiUsageStats(models.Model):
    """Estadísticas de uso de Gemini por usuario"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    date = models.DateField('Fecha')
    
    # Estadísticas del día
    total_requests = models.IntegerField('Total de requests', default=0)
    total_input_tokens = models.IntegerField('Total tokens de entrada', default=0)
    total_output_tokens = models.IntegerField('Total tokens de salida', default=0)
    total_cost_usd = models.DecimalField(
        'Costo total USD',
        max_digits=10,
        decimal_places=6,
        default=0
    )
    
    # Análisis exitosos vs fallidos
    successful_analyses = models.IntegerField('Análisis exitosos', default=0)
    failed_analyses = models.IntegerField('Análisis fallidos', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats de {self.user.email} - {self.date}"
    
    @property
    def success_rate(self):
        """Calcular tasa de éxito"""
        total = self.successful_analyses + self.failed_analyses
        if total == 0:
            return 0
        return round((self.successful_analyses / total) * 100, 2)
    
    @property
    def average_cost_per_request(self):
        """Calcular costo promedio por request"""
        if self.total_requests == 0:
            return 0
        return round(float(self.total_cost_usd) / self.total_requests, 6)
    
    class Meta:
        db_table = 'ai_analysis_geminiusagestats'
        verbose_name = 'Estadísticas de Uso de Gemini'
        verbose_name_plural = 'Estadísticas de Uso de Gemini'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]