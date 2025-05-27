from django.db import models
from django.conf import settings


class Food(models.Model):
    """Base de datos de alimentos común"""
    name = models.CharField('Nombre', max_length=200)
    brand = models.CharField('Marca', max_length=100, blank=True)
    barcode = models.CharField('Código de barras', max_length=50, blank=True)
    
    # Información nutricional por 100g
    calories_per_100g = models.FloatField('Calorías por 100g')
    protein_per_100g = models.FloatField('Proteínas por 100g (g)')
    carbs_per_100g = models.FloatField('Carbohidratos por 100g (g)')
    fat_per_100g = models.FloatField('Grasas por 100g (g)')
    
    # Metadatos
    is_verified = models.BooleanField(
        'Verificado',
        default=False,
        help_text='Si la información nutricional ha sido verificada'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.brand:
            return f"{self.name} ({self.brand})"
        return self.name
    
    class Meta:
        db_table = 'foods_food'
        verbose_name = 'Alimento'
        verbose_name_plural = 'Alimentos'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['barcode']),
            models.Index(fields=['created_at']),
        ]


class ScannedFood(models.Model):
    """Alimentos identificados por IA"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    
    # Información extraída por IA
    ai_identified_name = models.CharField('Nombre identificado por IA', max_length=200)
    serving_size = models.CharField('Tamaño de porción', max_length=100, blank=True)
    
    # Nutrición por porción (si disponible)
    calories_per_serving = models.FloatField('Calorías por porción', null=True, blank=True)
    protein_per_serving = models.FloatField('Proteínas por porción (g)', null=True, blank=True)
    carbs_per_serving = models.FloatField('Carbohidratos por porción (g)', null=True, blank=True)
    fat_per_serving = models.FloatField('Grasas por porción (g)', null=True, blank=True)
    
    # Nutrición por 100g (si disponible)  
    calories_per_100g = models.FloatField('Calorías por 100g', null=True, blank=True)
    protein_per_100g = models.FloatField('Proteínas por 100g (g)', null=True, blank=True)
    carbs_per_100g = models.FloatField('Carbohidratos por 100g (g)', null=True, blank=True)
    fat_per_100g = models.FloatField('Grasas por 100g (g)', null=True, blank=True)
    
    # Respuesta cruda de IA (para debugging)
    raw_ai_response = models.JSONField('Respuesta cruda de IA', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.ai_identified_name} (escaneado por {self.user.email})"
    
    class Meta:
        db_table = 'foods_scanned'
        verbose_name = 'Alimento Escaneado'
        verbose_name_plural = 'Alimentos Escaneados'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ai_identified_name']),
        ]