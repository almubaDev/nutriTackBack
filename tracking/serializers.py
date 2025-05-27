from rest_framework import serializers
from django.utils import timezone
from .models import DailyLog, LoggedFoodItem
from foods.models import Food, ScannedFood


class LoggedFoodItemSerializer(serializers.ModelSerializer):
    """Serializer para LoggedFoodItem"""
    food_name = serializers.CharField(source='food.name', read_only=True)
    scanned_food_name = serializers.CharField(source='scanned_food.ai_identified_name', read_only=True)
    meal_type_display = serializers.CharField(source='get_meal_type_display', read_only=True)
    
    class Meta:
        model = LoggedFoodItem
        fields = ('id', 'name', 'quantity', 'unit', 'calories', 'protein', 'carbs', 'fat',
                 'meal_type', 'meal_type_display', 'food', 'scanned_food', 
                 'food_name', 'scanned_food_name', 'logged_at')
        read_only_fields = ('id', 'logged_at')


class LoggedFoodItemCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear LoggedFoodItem"""
    class Meta:
        model = LoggedFoodItem
        fields = ('name', 'quantity', 'unit', 'calories', 'protein', 'carbs', 'fat',
                 'meal_type', 'food', 'scanned_food')
    
    def validate(self, data):
        """Validar que se proporcione food O scanned_food, no ambos"""
        food = data.get('food')
        scanned_food = data.get('scanned_food')
        
        if food and scanned_food:
            raise serializers.ValidationError(
                "No se puede referenciar tanto 'food' como 'scanned_food' al mismo tiempo"
            )
        
        return data


class DailyLogSerializer(serializers.ModelSerializer):
    """Serializer para DailyLog"""
    food_items = LoggedFoodItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = DailyLog
        fields = ('id', 'user_email', 'date', 'total_calories', 'total_protein', 
                 'total_carbs', 'total_fat', 'food_items', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user_email', 'total_calories', 'total_protein', 
                          'total_carbs', 'total_fat', 'created_at', 'updated_at')


class QuickLogFoodSerializer(serializers.Serializer):
    """Serializer para registrar comida rápidamente"""
    date = serializers.DateField(default=timezone.now().date)
    meal_type = serializers.ChoiceField(choices=LoggedFoodItem.MEAL_CHOICES, default='other')
    
    # Referencia a alimento existente (opcional)
    food_id = serializers.IntegerField(required=False)
    scanned_food_id = serializers.IntegerField(required=False)
    
    # Datos de entrada manual
    name = serializers.CharField(max_length=200, required=False)
    quantity = serializers.FloatField(min_value=0.1)
    unit = serializers.CharField(max_length=20)
    
    # Valores nutricionales
    calories = serializers.FloatField(min_value=0, required=False)
    protein = serializers.FloatField(min_value=0, required=False)
    carbs = serializers.FloatField(min_value=0, required=False)
    fat = serializers.FloatField(min_value=0, required=False)
    
    def validate(self, data):
        food_id = data.get('food_id')
        scanned_food_id = data.get('scanned_food_id')
        name = data.get('name')
        
        if food_id and scanned_food_id:
            raise serializers.ValidationError("No se puede referenciar tanto food_id como scanned_food_id")
        
        if not food_id and not scanned_food_id and not name:
            raise serializers.ValidationError("Se requiere food_id, scanned_food_id o name")
        
        # Si es entrada manual, validar valores nutricionales
        if not food_id and not scanned_food_id:
            required_fields = ['calories', 'protein', 'carbs', 'fat']
            for field in required_fields:
                if data.get(field) is None:
                    raise serializers.ValidationError(f"Se requiere {field} para entrada manual")
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        date = validated_data['date']
        
        # Obtener o crear DailyLog
        daily_log, created = DailyLog.objects.get_or_create(
            user=user,
            date=date
        )
        
        # Preparar datos
        food_id = validated_data.get('food_id')
        scanned_food_id = validated_data.get('scanned_food_id')
        quantity = validated_data['quantity']
        unit = validated_data['unit']
        meal_type = validated_data['meal_type']
        
        if food_id:
            # Registrar desde Food
            try:
                food = Food.objects.get(id=food_id)
                factor = quantity / 100
                logged_item = LoggedFoodItem.objects.create(
                    daily_log=daily_log,
                    food=food,
                    name=food.name,
                    quantity=quantity,
                    unit=unit,
                    calories=food.calories_per_100g * factor,
                    protein=food.protein_per_100g * factor,
                    carbs=food.carbs_per_100g * factor,
                    fat=food.fat_per_100g * factor,
                    meal_type=meal_type
                )
            except Food.DoesNotExist:
                raise serializers.ValidationError("Food no encontrado")
                
        elif scanned_food_id:
            # Registrar desde ScannedFood
            try:
                scanned_food = ScannedFood.objects.get(id=scanned_food_id, user=user)
                
                if scanned_food.calories_per_serving:
                    # Usar datos por porción
                    factor = quantity
                    calories = (scanned_food.calories_per_serving or 0) * factor
                    protein = (scanned_food.protein_per_serving or 0) * factor
                    carbs = (scanned_food.carbs_per_serving or 0) * factor
                    fat = (scanned_food.fat_per_serving or 0) * factor
                else:
                    # Usar datos por 100g
                    factor = quantity / 100
                    calories = (scanned_food.calories_per_100g or 0) * factor
                    protein = (scanned_food.protein_per_100g or 0) * factor
                    carbs = (scanned_food.carbs_per_100g or 0) * factor
                    fat = (scanned_food.fat_per_100g or 0) * factor
                
                logged_item = LoggedFoodItem.objects.create(
                    daily_log=daily_log,
                    scanned_food=scanned_food,
                    name=scanned_food.ai_identified_name,
                    quantity=quantity,
                    unit=unit,
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fat=fat,
                    meal_type=meal_type
                )
            except ScannedFood.DoesNotExist:
                raise serializers.ValidationError("Alimento escaneado no encontrado")
        
        else:
            # Entrada manual
            logged_item = LoggedFoodItem.objects.create(
                daily_log=daily_log,
                name=validated_data['name'],
                quantity=quantity,
                unit=unit,
                calories=validated_data['calories'],
                protein=validated_data['protein'],
                carbs=validated_data['carbs'],
                fat=validated_data['fat'],
                meal_type=meal_type
            )
        
        return logged_item