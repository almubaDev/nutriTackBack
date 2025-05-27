from django.contrib import admin
from .models import DailyLog, LoggedFoodItem


class LoggedFoodItemInline(admin.TabularInline):
    """Inline para mostrar alimentos registrados en el DailyLog"""
    model = LoggedFoodItem
    extra = 0
    readonly_fields = ('logged_at',)
    fields = ('name', 'quantity', 'unit', 'calories', 'protein', 'carbs', 'fat', 'meal_type')


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    """Admin para DailyLog"""
    list_display = ('user', 'date', 'total_calories', 'total_protein', 
                   'total_carbs', 'total_fat', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('total_calories', 'total_protein', 'total_carbs', 'total_fat',
                      'created_at', 'updated_at')
    date_hierarchy = 'date'
    inlines = [LoggedFoodItemInline]
    
    fieldsets = (
        ('Usuario y Fecha', {
            'fields': ('user', 'date')
        }),
        ('Totales Calculados', {
            'fields': ('total_calories', 'total_protein', 'total_carbs', 'total_fat'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoggedFoodItem)
class LoggedFoodItemAdmin(admin.ModelAdmin):
    """Admin para LoggedFoodItem"""
    list_display = ('name', 'daily_log', 'quantity', 'unit', 'calories', 
                   'meal_type', 'logged_at')
    list_filter = ('meal_type', 'daily_log__date', 'logged_at')
    search_fields = ('name', 'daily_log__user__email')
    readonly_fields = ('logged_at',)
    
    fieldsets = (
        ('Registro', {
            'fields': ('daily_log', 'meal_type')
        }),
        ('Alimento', {
            'fields': ('name', 'food', 'scanned_food')
        }),
        ('Cantidad', {
            'fields': ('quantity', 'unit')
        }),
        ('Información Nutricional', {
            'fields': ('calories', 'protein', 'carbs', 'fat')
        }),
        ('Fechas', {
            'fields': ('logged_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('daily_log', 'food', 'scanned_food')