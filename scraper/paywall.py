import requests
import time
import random
import logging
from urllib.parse import urljoin, quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import re

logger = logging.getLogger(__name__)

class PaywallDetector:
    """Paywall detection and bypass"""
    
    def __init__(self):
        self.paywall_indicators = {
            'spanish': [
                'suscríbete', 'suscribirse', 'regístrate', 'iniciar sesión',
                'contenido premium', 'artículo completo', 'leer más',
                'hazte suscriptor', 'acceso completo', 'usuario premium',
                'continúa leyendo', 'contenido exclusivo', 'membresía'
            ],
            'english': [
                'subscribe', 'sign up', 'log in', 'premium content',
                'full article', 'read more', 'become a subscriber',
                'exclusive content', 'membership required', 'paywall'
            ]
        }
        
        self.paywall_selectors = [
            '.paywall', '.subscription-wall', '.premium-content',
            '.subscriber-only', '.registration-required', '.login-wall',
            '#paywall', '#subscription', '.article-paywall',
            '[data-paywall]', '.content-gate', '.access-wall'
        ]
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Googlebot/2.1 (+http://www.google.com/bot.html)',
            'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
            'Twitterbot/1.0'
        ]
    
    def detect_paywall(self, driver, url):
        """Paywall detection"""
        detection_results = {
            'has_paywall': False,
            'confidence': 0.0,
            'indicators': [],
            'bypass_recommendations': []
        }
        
        try:
            page_source = driver.page_source.lower()
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            # 1. Text-based detection
            text_indicators = 0
            for lang, indicators in self.paywall_indicators.items():
                for indicator in indicators:
                    if indicator in page_text:
                        text_indicators += 1
                        detection_results['indicators'].append(f"Text: {indicator}")
            
            # 2. DOM-based detection
            dom_indicators = 0
            for selector in self.paywall_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        dom_indicators += 1
                        detection_results['indicators'].append(f"DOM: {selector}")
                except:
                    continue
            
            # 3. Content length analysis
            content_selectors = ['.a_c p', 'article p', '.content p', '.post-content p']
            total_content_length = 0
            
            for selector in content_selectors:
                try:
                    paragraphs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for p in paragraphs:
                        total_content_length += len(p.text.strip())
                    if total_content_length > 500:  # Sufficient content found
                        break
                except:
                    continue
            
            content_indicators = 0
            if total_content_length < 200:
                content_indicators += 2
                detection_results['indicators'].append("Content: Very short article")
            elif total_content_length < 500:
                content_indicators += 1
                detection_results['indicators'].append("Content: Short article")
            
            # 4. URL pattern analysis
            url_indicators = 0
            premium_patterns = ['/premium/', '/subscriber/', '/plus/', '/pro/']
            for pattern in premium_patterns:
                if pattern in url.lower():
                    url_indicators += 1
                    detection_results['indicators'].append(f"URL: {pattern}")
            
            # Calculate confidence score
            total_indicators = text_indicators + dom_indicators + content_indicators + url_indicators
            max_possible = 10  # Reasonable maximum
            detection_results['confidence'] = min(total_indicators / max_possible, 1.0)
            detection_results['has_paywall'] = detection_results['confidence'] > 0.3
            
            # Generate bypass recommendations
            if detection_results['has_paywall']:
                detection_results['bypass_recommendations'] = [
                    'try_archive_services',
                    'rotate_user_agent',
                    'clear_cookies',
                    'try_rss_feed',
                    'extract_meta_content'
                ]
            
            logger.info(f"Paywall detection - Confidence: {detection_results['confidence']:.2f}, "
                       f"Indicators: {len(detection_results['indicators'])}")
            
            return detection_results
            
        except Exception as e:
            logger.error(f"Paywall detection failed: {e}")
            return detection_results
    
    def bypass_paywall(self, driver, url, detection_results):
        """Attempt various paywall bypass methods"""
        bypass_results = {
            'success': False,
            'method_used': None,
            'content': None,
            'attempts': []
        }
        
        if not detection_results['has_paywall']:
            bypass_results['success'] = True
            bypass_results['method_used'] = 'no_paywall_detected'
            return bypass_results
        
        # Method 1: Archive services
        if 'try_archive_services' in detection_results['bypass_recommendations']:
            content = self._try_archive_services(url)
            if content:
                bypass_results['success'] = True
                bypass_results['method_used'] = 'archive_service'
                bypass_results['content'] = content
                return bypass_results
            bypass_results['attempts'].append('archive_services_failed')
        
        # Method 2: User agent rotation
        if 'rotate_user_agent' in detection_results['bypass_recommendations']:
            success = self._rotate_user_agent(driver)
            if success:
                time.sleep(3)
                content = self._extract_content_after_bypass(driver)
                if content:
                    bypass_results['success'] = True
                    bypass_results['method_used'] = 'user_agent_rotation'
                    bypass_results['content'] = content
                    return bypass_results
            bypass_results['attempts'].append('user_agent_rotation_failed')
        
        # Method 3: RSS feed extraction
        if 'try_rss_feed' in detection_results['bypass_recommendations']:
            content = self._try_rss_extraction(url)
            if content:
                bypass_results['success'] = True
                bypass_results['method_used'] = 'rss_feed'
                bypass_results['content'] = content
                return bypass_results
            bypass_results['attempts'].append('rss_extraction_failed')
        
        # Method 4: Meta content extraction
        if 'extract_meta_content' in detection_results['bypass_recommendations']:
            content = self._extract_meta_content(driver)
            if content:
                bypass_results['success'] = True
                bypass_results['method_used'] = 'meta_extraction'
                bypass_results['content'] = content
                return bypass_results
            bypass_results['attempts'].append('meta_extraction_failed')
        
        logger.warning(f"All bypass methods failed for {url}")
        return bypass_results
    
    def _try_archive_services(self, url):
        """Try to get content from archive services"""
        archive_urls = [
            f"https://web.archive.org/web/{url}",
            f"https://archive.today/{url}",
            f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        ]
        
        for archive_url in archive_urls:
            try:
                response = requests.get(archive_url, timeout=15, 
                                      headers={'User-Agent': random.choice(self.user_agents)})
                if response.status_code == 200 and len(response.text) > 1000:
                    logger.info(f"Archive content found: {archive_url}")
                    return response.text[:3000]  # Return first 3000 chars
            except:
                continue
        return None
    
    def _rotate_user_agent(self, driver):
        """Rotate user agent and refresh page"""
        try:
            # This requires restarting the driver with new user agent
            # For now, we'll use CDP commands if available
            new_user_agent = random.choice(self.user_agents)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": new_user_agent})
            driver.refresh()
            time.sleep(3)
            logger.info(f"User agent rotated to: {new_user_agent[:50]}...")
            return True
        except Exception as e:
            logger.warning(f"User agent rotation failed: {e}")
            return False
    
    def _try_rss_extraction(self, url):
        """Try to extract content from RSS feeds"""
        # Common RSS endpoints for El País
        rss_endpoints = [
            'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada',
            'https://elpais.com/rss/elpais/portada.xml',
            'https://elpais.com/rss/opinion.xml'
        ]
        
        for rss_url in rss_endpoints:
            try:
                response = requests.get(rss_url, timeout=10)
                if response.status_code == 200:
                    # Simple RSS parsing - look for content in the feed
                    if url in response.text:
                        # Extract description or content
                        import re
                        patterns = [
                            r'<description><!\[CDATA\[(.*?)\]\]></description>',
                            r'<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>',
                            r'<summary>(.*?)</summary>'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, response.text, re.DOTALL)
                            for match in matches:
                                if len(match.strip()) > 200:
                                    logger.info("RSS content extracted")
                                    return match.strip()[:2000]
            except:
                continue
        return None
    
    def _extract_meta_content(self, driver):
        """Extract content from meta tags and structured data"""
        try:
            meta_content = []
            
            # OpenGraph description
            try:
                og_desc = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                content = og_desc.get_attribute('content')
                if content and len(content) > 50:
                    meta_content.append(content)
            except:
                pass
            
            # Twitter description
            try:
                twitter_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="twitter:description"]')
                content = twitter_desc.get_attribute('content')
                if content and len(content) > 50:
                    meta_content.append(content)
            except:
                pass
            
            # Standard meta description
            try:
                meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                content = meta_desc.get_attribute('content')
                if content and len(content) > 50:
                    meta_content.append(content)
            except:
                pass
            
            # JSON-LD structured data
            try:
                json_scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                for script in json_scripts:
                    try:
                        data = json.loads(script.get_attribute('innerHTML'))
                        if isinstance(data, dict) and 'articleBody' in data:
                            meta_content.append(data['articleBody'][:1000])
                        elif isinstance(data, dict) and 'description' in data:
                            meta_content.append(data['description'])
                    except:
                        continue
            except:
                pass
            
            if meta_content:
                combined_content = " ".join(meta_content)
                logger.info("Meta content extracted successfully")
                return combined_content[:2000]
                
        except Exception as e:
            logger.error(f"Meta content extraction failed: {e}")
        
        return None
    
    def _extract_content_after_bypass(self, driver):
        """Extract content after attempting bypass"""
        content_selectors = [
            '.a_c p', '.articulo-cuerpo p', '.article-body p',
            '.story-body p', 'article p', '.content p',
            '.post-content p', '.entry-content p'
        ]
        
        for selector in content_selectors:
            try:
                paragraphs = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(paragraphs) >= 2:
                    content_parts = []
                    for p in paragraphs[:6]:
                        text = p.text.strip()
                        if len(text) > 30:
                            content_parts.append(text)
                    
                    if content_parts:
                        return " ".join(content_parts)
            except:
                continue
        
        return None
