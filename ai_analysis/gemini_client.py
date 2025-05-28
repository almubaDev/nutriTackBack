# ai_analysis/gemini_client.py
import os
import base64
import json
import time
from decimal import Decimal
import google.generativeai as genai
from django.conf import settings

class GeminiClient:
    def __init__(self):
        # Configurar Gemini API
        api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Precios por token (actualizar según documentación de Google)
        self.input_price_per_token = Decimal('0.00000015')  # $0.15 por 1M tokens
        self.output_price_per_token = Decimal('0.0000006')  # $0.60 por 1M tokens
    
    def analyze_food_image(self, image_data: str, image_format: str = 'jpeg') -> dict:
        """
        Analiza una imagen de alimento usando Gemini
        """
        try:
            # Decodificar imagen base64
            image_bytes = base64.b64decode(image_data)
            
            # Preparar prompt estructurado
            prompt = self._get_food_analysis_prompt()
            
            # Crear objeto de imagen para Gemini
            image_part = {
                "mime_type": f"image/{image_format}",
                "data": image_bytes
            }
            
            # Hacer request a Gemini
            start_time = time.time()
            response = self.model.generate_content([prompt, image_part])
            processing_time = time.time() - start_time
            
            # Procesar respuesta
            if response.text:
                parsed_data = self._parse_gemini_response(response.text)
                
                # Calcular costos (estimados)
                input_tokens = self._estimate_input_tokens(prompt, len(image_bytes))
                output_tokens = self._estimate_output_tokens(response.text)
                
                return {
                    'success': True,
                    'food_data': parsed_data,
                    'processing_time': processing_time,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'cost_usd': float(self._calculate_cost(input_tokens, output_tokens)),
                    'raw_response': response.text
                }
            else:
                return {
                    'success': False,
                    'error': 'No response from Gemini',
                    'processing_time': processing_time
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def _get_food_analysis_prompt(self) -> str:
        """Prompt estructurado para análisis de alimentos"""
        return """Analiza esta imagen de alimento y proporciona la información nutricional en formato JSON.

IMPORTANTE: Responde SOLO con JSON válido, sin texto adicional.

Formato requerido:
{
    "food_name": "Nombre del alimento identificado",
    "serving_size": "Tamaño de porción (ej: '1 manzana mediana', '100g', '1 taza')",
    "confidence": "alto|medio|bajo",
    "nutrition_per_serving": {
        "calories": número,
        "protein_g": número,
        "carbs_g": número,
        "fat_g": número
    },
    "nutrition_per_100g": {
        "calories": número,
        "protein_g": número,
        "carbs_g": número,
        "fat_g": número
    }
}

Si no puedes identificar el alimento, responde:
{
    "food_name": "No identificado",
    "confidence": "bajo",
    "error": "No se pudo identificar el alimento en la imagen"
}

Analiza la imagen ahora:"""
    
    def _parse_gemini_response(self, response_text: str) -> dict:
        """Parsea la respuesta JSON de Gemini"""
        try:
            # Limpiar la respuesta (remover markdown, etc.)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            # Parsear JSON
            data = json.loads(cleaned_text)
            
            # Validar estructura
            if 'food_name' not in data:
                raise ValueError("Respuesta inválida: falta food_name")
            
            return data
            
        except json.JSONDecodeError as e:
            return {
                'food_name': 'Error de parsing',
                'confidence': 'bajo',
                'error': f'Error parsing JSON: {str(e)}',
                'raw_text': response_text
            }
        except Exception as e:
            return {
                'food_name': 'Error desconocido',
                'confidence': 'bajo',
                'error': str(e)
            }
    
    def _estimate_input_tokens(self, prompt: str, image_size_bytes: int) -> int:
        """Estima tokens de input (prompt + imagen)"""
        # Estimación aproximada
        text_tokens = len(prompt.split()) * 1.3  # ~1.3 tokens por palabra
        image_tokens = image_size_bytes / 1000  # Aproximado para imágenes
        return int(text_tokens + image_tokens)
    
    def _estimate_output_tokens(self, response_text: str) -> int:
        """Estima tokens de output"""
        return int(len(response_text.split()) * 1.3)
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Calcula costo en USD"""
        input_cost = Decimal(input_tokens) * self.input_price_per_token
        output_cost = Decimal(output_tokens) * self.output_price_per_token
        return input_cost + output_cost