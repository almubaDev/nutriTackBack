from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', views.api_root, name='api-root'),  # ← AGREGAR ESTA LÍNEA
    path('health/', views.health_check, name='health'),  # ← AGREGAR ESTA LÍNEA
    path('api/users/', include('users.urls')),
    path('api/nutrition/', include('nutrition.urls')),
    path('api/foods/', include('foods.urls')),
    path('api/tracking/', include('tracking.urls')),
    path('api/ai/', include('ai_analysis.urls')),
]