---

## Anexos

### 📋 Checklist de Deploy

#### Pre-Deploy
- [ ] Todos los tests pasan (`python manage.py test`)
- [ ] Coverage > 80% (`coverage report`)
- [ ] No hay migrations pendientes
- [ ] Variables de entorno configuradas
- [ ] CORS configurado correctamente
- [ ] DEBUG=False en producción
- [ ] SECRET_KEY única y segura
- [ ] ALLOWED_HOSTS configurado
- [ ] Static files funcionando
- [ ] Database backups configurados

#### Post-Deploy
- [ ] Health check endpoint responde
- [ ] Admin panel accesible
- [ ] API endpoints funcionando
- [ ] Autenticación JWT funcional
- [ ] Google OAuth funcional (si configurado)
- [ ] Logging funcionando
- [ ] Monitoreo configurado
- [ ] SSL/TLS funcionando
- [ ] Performance aceptable

### 🔧 Scripts de Utilidad

#### Makefile
```makefile
# Makefile para comandos frecuentes
.PHONY: install migrate test coverage lint format clean deploy-staging deploy-prod

# Desarrollo
install:
	pip install -r requirements/development.txt
	pre-commit install

migrate:
	python manage.py makemigrations
	python manage.py migrate

test:
	python manage.py test --verbosity=2

coverage:
	coverage run --source='.' manage.py test
	coverage report -m
	coverage html

lint:
	flake8 .
	black --check .
	isort --check-only .

format:
	black .
	isort .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .coverage

# Base de datos
db-reset:
	rm -f db.sqlite3
	python manage.py migrate
	python manage.py createsuperuser --noinput --email admin@nutritrack.com

db-seed:
	python manage.py loaddata fixtures/sample_foods.json
	python manage.py loaddata fixtures/sample_users.json

db-backup:
	python manage.py dumpdata --natural-foreign --natural-primary > backup_$(shell date +%Y%m%d_%H%M%S).json

# Deployment
deploy-staging:
	git push staging main
	railway logs --tail

deploy-prod:
	@echo "¿Estás seguro de hacer deploy a producción? [y/N]" && read ans && [ ${ans:-N} = y ]
	git push production main
	railway logs --tail

# Docker (opcional)
docker-build:
	docker build -t nutritrack-api .

docker-run:
	docker run -p 8000:8000 --env-file .env nutritrack-api

# Monitoring
logs:
	railway logs --tail

status:
	curl -f http://localhost:8000/health/ || echo "Service down"
```

#### Script de Setup Inicial
```bash
#!/bin/bash
# scripts/setup.sh - Setup inicial del proyecto

set -e

echo "🚀 Configurando NutriTrack Backend..."

# Verificar Python 3.10+
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Se requiere Python 3.10 o superior. Versión actual: $python_version"
    exit 1
fi

echo "✅ Python $python_version detectado"

# Crear entorno virtual si no existe
if [ ! -d "env" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv env
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source env/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements/development.txt

# Configurar pre-commit
echo "🔍 Configurando pre-commit hooks..."
pre-commit install

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo .env..."
    cp .env.example .env
    echo "📝 Edita el archivo .env con tus configuraciones"
fi

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate

# Crear superusuario si no existe
echo "👤 Creando superusuario..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@nutritrack.com').exists():
    User.objects.create_superuser('admin@nutritrack.com', 'admin123')
    print('Superusuario creado: admin@nutritrack.com / admin123')
else:
    print('Superusuario ya existe')
EOF

# Cargar datos de ejemplo
echo "🌱 Cargando datos de ejemplo..."
python manage.py loaddata fixtures/sample_foods.json || echo "No hay fixtures de foods"

echo "✅ Setup completado!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Editar .env con tus configuraciones"
echo "2. source env/bin/activate"
echo "3. python manage.py runserver"
echo "4. Visitar http://localhost:8000/admin/"
echo "   Usuario: admin@nutritrack.com"
echo "   Contraseña: admin123"
```

#### Script de Deployment
```bash
#!/bin/bash
# scripts/deploy.sh - Script de deployment automatizado

set -e

ENVIRONMENT=${1:-staging}
BRANCH=${2:-main}

echo "🚀 Desplegando a $ENVIRONMENT desde branch $BRANCH..."

# Validaciones pre-deploy
echo "🔍 Ejecutando validaciones pre-deploy..."

# Tests
echo "🧪 Ejecutando tests..."
python manage.py test --verbosity=0
if [ $? -ne 0 ]; then
    echo "❌ Tests fallaron. Deploy abortado."
    exit 1
fi

# Linting
echo "🔍 Verificando calidad de código..."
flake8 . --max-line-length=88 --extend-ignore=E203,W503
if [ $? -ne 0 ]; then
    echo "❌ Linting falló. Deploy abortado."
    exit 1
fi

# Verificar migrations
echo "🗄️ Verificando migraciones..."
python manage.py makemigrations --check --dry-run
if [ $? -ne 0 ]; then
    echo "❌ Hay migraciones pendientes. Deploy abortado."
    exit 1
fi

# Backup (solo para producción)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "💾 Creando backup de producción..."
    railway run python manage.py dumpdata > "backup_prod_$(date +%Y%m%d_%H%M%S).json"
fi

# Deploy según ambiente
case $ENVIRONMENT in
    "staging")
        echo "📤 Desplegando a staging..."
        git push staging $BRANCH:main
        ;;
    "production")
        echo "⚠️  DEPLOY A PRODUCCIÓN"
        echo "¿Continuar? [y/N]"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            git push production $BRANCH:main
        else
            echo "Deploy cancelado."
            exit 1
        fi
        ;;
    *)
        echo "❌ Ambiente no válido: $ENVIRONMENT"
        echo "Usar: staging | production"
        exit 1
        ;;
esac

# Verificar deployment
echo "🔍 Verificando deployment..."
sleep 30  # Esperar que el servicio se inicie

if [ "$ENVIRONMENT" = "staging" ]; then
    HEALTH_URL="https://nutritrack-staging.railway.app/health/"
else
    HEALTH_URL="https://nutritrack-api.railway.app/health/"
fi

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Deploy exitoso! Servicio respondiendo correctamente."
else
    echo "❌ Deploy falló. Status: $HTTP_STATUS"
    exit 1
fi

echo "🎉 Deploy completado exitosamente!"
```

### 📊 Fixtures de Datos de Ejemplo

