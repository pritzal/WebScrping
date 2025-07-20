import logging
import json
import os
from datetime import datetime
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

class FailureDiagnostics:
    """Failure diagnostics and reporting"""
    
    def __init__(self):
        self.diagnostics_dir = "data/diagnostics"
        os.makedirs(self.diagnostics_dir, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.failure_log = []
        self.paywall_log = []
        self.performance_metrics = {}
    
    def log_failure(self, failure_type, error_message, url, additional_data=None):
        """Log a failure"""
        failure_entry = {
            "timestamp": datetime.now().isoformat(),
            "failure_type": failure_type,
            "error_message": error_message,
            "url": url,
            "additional_data": additional_data or {}
        }
        
        self.failure_log.append(failure_entry)
        logger.warning(f"Failure logged: {failure_type} at {url}")
    
    def log_detailed_failure(self, driver, url, title, index, error=None):
        """Log failure information with page state"""
        try:
            # Capture page state
            page_title = driver.title
            current_url = driver.current_url
            page_source_length = len(driver.page_source)
            

            issues_found = []
            
            # Check for paywall indicators
            paywall_keywords = ['suscr', 'premium', 'regist', 'login', 'sign up']
            body_text = ""
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                for keyword in paywall_keywords:
                    if keyword in body_text:
                        issues_found.append(f"paywall_keyword_{keyword}")
            except:
                pass
            
            # Check for content containers
            content_containers = ['.a_c', 'article', '.content', '.main']
            containers_found = []
            for container in content_containers:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, container)
                    containers_found.append(f"{container}:{len(elements)}")
                except:
                    pass
            
            # Save page snapshot for analysis
            snapshot_filename = f"failure_snapshot_{self.session_id}_{index}.html"
            snapshot_path = os.path.join(self.diagnostics_dir, snapshot_filename)
            
            try:
                with open(snapshot_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
            except Exception as e:
                logger.warning(f"Could not save page snapshot: {e}")
                snapshot_path = None
            
            failure_data = {
                "article_index": index,
                "article_title": title,
                "target_url": url,
                "actual_url": current_url,
                "page_title": page_title,
                "page_source_length": page_source_length,
                "issues_identified": issues_found,
                "content_containers": containers_found,
                "error": error,
                "snapshot_file": snapshot_path,
                "body_text_sample": body_text[:500] if body_text else ""
            }
            
            self.log_failure("detailed_extraction_failure", error or "Content extraction failed", 
                           url, failure_data)
            
        except Exception as e:
            logger.error(f"Failed to log detailed failure information: {e}")
    
    def log_paywall_detection(self, url, detection_results):
        """Log paywall detection results"""
        paywall_entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "has_paywall": detection_results['has_paywall'],
            "confidence": detection_results['confidence'],
            "indicators": detection_results['indicators'],
            "bypass_recommendations": detection_results['bypass_recommendations']
        }
        
        self.paywall_log.append(paywall_entry)
        
        if detection_results['has_paywall']:
            logger.info(f"Paywall detected at {url} (confidence: {detection_results['confidence']:.2f})")
    
    def log_session_stats(self, session_stats):
        """Log comprehensive session statistics"""
        self.performance_metrics = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "statistics": session_stats,
            "total_failures": len(self.failure_log),
            "total_paywall_detections": len(self.paywall_log),
            "paywall_detection_rate": len([p for p in self.paywall_log if p['has_paywall']]) / max(len(self.paywall_log), 1)
        }
        
        # Save to file
        stats_filename = f"session_stats_{self.session_id}.json"
        stats_path = os.path.join(self.diagnostics_dir, stats_filename)
        
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.performance_metrics, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Session statistics saved to {stats_path}")
        except Exception as e:
            logger.error(f"Failed to save session statistics: {e}")
    
    def generate_failure_report(self):
        """Generate comprehensive failure analysis report"""
        if not self.failure_log:
            return "No failures to report"
        
        # Analyze failure patterns
        failure_types = {}
        error_patterns = {}
        
        for failure in self.failure_log:
            f_type = failure['failure_type']
            failure_types[f_type] = failure_types.get(f_type, 0) + 1
            
            error_msg = failure['error_message']
            if error_msg:
                error_patterns[error_msg] = error_patterns.get(error_msg, 0) + 1
        
        # Generate recommendations
        recommendations = []
        
        if failure_types.get('detailed_extraction_failure', 0) > 2:
            recommendations.append("Consider updating content extraction selectors")
            recommendations.append("Implement additional paywall bypass methods")
        
        if len([p for p in self.paywall_log if p['has_paywall']]) > 3:
            recommendations.append("High paywall rate detected - consider premium bypass solutions")
        
        report = {
            "session_id": self.session_id,
            "total_failures": len(self.failure_log),
            "failure_types": failure_types,
            "most_common_errors": dict(list(error_patterns.items())[:5]),
            "paywall_statistics": {
                "total_checked": len(self.paywall_log),
                "paywalls_detected": len([p for p in self.paywall_log if p['has_paywall']]),
                "average_confidence": sum(p['confidence'] for p in self.paywall_log) / max(len(self.paywall_log), 1)
            },
            "recommendations": recommendations
        }
        
        # Save failure report
        report_filename = f"failure_report_{self.session_id}.json"
        report_path = os.path.join(self.diagnostics_dir, report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Failure report generated: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save failure report: {e}")
        
        return report
    
    def print_diagnostics_summary(self):
        """Print a summary of diagnostics to console"""
        print("\n" + "="*60)
        print("🔍 ENHANCED DIAGNOSTICS SUMMARY")
        print("="*60)
        
        if self.failure_log:
            print(f"\n Failures Detected: {len(self.failure_log)}")
            failure_types = {}
            for failure in self.failure_log:
                f_type = failure['failure_type']
                failure_types[f_type] = failure_types.get(f_type, 0) + 1
            
            for f_type, count in failure_types.items():
                print(f"   • {f_type}: {count}")
        
        if self.paywall_log:
            paywall_count = len([p for p in self.paywall_log if p['has_paywall']])
            print(f"\n Paywall Analysis:")
            print(f"   • URLs checked: {len(self.paywall_log)}")
            print(f"   • Paywalls detected: {paywall_count}")
            print(f"   • Detection rate: {paywall_count/max(len(self.paywall_log), 1)*100:.1f}%")
        
        print(f"\n Diagnostics saved in: {self.diagnostics_dir}/")
        print("="*60)
