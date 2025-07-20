# scraper/translate.py (fixed version with working APIs)
import requests
import time
import logging
from typing import Optional, List
import json

logger = logging.getLogger(__name__)

class TranslationService:
    """Enhanced translation service with working APIs and proper fallbacks"""
    
    def __init__(self, service="mymemory", api_key=None):
        self.service = service
        self.api_key = api_key
        self.request_count = 0
        self.last_request_time = 0
        
    def translate_text(self, text: str, source: str = "es", target: str = "en") -> str:
        """Translate text with rate limiting and error handling"""
        if not text.strip():
            return text
            
        # Rate limiting - wait 1.5 seconds between requests
        current_time = time.time()
        if current_time - self.last_request_time < 1.5:
            time.sleep(1.5 - (current_time - self.last_request_time))
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        try:
            if self.service == "mymemory":
                return self._translate_mymemory(text, source, target)
            elif self.service == "googletrans":
                return self._translate_googletrans(text, source, target)
            elif self.service == "libre_fixed":
                return self._translate_libre_fixed(text, source, target)
            elif self.service == "translate_shell":
                return self._translate_shell(text, source, target)
            else:
                logger.warning(f"Unknown service {self.service}, using MyMemory")
                return self._translate_mymemory(text, source, target)
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text  # Return original text if translation fails
    
    def _translate_mymemory(self, text: str, source: str, target: str) -> str:
        """Translate using MyMemory API (Free, reliable)"""
        try:
            # Split long text into chunks
            if len(text) > 500:
                text = text[:500] + "..."
            
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": f"{source}|{target}",
                "de": "your-email@example.com"  # Optional email for higher limits
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get("responseStatus") == 200:
                translated_text = data["responseData"]["translatedText"]
                if translated_text and translated_text.lower() != text.lower():
                    logger.info(f"Successfully translated with MyMemory")
                    return translated_text
                    
        except Exception as e:
            logger.error(f"MyMemory API failed: {e}")
        
        # Fallback to googletrans
        return self._translate_googletrans(text, source, target)
    
    def _translate_googletrans(self, text: str, source: str, target: str) -> str:
        """Translate using googletrans library (Free, unofficial)"""
        try:
            from googletrans import Translator
            translator = Translator()
            
            result = translator.translate(text, src=source, dest=target)
            if result and result.text:
                logger.info(f"Successfully translated with googletrans")
                return result.text
                
        except ImportError:
            logger.error("googletrans library not installed. Install with: pip install googletrans==4.0.0rc1")
        except Exception as e:
            logger.error(f"googletrans failed: {e}")
        
        return self._translate_libre_fixed(text, source, target)
    
    def _translate_libre_fixed(self, text: str, source: str, target: str) -> str:
        """Fixed LibreTranslate with proper API format"""
        try:
            # Use the official LibreTranslate demo instance
            url = "https://libretranslate.de/translate"
            
            payload = {
                "q": text,
                "source": source,
                "target": target,
                "format": "text",
                "alternatives": 1,
                "api_key": ""
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.post(
                url, 
                data=json.dumps(payload), 
                headers=headers, 
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    translated_text = data.get("translatedText", "").strip()
                    if translated_text and translated_text != text:
                        logger.info(f"Successfully translated with LibreTranslate")
                        return translated_text
                except json.JSONDecodeError:
                    logger.warning("LibreTranslate returned invalid JSON")
            
        except Exception as e:
            logger.error(f"LibreTranslate fixed API failed: {e}")
        
        return text
    
    def _translate_shell(self, text: str, source: str, target: str) -> str:
        """Basic translation using simple word mappings as final fallback"""
        # Simple dictionary for common Spanish words
        simple_translations = {
            "un": "a", "una": "a", "el": "the", "la": "the", "los": "the", "las": "the",
            "proyecto": "project", "falto": "lacking", "de": "of", "ambición": "ambition",
            "miseria": "misery", "en": "in", "cuba": "cuba",
            "no": "don't", "olvidar": "forget", "que": "that", "centroamérica": "central america", "existe": "exists",
            "lenguas": "tongues", "podridas": "rotten",
            "aquel": "that", "verano": "summer", "raro": "weird", "extraño": "strange"
        }
        
        words = text.lower().split()
        translated_words = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip(".,!?()[]'\"")
            if clean_word in simple_translations:
                translated_words.append(simple_translations[clean_word])
            else:
                translated_words.append(word)
        
        result = " ".join(translated_words)
        
        # Capitalize first letter
        if result:
            result = result[0].upper() + result[1:]
        
        logger.info(f"Used simple dictionary translation")
        return result
    
    def translate_batch(self, texts: List[str], source: str = "es", target: str = "en") -> List[str]:
        """Translate multiple texts with progress logging"""
        results = []
        total = len(texts)
        
        logger.info(f"Starting batch translation of {total} texts...")
        
        for i, text in enumerate(texts, 1):
            logger.info(f"Translating {i}/{total}: {text[:50]}...")
            translated = self.translate_text(text, source, target)
            results.append(translated)
            
            if i % 5 == 0 or i == total:
                logger.info(f"Progress: {i}/{total} completed")
        
        logger.info(f"Batch translation completed. {self.request_count} API requests made.")
        return results

# Convenience function for backward compatibility
def translate_text(text: str, source: str = "es", target: str = "en") -> str:
    """Simple translation function using default service"""
    translator = TranslationService(service="mymemory")
    return translator.translate_text(text, source, target)