from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import os
import requests
from urllib.parse import urljoin
import logging
import platform
import subprocess
import shutil
import json
from datetime import datetime
from .paywall import PaywallDetector
from .extractor import EnhancedContentExtractor
from .diagnostics import FailureDiagnostics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedScraper:
    """Enhanced scraper with paywall bypass and advanced content extraction"""
    
    def __init__(self):
        self.paywall_detector = PaywallDetector()
        self.content_extractor = EnhancedContentExtractor()
        self.diagnostics = FailureDiagnostics()
        self.session_stats = {
            'total_articles': 0,
            'successful_extractions': 0,
            'paywall_bypasses': 0,
            'extraction_methods': {},
            'failure_reasons': {}
        }

def get_chrome_version():
    """Get Chrome version on Windows"""
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            return version
    except:
        try:
            result = subprocess.run(['chrome', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split()[-1]
        except:
            pass
    return None

def setup_enhanced_driver():
    """Enhanced WebDriver setup with anti-detection features"""
    chrome_options = Options()
    
    # Anti-detection options
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=es")
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # Faster loading
    chrome_options.add_argument('--disable-javascript')  # For some paywalls
    
    # Additional stealth options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('prefs', {
        'intl.accept_languages': 'es,es_ES,en',
        'profile.default_content_setting_values.notifications': 2,
        'profile.default_content_settings.popups': 0,
        'profile.managed_default_content_settings.images': 2
    })
    
    try:
        logger.info("Setting up enhanced WebDriver...")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        # Execute stealth script
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']});
        window.chrome = { runtime: {} };
        """
        driver.execute_script(stealth_script)
        
        logger.info("Enhanced WebDriver created successfully")
        return driver
    except Exception as e:
        logger.error(f"Enhanced driver setup failed: {e}")
        # Fallback to original setup
        return setup_driver_original()

def setup_driver_original():
    """Original driver setup as fallback"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=es")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        raise Exception(f"All WebDriver setup methods failed: {e}")

def setup_driver():
    """Main setup function"""
    return setup_enhanced_driver()

def handle_cookies(driver):
    """Enhanced cookie handling"""
    cookie_selectors = [
        "#didomi-notice-agree-button",
        ".cookie-accept",
        ".accept-cookies",
        "[data-accept-cookies]",
        ".gdpr-accept"
    ]
    
    for selector in cookie_selectors:
        try:
            cookie_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            cookie_button.click()
            logger.info(f"Accepted cookies using selector: {selector}")
            time.sleep(1)
            return
        except:
            continue
    
    logger.info("No cookie popup found or already handled")

