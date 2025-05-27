from django.urls import path
from . import views

app_name = 'ai_analysis'

urlpatterns = [
    # Análisis de imágenes
    path('analyses/', views.ImageAnalysisListView.as_view(), name='analysis-list'),
    path('analyses/<int:pk>/', views.ImageAnalysisDetailView.as_view(), name='analysis-detail'),
    path('analyze/', views.analyze_food_image, name='analyze-food-image'),
    
    # Estadísticas
    path('stats/', views.user_stats, name='user-stats'),
    path('stats/by-date/', views.usage_stats_by_date, name='usage-stats-by-date'),
]