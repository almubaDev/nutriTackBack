from django.contrib import admin
from .models import Food, ScannedFood


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    """Admin para Food"""
    list_display = ('name', 'brand', 'calories_per_100g', 'protein_per_100g', 
                   'is_verified', 'created_by', 'created_at')
    list_filter = ('is_verified', 'brand', 'created_at')
    search_fields = ('name', 'brand', 'barcode')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'brand', 'barcode')
        }),
        ('Información Nutricional (por 100g)', {
            'fields': ('calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g')
        }),
        ('Metadatos', {
            'fields': ('is_verified', 'created_by')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScannedFood)
class ScannedFoodAdmin(admin.ModelAdmin):
    """Admin para ScannedFood"""
    list_display = ('ai_identified_name', 'user', 'serving_size', 'calories_per_serving', 
                   'calories_per_100g', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('ai_identified_name', 'user__email')
    readonly_fields = ('created_at', 'raw_ai_response')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información de IA', {
            'fields': ('ai_identified_name', 'serving_size')
        }),
        ('Nutrición por Porción', {
            'fields': ('calories_per_serving', 'protein_per_serving', 
                      'carbs_per_serving', 'fat_per_serving'),
            'classes': ('collapse',)
        }),
        ('Nutrición por 100g', {
            'fields': ('calories_per_100g', 'protein_per_100g', 
                      'carbs_per_100g', 'fat_per_100g'),
            'classes': ('collapse',)
        }),
        ('Datos Técnicos', {
            'fields': ('raw_ai_response', 'created_at'),
            'classes': ('collapse',)
        }),
    )