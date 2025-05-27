from django.urls import path
from . import views

app_name = 'foods'

urlpatterns = [
    # Alimentos base de datos
    path('', views.FoodListCreateView.as_view(), name='food-list-create'),
    path('<int:pk>/', views.FoodDetailView.as_view(), name='food-detail'),
    path('search/', views.search_foods, name='search-foods'),
    
    # Alimentos escaneados
    path('scanned/', views.ScannedFoodListCreateView.as_view(), name='scanned-food-list-create'),
    path('scanned/<int:pk>/', views.ScannedFoodDetailView.as_view(), name='scanned-food-detail'),
    path('scanned/my/', views.my_scanned_foods, name='my-scanned-foods'),
    path('scanned/<int:scanned_id>/convert/', views.convert_scanned_to_food, name='convert-scanned-food'),
]