def fetch_articles_enhanced():
    """Enhanced article fetching with comprehensive error handling and diagnostics"""
    scraper = EnhancedScraper()
    driver = setup_driver()
    
    try:
        driver.get("https://elpais.com/opinion/")
        time.sleep(3)
        
        handle_cookies(driver)
        
        # Enhanced article discovery
        article_selectors = [
            "article.c_t", "article", ".c_t", ".articulo",
            "[data-dtm-region='articulo']", ".story_container",
            ".article-item", ".news-item", ".content-item",
            "a[href*='/opinion/']"
        ]
        
        articles_found = []
        for selector in article_selectors:
            try:
                article_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(article_elements) >= 5:
                    articles_found = article_elements[:5]
                    logger.info(f"Found {len(articles_found)} articles using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not articles_found:
            # Fallback methods
            try:
                link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/opinion/']")[:5]
                articles_found = link_elements
                logger.info(f"Fallback: Found {len(link_elements)} article links")
            except Exception as e:
                logger.error(f"All article discovery methods failed: {e}")
                scraper.diagnostics.log_failure("article_discovery", str(e), driver.current_url)
                return []
        
        # Extract article information
        articles = []
        for i, article in enumerate(articles_found):
            try:
                title, link = extract_title_and_link_enhanced(article, driver)
                if title and link:
                    articles.append((title, link, i+1))
                    logger.info(f"Successfully extracted article {i+1}: {title[:50]}...")
                else:
                    logger.warning(f"Could not extract title/link for article {i+1}")
                    scraper.diagnostics.log_failure("title_link_extraction", 
                                                   "No title or link found", 
                                                   driver.current_url)
            except Exception as e:
                logger.error(f"Error processing article {i+1}: {e}")
                scraper.diagnostics.log_failure("article_processing", str(e), driver.current_url)
                continue
        
        # Fetch full articles with enhanced extraction
        result = []
        for title, link, index in articles:
            article_data = fetch_full_article_enhanced(driver, title, link, index, scraper)
            if article_data:
                result.append(article_data)
        
        # Log session statistics
        scraper.diagnostics.log_session_stats(scraper.session_stats)
        return result
        
    finally:
        driver.quit()

def extract_title_and_link_enhanced(article_element, driver):
    """Enhanced title and link extraction with multiple fallback strategies"""
    # Expanded selectors for better coverage
    title_selectors = [
        "h2 a", "h3 a", "h1 a", "h4 a",
        ".c_t_t a", ".articulo-titulo a", ".headline a",
        ".title a", ".article-title a", ".post-title a",
        "a[href*='/opinion/']", "a[href*='/articulo/']",
        "h2", "h3", "h1", "h4",
        ".c_t_t", ".headline", ".title", ".article-title",
        "[data-title]", "[data-headline]"
    ]
    
    for selector in title_selectors:
        try:
            element = article_element.find_element(By.CSS_SELECTOR, selector)
            
            # Get title text
            title = element.text.strip()
            if not title:
                title = element.get_attribute('title') or element.get_attribute('data-title') or ""
            
            # Get link
            if element.tag_name == 'a':
                link = element.get_attribute('href')
            else:
                # Look for link in various places
                link_found = False
                for link_selector in ['a', 'a[href*="/opinion/"]']:
                    try:
                        link_element = element.find_element(By.CSS_SELECTOR, link_selector)
                        link = link_element.get_attribute('href')
                        link_found = True
                        break
                    except:
                        continue
                
                if not link_found:
                    # Try parent elements
                    try:
                        parent = element.find_element(By.XPATH, '..')
                        link_element = parent.find_element(By.TAG_NAME, 'a')
                        link = link_element.get_attribute('href')
                    except:
                        continue
            
            if title and link:
                if not link.startswith('http'):
                    link = urljoin("https://elpais.com", link)
                return title, link
                
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue
    
    return None, None

def fetch_full_article_enhanced(driver, title, link, index, scraper):
    """Enhanced article fetching with paywall detection and bypass"""
    scraper.session_stats['total_articles'] += 1
    
    try:
        logger.info(f"Fetching article {index}: {link}")
        driver.get(link)
        time.sleep(4)
        
        # Step 1: Detect paywall
        paywall_results = scraper.paywall_detector.detect_paywall(driver, link)
        scraper.diagnostics.log_paywall_detection(link, paywall_results)
        
        # Step 2: Attempt bypass if needed
        bypass_results = {'success': True, 'method_used': 'direct_access', 'content': None}
        if paywall_results['has_paywall']:
            logger.info(f"Paywall detected (confidence: {paywall_results['confidence']:.2f}), attempting bypass...")
            bypass_results = scraper.paywall_detector.bypass_paywall(driver, link, paywall_results)
            if bypass_results['success']:
                scraper.session_stats['paywall_bypasses'] += 1
                logger.info(f"Paywall bypassed using: {bypass_results['method_used']}")
        
        # Step 3: Extract content using enhanced methods
        if bypass_results['content']:
            content = bypass_results['content']
            extraction_method = f"bypass_{bypass_results['method_used']}"
        else:
            content = scraper.content_extractor.extract_content_comprehensive(driver, link)
            extraction_method = scraper.content_extractor.last_successful_method
        
        # Step 4: Extract image
        image_path = download_article_image_enhanced(driver, index)
        
        # Step 5: Validate and score content
        content_score = scraper.content_extractor.score_content_quality(content)
        
        if content and content != "Content could not be extracted":
            scraper.session_stats['successful_extractions'] += 1
            method_key = extraction_method or 'unknown'
            scraper.session_stats['extraction_methods'][method_key] = \
                scraper.session_stats['extraction_methods'].get(method_key, 0) + 1
        else:
            # Log detailed failure information
            scraper.diagnostics.log_detailed_failure(driver, link, title, index)
            reason = "content_extraction_failed"
            scraper.session_stats['failure_reasons'][reason] = \
                scraper.session_stats['failure_reasons'].get(reason, 0) + 1
        
        article_data = {
            "title": title,
            "content": content,
            "image": image_path,
            "url": link,
            "paywall_detected": paywall_results['has_paywall'],
            "paywall_confidence": paywall_results['confidence'],
            "bypass_method": bypass_results.get('method_used'),
            "extraction_method": extraction_method,
            "content_score": content_score,
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        return article_data
        
    except Exception as e:
        logger.error(f"Failed to fetch article {index} from {link}: {e}")
        scraper.diagnostics.log_detailed_failure(driver, link, title, index, str(e))
        return {
            "title": title,
            "content": "Content could not be extracted",
            "image": None,
            "url": link,
            "error": str(e),
            "extraction_timestamp": datetime.now().isoformat()
        }

def download_article_image_enhanced(driver, article_index):
    """Enhanced image download with better selection and fallback"""
    # Expanded image selectors
    image_selectors = [
        "figure.a_m img", ".a_m img", "figure img",
        ".imagen img", ".article-image img", ".hero-image img",
        ".featured-image img", ".post-image img",
        ".foto img", ".photo img", ".picture img",
        "img[src*='jpg']", "img[src*='jpeg']", 
        "img[src*='png']", "img[src*='webp']",
        "img[alt*='articulo']", "img[alt*='noticia']"
    ]
    
    for selector in image_selectors:
        try:
            images = driver.find_elements(By.CSS_SELECTOR, selector)
            for img in images:
                src = (img.get_attribute("src") or 
                      img.get_attribute("data-src") or 
                      img.get_attribute("data-lazy-src"))
                
                if src and is_valid_image_url_enhanced(src):
                    downloaded_path = download_image_enhanced(src, article_index)
                    if downloaded_path:
                        return downloaded_path
        except Exception as e:
            logger.debug(f"Image selector {selector} failed: {e}")
            continue
    
    logger.warning(f"No suitable image found for article {article_index}")
    return None

def is_valid_image_url_enhanced(url):
    """Enhanced image URL validation"""
    if not url or len(url) < 10:
        return False
    
    url_lower = url.lower()
    
    # Skip unwanted image types
    skip_keywords = [
        'logo', 'icon', 'avatar', 'banner', 'ads', 'pixel', 
        'tracking', 'social', 'share', 'button', 'arrow',
        'placeholder', 'loading', 'spinner'
    ]
    
    if any(keyword in url_lower for keyword in skip_keywords):
        return False
    
    # Valid image extensions
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    if not any(ext in url_lower for ext in valid_extensions):
        return False
    
    # Check minimum URL structure
    if 'elpais.com' in url_lower or 'static' in url_lower or 'media' in url_lower:
        return True
    
    return True

def download_image_enhanced(image_url, article_index):
    """Enhanced image download with better error handling"""
    try:
        if not image_url.startswith('http'):
            image_url = urljoin("https://elpais.com", image_url)
        
        # Enhanced headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://elpais.com/',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(image_url, headers=headers, timeout=20, stream=True)
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"Invalid content type for image: {content_type}")
            return None
        
        # Determine extension from content type
        extension_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp',
            'image/gif': '.gif'
        }
        extension = extension_map.get(content_type, '.jpg')
        
        # If extension not found, try URL
        if extension == '.jpg':
            for ext in ['.png', '.webp', '.gif']:
                if ext in image_url.lower():
                    extension = ext
                    break
        
        filename = f"article_{article_index}_image{extension}"
        os.makedirs("images", exist_ok=True)
        filepath = os.path.join("images", filename)
        
        # Download with streaming
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Validate file size
        file_size = os.path.getsize(filepath)
        if file_size < 1024:  # Less than 1KB
            os.remove(filepath)
            logger.warning(f"Downloaded image too small: {file_size} bytes")
            return None
        
        logger.info(f"Downloaded image: {filename} ({file_size} bytes)")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to download image {image_url}: {e}")
        return None

# Export the enhanced fetch function
fetch_articles = fetch_articles_enhanced
