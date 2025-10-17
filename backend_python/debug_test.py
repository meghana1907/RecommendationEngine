"""
Debug script to test the intelligent pipeline isolated
"""
import traceback
from services.domain_aware_test_engine import DomainAwareTestEngine
from services.universal_test_architect import DomainAgnosticTestArchitect
from services.document_processor import document_storage

# Add test documents
document_storage["test_brd"] = "IoT Smart Home System Business Requirements - Device connectivity management for multiple protocol support (WiFi, Zigbee, Z-Wave), sensor data collection and real-time aggregation from temperature, humidity, motion, and security sensors, edge computing gateway functionality for local processing and reduced latency, real-time monitoring dashboard with customizable alerts and notifications"

document_storage["test_user_stories"] = "As a homeowner, I want to monitor temperature and humidity sensors remotely so I can ensure optimal comfort. As a homeowner, I want to receive instant notifications when motion sensors detect activity so I can ensure security. As a system admin, I want device authentication with secure protocols so unauthorized devices cannot access the network."

try:
    # Test domain-aware engine
    print("Testing domain-aware engine...")
    domain_aware_engine = DomainAwareTestEngine()
    
    brd_content = document_storage["test_brd"]
    user_stories = document_storage["test_user_stories"]
    
    # Generate domain-aware tests
    domain_standard_tests, domain_recommended_tests = domain_aware_engine.generate_recommendations(
        brd_content=brd_content,
        user_stories=user_stories
    )
    
    print(f"Domain tests generated: {len(domain_standard_tests)} standard, {len(domain_recommended_tests)} recommended")
    
    # Format domain-aware tests  
    domain_formatted = domain_aware_engine.format_recommendations(domain_standard_tests, domain_recommended_tests)
    
    print("Domain formatting successful!")
    
    # Check field names in formatted output
    if domain_formatted['standard_testing_types']['tests']:
        test_sample = domain_formatted['standard_testing_types']['tests'][0]
        print(f"Sample test fields: {list(test_sample.keys())}")
        if 'estimated_effort' in test_sample:
            print(f"✓ estimated_effort found: {test_sample['estimated_effort']}")
        else:
            print("✗ estimated_effort not found!")
            
    # Test universal architect
    print("\nTesting universal architect...")
    universal_architect = DomainAgnosticTestArchitect()
    universal_strategy = universal_architect.generate_test_strategy(brd_content, user_stories)
    
    print(f"Universal tests generated: {len(universal_strategy['required_tests'])} required, {len(universal_strategy['recommended_tests'])} recommended")
    
    # Check universal test objects
    if universal_strategy['required_tests']:
        test_obj = universal_strategy['required_tests'][0]
        print(f"Universal test object type: {type(test_obj)}")
        print(f"Universal test fields: {test_obj.__dict__.keys() if hasattr(test_obj, '__dict__') else 'Not an object'}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"✗ Error occurred: {str(e)}")
    print(f"Full traceback:\n{traceback.format_exc()}")