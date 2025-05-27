from rest_framework import serializers
from .models import Food, ScannedFood


class FoodSerializer(serializers.ModelSerializer):
    """Serializer para Food"""
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Food
        fields = ('id', 'name', 'brand', 'barcode', 'calories_per_100g', 
                 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g', 
                 'is_verified', 'created_by_email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by_email', 'created_at', 'updated_at')


class FoodCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear alimentos"""
    class Meta:
        model = Food
        fields = ('name', 'brand', 'barcode', 'calories_per_100g', 
                 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g')
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ScannedFoodSerializer(serializers.ModelSerializer):
    """Serializer para ScannedFood"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ScannedFood
        fields = ('id', 'user_email', 'ai_identified_name', 'serving_size',
                 'calories_per_serving', 'protein_per_serving', 'carbs_per_serving', 'fat_per_serving',
                 'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g',
                 'created_at')
        read_only_fields = ('id', 'user_email', 'created_at')


class ScannedFoodCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear alimentos escaneados"""
    class Meta:
        model = ScannedFood
        fields = ('ai_identified_name', 'serving_size',
                 'calories_per_serving', 'protein_per_serving', 'carbs_per_serving', 'fat_per_serving',
                 'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g',
                 'raw_ai_response')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FoodSearchSerializer(serializers.Serializer):
    """Serializer para búsqueda de alimentos"""
    query = serializers.CharField(max_length=200)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)