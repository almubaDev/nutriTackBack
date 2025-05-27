from django.db import models
from django.conf import settings


class DailyLog(models.Model):
    """Registro diario del usuario"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    date = models.DateField('Fecha')
    
    # Totales calculados del día
    total_calories = models.FloatField('Total calorías', default=0)
    total_protein = models.FloatField('Total proteínas (g)', default=0)
    total_carbs = models.FloatField('Total carbohidratos (g)', default=0)
    total_fat = models.FloatField('Total grasas (g)', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Log de {self.user.email} - {self.date}"
    
    def calculate_totals(self):
        """Recalcular totales basado en los items de comida"""
        totals = self.food_items.aggregate(
            total_calories=models.Sum('calories'),
            total_protein=models.Sum('protein'),
            total_carbs=models.Sum('carbs'),
            total_fat=models.Sum('fat')
        )
        
        self.total_calories = totals['total_calories'] or 0
        self.total_protein = totals['total_protein'] or 0
        self.total_carbs = totals['total_carbs'] or 0
        self.total_fat = totals['total_fat'] or 0
        self.save()
    
    class Meta:
        db_table = 'tracking_dailylog'
        verbose_name = 'Registro Diario'
        verbose_name_plural = 'Registros Diarios'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['created_at']),
        ]


class LoggedFoodItem(models.Model):
    """Elemento de comida registrado"""
    
    MEAL_CHOICES = [
        ('breakfast', 'Desayuno'),
        ('lunch', 'Almuerzo'),
        ('dinner', 'Cena'),
        ('snack', 'Snack'),
        ('other', 'Otro'),
    ]
    
    daily_log = models.ForeignKey(
        DailyLog,
        on_delete=models.CASCADE,
        related_name='food_items',
        verbose_name='Registro diario'
    )
    
    # Referencia al alimento (puede ser Food o ScannedFood)
    food = models.ForeignKey(
        'foods.Food',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Alimento'
    )
    scanned_food = models.ForeignKey(
        'foods.ScannedFood',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Alimento escaneado'
    )
    
    # Datos del consumo específico
    name = models.CharField('Nombre', max_length=200)  # Nombre en el momento del registro
    quantity = models.FloatField('Cantidad')  # Cantidad consumida
    unit = models.CharField('Unidad', max_length=20)  # 'g', 'ml', 'porción', etc.
    
    # Valores nutricionales calculados para esta porción
    calories = models.FloatField('Calorías')
    protein = models.FloatField('Proteínas (g)')
    carbs = models.FloatField('Carbohidratos (g)')
    fat = models.FloatField('Grasas (g)')
    
    # Metadatos
    meal_type = models.CharField(
        'Tipo de comida',
        max_length=20,
        choices=MEAL_CHOICES,
        default='other'
    )
    logged_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.quantity}{self.unit} ({self.daily_log.date})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalcular totales del día
        self.daily_log.calculate_totals()
    
    def delete(self, *args, **kwargs):
        daily_log = self.daily_log
        super().delete(*args, **kwargs)
        # Recalcular totales después de eliminar
        daily_log.calculate_totals()
    
    class Meta:
        db_table = 'tracking_loggedfooditem'
        verbose_name = 'Alimento Registrado'
        verbose_name_plural = 'Alimentos Registrados'
        indexes = [
            models.Index(fields=['daily_log', 'logged_at']),
            models.Index(fields=['meal_type']),
        ]