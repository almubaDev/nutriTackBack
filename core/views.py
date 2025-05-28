from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.db import connection

@api_view(['GET'])
def api_root(request):
    return Response({'message': 'NutriTrack API is working!'})

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'healthy'})
    except Exception:
        return JsonResponse({'status': 'unhealthy'}, status=503)