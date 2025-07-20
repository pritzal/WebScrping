# browserstack_config.py (FIXED - Schema Compliant)
import os

# BrowserStack credentials
BROWSERSTACK_USERNAME = os.getenv('BROWSERSTACK_USERNAME', 'aayushchaudhary_fQyx8D')
BROWSERSTACK_ACCESS_KEY = os.getenv('BROWSERSTACK_ACCESS_KEY', '6U8WBhzVqckBTJX3vxzp')

# BrowserStack Hub URL
BROWSERSTACK_URL = f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"

# Fixed browser configurations (Schema Compliant)
BROWSER_CONFIGS = [
    {
        'name': 'Chrome Windows 11 Desktop Test',
        'browserName': 'Chrome',
        'browserVersion': 'latest',
        'os': 'Windows',
        'osVersion': '11',
        'resolution': '1920x1080',
        'project': 'El País Scraper Cross-Browser',
        'build': 'Enhanced Web Scraping Test - Fixed Schema'
    },
    {
        'name': 'Firefox macOS Desktop Test',
        'browserName': 'Firefox',
        'browserVersion': 'latest',
        'os': 'OS X',
        'osVersion': 'Monterey',
        'resolution': '1920x1080',
        'project': 'El País Scraper Cross-Browser',
        'build': 'Enhanced Web Scraping Test - Fixed Schema'
    },
    {
        'name': 'Safari macOS Desktop Test',
        'browserName': 'Safari',
        'browserVersion': 'latest',
        'os': 'OS X',
        'osVersion': 'Monterey',
        'resolution': '1920x1080',
        'project': 'El País Scraper Cross-Browser',
        'build': 'Enhanced Web Scraping Test - Fixed Schema'
    },
    {
        'name': 'Chrome Android Mobile Test',
        'browserName': 'chrome',
        'deviceName': 'Samsung Galaxy S22',
        'platformName': 'android',
        'osVersion': '12.0',
        'realMobile': 'true',
        'project': 'El País Scraper Cross-Browser',
        'build': 'Enhanced Web Scraping Test - Fixed Schema'
    },
    {
        'name': 'Safari iOS Mobile Test',
        'browserName': 'safari',
        'deviceName': 'iPhone 13',
        'platformName': 'ios',
        'osVersion': '15',
        'realMobile': 'true',
        'project': 'El País Scraper Cross-Browser',
        'build': 'Enhanced Web Scraping Test - Fixed Schema'
    }
]
