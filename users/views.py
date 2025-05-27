from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer, UserUpdateSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """Endpoint para obtener info del usuario actual"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user(request):
    """Actualizar datos básicos del usuario"""
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """Eliminar cuenta del usuario"""
    user = request.user
    user.delete()
    return Response({'message': 'Cuenta eliminada exitosamente'}, 
                   status=status.HTTP_204_NO_CONTENT)