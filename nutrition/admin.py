from django.contrib import admin
from .models import UserProfile, FitnessGoal, NutritionTargets


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para UserProfile"""
    list_display = ('user', 'weight', 'height', 'age', 'gender', 'activity_level', 'bmi', 'created_at')
    list_filter = ('gender', 'activity_level', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('bmi', 'bmr', 'tdee', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Datos Físicos', {
            'fields': ('weight', 'height', 'age', 'gender')
        }),
        ('Actividad', {
            'fields': ('activity_level',)
        }),
        ('Cálculos', {
            'fields': ('bmi', 'bmr', 'tdee'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FitnessGoal)
class FitnessGoalAdmin(admin.ModelAdmin):
    """Admin para FitnessGoal"""
    list_display = ('user', 'goal_type', 'is_active', 'created_at')
    list_filter = ('goal_type', 'is_active', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NutritionTargets)
class NutritionTargetsAdmin(admin.ModelAdmin):
    """Admin para NutritionTargets"""
    list_display = ('user', 'date', 'calories', 'protein', 'carbs', 'fat', 'fitness_goal')
    list_filter = ('date', 'fitness_goal__goal_type', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Usuario y Fecha', {
            'fields': ('user', 'date', 'fitness_goal')
        }),
        ('Metas Nutricionales', {
            'fields': ('calories', 'protein', 'carbs', 'fat')
        }),
        ('Datos Base', {
            'fields': ('bmi', 'tdee', 'bmr'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )