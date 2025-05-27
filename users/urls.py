from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    # Endpoints de dj-rest-auth
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/google/', include('allauth.socialaccount.providers.google.urls')),
    
    # Endpoints personalizados del User
    path('me/', views.user_info, name='user-info'),
    path('update/', views.update_user, name='update-user'),
    path('delete/', views.delete_account, name='delete-account'),
]