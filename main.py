import json
import os
import logging
from datetime import datetime
from scraper.Scrap import fetch_articles_enhanced
from scraper.translate import TranslationService
from scraper.analyse import analyze_headers

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/scraping_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def save_enhanced_data_to_json(articles, translated_titles, filename_prefix="elpais_enhanced_data"):
    """Save enhanced scraped data with additional metadata"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    os.makedirs("data", exist_ok=True)
    
    # Enhanced articles file with additional metadata
    articles_file = f"data/{filename_prefix}_articles_{timestamp}.json"
    enhanced_articles = []
    
    for i, (article, translated) in enumerate(zip(articles, translated_titles)):
        enhanced_article = {
            **article,  # Original article data
            "article_number": i + 1,
            "translated_title": translated,
            "processing_metadata": {
                "content_extracted": len(article.get('content', '')) > 50 and article.get('content') != "Content could not be extracted",
                "image_downloaded": article.get('image') is not None,
                "paywall_detected": article.get('paywall_detected', False),
                "paywall_confidence": article.get('paywall_confidence', 0.0),
                "bypass_method": article.get('bypass_method'),
                "extraction_method": article.get('extraction_method'),
                "content_quality_score": article.get('content_score', 0.0)
            }
        }
        enhanced_articles.append(enhanced_article)
    
    with open(articles_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_articles, f, ensure_ascii=False, indent=2)
    
    # Translations summary file
    translations_file = f"data/{filename_prefix}_translations_{timestamp}.json"
    translation_data = []
    for i, (article, translated) in enumerate(zip(articles, translated_titles)):
        translation_data.append({
            "article_number": i + 1,
            "original_title": article['title'],
            "translated_title": translated,
            "url": article.get('url', ''),
            "translation_successful": article['title'].lower() != translated.lower()
        })
    
    with open(translations_file, 'w', encoding='utf-8') as f:
        json.dump(translation_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Enhanced data saved to {articles_file} and {translations_file}")
    return articles_file, translations_file

def display_enhanced_results(articles, translated_titles, repeated_words):
    """Display enhanced results with additional diagnostics"""
    print("\n" + "="*90)
    print("  EL PAÍS OPINION SECTION - ENHANCED SCRAPING RESULTS")
    print("="*90)
    
    print(f"\n Successfully processed {len(articles)} articles from El País Opinion section")
    print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Enhanced article display with additional metadata
    print("\n" + "-"*70)
    print(" ARTICLES WITH ENHANCED EXTRACTION ANALYSIS:")
    print("-"*70)
    
    for idx, article in enumerate(articles, 1):
        print(f"\n ARTICLE {idx}:")
        print(f"   Title: {article['title']}")
        
        # Content analysis
        content = article.get('content', '')
        content_score = article.get('content_score', 0.0)
        
        if content and len(content) > 50 and content != "Content could not be extracted":
            print(f"    Content: {content[:200]}{'...' if len(content) > 200 else ''}")
            print(f"    Content length: {len(content)} characters")
            print(f"    Quality score: {content_score:.2f}/1.0")
            if article.get('extraction_method'):
                print(f"    Extraction method: {article['extraction_method']}")
        else:
            print(f"    Content: Failed to extract")
            if article.get('error'):
                print(f"     Error: {article['error']}")
        
        # Paywall analysis
        if article.get('paywall_detected'):
            confidence = article.get('paywall_confidence', 0.0)
            print(f"    Paywall: Detected (confidence: {confidence:.2f})")
            if article.get('bypass_method'):
                print(f"    Bypass: {article['bypass_method']}")
        else:
            print(f"    Paywall: Not detected")
        
        print(f"    URL: {article.get('url', 'N/A')}")
        
        # Image analysis
        if article.get('image'):
            print(f"     Image:  Downloaded as {article['image']}")
        else:
            print(f"     Image:  No image available")
    
    # Enhanced translation display
    print("\n" + "-"*70)
    print(" TRANSLATED TITLES (SPANISH → ENGLISH):")
    print("-"*70)
    
    for idx, (original, translated) in enumerate(zip([a['title'] for a in articles], translated_titles), 1):
        print(f"\n TRANSLATION {idx}:")
        print(f"   🇪🇸 ES: {original}")
        print(f"   🇺🇸 EN: {translated}")
        
        if original.lower() != translated.lower():
            print(f"    Status: Successfully translated")
        else:
            print(f"     Status: Translation may have failed (identical text)")
    
    # Word frequency analysis
    print("\n" + "-"*70)
    print(" WORD FREQUENCY ANALYSIS:")
    print("-"*70)
    
    if repeated_words:
        print(f"\n Found {len(repeated_words)} words repeated more than twice:")
        sorted_words = sorted(repeated_words.items(), key=lambda x: x[1], reverse=True)
        for word, count in sorted_words:
            print(f"       '{word}': {count} occurrences")
    else:
        print("\n No words were repeated more than twice across all translated titles.")
        print("   This suggests excellent diversity in article topics!")
    
    print("\n" + "="*90)

def validate_enhanced_results(articles, translated_titles):
    """Enhanced validation with detailed analytics"""
    issues = []
    warnings = []
    insights = []
    
    # Content extraction analysis
    failed_content = sum(1 for a in articles if 
                        not a.get('content') or 
                        len(a.get('content', '')) < 50 or 
                        a.get('content') == "Content could not be extracted")
    
    successful_content = len(articles) - failed_content
    content_quality_scores = [a.get('content_score', 0.0) for a in articles if a.get('content_score')]
    avg_quality = sum(content_quality_scores) / max(len(content_quality_scores), 1)
    
    if failed_content > 0:
        issues.append(f"  {failed_content}/{len(articles)} articles failed content extraction")
    
    # Paywall analysis
    paywall_detected = sum(1 for a in articles if a.get('paywall_detected', False))
    bypasses_successful = sum(1 for a in articles if a.get('bypass_method') and a.get('bypass_method') != 'direct_access')
    
    if paywall_detected > 0:
        insights.append(f" {paywall_detected}/{len(articles)} articles had paywalls detected")
        if bypasses_successful > 0:
            insights.append(f" {bypasses_successful} paywall bypasses were successful")
    
    # Translation analysis
    failed_translations = sum(1 for orig, trans in zip([a['title'] for a in articles], translated_titles)
                             if orig.lower() == trans.lower())
    
    if failed_translations > 0:
        warnings.append(f"  {failed_translations}/{len(translated_titles)} translations may have failed")
    
    # Image analysis
    failed_images = sum(1 for a in articles if not a.get('image'))
    
    if failed_images > 0:
        warnings.append(f"  {failed_images}/{len(articles)} articles have no images")
    
    # Extraction method analysis
    extraction_methods = {}
    for article in articles:
        method = article.get('extraction_method', 'unknown')
        extraction_methods[method] = extraction_methods.get(method, 0) + 1
    
    # Display results
    if issues or warnings or insights:
        print("\n" + "="*80)
        print(" ENHANCED ANALYSIS & RECOMMENDATIONS:")
        print("="*80)
        
        for issue in issues:
            print(f"\n {issue}")
        
        for warning in warnings:
            print(f"\n  {warning}")
        
        for insight in insights:
            print(f"\n {insight}")
        
        # Quality insights
        print(f"\n CONTENT QUALITY METRICS:")
        print(f"   • Successful extractions: {successful_content}/{len(articles)}")
        print(f"   • Average quality score: {avg_quality:.2f}/1.0")
        print(f"   • Extraction methods used:")
        for method, count in extraction_methods.items():
            print(f"     - {method}: {count}")
        
        # Recommendations
        if failed_content > 2:
            print(f"\n CONTENT EXTRACTION RECOMMENDATIONS:")
            print(f"   • {failed_content} articles failed - likely paywall or structure changes")
            print(f"   • Consider implementing additional bypass methods")
            print(f"   • Update CSS selectors for current site structure")
        
        if paywall_detected > bypasses_successful:
            print(f"\n PAYWALL BYPASS RECOMMENDATIONS:")
            print(f"   • {paywall_detected - bypasses_successful} paywalls not bypassed")
            print(f"   • Consider implementing archive service integration")
            print(f"   • Add cookie clearing and user-agent rotation")
        
        if avg_quality < 0.6:
            print(f"\n CONTENT QUALITY RECOMMENDATIONS:")
            print(f"   • Average quality score is {avg_quality:.2f} (below 0.6)")
            print(f"   • Consider improving content filtering and extraction")
            print(f"   • Add structured data extraction methods")

def main():
    """Enhanced main execution with comprehensive analytics"""
    try:
        print(" Starting Enhanced El País Opinion scraper...")
        print(" Features: Paywall detection, bypass capabilities, enhanced diagnostics")
        print(" This will scrape 5 articles with advanced extraction methods.")
        print("-" * 70)
        
        # Step 1: Enhanced scraping
        logger.info("Step 1: Enhanced scraping with paywall detection...")
        articles = fetch_articles_enhanced()
        
        if not articles:
            logger.error("No articles were successfully scraped. Check diagnostics.")
            print(" Failed to scrape any articles. Check logs and diagnostics for details.")
            return
        
        logger.info(f"Successfully scraped {len(articles)} articles with enhanced methods")
        
        # Step 2: Translation
        logger.info("Step 2: Translating article titles...")
        translator = TranslationService(service="mymemory")
        
        titles_to_translate = [article['title'] for article in articles]
        translated_titles = translator.translate_batch(titles_to_translate)
        
        if not translated_titles:
            logger.error("Translation failed for all titles")
            translated_titles = titles_to_translate
        
        # Step 3: Analysis
        logger.info("Step 3: Analyzing word frequency...")
        repeated_words = analyze_headers(translated_titles)
        
        # Step 4: Display enhanced results
        display_enhanced_results(articles, translated_titles, repeated_words)
        
        # Step 5: Enhanced validation
        validate_enhanced_results(articles, translated_titles)
        
        # Step 6: Save enhanced data
        logger.info("Step 6: Saving enhanced data with metadata...")
        save_enhanced_data_to_json(articles, translated_titles)
        
        # Step 7: Enhanced statistics
        successful_content = sum(1 for a in articles if 
                               a.get('content') and 
                               len(a.get('content', '')) > 50 and 
                               a.get('content') != "Content could not be extracted")
        successful_images = sum(1 for a in articles if a.get('image'))
        successful_translations = sum(1 for orig, trans in zip([a['title'] for a in articles], translated_titles)
                                    if orig.lower() != trans.lower())
        paywall_detections = sum(1 for a in articles if a.get('paywall_detected', False))
        successful_bypasses = sum(1 for a in articles if a.get('bypass_method') and a.get('bypass_method') != 'direct_access')
        
        avg_quality = sum(a.get('content_score', 0.0) for a in articles) / len(articles)
        
        print(f"\n  ENHANCED FINAL STATISTICS:")
        print(f"    Articles scraped: {len(articles)}")
        print(f"    Content extracted: {successful_content}/{len(articles)}")
        print(f"    Images downloaded: {successful_images}/{len(articles)}")
        print(f"    Titles translated: {successful_translations}/{len(translated_titles)}")
        print(f"    Paywalls detected: {paywall_detections}")
        print(f"    Bypasses successful: {successful_bypasses}")
        print(f"    Average content quality: {avg_quality:.2f}/1.0")
        print(f"    Words repeated >2 times: {len(repeated_words)}")
        print(f"    API requests made: {translator.request_count}")
        
        # Enhanced success rate calculation
        total_operations = len(articles) * 4  # content, image, translation, paywall handling
        successful_operations = successful_content + successful_images + successful_translations + (len(articles) - paywall_detections + successful_bypasses)
        success_rate = (successful_operations / total_operations) * 100
        
        print(f"\n Enhanced Success Rate: {success_rate:.1f}%")
        
        if success_rate > 85:
            print(" Excellent! Enhanced scraping completed with high success rate!")
        elif success_rate > 70:
            print(" Good! Most operations completed successfully.")
        else:
            print("  Some issues detected. Check enhanced recommendations above.")
        
        print(f"\nCheck the 'images/' folder for downloaded images")
        print(f"Check the 'data/' folder for enhanced JSON files and logs")
        print(f"Check 'data/diagnostics/' folder for detailed failure analysis")
        print(f"Check 'data/scraping_enhanced.log' for comprehensive logs")
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        print("\n Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in enhanced execution: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        print("Check the enhanced log files for detailed error information")

if __name__ == "__main__":
    # Ensure required directories exist
    for directory in ['images', 'data', 'data/diagnostics']:
        os.makedirs(directory, exist_ok=True)
    
    main()
