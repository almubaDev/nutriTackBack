from rest_framework import serializers
from .models import UserProfile, FitnessGoal, NutritionTargets


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para UserProfile"""
    bmi = serializers.ReadOnlyField()
    bmr = serializers.ReadOnlyField()
    tdee = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = ('id', 'weight', 'height', 'age', 'gender', 'activity_level', 
                 'bmi', 'bmr', 'tdee', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class FitnessGoalSerializer(serializers.ModelSerializer):
    """Serializer para FitnessGoal"""
    goal_type_display = serializers.CharField(source='get_goal_type_display', read_only=True)
    
    class Meta:
        model = FitnessGoal
        fields = ('id', 'goal_type', 'goal_type_display', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class NutritionTargetsSerializer(serializers.ModelSerializer):
    """Serializer para NutritionTargets"""
    fitness_goal_display = serializers.CharField(source='fitness_goal.get_goal_type_display', read_only=True)
    
    class Meta:
        model = NutritionTargets
        fields = ('id', 'date', 'calories', 'protein', 'carbs', 'fat', 
                 'bmi', 'tdee', 'bmr', 'fitness_goal', 'fitness_goal_display', 'created_at')
        read_only_fields = ('id', 'created_at')


class NutritionTargetsCreateSerializer(serializers.Serializer):
    """Serializer para crear/calcular metas nutricionales"""
    profile_data = UserProfileSerializer()
    goal_type = serializers.ChoiceField(choices=FitnessGoal.GOAL_CHOICES)
    date = serializers.DateField()
    
    def create(self, validated_data):
        user = self.context['request'].user
        profile_data = validated_data['profile_data']
        goal_type = validated_data['goal_type']
        date = validated_data['date']
        
        # Crear o actualizar perfil
        profile, created = UserProfile.objects.update_or_create(
            user=user,
            defaults=profile_data
        )
        
        # Crear o actualizar objetivo fitness
        fitness_goal, created = FitnessGoal.objects.update_or_create(
            user=user,
            goal_type=goal_type,
            defaults={'is_active': True}
        )
        
        # Desactivar otros objetivos
        FitnessGoal.objects.filter(user=user).exclude(id=fitness_goal.id).update(is_active=False)
        
        # Calcular metas nutricionales
        targets = self._calculate_nutrition_targets(profile, fitness_goal, date)
        
        return targets
    
    def _calculate_nutrition_targets(self, profile, fitness_goal, date):
        """Calcular metas nutricionales basadas en perfil y objetivo"""
        bmr = profile.bmr
        tdee = profile.tdee
        bmi = profile.bmi
        
        # Ajustar calorías según objetivo
        if fitness_goal.goal_type == 'weight_loss':
            calorie_target = tdee - 500  # Déficit de 500 kcal
        elif fitness_goal.goal_type == 'muscle_gain':
            calorie_target = tdee + 300  # Superávit de 300 kcal
        elif fitness_goal.goal_type == 'recomposition':
            calorie_target = tdee  # Mantenimiento
        else:  # maintenance
            calorie_target = tdee
        
        # Distribución de macronutrientes
        if fitness_goal.goal_type in ['muscle_gain', 'recomposition']:
            protein_percentage = 0.30
        else:
            protein_percentage = 0.25
        
        fat_percentage = 0.25
        
        # Calcular gramos de macronutrientes
        protein_grams = round((calorie_target * protein_percentage) / 4)  # 4 kcal/g
        fat_grams = round((calorie_target * fat_percentage) / 9)  # 9 kcal/g
        carb_calories = calorie_target - (protein_grams * 4 + fat_grams * 9)
        carb_grams = round(carb_calories / 4)  # 4 kcal/g
        
        # Crear o actualizar metas nutricionales
        targets, created = NutritionTargets.objects.update_or_create(
            user=profile.user,
            date=date,
            defaults={
                'calories': round(calorie_target),
                'protein': protein_grams,
                'carbs': carb_grams,
                'fat': fat_grams,
                'bmi': bmi,
                'tdee': tdee,
                'bmr': round(bmr),
                'fitness_goal': fitness_goal,
            }
        )
        
        return targets