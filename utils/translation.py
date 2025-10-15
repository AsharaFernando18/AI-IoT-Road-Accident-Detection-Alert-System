"""
Multilingual Translation Service using Hugging Face Transformers
Supports English, Spanish, Arabic, Hindi, and Mandarin Chinese
"""

from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
import torch
from typing import Dict, List, Optional
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Multilingual translation service using mBART-50 model
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize translation service
        
        Args:
            model_name: Hugging Face model name (default: mBART-50)
        """
        self.model_name = model_name or Config.HF_MODEL_NAME
        self.cache_dir = Config.HF_CACHE_DIR
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading translation model: {self.model_name}")
        logger.info(f"Using device: {self.device}")
        
        try:
            # Load model and tokenizer
            self.tokenizer = MBart50TokenizerFast.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir)
            )
            self.model = MBartForConditionalGeneration.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir)
            ).to(self.device)
            
            logger.info("✓ Translation model loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load translation model: {e}")
            raise
        
        # Language code mapping
        self.lang_codes = Config.LANGUAGE_CODES
        self.supported_languages = list(self.lang_codes.keys())
    
    def translate(self, text: str, source_lang: str = "en", 
                  target_lang: str = "es") -> Optional[str]:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (en, es, ar, hi, zh)
            target_lang: Target language code
            
        Returns:
            Translated text or None if failed
        """
        if source_lang not in self.lang_codes:
            logger.error(f"Unsupported source language: {source_lang}")
            return None
        
        if target_lang not in self.lang_codes:
            logger.error(f"Unsupported target language: {target_lang}")
            return None
        
        if source_lang == target_lang:
            return text
        
        try:
            # Set source language
            self.tokenizer.src_lang = self.lang_codes[source_lang]
            
            # Tokenize
            encoded = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # Generate translation
            forced_bos_token_id = self.tokenizer.lang_code_to_id[
                self.lang_codes[target_lang]
            ]
            
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512
            )
            
            # Decode
            translated = self.tokenizer.batch_decode(
                generated_tokens, 
                skip_special_tokens=True
            )[0]
            
            logger.info(f"✓ Translated from {source_lang} to {target_lang}")
            logger.debug(f"Original: {text}")
            logger.debug(f"Translated: {translated}")
            
            return translated
        
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return None
    
    def translate_to_all(self, text: str, source_lang: str = "en") -> Dict[str, str]:
        """
        Translate text to all supported languages
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Dictionary mapping language codes to translated text
        """
        translations = {source_lang: text}
        
        for lang in self.supported_languages:
            if lang != source_lang:
                translated = self.translate(text, source_lang, lang)
                if translated:
                    translations[lang] = translated
        
        return translations
    
    def format_accident_message(self, accident_data: Dict, language: str = "en") -> str:
        """
        Format accident alert message with proper template
        
        Args:
            accident_data: Dictionary with accident details
            language: Target language
            
        Returns:
            Formatted message
        """
        # Base template in English
        template = (
            "⚠️ ACCIDENT DETECTED!\n"
            "Location: {location}\n"
            "Time: {time}\n"
            "Severity: {severity}\n"
            "Confidence: {confidence}\n"
            "Please respond immediately."
        )
        
        message = template.format(
            location=accident_data.get("location", "Unknown"),
            time=accident_data.get("time", "Unknown"),
            severity=accident_data.get("severity", "Unknown"),
            confidence=f"{accident_data.get('confidence', 0):.1%}"
        )
        
        # Translate if not English
        if language != "en":
            translated = self.translate(message, "en", language)
            return translated if translated else message
        
        return message
    
    def batch_translate(self, texts: List[str], source_lang: str = "en",
                       target_lang: str = "es") -> List[str]:
        """
        Translate multiple texts (batch processing)
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        translations = []
        
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            translations.append(translated if translated else text)
        
        return translations


class SimpleTranslator:
    """
    Fallback simple translation service using predefined templates
    Used when Hugging Face model is not available
    """
    
    def __init__(self):
        """Initialize simple translator with templates"""
        self.templates = {
            "en": {
                "accident_alert": "⚠️ ACCIDENT DETECTED!\nLocation: {location}\nTime: {time}\nSeverity: {severity}\nPlease respond immediately.",
                "severity_low": "Low",
                "severity_medium": "Medium",
                "severity_high": "High",
                "severity_critical": "Critical"
            },
            "es": {
                "accident_alert": "⚠️ ¡ACCIDENTE DETECTADO!\nUbicación: {location}\nHora: {time}\nGravedad: {severity}\nPor favor responda inmediatamente.",
                "severity_low": "Bajo",
                "severity_medium": "Medio",
                "severity_high": "Alto",
                "severity_critical": "Crítico"
            },
            "ar": {
                "accident_alert": "⚠️ تم اكتشاف حادث!\nالموقع: {location}\nالوقت: {time}\nالخطورة: {severity}\nيرجى الرد فوراً.",
                "severity_low": "منخفض",
                "severity_medium": "متوسط",
                "severity_high": "عالي",
                "severity_critical": "حرج"
            },
            "hi": {
                "accident_alert": "⚠️ दुर्घटना का पता चला!\nस्थान: {location}\nसमय: {time}\nगंभीरता: {severity}\nकृपया तुरंत जवाब दें।",
                "severity_low": "कम",
                "severity_medium": "मध्यम",
                "severity_high": "उच्च",
                "severity_critical": "गंभीर"
            },
            "zh": {
                "accident_alert": "⚠️ 检测到事故！\n位置：{location}\n时间：{time}\n严重程度：{severity}\n请立即响应。",
                "severity_low": "低",
                "severity_medium": "中",
                "severity_high": "高",
                "severity_critical": "危急"
            }
        }
    
    def format_message(self, accident_data: Dict, language: str = "en") -> str:
        """Format accident message in specified language"""
        if language not in self.templates:
            language = "en"
        
        template = self.templates[language]["accident_alert"]
        severity_key = f"severity_{accident_data.get('severity', 'medium')}"
        severity = self.templates[language].get(severity_key, accident_data.get('severity', 'Unknown'))
        
        return template.format(
            location=accident_data.get("location", "Unknown"),
            time=accident_data.get("time", "Unknown"),
            severity=severity
        )


if __name__ == "__main__":
    # Test translation service
    try:
        translator = TranslationService()
        
        # Test single translation
        text = "A serious accident has been detected on Main Street. Emergency services required immediately."
        
        print("Original (English):", text)
        print("\nTranslations:")
        
        for lang in ["es", "ar", "hi", "zh"]:
            translated = translator.translate(text, "en", lang)
            lang_name = Config.LANGUAGE_NAMES[lang]
            print(f"\n{lang_name} ({lang}):")
            print(translated)
        
        # Test accident message formatting
        print("\n" + "="*50)
        print("Testing accident message formatting:")
        
        accident_data = {
            "location": "Main Street, New York",
            "time": "2025-10-15 14:30:00",
            "severity": "high",
            "confidence": 0.92
        }
        
        for lang in Config.SUPPORTED_LANGUAGES:
            message = translator.format_accident_message(accident_data, lang)
            lang_name = Config.LANGUAGE_NAMES[lang]
            print(f"\n{lang_name} ({lang}):")
            print(message)
    
    except Exception as e:
        logger.error(f"Error testing translation service: {e}")
        
        # Test fallback translator
        print("\nTesting fallback simple translator:")
        simple = SimpleTranslator()
        
        for lang in ["en", "es", "ar", "hi", "zh"]:
            message = simple.format_message(accident_data, lang)
            print(f"\n{lang}:")
            print(message)