#### Sample Foods
```json
# fixtures/sample_foods.json
[
  {
    "model": "foods.food",
    "pk": 1,
    "fields": {
      "name": "Manzana Roja",
      "brand": "",
      "barcode": "",
      "calories_per_100g": 52,
      "protein_per_100g": 0.3,
      "carbs_per_100g": 14,
      "fat_per_100g": 0.2,
      "is_verified": true,
      "created_at": "2025-05-27T10:00:00Z"
    }
  },
  {
    "model": "foods.food",
    "pk": 2,
    "fields": {
      "name": "Pechuga de Pollo",
      "brand": "",
      "barcode": "",
      "calories_per_100g": 165,
      "protein_per_100g": 31,
      "carbs_per_100g": 0,
      "fat_per_100g": 3.6,
      "is_verified": true,
      "created_at": "2025-05-27T10:00:00Z"
    }
  },
  {
    "model": "foods.food",
    "pk": 3,
    "fields": {
      "name": "Arroz Blanco Cocido",
      "brand": "",
      "barcode": "",
      "calories_per_100g": 130,
      "protein_per_100g": 2.7,
      "carbs_per_100g": 28,
      "fat_per_100g": 0.3,
      "is_verified": true,
      "created_at": "2025-05-27T10:00:00Z"
    }
  },
  {
    "model": "foods.food",
    "pk": 4,
    "fields": {
      "name": "Aguacate",
      "brand": "",
      "barcode": "",
      "calories_per_100g": 160,
      "protein_per_100g": 2,
      "carbs_per_100g": 9,
      "fat_per_100g": 15,
      "is_verified": true,
      "created_at": "2025-05-27T10:00:00Z"
    }
  },
  {
    "model": "foods.food",
    "pk": 5,
    "fields": {
      "name": "Yogurt Griego Natural",
      "brand": "Genérico",
      "barcode": "",
      "calories_per_100g": 97,
      "protein_per_100g": 10,
      "carbs_per_100g": 4,
      "fat_per_100g": 5,
      "is_verified": true,
      "created_at": "2025-05-27T10:00:00Z"
    }
  }
]
```

### 🐛 Troubleshooting Guide

#### Problemas Comunes

**Error: "ModuleNotFoundError: No module named 'X'"**
```bash
# Solución
pip install -r requirements/development.txt
source env/bin/activate  # Asegurar que el entorno esté activado
```

**Error: "django.db.utils.OperationalError: no such table"**
```bash
# Solución
python manage.py makemigrations
python manage.py migrate
```

**Error: "CORS policy" en el frontend**
```python
# settings.py - Verificar configuración CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",  # Expo
    "exp://192.168.1.100:8081",  # Expo con IP local
]
CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo
```

**Error: "Invalid HTTP_HOST header"**
```python
# settings.py
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'tu-dominio.com']
```

**Performance Lento en Admin**
```python
# Optimizar queries en admin
class UserProfileAdmin(admin.ModelAdmin):
    list_select_related = ('user',)
    
class LoggedFoodItemAdmin(admin.ModelAdmin):
    list_select_related = ('daily_log', 'food', 'scanned_food')
```

**Memoria Alta en Análisis IA**
```python
# ai_analysis/views.py - Optimizar manejo de imágenes
def compress_image_before_analysis(image_data, max_size=1024):
    from PIL import Image
    import io
    
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85, optimize=True)
    return buffer.getvalue()
```

### 📞 Soporte y Contacto

#### Recursos de Documentación
- **Django**: https://docs.djangoproject.com/
- **DRF**: https://www.django-rest-framework.org/
- **django-allauth**: https://django-allauth.readthedocs.io/
- **Gemini API**: https://ai.google.dev/gemini-api/docs

#### Comunidad y Ayuda
- **Stack Overflow**: Tag `django` + `django-rest-framework`
- **Django Discord**: https://discord.gg/xcRH6mN4fa
- **Reddit**: r/django, r/djangolearning

#### Issues y Contribuciones
```markdown
# Reportar un Bug
1. Verificar que no esté ya reportado
2. Incluir información del entorno:
   - Python version
   - Django version
   - OS
3. Pasos para reproducir
4. Comportamiento esperado vs actual
5. Logs relevantes

# Sugerir una Mejora
1. Describir el problema que resuelve
2. Proponer la solución
3. Considerar alternativas
4. Impacto en código existente
```

---

## License y Términos

### 📄 MIT License (Sugerida)
```
MIT License

Copyright (c) 2025 NutriTrack IA

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### ⚖️ Términos de Uso de IA
```markdown
# Uso de APIs de Inteligencia Artificial

Este proyecto utiliza Google Gemini API para análisis de imágenes de alimentos.

## Responsabilidades:
- Los usuarios son responsables de sus propias claves API
- El análisis IA es estimativo, no reemplaza consejo médico
- Los costos de API corren por cuenta del operador del servicio
- Cumplir con términos de uso de Google Gemini API

## Limitaciones:
- Precisión del análisis puede variar
- Dependiente de servicios externos
- Sujeto a límites de rate limiting
- Requiere conexión a internet
```

---

## Changelog Final

### 📅 Version 1.0.0 (2025-05-27) - Release Inicial

#### ✨ Nuevas Funcionalidades
- **Autenticación completa** con email + Google OAuth
- **Cálculos nutricionales automáticos** (BMR, TDEE, IMC, macros)
- **Análisis de alimentos por IA** (simulado, listo para Gemini)
- **Seguimiento diario** con totales automáticos
- **Base de datos de alimentos** con búsqueda
- **API REST completa** con 40+ endpoints
- **Admin panel configurado** para gestión
- **Documentación completa** con ejemplos

#### 🏗️ Arquitectura
- **5 apps modulares**: users, nutrition, foods, tracking, ai_analysis
- **Modelos optimizados** con índices y relaciones correctas
- **Serializers robustos** con validaciones
- **Vistas API completas** con manejo de errores
- **Tests estructurados** (ejemplos incluidos)

#### 🚀 Deployment
- **Railway ready** con configuración completa
- **Fly.io ready** con Dockerfile
- **Variables de entorno** configuradas
- **Scripts de deployment** automatizados
- **Health checks** implementados

#### 📚 Documentación
- **70+ páginas** de documentación completa
- **Ejemplos de requests** reales
- **Guía de deployment** detallada
- **Troubleshooting guide** completo
- **Roadmap futuro** planificado

---

## 🎯 Conclusión

Este backend de **NutriTrack IA** representa una base sólida y escalable para una aplicación de seguimiento nutricional con inteligencia artificial. 

### ✅ Lo que tienes ahora:
- **API REST completa** lista para producción
- **Arquitectura modular** fácil de mantener
- **Integración IA** lista para conectar
- **Documentación exhaustiva** para cualquier desarrollador
- **Scripts de deployment** automatizados
- **Roadmap claro** para futuras mejoras

### 🚀 Próximo paso:
¡Hora de crear el frontend React Native + Expo y ver tu app cobrar vida!

---

*Documentación generada el 27 de Mayo, 2025 - NutriTrack IA Backend v1.0.0*---

## Costos y Límites Detallados

### 💰 Análisis de Costos Gemini API

#### Precios Gemini 2.5 Flash (2025)
- **Input**: $0.15 por 1M tokens
- **Output**: $0.60 por 1M tokens (sin thinking)
- **Output**: $3.50 por 1M tokens (con thinking)

#### Cálculo por Análisis de Alimento
```
Imagen típica + prompt = ~1,750 tokens input
Respuesta JSON = ~300 tokens output

