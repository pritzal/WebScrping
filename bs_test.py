# run_browserstack_tests.py
import os
import json
from datetime import datetime
from bs__scraper import BrowserStackScraper
from scraper.analyse import analyze_headers

def save_test_results(results, filename_prefix="browserstack_results"):
    """Save test results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data/browserstack", exist_ok=True)
    
    filename = f"data/browserstack/{filename_prefix}_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to: {filename}")
    return filename

def display_browserstack_results(results):
    """Display comprehensive test results"""
    print("\n" + "="*80)
    print("  BROWSERSTACK CROSS-BROWSER TEST RESULTS")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['status'] == 'passed')
    failed_tests = total_tests - passed_tests
    
    print(f"\n📊 SUMMARY:")
    print(f"   • Total Browsers Tested: {total_tests}")
    print(f"   • Tests Passed: {passed_tests}")
    print(f"   • Tests Failed: {failed_tests}")
    print(f"   • Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n🌐 DETAILED RESULTS:")
    print("-" * 80)
    
    for result in results:
        browser = result['browser']
        status = result['status']
        status_icon = "✅" if status == 'passed' else "❌"
        
        print(f"\n{status_icon} {browser}")
        print(f"   Status: {status}")
        
        if result.get('articles_count'):
            print(f"   Articles Scraped: {result['articles_count']}")
        
        if result.get('execution_time'):
            print(f"   Execution Time: {result['execution_time']:.1f}s")
        
        if result.get('session_url'):
            print(f"   BrowserStack Session: https://app.browserstack.com/automate/sessions/{result['session_url']}")
        
        if result.get('error'):
            print(f"   Error: {result['error'][:100]}...")
        
        # Show first article title if available
        if result.get('articles') and len(result['articles']) > 0:
            first_article = result['articles'][0]['title'][:50]
            print(f"   First Article: {first_article}...")
    
    # Analyze translations across all successful tests
    all_translated_titles = []
    for result in results:
        if result['status'] == 'passed' and result.get('translated_titles'):
            all_translated_titles.extend(result['translated_titles'])
    
    if all_translated_titles:
        repeated_words = analyze_headers(all_translated_titles)
        
        print(f"\n📝 TRANSLATION ANALYSIS ACROSS ALL BROWSERS:")
        print("-" * 60)
        
        if repeated_words:
            print(f"Words repeated more than twice:")
            for word, count in sorted(repeated_words.items(), key=lambda x: x[1], reverse=True):
                print(f"   • '{word}': {count} occurrences")
        else:
            print("   No words repeated more than twice across all tests")
    
    print("\n" + "="*80)

def main():
    """Main execution function for BrowserStack testing"""
    
    print("🚀 Starting BrowserStack Cross-Browser Testing")
    print("   Testing El País scraper across 5 different browser configurations")
    print("   This will run in parallel across desktop and mobile browsers")
    print("-" * 70)
    
    # Create scraper instance
    scraper = BrowserStackScraper()
    
    try:
        # Run parallel tests
        print("⏳ Executing tests in parallel (this may take 5-10 minutes)...")
        results = scraper.run_parallel_tests(max_workers=5)
        
        # Display results
        display_browserstack_results(results)
        
        # Save results
        save_test_results(results)
        
        # Final summary
        passed = sum(1 for r in results if r['status'] == 'passed')
        total = len(results)
        
        if passed == total:
            print(f"🎉 All {total} browser tests passed successfully!")
        elif passed > total // 2:
            print(f"✅ {passed}/{total} tests passed - Good cross-browser compatibility")
        else:
            print(f"⚠️  Only {passed}/{total} tests passed - Review failed browsers")
        
        print(f"\nCheck BrowserStack dashboard for detailed session recordings:")
        print(f"https://app.browserstack.com/automate")
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()
