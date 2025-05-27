from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-9kva3o4(!)h_ve3$$($)wj*pi$&qq(uo6hsw+2yqa(%ncqw9me'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',  # AGREGAR ESTA LÍNEA
    'rest_framework_simplejwt',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    
    # Local apps
    'users',
    'nutrition',
    'foods',
    'tracking',
    'ai_analysis'
]

# Site ID requerido por allauth
SITE_ID = 1

REST_FRAMEWORK = {
   'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework_simplejwt.authentication.JWTAuthentication',
   ),
   'DEFAULT_PERMISSION_CLASSES': [
       'rest_framework.permissions.IsAuthenticated',
   ],
   'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
   'PAGE_SIZE': 20
}

# JWT Configuration
SIMPLE_JWT = {
   'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
   'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
   'ROTATE_REFRESH_TOKENS': True,
}

# Configuración de allauth (actualizar la sección existente)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # AGREGAR ESTA LÍNEA
ACCOUNT_USERNAME_REQUIRED = False  # AGREGAR ESTA LÍNEA

# Configuración de proveedores sociales
SOCIALACCOUNT_PROVIDERS = {
   'google': {
       'SCOPE': [
           'profile',
           'email',
       ],
       'AUTH_PARAMS': {
           'access_type': 'online',
       },
       'OAUTH_PKCE_ENABLED': True,
   }
}

# Configuración de dj-rest-auth
REST_AUTH = {
   'USE_JWT': True,
   'JWT_AUTH_COOKIE': 'jwt-auth',
   'JWT_AUTH_REFRESH_COOKIE': 'jwt-refresh-token',
}

# CORS Configuration (para React Native)
CORS_ALLOWED_ORIGINS = [
   "http://localhost:3000",  # Para desarrollo web
   "http://127.0.0.1:3000",
   "http://localhost:8081",  # Para Expo
   "http://192.168.0.11:8081",  # Tu IP local (ajustar según tu red)
]

CORS_ALLOW_ALL_ORIGINS = True 

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # AGREGAR ESTA LÍNEA
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
   {
       'BACKEND': 'django.template.backends.django.DjangoTemplates',
       'DIRS': [],
       'APP_DIRS': True,
       'OPTIONS': {
           'context_processors': [
               'django.template.context_processors.request',
               'django.contrib.auth.context_processors.auth',
               'django.contrib.messages.context_processors.messages',
               'django.template.context_processors.request',  # Requerido para allauth
           ],
       },
   },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.sqlite3',
       'NAME': BASE_DIR / 'db.sqlite3',
   }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
   {
       'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
   },
   {
       'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
   },
   {
       'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
   },
   {
       'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
   },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Usuario personalizado
AUTH_USER_MODEL = 'users.User'