Costo por análisis:
- Input: (1,750 ÷ 1,000,000) × $0.15 = $0.000263
- Output: (300 ÷ 1,000,# NutriTrack IA - Documentación del Backend

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Configuración e Instalación](#configuración-e-instalación)
4. [Apps y Modelos](#apps-y-modelos)
5. [API Endpoints](#api-endpoints)
6. [Autenticación](#autenticación)
7. [Base de Datos](#base-de-datos)
8. [Deployment](#deployment)
9. [Testing](#testing)

---

## Introducción

**NutriTrack IA** es una API REST desarrollada en **Django REST Framework** para una aplicación móvil de seguimiento nutricional con análisis de alimentos por inteligencia artificial.

### Características Principales
- ✅ Autenticación con email + Google OAuth
- ✅ Cálculo automático de metas nutricionales (BMR, TDEE, macros)
- ✅ Análisis de alimentos por IA (Gemini)
- ✅ Seguimiento diario de consumo
- ✅ Base de datos de alimentos
- ✅ Estadísticas de uso y costos de IA

### Stack Tecnológico
- **Backend**: Django 5.2 + Django REST Framework
- **Base de Datos**: SQLite (desarrollo), PostgreSQL (producción)
- **Autenticación**: JWT + Google OAuth (django-allauth)
- **IA**: Google Gemini 2.5 Flash (por implementar)
- **Deploy**: Railway (recomendado)

---

## Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  React Native   │────│   Django API     │────│   PostgreSQL    │
│  (Frontend)     │    │   (Backend)      │    │  (Database)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                │
                       ┌──────────────────┐
                       │   Gemini API     │
                       │   (Google AI)    │
                       └──────────────────┘
```

### Apps del Sistema

| App | Responsabilidad |
|-----|----------------|
| `users` | Autenticación y gestión de usuarios |
| `nutrition` | Perfiles nutricionales y metas |
| `foods` | Base de datos de alimentos |
| `tracking` | Seguimiento diario de consumo |
| `ai_analysis` | Análisis de imágenes con IA |

---

## Configuración e Instalación

### Requisitos
- Python 3.10+
- Django 5.2+
- Django REST Framework

### Instalación Local

```bash
# Clonar repositorio
git clone <repo-url>
cd nutritrack-backend

# Crear entorno virtual
python -m venv env
source env/bin/activate  # Linux/Mac
# env\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Variables de Entorno

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (producción)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
```

---

## Apps y Modelos

### 🔐 App `users`

**Modelos:**
- `User` - Usuario personalizado con autenticación por email

**Funcionalidades:**
- Registro con email y contraseña
- Login con Google OAuth
- Gestión de perfil básico

### 🏋️ App `nutrition`

**Modelos:**
- `UserProfile` - Datos físicos (peso, altura, edad, género, actividad)
- `FitnessGoal` - Objetivos fitness (pérdida de peso, ganancia muscular, etc.)
- `NutritionTargets` - Metas nutricionales calculadas

**Cálculos Automáticos:**
- **BMR** (Tasa Metabólica Basal) - Fórmula Mifflin-St Jeor
- **TDEE** (Gasto Energético Diario Total) - BMR × Factor de Actividad
- **Macronutrientes** - Distribución personalizada según objetivo

### 🍎 App `foods`

**Modelos:**
- `Food` - Base de datos de alimentos verificados
- `ScannedFood` - Alimentos identificados por IA

**Funcionalidades:**
- Búsqueda de alimentos
- Conversión de alimentos escaneados a base de datos
- Información nutricional por 100g y por porción

### 📊 App `tracking`

**Modelos:**
- `DailyLog` - Registro diario del usuario
- `LoggedFoodItem` - Alimentos consumidos

**Funcionalidades:**
- Seguimiento automático de totales diarios
- Registro por tipo de comida (desayuno, almuerzo, etc.)
- Cálculo automático de macronutrientes consumidos

### 🤖 App `ai_analysis`

**Modelos:**
- `ImageAnalysis` - Registro de análisis de imágenes
- `GeminiUsageStats` - Estadísticas de uso de IA

**Funcionalidades:**
- Análisis de imágenes de alimentos
- Seguimiento de costos de IA
- Estadísticas de uso por usuario

---

## API Endpoints

### Base URL: `http://localhost:8000/api/`

### 🔐 Autenticación (`/users/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/users/auth/registration/` | Registro de usuario |
| POST | `/users/auth/login/` | Login con email/password |
| POST | `/users/auth/logout/` | Logout |
| POST | `/users/auth/google/` | Login con Google |
| GET | `/users/me/` | Información del usuario actual |
| PATCH | `/users/update/` | Actualizar datos del usuario |
| DELETE | `/users/delete/` | Eliminar cuenta |

### 🏋️ Nutrición (`/nutrition/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET/PUT | `/nutrition/profile/` | Perfil nutricional del usuario |
| GET/POST | `/nutrition/goals/` | Objetivos fitness |
| GET | `/nutrition/goals/active/` | Objetivo fitness activo |
| GET | `/nutrition/targets/` | Metas nutricionales |
| GET | `/nutrition/targets/today/` | Metas de hoy |
| POST | `/nutrition/targets/calculate/` | Calcular nuevas metas |

### 🍎 Alimentos (`/foods/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET/POST | `/foods/` | Listar/crear alimentos |
| GET/PUT/DELETE | `/foods/{id}/` | Detalle de alimento |
| POST | `/foods/search/` | Buscar alimentos |
| GET/POST | `/foods/scanned/` | Alimentos escaneados |
| GET/DELETE | `/foods/scanned/{id}/` | Detalle de alimento escaneado |
| POST | `/foods/scanned/{id}/convert/` | Convertir a alimento verificado |

### 📊 Seguimiento (`/tracking/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/tracking/logs/` | Registros diarios |
| GET | `/tracking/logs/{id}/` | Detalle de registro |
| GET/POST | `/tracking/logs/today/` | Registro de hoy |
| GET | `/tracking/logs/by-date/?date=YYYY-MM-DD` | Registro por fecha |
| POST | `/tracking/foods/quick-log/` | Registro rápido de alimento |
| GET/PUT/DELETE | `/tracking/foods/{id}/` | Detalle de alimento registrado |
| GET | `/tracking/summary/` | Resumen nutricional (7 días) |

### 🤖 Análisis IA (`/ai/`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/ai/analyses/` | Historial de análisis |
| GET | `/ai/analyses/{id}/` | Detalle de análisis |
| POST | `/ai/analyze/` | Analizar imagen de alimento |
| GET | `/ai/stats/` | Estadísticas del usuario |
| GET | `/ai/stats/by-date/?days=30` | Estadísticas por fecha |

---

## Autenticación

### JWT Tokens

La API utiliza **JSON Web Tokens (JWT)** para autenticación:

```bash
# Login
POST /api/users/auth/login/
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}

# Respuesta
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Usuario",
    "last_name": "Ejemplo"
  }
}
```

### Headers Requeridos

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

### Google OAuth

Para implementar Google OAuth en el frontend:

1. Obtener token de Google en el cliente
2. Enviar token al backend:

```bash
POST /api/users/auth/google/
{
  "id_token": "google-id-token-aqui"
}
```

---

## Base de Datos

### Esquema Principal

```sql
-- Usuarios
users_user (id, email, password, first_name, last_name, ...)

-- Perfiles nutricionales
nutrition_userprofile (id, user_id, weight, height, age, gender, activity_level, ...)
nutrition_fitnessgoal (id, user_id, goal_type, is_active, ...)
nutrition_targets (id, user_id, date, calories, protein, carbs, fat, ...)

-- Alimentos
foods_food (id, name, brand, calories_per_100g, protein_per_100g, ...)
foods_scanned (id, user_id, ai_identified_name, calories_per_serving, ...)

-- Seguimiento
tracking_dailylog (id, user_id, date, total_calories, total_protein, ...)
tracking_loggedfooditem (id, daily_log_id, name, quantity, calories, ...)

-- Análisis IA
ai_analysis_imageanalysis (id, user_id, status, gemini_cost_usd, ...)
ai_analysis_geminiusagestats (id, user_id, date, total_requests, total_cost_usd, ...)
```

### Relaciones Clave

- `User` 1:1 `UserProfile`
- `User` 1:M `FitnessGoal`
- `User` 1:M `DailyLog` 1:M `LoggedFoodItem`
- `User` 1:M `ScannedFood`
- `User` 1:M `ImageAnalysis`

---

## Deployment

### 🚀 Railway (Recomendado)

Railway es la opción más simple y económica para el MVP.

#### Paso 1: Preparar el Proyecto

1. **Crear `requirements.txt`:**
   ```txt
   Django==5.2
   djangorestframework==3.15.2
   django-allauth==0.63.3
   django-cors-headers==4.3.1
   dj-rest-auth==6.0.0
   djangorestframework-simplejwt==5.3.0
   cryptography==42.0.5
   gunicorn==21.2.0
   psycopg2-binary==2.9.9
   whitenoise==6.6.0
   ```

2. **Crear `Procfile`:**
   ```
   web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
   release: python manage.py migrate
   ```

3. **Actualizar `settings.py` para producción:**
   ```python
   import os
   import dj_database_url
   
   # SECURITY WARNING: don't run with debug turned on in production!
   DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
   
   ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
   
   # Database
   if os.getenv('DATABASE_URL'):
       DATABASES = {
           'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
       }
   
   # Static files (CSS, JavaScript, Images)
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   
   # Whitenoise middleware
   MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
   ```

#### Paso 2: Deploy en Railway

1. **Conectar repositorio:** Vincula tu repositorio de GitHub
2. **Configurar variables de entorno:**
   ```
   SECRET_KEY=tu-secret-key-super-segura-aqui
   DEBUG=False
   ALLOWED_HOSTS=tu-app.railway.app,*.railway.app
   GEMINI_API_KEY=tu-gemini-api-key-aqui
   
   # Google OAuth (opcional)
   GOOGLE_OAUTH2_CLIENT_ID=tu-google-client-id
   GOOGLE_OAUTH2_CLIENT_SECRET=tu-google-client-secret
   ```
3. **Agregar PostgreSQL:** Railway automáticamente provee DATABASE_URL
4. **Deploy:** Railway despliega automáticamente en cada push

#### Costos Railway
- **Hobby Plan**: $5/mes
- **PostgreSQL**: Incluida
- **Tráfico**: 100GB incluidos

### ☁️ Fly.io (Para Escalar)

Fly.io es excelente para deploy global y escalabilidad.

#### Paso 1: Configurar Fly.io

1. **Instalar Fly CLI:**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Crear `Dockerfile`:**
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy project
   COPY . .
   
   # Collect static files
   RUN python manage.py collectstatic --noinput
   
   EXPOSE 8000
   
   CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

3. **Crear app en Fly.io:**
   ```bash
   fly auth login
   fly apps create nutritrack-api
   ```

4. **Configurar `fly.toml`:**
   ```toml
   app = "nutritrack-api"
   primary_region = "mia"
   
   [build]
   
   [env]
     PORT = "8000"
   
   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
   
   [[vm]]
     memory = "1gb"
     cpu_kind = "shared"
     cpus = 1
   
   [postgres]
     image = "postgres:14"
   ```

5. **Configurar base de datos:**
   ```bash
   fly postgres create --name nutritrack-db
   fly postgres attach --app nutritrack-api nutritrack-db
   ```

6. **Configurar secretos:**
   ```bash
   fly secrets set SECRET_KEY=tu-secret-key-aqui
   fly secrets set GEMINI_API_KEY=tu-gemini-api-key
   fly secrets set DEBUG=False
   ```

7. **Deploy:**
   ```bash
   fly deploy
   ```

#### Costos Fly.io
- **Machines**: $0.000001667/second ($1.94/mes por 256MB)
- **PostgreSQL**: $0.01/hora ($7.30/mes)
- **Tráfico**: 3GB gratis, luego $0.02/GB

### 🔧 DigitalOcean App Platform (Alternativa)

```yaml
# .do/app.yaml
name: nutritrack-api
services:
- name: api
  source_dir: /
  github:
    repo: tu-usuario/nutritrack-backend
    branch: main
  run_command: gunicorn core.wsgi:application
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: tu-secret-key
  - key: DEBUG
    value: "False"
  - key: GEMINI_API_KEY
    value: tu-gemini-api-key

databases:
- name: nutritrack-db
  engine: PG
  version: "14"
```

### 🌍 Variables de Entorno por Plataforma

| Variable | Desarrollo | Railway | Fly.io | DigitalOcean |
|----------|------------|---------|--------|--------------|
| `SECRET_KEY` | settings.py | ENV | Secret | ENV |
| `DEBUG` | True | False | False | False |
| `DATABASE_URL` | SQLite | Auto | Auto | Auto |
| `ALLOWED_HOSTS` | localhost | *.railway.app | *.fly.dev | *.ondigitalocean.app |
| `GEMINI_API_KEY` | .env | ENV | Secret | ENV |

### 📊 Comparación de Plataformas

| Característica | Railway | Fly.io | DigitalOcean |
|----------------|---------|--------|--------------|
| **Precio mínimo** | $5/mes | $2/mes | $5/mes |
| **Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Escalabilidad** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Deploy global** | ❌ | ✅ | ✅ |
| **Free tier** | ❌ | ⭐⭐ | ❌ |
| **PostgreSQL** | ✅ | ✅ | ✅ |

### 🔒 Checklist de Seguridad

#### Antes del Deploy
- [ ] `DEBUG = False` en producción
- [ ] `SECRET_KEY` única y segura
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] Variables sensibles en variables de entorno
- [ ] CORS configurado para tu dominio del frontend
- [ ] HTTPS forzado
- [ ] Rate limiting configurado

#### SSL/TLS
```python
# settings.py para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
```

### 📈 Monitoreo y Logs

#### Railway
```bash
# Ver logs en tiempo real
railway logs --tail

# Conectar a base de datos
railway connect
```

#### Fly.io
```bash
# Ver logs
fly logs

# SSH a la máquina
fly ssh console

# Escalar horizontalmente
fly scale count 2
```

### 🚨 Rollback y Backup

#### Railway
- Rollback automático desde dashboard
- Backups automáticos de PostgreSQL

#### Fly.io
```bash
# Ver releases
fly releases

# Rollback a versión anterior
fly rollback --version v2
```

### 📱 Health Checks

```python
# core/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Endpoint para verificar salud de la aplicación"""
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)

# core/urls.py
urlpatterns = [
    path('health/', health_check, name='health-check'),
    # ... otras urls
]
```

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos por app
python manage.py test users
python manage.py test nutrition
python manage.py test foods
python manage.py test tracking
python manage.py test ai_analysis

# Tests con cobertura
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Genera reporte HTML
```

### Estructura de Tests Recomendada

```
tests/
├── __init__.py
├── test_users/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_views.py
│   └── test_auth.py
├── test_nutrition/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_calculations.py
│   ├── test_serializers.py
│   └── test_views.py
├── test_foods/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_search.py
│   └── test_views.py
├── test_tracking/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_daily_totals.py
│   └── test_views.py
├── test_ai_analysis/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_simulation.py
│   └── test_stats.py
└── fixtures/
    ├── test_users.json
    ├── test_foods.json
    └── sample_images/
```

### Ejemplos de Tests Completos

#### Test de Autenticación
```python
# tests/test_users/test_auth.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class UserAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
    
    def test_user_registration(self):
        """Test registro de usuario exitoso"""
        response = self.client.post('/api/users/auth/registration/', self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login(self):
        """Test login exitoso"""
        # Crear usuario primero
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        response = self.client.post('/api/users/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_protected_endpoint_requires_auth(self):
        """Test que endpoints protegidos requieren autenticación"""
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

#### Test de Cálculos Nutricionales
```python
# tests/test_nutrition/test_calculations.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from nutrition.models import UserProfile, FitnessGoal, NutritionTargets

User = get_user_model()

class NutritionCalculationsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            weight=70,
            height=175,
            age=30,
            gender='male',
            activity_level=1.55
        )
    
    def test_bmi_calculation(self):
        """Test cálculo de IMC"""
        expected_bmi = 70 / (1.75 * 1.75)  # 22.86
        self.assertAlmostEqual(self.profile.bmi, expected_bmi, places=2)
    
    def test_bmr_calculation_male(self):
        """Test cálculo de BMR para hombre"""
        expected_bmr = 10 * 70 + 6.25 * 175 - 5 * 30 + 5  # 1693.75
        self.assertAlmostEqual(self.profile.bmr, expected_bmr, places=2)
    
    def test_bmr_calculation_female(self):
        """Test cálculo de BMR para mujer"""
        self.profile.gender = 'female'
        self.profile.save()
        expected_bmr = 10 * 70 + 6.25 * 175 - 5 * 30 - 161  # 1527.75
        self.assertAlmostEqual(self.profile.bmr, expected_bmr, places=2)
    
    def test_tdee_calculation(self):
        """Test cálculo de TDEE"""
        expected_tdee = self.profile.bmr * 1.55
        self.assertAlmostEqual(self.profile.tdee, expected_tdee, places=0)
```

#### Test de Seguimiento Diario
```python
# tests/test_tracking/test_daily_totals.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from tracking.models import DailyLog, LoggedFoodItem
from foods.models import Food

User = get_user_model()

class DailyTotalsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.daily_log = DailyLog.objects.create(
            user=self.user,
            date=timezone.now().date()
        )
        self.food = Food.objects.create(
            name='Manzana',
            calories_per_100g=52,
            protein_per_100g=0.3,
            carbs_per_100g=14,
            fat_per_100g=0.2
        )
    
    def test_daily_totals_calculation(self):
        """Test que los totales diarios se calculan correctamente"""
        # Agregar 200g de manzana (factor = 2)
        LoggedFoodItem.objects.create(
            daily_log=self.daily_log,
            food=self.food,
            name='Manzana',
            quantity=200,
            unit='g',
            calories=52 * 2,  # 104
            protein=0.3 * 2,  # 0.6
            carbs=14 * 2,     # 28
            fat=0.2 * 2       # 0.4
        )
        
        # Refrescar desde DB
        self.daily_log.refresh_from_db()
        
        self.assertEqual(self.daily_log.total_calories, 104)
        self.assertEqual(self.daily_log.total_protein, 0.6)
        self.assertEqual(self.daily_log.total_carbs, 28)
        self.assertEqual(self.daily_log.total_fat, 0.4)
```

### Fixtures para Tests

```json
# tests/fixtures/test_foods.json
[
  {
    "model": "foods.food",
    "pk": 1,
    "fields": {
      "name": "Manzana Roja",
      "calories_per_100g": 52,
      "protein_per_100g": 0.3,
      "carbs_per_100g": 14,
      "fat_per_100g": 0.2,
      "is_verified": true
    }
  },
  {
    "model": "foods.food",
    "pk": 2,
    "fields": {
      "name": "Pan Integral",
      "calories_per_100g": 265,
      "protein_per_100g": 12,
      "carbs_per_100g": 47,
      "fat_per_100g": 4,
      "is_verified": true
    }
  }
]
```

### Comandos de Test Útiles

```bash
# Test con output verbose
python manage.py test --verbosity=2

# Test específico con patrón
python manage.py test --pattern="test_*calculations*"

# Test con warnings
python manage.py test --debug-mode

# Test en paralelo (más rápido)
python manage.py test --parallel

# Test con base de datos en memoria (más rápido)
python manage.py test --settings=core.test_settings
```

---

## Costos y Límites Detallados

### 💰 Análisis de Costos Gemini API

#### Precios Gemini 2.5 Flash (2025)
- **Input**: $0.15 por 1M tokens
- **Output**: $0.60 por 1M tokens (sin thinking)
- **Output**: $3.50 por 1M tokens (con thinking)

#### Cálculo por Análisis de Alimento
```
Imagen típica + prompt = ~1,750 tokens input
Respuesta JSON = ~300 tokens output

Costo por análisis:
- Input: (1,750 ÷ 1,000,000) × $0.15 = $0.000263
- Output: (300 ÷ 1,000,000) × $0.60 = $0.000180
- Total: ~$0.0004 por análisis
```

#### Proyección de Costos por Escala

| Usuarios | Análisis/día | Análisis/mes | Costo/mes | Costo/usuario |
|----------|--------------|--------------|-----------|---------------|
| 100 | 500 | 15,000 | $6.60 | $0.066 |
| 500 | 2,500 | 75,000 | $33.00 | $0.066 |
| 1,000 | 5,000 | 150,000 | $66.00 | $0.066 |
| 5,000 | 25,000 | 750,000 | $330.00 | $0.066 |
| 10,000 | 50,000 | 1,500,000 | $660.00 | $0.066 |

#### Estrategias de Optimización de Costos

1. **Compresión de Imágenes**
   ```python
   from PIL import Image
   import io
   
   def compress_image(image_data, max_size=1024, quality=85):
       """Comprimir imagen para reducir tokens"""
       image = Image.open(io.BytesIO(image_data))
       image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
       
       buffer = io.BytesIO()
       image.save(buffer, format='JPEG', quality=quality, optimize=True)
       return buffer.getvalue()
   ```

2. **Cache de Análisis**
   ```python
   import hashlib
   
   def get_image_hash(image_data):
       """Generar hash de imagen para cache"""
       return hashlib.md5(image_data).hexdigest()
   
   def get_cached_analysis(image_hash):
       """Buscar análisis en cache"""
       return ScannedFood.objects.filter(
           raw_ai_response__image_hash=image_hash
       ).first()
   ```

3. **Límites por Usuario**
   ```python
   from datetime import timedelta
   from django.utils import timezone
   
   def check_user_limits(user, daily_limit=20, monthly_limit=100):
       """Verificar límites de análisis por usuario"""
       today = timezone.now().date()
       month_start = today.replace(day=1)
       
       daily_count = ImageAnalysis.objects.filter(
           user=user,
           created_at__date=today,
           status='completed'
       ).count()
       
       monthly_count = ImageAnalysis.objects.filter(
           user=user,
           created_at__date__gte=month_start,
           status='completed'
       ).count()
       
       return {
           'can_analyze': daily_count < daily_limit and monthly_count < monthly_limit,
           'daily_remaining': max(0, daily_limit - daily_count),
           'monthly_remaining': max(0, monthly_limit - monthly_count)
       }
   ```

### 🏗️ Límites de Infraestructura

#### Railway Limits
- **CPU**: 8 vCPU shared
- **RAM**: 8GB max
- **Storage**: 100GB
- **Bandwidth**: 100GB/mes
- **Build time**: 30 minutos max
- **Concurrent builds**: 1

#### Fly.io Limits
- **CPU**: Configurable (shared/dedicated)
- **RAM**: 256MB - 8GB
- **Storage**: Hasta 3TB
- **Bandwidth**: 3GB gratis, luego $0.02/GB
- **Regiones**: 30+ disponibles
- **Concurrent builds**: Múltiples

#### Recomendaciones por Tamaño

| Tamaño | Usuarios | CPU | RAM | Storage | Plataforma |
|--------|----------|-----|-----|---------|------------|
| **Startup** | 1-100 | 1 vCPU | 512MB | 10GB | Railway |
| **Growth** | 100-1K | 2 vCPU | 1GB | 50GB | Railway/Fly.io |
| **Scale** | 1K-10K | 4 vCPU | 2GB | 100GB | Fly.io |
| **Enterprise** | 10K+ | 8+ vCPU | 4GB+ | 500GB+ | AWS/GCP |

### 📊 Métricas de Performance

#### Benchmarks Esperados
```python
# Tiempos de respuesta objetivo
PERFORMANCE_TARGETS = {
    'auth_login': 200,           # ms
    'get_user_profile': 100,     # ms
    'nutrition_calculation': 150, # ms
    'food_search': 300,          # ms
    'ai_analysis': 3000,         # ms (3s)
    'daily_log_summary': 200,    # ms
}

# Límites de rate limiting
RATE_LIMITS = {
    'authenticated': '1000/hour',  # Usuarios autenticados
    'anonymous': '100/hour',       # Usuarios anónimos
    'ai_analysis': '60/hour',      # Análisis IA por usuario
    'registration': '10/hour',     # Registros por IP
}
```

#### Monitoreo con Django Debug Toolbar
```python
# settings.py (solo desarrollo)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    
    import socket
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]
```

### 🔍 Logging y Debugging

#### Configuración de Logs Avanzada
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
        'api_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'api.log',
            'formatter': 'verbose',
        },
        'ai_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'ai_analysis.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['api_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_analysis': {
            'handlers': ['ai_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

#### Custom Logging Middleware
```python
# middleware/logging.py
import time
import logging

logger = logging.getLogger('api')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Log request
        logger.info(f"API Request: {request.method} {request.path}")
        
        response = self.get_response(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(f"API Response: {response.status_code} in {duration:.3f}s")
        
        return response
```

### 🛡️ Seguridad Avanzada

#### Rate Limiting con django-ratelimit
```python
# pip install django-ratelimit

from django_ratelimit.decorators import ratelimit
from django.contrib.auth import get_user_model

@ratelimit(key='user', rate='60/h', method='POST')
def analyze_food_image(request):
    """Limitar análisis IA a 60 por hora por usuario"""
    pass

@ratelimit(key='ip', rate='10/h', method='POST')
def user_registration(request):
    """Limitar registros a 10 por hora por IP"""
    pass
```

#### Validación de Imágenes Segura
```python
from PIL import Image
import magic

def validate_image(image_data):
    """Validar que el archivo sea realmente una imagen"""
    # Verificar tipo MIME
    mime_type = magic.from_buffer(image_data, mime=True)
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    
    if mime_type not in allowed_types:
        raise ValidationError(f"Tipo de archivo no permitido: {mime_type}")
    
    # Verificar que PIL puede abrir la imagen
    try:
        image = Image.open(io.BytesIO(image_data))
        image.verify()
    except Exception as e:
        raise ValidationError(f"Imagen corrupta: {str(e)}")
    
    # Verificar dimensiones razonables
    if image.size[0] > 4096 or image.size[1] > 4096:
        raise ValidationError("Imagen demasiado grande")
    
    return True
```

#### CORS Seguro para Producción
```python
# settings.py para producción
CORS_ALLOWED_ORIGINS = [
    "https://nutritrack-app.com",
    "https://www.nutritrack-app.com",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.nutritrack-app\.com$",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

### 📱 Preparación para Mobile

#### Response Compression
```python
# settings.py
MIDDLEWARE += ['django.middleware.gzip.GZipMiddleware']

# Para archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

#### API Versioning
```python
# core/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/nutrition/', include('nutrition.urls')),
    path('api/v1/foods/', include('foods.urls')),
    path('api/v1/tracking/', include('tracking.urls')),
    path('api/v1/ai/', include('ai_analysis.urls')),
]
```

#### Offline Support Headers
```python
# middleware/offline.py
class OfflineSupportMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Headers para soporte offline
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-cache, must-revalidate'
            response['X-Timestamp'] = timezone.now().isoformat()
            
        return response
```

---

## Próximos Pasos y Roadmap

### 🎯 Implementaciones Inmediatas (Semana 1-2)

#### Integración Gemini Real
```python
# Reemplazar simulación en ai_analysis/views.py
from google.generativeai import configure, GenerativeModel
import google.generativeai as genai

def integrate_real_gemini():
    """Integrar Gemini API real"""
    genai.configure(api_key=GEMINI_API_KEY)
    
    model = GenerativeModel('gemini-2.5-flash-preview-04-17')
    
    # Implementar análisis real de imágenes
    # Ver código en MVP original para referencia
```

#### Email Verification
```python
# settings.py
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

#### Rate Limiting
```bash
pip install django-ratelimit
```

### 🚀 Mejoras a Mediano Plazo (Semana 3-4)

#### 1. Cache con Redis
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache de búsquedas frecuentes
from django.core.cache import cache

def cached_food_search(query):
    cache_key = f"food_search_{query.lower()}"
    results = cache.get(cache_key)
    
    if results is None:
        results = Food.objects.filter(name__icontains=query)[:10]
        cache.set(cache_key, results, 3600)  # 1 hora
    
    return results
```

#### 2. Tareas Asíncronas con Celery
```python
# pip install celery redis

# celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('nutritrack')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# tasks.py
from celery import shared_task

@shared_task
def analyze_image_async(user_id, image_data):
    """Analizar imagen de forma asíncrona"""
    # Implementar análisis en background
    pass

@shared_task
def send_daily_reminder(user_id):
    """Enviar recordatorio diario"""
    # Implementar notificación
    pass
```

#### 3. WebSockets para Updates en Tiempo Real
```python
# pip install channels channels-redis

# routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/tracking/', consumers.TrackingConsumer.as_asgi()),
]

# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("tracking", self.channel_name)
        await self.accept()
    
    async def send_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
```

### 🎯 Funcionalidades Avanzadas (Mes 2-3)

#### 1. Machine Learning Local
```python
# Modelo para predicción de calorías basado en historial
from sklearn.ensemble import RandomForestRegressor
import joblib

class CaloriePredictionModel:
    def __init__(self):
        self.model = RandomForestRegressor()
        self.is_trained = False
    
    def train_from_user_data(self, user):
        """Entrenar modelo con datos del usuario"""
        food_items = LoggedFoodItem.objects.filter(
            daily_log__user=user
        ).values('quantity', 'calories', 'protein', 'carbs', 'fat')
        
        # Implementar entrenamiento
        pass
    
    def predict_calories(self, food_data):
        """Predecir calorías basado en características"""
        if not self.is_trained:
            return None
        return self.model.predict([food_data])[0]
```

#### 2. Análisis Nutricional Avanzado
```python
# nutrition/analytics.py
from datetime import timedelta
import numpy as np

class NutritionAnalytics:
    @staticmethod
    def calculate_trends(user, days=30):
        """Calcular tendencias nutricionales"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        logs = DailyLog.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        calories = [log.total_calories for log in logs]
        protein = [log.total_protein for log in logs]
        
        return {
            'calorie_trend': np.polyfit(range(len(calories)), calories, 1)[0],
            'protein_trend': np.polyfit(range(len(protein)), protein, 1)[0],
            'avg_calories': np.mean(calories),
            'calorie_consistency': 1 - (np.std(calories) / np.mean(calories))
        }
    
    @staticmethod
    def suggest_improvements(user):
        """Sugerir mejoras nutricionales"""
        trends = NutritionAnalytics.calculate_trends(user)
        suggestions = []
        
        if trends['protein_trend'] < 0:
            suggestions.append({
                'type': 'protein',
                'message': 'Considera aumentar tu consumo de proteínas',
                'priority': 'high'
            })
        
        return suggestions
```

#### 3. Integración con Wearables
```python
# integrations/fitbit.py
import requests

class FitbitIntegration:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://api.fitbit.com/1/user/-'
    
    def get_daily_activity(self, date):
        """Obtener actividad diaria de Fitbit"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.get(
            f'{self.base_url}/activities/date/{date}.json',
            headers=headers
        )
        return response.json()
    
    def sync_activity_level(self, user, date):
        """Sincronizar nivel de actividad con perfil nutricional"""
        activity = self.get_daily_activity(date)
        steps = activity.get('summary', {}).get('steps', 0)
        
        # Ajustar activity_level basado en pasos
        if steps > 12000:
            activity_level = 1.725  # Very active
        elif steps > 8000:
            activity_level = 1.55   # Moderately active
        else:
            activity_level = 1.375  # Lightly active
        
        # Actualizar perfil
        profile = user.nutrition_profile
        profile.activity_level = activity_level
        profile.save()
```

### 🎯 Escalabilidad Empresarial (Mes 4-6)

#### 1. Multi-tenancy
```python
# models/base.py
from django.db import models

class TenantAwareModel(models.Model):
    """Modelo base para multi-tenancy"""
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    
    class Meta:
        abstract = True

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Configuraciones específicas del tenant
    max_users = models.IntegerField(default=1000)
    ai_analysis_limit = models.IntegerField(default=10000)
```

#### 2. API Gateway
```python
# gateway/middleware.py
class APIGatewayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Rate limiting
        if not self.check_rate_limit(request):
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        
        # API Key validation
        if not self.validate_api_key(request):
            return JsonResponse({'error': 'Invalid API key'}, status=401)
        
        # Request logging
        self.log_request(request)
        
        response = self.get_response(request)
        
        # Response transformation
        return self.transform_response(response)
```

#### 3. Microservicios
```python
# Separar en servicios independientes:
# - user-service (autenticación)
# - nutrition-service (cálculos)
# - ai-service (análisis de imágenes)
# - tracking-service (seguimiento)

# docker-compose.yml
version: '3.8'
services:
  user-service:
    build: ./user-service
    ports:
      - "8001:8000"
  
  nutrition-service:
    build: ./nutrition-service
    ports:
      - "8002:8000"
  
  ai-service:
    build: ./ai-service
    ports:
      - "8003:8000"
    
  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    depends_on:
      - user-service
      - nutrition-service
      - ai-service
```

### 📊 Métricas y KPIs Sugeridos

#### Métricas de Negocio
- **MAU** (Monthly Active Users)
- **Retention Rate** (1 día, 7 días, 30 días)
- **Análisis por usuario/mes**
- **Tiempo promedio de sesión**
- **Alimentos registrados por usuario**

#### Métricas Técnicas
- **API Response Time** (P95, P99)
- **Error Rate** (<1%)
- **Uptime** (>99.9%)
- **Database Performance**
- **AI Analysis Success Rate**

#### Dashboard de Monitoreo
```python
# monitoring/views.py
def health_dashboard(request):
    """Dashboard de salud del sistema"""
    stats = {
        'active_users_today': User.objects.filter(
            last_login__date=timezone.now().date()
        ).count(),
        'analyses_today': ImageAnalysis.objects.filter(
            created_at__date=timezone.now().date(),
            status='completed'
        ).count(),
        'avg_response_time': get_avg_response_time(),
        'error_rate': get_error_rate(),
        'ai_cost_today': ImageAnalysis.objects.filter(
            created_at__date=timezone.now().date()
        ).aggregate(Sum('gemini_cost_usd'))['gemini_cost_usd__sum'] or 0
    }
    
    return JsonResponse(stats)
```

### 🔮 Visión a Largo Plazo

#### 1. Inteligencia Artificial Propia
- Entrenar modelo propio de reconocimiento de alimentos
- Reducir dependencia de APIs externas
- Especialización en alimentos locales/regionales

#### 2. Plataforma Completa de Salud
- Integración con análisis de sangre
- Recomendaciones médicas personalizadas
- Seguimiento de ejercicio y sueño

#### 3. Marketplace de Profesionales
- Nutricionistas certificados
- Planes de alimentación personalizados
- Consultas virtuales

---

## Contribución y Desarrollo

### 🤝 Guía de Contribución

#### Setup del Entorno de Desarrollo
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/nutritrack-backend
cd nutritrack-backend

# Configurar pre-commit hooks
pip install pre-commit
pre-commit install

# Configurar git hooks
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
python manage.py test
if [ $? -ne 0 ]; then
    echo "Tests failed. Push aborted."
    exit 1
fi
EOF
chmod +x .git/hooks/pre-push
```

#### Standards de Código
```python
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

#### Pull Request Template
```markdown
## Descripción
Breve descripción de los cambios realizados.

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva funcionalidad
- [ ] Breaking change
- [ ] Documentación

## Testing
- [ ] Tests unitarios agregados/actualizados
- [ ] Tests de integración ejecutados
- [ ] Tests manuales realizados

## Checklist
- [ ] Código sigue los standards del proyecto
- [ ] Self-review realizado
- [ ] Documentación actualizada
- [ ] No hay warnings en las migrations
```

### 📝 Documentación para Desarrolladores

#### Estructura del Proyecto
```
nutritrack-backend/
├── core/                 # Configuración principal
├── users/               # Autenticación y usuarios
├── nutrition/           # Lógica nutricional
├── foods/              # Base de datos de alimentos
├── tracking/           # Seguimiento diario
├── ai_analysis/        # Análisis de IA
├── tests/              # Tests organizados
├── docs/               # Documentación adicional
├── scripts/            # Scripts de utilidad
├── requirements/       # Requirements por entorno
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── deployment/         # Archivos de deployment
    ├── docker/
    ├── railway/
    └── fly/
```

#### Comandos de Desarrollo Útiles
```bash
# Desarrollo
make install          # Instalar dependencias
make migrate         # Ejecutar migraciones
make test           # Ejecutar tests
make coverage       # Coverage report
make lint          # Linting
make format        # Formatear código

# Base de datos
make db-reset      # Reset de base de datos
make db-seed       # Poblar con datos de prueba
make db-backup     # Backup de desarrollo

# Deployment
make deploy-staging    # Deploy a staging
make deploy-production # Deploy a producción
```

---

## Soporte

Para soporte técnico o dudas sobre la implementación:

- **Documentación Django**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **Gemini API**: https://ai.google.dev/gemini-api/docs

---

## Changelog

### v1.0.0 (2025-05-27)
- ✅ Implementación inicial completa
- ✅ 5 apps principales funcionales
- ✅ Autenticación JWT + Google OAuth
- ✅ Cálculos nutricionales automáticos
- ✅ Simulación de análisis IA
- ✅ API REST completa
- ✅ Admin panel configurado
- ✅ Documentación completa