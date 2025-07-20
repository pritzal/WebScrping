import logging
import json
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

class EnhancedContentExtractor:
    """Advanced content extraction with multiple strategies"""
    
    def __init__(self):
        self.last_successful_method = None
        self.content_selectors = {
            'primary': [
                '.a_c.paywall p', '.a_c p', '.articulo-cuerpo p',
                '.article-body p', '.story-body p', '.post-content p',
                'div[data-dtm-region="articulo"] p', '.paywall p',
                '.content p', '.entry-content p'
            ],
            'secondary': [
                'article p', '.main-content p', '.text p',
                '.article-text p', '.story-text p', '.news-content p',
                '[data-content] p', '.article-container p'
            ],
            'fallback': [
                'p', '.paragraph', '.texto', '.content-text',
                '[data-paragraph]', '.article-paragraph'
            ]
        }
        
        self.structured_data_selectors = [
            'script[type="application/ld+json"]',
            'script[type="application/json+ld"]',
            '[data-json-ld]'
        ]
        
        self.meta_selectors = {
            'og_description': 'meta[property="og:description"]',
            'twitter_description': 'meta[name="twitter:description"]',
            'meta_description': 'meta[name="description"]',
            'article_summary': 'meta[name="article:summary"]'
        }
    
    def extract_content_comprehensive(self, driver, url):
        """Comprehensive content extraction using multiple methods"""
        
        # Method 1: Primary content selectors
        content = self._extract_with_selectors(driver, self.content_selectors['primary'])
        if content:
            self.last_successful_method = 'primary_selectors'
            return content
        
        # Method 2: Secondary content selectors
        content = self._extract_with_selectors(driver, self.content_selectors['secondary'])
        if content:
            self.last_successful_method = 'secondary_selectors'
            return content
        
        # Method 3: Structured data extraction (JSON-LD)
        content = self._extract_structured_data(driver)
        if content:
            self.last_successful_method = 'structured_data'
            return content
        
        # Method 4: Meta tag extraction
        content = self._extract_meta_content(driver)
        if content:
            self.last_successful_method = 'meta_tags'
            return content
        
        # Method 5: Full-text search and extraction
        content = self._extract_full_text_analysis(driver)
        if content:
            self.last_successful_method = 'full_text_analysis'
            return content
        
        # Method 6: Fallback selectors
        content = self._extract_with_selectors(driver, self.content_selectors['fallback'])
        if content:
            self.last_successful_method = 'fallback_selectors'
            return content
        
        logger.warning(f"All extraction methods failed for {url}")
        self.last_successful_method = None
        return "Content could not be extracted"
    
    def _extract_with_selectors(self, driver, selectors):
        """Extract content using CSS selectors"""
        for selector in selectors:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                paragraphs = driver.find_elements(By.CSS_SELECTOR, selector)
                meaningful_paragraphs = []
                
                for p in paragraphs:
                    text = p.text.strip()
                    if self._is_meaningful_paragraph(text):
                        meaningful_paragraphs.append(text)
                
                if len(meaningful_paragraphs) >= 2:
                    content = " ".join(meaningful_paragraphs[:8])  # Take first 8 paragraphs
                    if len(content) > 200:  # Minimum content length
                        logger.info(f"Content extracted using selector: {selector} "
                                  f"({len(meaningful_paragraphs)} paragraphs)")
                        return content
                        
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return None
    
    def _extract_structured_data(self, driver):
        """Extract content from JSON-LD structured data"""
        for selector in self.structured_data_selectors:
            try:
                scripts = driver.find_elements(By.CSS_SELECTOR, selector)
                for script in scripts:
                    try:
                        json_text = script.get_attribute('innerHTML')
                        if not json_text.strip():
                            continue
                            
                        data = json.loads(json_text)
                        
                        # Handle arrays of structured data
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        
                        # Look for article content
                        content_fields = ['articleBody', 'text', 'description', 'abstract']
                        for field in content_fields:
                            if field in data and data[field]:
                                content = str(data[field]).strip()
                                if len(content) > 200:
                                    logger.info(f"Structured data content extracted from field: {field}")
                                    return content[:3000]  # Limit to 3000 chars
                        
                        # Check nested objects
                        if '@graph' in data:
                            for item in data['@graph']:
                                if isinstance(item, dict):
                                    for field in content_fields:
                                        if field in item and item[field]:
                                            content = str(item[field]).strip()
                                            if len(content) > 200:
                                                logger.info(f"Structured data content extracted from @graph.{field}")
                                                return content[:3000]
                        
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON decode error in structured data: {e}")
                        continue
                    except Exception as e:
                        logger.debug(f"Error processing structured data: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Structured data selector {selector} failed: {e}")
                continue
        
        return None
    
    def _extract_meta_content(self, driver):
        """Extract content from meta tags"""
        meta_content = []
        
        for meta_name, selector in self.meta_selectors.items():
            try:
                meta_element = driver.find_element(By.CSS_SELECTOR, selector)
                content = meta_element.get_attribute('content')
                if content and len(content) > 50:
                    meta_content.append(content)
                    logger.debug(f"Meta content found: {meta_name}")
            except Exception as e:
                logger.debug(f"Meta selector {selector} failed: {e}")
                continue
        
        if meta_content:
            combined_content = " ".join(meta_content)
            logger.info("Meta tag content extracted successfully")
            return combined_content[:2000]
        
        return None
    
    def _extract_full_text_analysis(self, driver):
        """Extract content using full-page text analysis"""
        try:
            # Get all text from the page
            body_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', body_text)
            meaningful_sentences = []
            
            # Filter out navigation, ads, and other noise
            noise_patterns = [
                r'compartir', r'seguir', r'suscr', r'más info', r'leer más',
                r'newsletter', r'notificaciones', r'publicidad', r'cookies',
                r'twitter', r'facebook', r'instagram', r'whatsapp',
                r'menú', r'inicio', r'portada', r'sección', r'edición',
                r'copyright', r'derechos reservados', r'política de privacidad'
            ]
            
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 40 and len(sentence) < 500 and  # Reasonable length
                    not any(re.search(pattern, sentence, re.IGNORECASE) for pattern in noise_patterns)):
                    meaningful_sentences.append(sentence)
            
            if len(meaningful_sentences) >= 3:
                # Take the sentences that appear in the middle part of the page
                # (likely to be article content rather than navigation)
                middle_start = len(meaningful_sentences) // 4
                middle_end = 3 * len(meaningful_sentences) // 4
                content_sentences = meaningful_sentences[middle_start:middle_end][:6]
                
                content = ". ".join(content_sentences) + "."
                if len(content) > 300:
                    logger.info("Full-text analysis content extracted")
                    return content
            
        except Exception as e:
            logger.debug(f"Full-text analysis failed: {e}")
        
        return None
    
    def _is_meaningful_paragraph(self, text):
        """Check if a paragraph contains meaningful content"""
        if not text or len(text) < 30:
            return False
        
        # Skip common navigation and promotional text
        skip_patterns = [
            'compartir', 'seguir', 'suscr', 'más info', 'leer más',
            'newsletter', 'notificaciones', 'publicidad', 'cookies',
            'iniciar sesión', 'registrarse', 'premium', 'hazte suscriptor',
            'twitter', 'facebook', 'instagram', 'whatsapp', 'telegram',
            'menú principal', 'volver arriba', 'ir al contenido'
        ]
        
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in skip_patterns):
            return False
        
        # Check for reasonable content characteristics
        word_count = len(text.split())
        if word_count < 5 or word_count > 200:  # Too short or too long
            return False
        
        # Must contain some letters (not just numbers/symbols)
        if not re.search(r'[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]{3,}', text):
            return False
        
        return True
    
    def score_content_quality(self, content):
        """Score the quality of extracted content"""
        if not content or content == "Content could not be extracted":
            return 0.0
        
        score = 0.0
        
        # Length score (0.0-0.3)
        length = len(content)
        if length > 2000:
            score += 0.3
        elif length > 1000:
            score += 0.2
        elif length > 500:
            score += 0.1
        
        # Word count score (0.0-0.2)
        word_count = len(content.split())
        if word_count > 300:
            score += 0.2
        elif word_count > 150:
            score += 0.15
        elif word_count > 75:
            score += 0.1
        
        # Sentence structure score (0.0-0.2)
        sentences = re.split(r'[.!?]+', content)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        if len(meaningful_sentences) > 5:
            score += 0.2
        elif len(meaningful_sentences) > 2:
            score += 0.1
        
        # Language quality score (0.0-0.2)
        spanish_indicators = ['que', 'del', 'con', 'por', 'para', 'esta', 'una', 'como']
        spanish_count = sum(1 for indicator in spanish_indicators if indicator in content.lower())
        if spanish_count > 5:
            score += 0.2
        elif spanish_count > 2:
            score += 0.1
        
        # Diversity score (0.0-0.1)
        unique_words = len(set(content.lower().split()))
        total_words = len(content.split())
        if total_words > 0:
            diversity = unique_words / total_words
            if diversity > 0.7:
                score += 0.1
            elif diversity > 0.5:
                score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
