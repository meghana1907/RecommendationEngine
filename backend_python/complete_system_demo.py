"""
Comprehensive Test Recommendation System Demo

This demonstrates the complete intelligent test recommendation system
that analyzes BRD/User Stories and generates Standard vs Recommended tests
with clear rationale and cluster attribution.
"""

import sys
import os

# Add the parent directory to the path to import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.domain_aware_test_engine import DomainAwareTestEngine
from services.universal_test_architect import DomainAgnosticTestArchitect

class ComprehensiveTestRecommendationDemo:
    """Complete demonstration of the intelligent test recommendation system"""
    
    def __init__(self):
        self.domain_engine = DomainAwareTestEngine()
        self.universal_architect = DomainAgnosticTestArchitect()
    
    def demonstrate_complete_system(self):
        """Show how the complete system works with your subscription management BRD"""
        
        print("🚀 COMPREHENSIVE TEST RECOMMENDATION SYSTEM")
        print("=" * 70)
        print("Intelligent BRD/User Stories → Standard vs Recommended Tests")
        print("=" * 70)
        
        # Your subscription management requirements
        subscription_brd = """
        Business Requirements Document (BRD) - Module: Subscription Management
        
        The Subscription Module is designed for Charge Network Operators (CNOs) to manage and 
        administer annual subscriptions for Charge Station Operators (CSOs). The CNO retains 
        overall network ownership, constructs subscription plans, and oversees the complete 
        subscription lifecycle — from creation to renewal and activation.

        Functional Requirements:
        - Organization Selection: Users can select only CSO-type organizations for subscription
        - Location Selection: Locations are filtered and displayed based on the selected CSO organization
        - Chargers Association: User selects chargers to include in the subscription
        - Subscription Details: Term set in years, Type (New or Renewal), Total Ports manually entered, Amount auto-calculated
        
        Business Rules:
        - BR-01: A charger cannot be associated with more than one Active or Pending subscription
        - BR-02: Only Operational chargers can be included (Decommissioned/Uncommissioned excluded)  
        - BR-03: Subscription submission requires a valid reseller and billing contact
        - BR-04: Amount field is system-calculated and not user-editable
        
        Non-Functional Requirements:
        - Security: All organizational, payment, and contact data must be securely handled (encrypted transmission and storage)
        - Auditability: Every action — creation, update, activation — must be logged for traceability and compliance
        - Performance: Invoice generation and payment updates should reflect in real time on the dashboard
        
        User Stories:
        - CNO can log in and access Subscription Management
        - System filters Organization Selection to only CSO types
        - CNO can select specific chargers to include in the subscription
        - System prevents selection of Decommissioned/Uncommissioned chargers
        - System blocks submission if selected chargers are Active or Pending on another subscription
        - CNO can set the subscription Term and manually input Total Ports count
        - Amount field is auto-calculated and read-only
        - System auto-generates an invoice upon submission
        - Subscription Status defaults to 'Pending' after creation
        - Status updates automatically to 'Paid' upon payment receipt
        - Authorized CNO can manually activate the Paid subscription
        """
        
        print("📋 ANALYZING YOUR SUBSCRIPTION MANAGEMENT BRD...")
        print("-" * 50)
        
        # 1. Domain-Aware Analysis
        print("🧠 STEP 1: Domain-Aware Analysis")
        domain_analysis = self.domain_engine.analyze_requirements(subscription_brd)
        domain_recs = self.domain_engine.generate_recommendations(domain_analysis)
        
        print(f"   ✓ Functional Areas Identified: {len(domain_analysis.get('functional_areas', []))}")
        print(f"   ✓ Business Rules Extracted: {len(domain_analysis.get('business_rules', []))}")
        print(f"   ✓ Technical Components: {len(domain_analysis.get('technical_components', []))}")
        print(f"   ✓ Risk Areas Identified: {len(domain_analysis.get('risk_areas', []))}")
        
        # 2. Universal Architecture Analysis
        print("\n🏗️  STEP 2: Universal Architecture Analysis")
        universal_strategy = self.universal_architect.generate_universal_testing_strategy(subscription_brd)
        arch_analysis = universal_strategy['architecture_analysis']
        
        print(f"   ✓ Architectural Patterns: {len(arch_analysis['identified_patterns'])}")
        print(f"   ✓ System Complexity: {arch_analysis['system_complexity']}")
        print(f"   ✓ Security Posture: {arch_analysis['security_posture']}")
        print(f"   ✓ Quality Attributes: {', '.join(arch_analysis['quality_attributes'])}")
        
        # 3. Integrate Results
        print("\n🔀 STEP 3: Intelligent Integration")
        integrated_tests = self._integrate_recommendations(domain_recs, universal_strategy)
        
        print(f"   ✓ Total Tests Generated: {len(integrated_tests['standard_tests']) + len(integrated_tests['recommended_tests'])}")
        print(f"   ✓ Standard (MVP/UAT): {len(integrated_tests['standard_tests'])}")
        print(f"   ✓ Recommended (Advanced): {len(integrated_tests['recommended_tests'])}")
        
        # 4. Display Results
        self._display_test_results(integrated_tests)
        
        return integrated_tests
    
    def _integrate_recommendations(self, domain_recs, universal_strategy):
        """Combine domain-aware and universal recommendations"""
        
        # Collect all tests with source attribution
        all_tests = {}
        
        # Add domain-aware tests
        for test in domain_recs.get('standard_tests', []):
            test_key = test['test_type']
            all_tests[test_key] = {
                'test_type': test['test_type'],
                'category': 'standard',
                'priority': test.get('priority', 'medium'),
                'sources': ['Domain-Aware Analysis'],
                'rationales': [test.get('rationale', 'Domain-specific requirement')],
                'domain_context': test.get('domain_context', {}),
                'techniques': test.get('techniques', [])
            }
        
        for test in domain_recs.get('recommended_tests', []):
            test_key = test['test_type']
            all_tests[test_key] = {
                'test_type': test['test_type'],
                'category': 'recommended',
                'priority': test.get('priority', 'medium'),
                'sources': ['Domain-Aware Analysis'],
                'rationales': [test.get('rationale', 'Domain-specific enhancement')],
                'domain_context': test.get('domain_context', {}),
                'techniques': test.get('techniques', [])
            }
        
        # Add universal architecture tests
        for test in universal_strategy.get('standard_tests', []):
            test_key = test.test_type
            if test_key in all_tests:
                all_tests[test_key]['sources'].append('Universal Architecture')
                all_tests[test_key]['rationales'].append(test.rationale)
                all_tests[test_key]['category'] = 'standard'  # Upgrade if both agree
            else:
                all_tests[test_key] = {
                    'test_type': test.test_type,
                    'category': 'standard',
                    'priority': test.priority,
                    'sources': ['Universal Architecture'],
                    'rationales': [test.rationale],
                    'domain_context': {},
                    'techniques': test.techniques,
                    'architectural_pattern': getattr(test, 'architectural_pattern', 'General')
                }
        
        for test in universal_strategy.get('recommended_tests', []):
            test_key = test.test_type
            if test_key in all_tests:
                all_tests[test_key]['sources'].append('Universal Architecture')
                all_tests[test_key]['rationales'].append(test.rationale)
            else:
                all_tests[test_key] = {
                    'test_type': test.test_type,
                    'category': 'recommended',
                    'priority': test.priority,
                    'sources': ['Universal Architecture'],
                    'rationales': [test.rationale],
                    'domain_context': {},
                    'techniques': test.techniques,
                    'architectural_pattern': getattr(test, 'architectural_pattern', 'General')
                }
        
        # Separate into categories
        standard_tests = [test for test in all_tests.values() if test['category'] == 'standard']
        recommended_tests = [test for test in all_tests.values() if test['category'] == 'recommended']
        
        return {
            'standard_tests': standard_tests,
            'recommended_tests': recommended_tests,
            'integration_summary': {
                'total_tests': len(all_tests),
                'multi_source_validation': sum(1 for test in all_tests.values() if len(test['sources']) > 1)
            }
        }
    
    def _display_test_results(self, results):
        """Display the integrated test results with clear categorization"""
        
        print("\n" + "🎯 INTELLIGENT TEST RECOMMENDATIONS" + "=" * 30)
        
        print(f"\n✅ STANDARD TESTS (MVP/UAT Critical) - {len(results['standard_tests'])} tests")
        print("   These tests are ESSENTIAL for basic system functionality")
        print("-" * 60)
        
        for i, test in enumerate(results['standard_tests'], 1):
            sources_str = " + ".join(test['sources'])
            validation_icon = "🔗" if len(test['sources']) > 1 else "📋"
            
            print(f"{i:2d}. {validation_icon} {test['test_type']}")
            print(f"     Sources: {sources_str}")
            print(f"     Priority: {test['priority'].upper()}")
            
            if test['rationales']:
                print(f"     Why: {test['rationales'][0][:70]}...")
            
            if 'architectural_pattern' in test:
                print(f"     Pattern: {test['architectural_pattern']}")
            
            print()
        
        print(f"\n🎯 RECOMMENDED TESTS (Advanced/Post-MVP) - {len(results['recommended_tests'])} tests")
        print("   These tests enhance quality and production readiness")
        print("-" * 60)
        
        for i, test in enumerate(results['recommended_tests'], 1):
            sources_str = " + ".join(test['sources'])
            validation_icon = "🔗" if len(test['sources']) > 1 else "📋"
            
            print(f"{i:2d}. {validation_icon} {test['test_type']}")
            print(f"     Sources: {sources_str}")
            print(f"     Priority: {test['priority'].upper()}")
            
            if test['rationales']:
                print(f"     Why: {test['rationales'][0][:70]}...")
            
            print()
        
        # Summary statistics
        multi_source = results['integration_summary']['multi_source_validation']
        total = results['integration_summary']['total_tests']
        confidence = round((multi_source / total) * 100, 1) if total > 0 else 0
        
        print(f"\n📊 RECOMMENDATION QUALITY METRICS:")
        print(f"   • Total Tests: {total}")
        print(f"   • Multi-Source Validated: {multi_source}/{total}")
        print(f"   • Confidence Score: {confidence}%")
        print(f"   • Standard/Recommended Ratio: {len(results['standard_tests'])}:{len(results['recommended_tests'])}")
    
    def demonstrate_domain_adaptability(self):
        """Show how the same system works across different domains"""
        
        print(f"\n🌍 DOMAIN ADAPTABILITY DEMONSTRATION")
        print("=" * 50)
        print("Same intelligent engine → Different domains → Contextual recommendations")
        
        domains = {
            "Healthcare": """
            Electronic Health Records (EHR) System
            - Patient registration with HIPAA compliance
            - Appointment scheduling with doctor availability
            - Prescription management with drug interaction checks
            - Lab results integration with external systems
            - Secure messaging between patients and providers
            - Role-based access for doctors, nurses, patients
            """,
            
            "E-commerce": """
            Online Shopping Platform
            - Product catalog with categories and inventory
            - Shopping cart with add/remove/update operations
            - Payment processing through multiple gateways
            - Order management with status tracking
            - Customer reviews and ratings system
            - Admin dashboard with sales analytics
            """,
            
            "IoT Platform": """
            Smart Device Management System
            - Device registration and provisioning
            - Real-time sensor data collection
            - Remote device configuration and updates
            - Alert and notification system
            - Data analytics and reporting dashboard
            - Integration with third-party monitoring tools
            """
        }
        
        for domain_name, requirements in domains.items():
            print(f"\n📱 {domain_name.upper()} DOMAIN:")
            print("-" * 30)
            
            # Quick analysis
            universal_strategy = self.universal_architect.generate_universal_testing_strategy(requirements)
            arch_analysis = universal_strategy['architecture_analysis']
            
            # Top patterns
            top_patterns = [p[0] for p in arch_analysis['identified_patterns'][:3]]
            print(f"Key Patterns: {', '.join(top_patterns)}")
            
            # System characteristics  
            print(f"Complexity: {arch_analysis['system_complexity']} | Security: {arch_analysis['security_posture']}")
            
            # Sample recommendations
            standard_count = len(universal_strategy['standard_tests'])
            recommended_count = len(universal_strategy['recommended_tests'])
            print(f"Generated: {standard_count} Standard + {recommended_count} Recommended tests")

if __name__ == "__main__":
    demo = ComprehensiveTestRecommendationDemo()
    
    # Main demonstration
    results = demo.demonstrate_complete_system()
    
    # Show domain adaptability
    demo.demonstrate_domain_adaptability()
    
    print(f"\n🎉 SYSTEM CAPABILITIES SUMMARY:")
    print("=" * 40)
    print("✅ Analyzes ANY BRD/User Stories content")
    print("✅ Identifies domain-specific requirements") 
    print("✅ Recognizes universal architectural patterns")
    print("✅ Categorizes as Standard vs Recommended")
    print("✅ Provides clear rationale and source attribution")
    print("✅ Works across all business domains")
    print("✅ Integrates multiple analysis approaches")
    
    print(f"\n🚀 Your robust recommendation engine is READY!")
    print("   Ready to handle subscription management and beyond!")