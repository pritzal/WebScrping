# browserstack_scraper.py (FIXED VERSION - Better Error Handling)
import os
import time
import json
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs_config import BROWSERSTACK_URL, BROWSER_CONFIGS
from scraper.translate import TranslationService
from scraper.analyse import analyze_headers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserStackScraper:
    """BrowserStack scraper with comprehensive error handling"""
    
    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()
    
    def test_browserstack_connection(self):
        """Test BrowserStack connection before running full tests"""
        logger.info("Testing BrowserStack connection...")
        
        try:
            # Test with simplest Chrome configuration
            test_config = {
                'name': 'Connection Test',
                'browserName': 'Chrome',
                'browserVersion': 'latest',
                'os': 'Windows',
                'osVersion': '10'
            }
            
            driver = self.create_browserstack_driver(test_config)
            if driver:
                logger.info("✅ BrowserStack connection successful")
                driver.quit()
                return True
            else:
                logger.error("❌ BrowserStack connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ BrowserStack connection test failed: {e}")
            return False
    
    def create_browserstack_driver(self, config):
        """Create BrowserStack WebDriver with enhanced error handling"""
        try:
            browser_name = config.get('browserName', 'Chrome').lower()
            
            # Create appropriate options object
            if browser_name == 'chrome':
                options = ChromeOptions()
            elif browser_name == 'firefox':
                options = FirefoxOptions()
            elif browser_name == 'safari':
                options = SafariOptions()
            else:
                options = ChromeOptions()
            
            # Build BrowserStack options
            bstack_options = {}
            
            # Add desktop browser options
            if config.get('os'):
                bstack_options['os'] = config['os']
                bstack_options['osVersion'] = config['osVersion']
                bstack_options['browserVersion'] = config.get('browserVersion', 'latest')
                if config.get('resolution'):
                    bstack_options['resolution'] = config['resolution']
            
            # Add mobile device options
            if config.get('deviceName'):
                bstack_options['deviceName'] = config['deviceName']
                bstack_options['osVersion'] = config['osVersion']
                bstack_options['realMobile'] = config.get('realMobile', 'true')
            
            # Add project metadata
            bstack_options['projectName'] = config.get('project', 'El País Scraper')
            bstack_options['buildName'] = config.get('build', 'Cross Browser Test')
            bstack_options['sessionName'] = config.get('name', 'Test Session')
            
            # Essential debugging options
            bstack_options['debug'] = 'true'
            bstack_options['networkLogs'] = 'true'
            
            # Set capabilities
            options.set_capability('bstack:options', bstack_options)
            
            # Enhanced logging for debugging
            logger.info(f"Creating driver for {config.get('name')} with URL: {BROWSERSTACK_URL[:50]}...")
            logger.debug(f"BrowserStack options: {bstack_options}")
            
            driver = webdriver.Remote(
                command_executor=BROWSERSTACK_URL,
                options=options
            )
            
            if driver:
                driver.implicitly_wait(10)
                logger.info(f"✅ Successfully created driver for {config.get('name')}")
                return driver
            else:
                logger.error(f"❌ Driver creation returned None for {config.get('name')}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create BrowserStack driver for {config.get('name', 'Unknown')}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Additional debugging information
            if "Authentication" in str(e) or "Unauthorized" in str(e):
                logger.error("🔑 Authentication failed - check your BrowserStack credentials")
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                logger.error("⚠️ Account quota/limit exceeded - check your BrowserStack plan")
            elif "timeout" in str(e).lower():
                logger.error("⏰ Connection timeout - check your internet connection")
            
            return None
    
    def scrape_articles_browserstack(self, driver, browser_name):
        """Scraping with enhanced error handling"""
        if not driver:
            logger.error(f"Cannot scrape - driver is None for {browser_name}")
            return []
        
        try:
            logger.info(f"Starting scraping for {browser_name}")
            
            driver.get("https://elpais.com/opinion/")
            time.sleep(5)
            
            # Handle cookies
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#didomi-notice-agree-button"))
                )
                cookie_button.click()
                time.sleep(2)
                logger.info(f"Accepted cookies for {browser_name}")
            except:
                logger.info(f"No cookie popup found for {browser_name}")
            
            # Find articles
            articles = []
            article_selectors = ["article.c_t", "article", ".c_t"]
            
            for selector in article_selectors:
                try:
                    article_elements = driver.find_elements(By.CSS_SELECTOR, selector)[:5]
                    if len(article_elements) >= 3:
                        logger.info(f"Found {len(article_elements)} articles using {selector} in {browser_name}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed in {browser_name}: {e}")
                    continue
            
            # Extract titles and links
            for i, article in enumerate(article_elements[:5]):
                try:
                    title_element = article.find_element(By.CSS_SELECTOR, "h2 a, h3 a, h1 a")
                    title = title_element.text.strip()
                    link = title_element.get_attribute('href')
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'url': link,
                            'index': i + 1
                        })
                        logger.info(f"Extracted article {i+1} in {browser_name}: {title[:30]}...")
                        
                except Exception as e:
                    logger.warning(f"Failed to extract article {i+1} in {browser_name}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(articles)} articles from {browser_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Scraping failed in {browser_name}: {e}")
            return []
    
    def test_browser_config(self, config):
        """Test with comprehensive error handling and logging"""
        browser_name = config.get('name', 'Unknown Browser')
        logger.info(f"🚀 Starting test on {browser_name}")
        
        try:
            # Step 1: Create driver with detailed logging
            logger.info(f"Step 1: Creating driver for {browser_name}")
            driver = self.create_browserstack_driver(config)
            
            if not driver:
                error_msg = "Driver creation failed - returned None"
                logger.error(f"❌ {browser_name}: {error_msg}")
                return {
                    'browser': browser_name,
                    'status': 'failed',
                    'error': error_msg,
                    'articles': [],
                    'session_url': None
                }
            
            logger.info(f"✅ Driver created successfully for {browser_name}")
            
            # Step 2: Mark test as started
            try:
                driver.execute_script('browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"running", "reason": "Test started"}}')
                logger.info(f"Marked session as running for {browser_name}")
            except Exception as e:
                logger.warning(f"Could not set session status for {browser_name}: {e}")
            
            # Step 3: Scrape articles
            start_time = time.time()
            logger.info(f"Step 2: Starting article scraping for {browser_name}")
            
            articles = self.scrape_articles_browserstack(driver, browser_name)
            
            # Step 4: Test translation
            translated_titles = []
            if articles:
                logger.info(f"Step 3: Translating first article title for {browser_name}")
                try:
                    translator = TranslationService(service="mymemory")
                    first_title = articles[0]['title']
                    translated_title = translator.translate_text(first_title)
                    translated_titles.append(translated_title)
                    logger.info(f"Translation successful for {browser_name}")
                except Exception as e:
                    logger.warning(f"Translation failed for {browser_name}: {e}")
            
            execution_time = time.time() - start_time
            success = len(articles) >= 3
            
            # Step 5: Get session URL
            session_url = None
            try:
                session_info = driver.execute_script('browserstack_executor: {"action": "getSessionDetails"}')
                if session_info and isinstance(session_info, dict):
                    session_url = session_info.get('hashed_id')
                    logger.info(f"Got session URL for {browser_name}")
            except Exception as e:
                logger.warning(f"Could not get session details for {browser_name}: {e}")
            
            # Step 6: Mark test result
            try:
                if success:
                    driver.execute_script('browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Test completed successfully"}}')
                else:
                    driver.execute_script('browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Insufficient articles scraped"}}')
            except Exception as e:
                logger.warning(f"Could not set final session status for {browser_name}: {e}")
            
            result = {
                'browser': browser_name,
                'status': 'passed' if success else 'failed',
                'articles_count': len(articles),
                'articles': articles,
                'translated_titles': translated_titles,
                'execution_time': execution_time,
                'session_url': session_url,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                logger.info(f"✅ {browser_name}: Test PASSED - {len(articles)} articles scraped")
            else:
                logger.warning(f"⚠️ {browser_name}: Test FAILED - Only {len(articles)} articles scraped")
            
            return result
            
        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            logger.error(f"❌ {browser_name}: {error_msg}")
            logger.error(f"Error type: {type(e).__name__}")
            
            return {
                'browser': browser_name,
                'status': 'error',
                'error': error_msg,
                'articles': [],
                'session_url': None,
                'timestamp': datetime.now().isoformat()
            }
        
        finally:
            # Always cleanup driver
            try:
                if 'driver' in locals() and driver:
                    driver.quit()
                    logger.info(f"Driver cleaned up for {browser_name}")
            except Exception as e:
                logger.warning(f"Error cleaning up driver for {browser_name}: {e}")
    
    def run_parallel_tests(self, max_workers=5):
        """Run tests with connection validation first"""
        logger.info("🔍 Validating BrowserStack connection before starting tests...")
        
        # Test connection first
        if not self.test_browserstack_connection():
            logger.error("❌ BrowserStack connection test failed. Cannot proceed with tests.")
            logger.error("Please check:")
            logger.error("  1. Your BrowserStack credentials")
            logger.error("  2. Your account status and trial period")
            logger.error("  3. Your internet connection")
            logger.error("  4. BrowserStack service status")
            return []
        
        logger.info(f"✅ Connection validated. Starting parallel execution across {len(BROWSER_CONFIGS)} browsers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_config = {
                executor.submit(self.test_browser_config, config): config 
                for config in BROWSER_CONFIGS
            }
            
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result(timeout=300)
                    results.append(result)
                    logger.info(f"Completed test for {config.get('name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Test failed for {config.get('name', 'Unknown')}: {e}")
                    results.append({
                        'browser': config.get('name', 'Unknown'),
                        'status': 'timeout_error',
                        'error': f"Test execution timeout or error: {str(e)}",
                        'articles': []
                    })
        
        return results
