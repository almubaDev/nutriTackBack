from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """Perfil del usuario con datos físicos y de actividad"""
    
    GENDER_CHOICES = [
        ('male', 'Masculino'),
        ('female', 'Femenino'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        (1.2, 'Sedentario (poco o ningún ejercicio)'),
        (1.375, 'Ejercicio ligero (1-3 días/semana)'),
        (1.55, 'Ejercicio moderado (3-5 días/semana)'),
        (1.725, 'Ejercicio intenso (6-7 días/semana)'),
        (1.9, 'Ejercicio muy intenso (dos veces al día, trabajos físicos)'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nutrition_profile',
        verbose_name='Usuario'
    )
    weight = models.FloatField(
        'Peso',
        help_text="Peso en kilogramos"
    )
    height = models.FloatField(
        'Altura',
        help_text="Altura en centímetros"
    ) 
    age = models.PositiveIntegerField(
        'Edad',
        help_text="Edad en años"
    )
    gender = models.CharField(
        'Género',
        max_length=10, 
        choices=GENDER_CHOICES,
        help_text="Género del usuario"
    )
    activity_level = models.FloatField(
        'Nivel de actividad',
        choices=ACTIVITY_LEVEL_CHOICES,
        help_text="Nivel de actividad física"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Perfil nutricional de {self.user.email}"
    
    @property
    def bmi(self):
        """Calcula el IMC (Índice de Masa Corporal)"""
        if self.height > 0:
            height_m = self.height / 100  # convertir cm a metros
            return round(self.weight / (height_m * height_m), 2)
        return 0
    
    @property
    def bmr(self):
        """Calcula la Tasa Metabólica Basal usando fórmula Mifflin-St Jeor"""
        if self.gender == 'male':
            return 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            return 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
    
    @property 
    def tdee(self):
        """Calcula el Gasto Energético Diario Total"""
        return round(self.bmr * self.activity_level)
    
    class Meta:
        db_table = 'nutrition_userprofile'
        verbose_name = 'Perfil Nutricional'
        verbose_name_plural = 'Perfiles Nutricionales'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]


class FitnessGoal(models.Model):
    """Objetivo fitness del usuario"""
    
    GOAL_CHOICES = [
        ('weight_loss', 'Bajar de peso'),
        ('muscle_gain', 'Ganar musculatura'),
        ('maintenance', 'Mantener peso actual'),
        ('recomposition', 'Recomposición corporal'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    goal_type = models.CharField(
        'Tipo de objetivo',
        max_length=20, 
        choices=GOAL_CHOICES,
        help_text="Objetivo fitness principal"
    )
    is_active = models.BooleanField(
        'Activo',
        default=True,
        help_text="Si este objetivo está actualmente activo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_goal_type_display()}"
    
    class Meta:
        db_table = 'nutrition_fitnessgoal'
        verbose_name = 'Objetivo Fitness'
        verbose_name_plural = 'Objetivos Fitness'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['created_at']),
        ]


class NutritionTargets(models.Model):
    """Metas nutricionales calculadas para el usuario"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    date = models.DateField(
        'Fecha',
        help_text="Fecha para la cual aplican estas metas"
    )
    
    # Metas calculadas
    calories = models.IntegerField('Calorías objetivo')
    protein = models.FloatField('Proteínas objetivo (g)')
    carbs = models.FloatField('Carbohidratos objetivo (g)')
    fat = models.FloatField('Grasas objetivo (g)')
    
    # Datos base para el cálculo
    bmi = models.FloatField('IMC')
    tdee = models.IntegerField('TDEE')
    bmr = models.IntegerField('TMB')
    
    # Referencia al goal usado para calcular
    fitness_goal = models.ForeignKey(
        FitnessGoal,
        on_delete=models.CASCADE,
        verbose_name='Objetivo fitness'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Metas de {self.user.email} - {self.date}"
    
    class Meta:
        db_table = 'nutrition_targets'
        verbose_name = 'Metas Nutricionales'
        verbose_name_plural = 'Metas Nutricionales'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['created_at']),
        ]