from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/nutrition/', include('nutrition.urls')),
    path('api/foods/', include('foods.urls')),
    path('api/tracking/', include('tracking.urls')),
    path('api/ai/', include('ai_analysis.urls')),  # AGREGAR ESTA LÍNEA
]