from django.urls import path
from . import views

app_name = 'tracking'

urlpatterns = [
    # Registro diario
    path('logs/', views.DailyLogListView.as_view(), name='daily-log-list'),
    path('logs/<int:pk>/', views.DailyLogDetailView.as_view(), name='daily-log-detail'),
    path('logs/today/', views.today_log, name='today-log'),
    path('logs/by-date/', views.daily_log_by_date, name='daily-log-by-date'),
    
    # Alimentos registrados
    path('logs/<int:daily_log_id>/foods/', views.LoggedFoodItemListCreateView.as_view(), name='logged-food-list-create'),
    path('foods/<int:pk>/', views.LoggedFoodItemDetailView.as_view(), name='logged-food-detail'),
    path('foods/quick-log/', views.quick_log_food, name='quick-log-food'),
    
    # Resumen nutricional
    path('summary/', views.nutrition_summary, name='nutrition-summary'),
]