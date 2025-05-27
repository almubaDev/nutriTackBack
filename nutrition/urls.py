from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    # Perfil nutricional
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Objetivos fitness
    path('goals/', views.FitnessGoalListCreateView.as_view(), name='fitness-goals'),
    path('goals/active/', views.ActiveFitnessGoalView.as_view(), name='active-goal'),
    
    # Metas nutricionales
    path('targets/', views.NutritionTargetsView.as_view(), name='nutrition-targets'),
    path('targets/today/', views.today_targets, name='today-targets'),
    path('targets/calculate/', views.calculate_nutrition_targets, name='calculate-targets'),
]