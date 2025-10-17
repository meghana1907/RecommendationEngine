#!/usr/bin/env python3
"""
Demo: Domain-Agnostic Test Strategy Architect

This script demonstrates how the universal test recommendation engine
analyzes requirements from ANY domain and generates testing strategies
based on architectural patterns rather than business domain specifics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.universal_test_architect import DomainAgnosticTestArchitect

def demo_subscription_management():
    """Demo with subscription management requirements"""
    
    print("🎯 DEMO: Domain-Agnostic Test Strategy Architect")
    print("=" * 60)
    
    # Your subscription management BRD + User Stories
    subscription_requirements = """
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
    
    # Initialize the domain-agnostic architect
    architect = DomainAgnosticTestArchitect()
    
    print("📋 ANALYZING REQUIREMENTS...")
    print("-" * 40)
    
    # Generate universal testing strategy
    strategy = architect.generate_universal_testing_strategy(subscription_requirements)
    
    # Display analysis results
    analysis = strategy['architecture_analysis']
    print(f"🏗️  ARCHITECTURAL PATTERNS IDENTIFIED:")
    for pattern_name, pattern_data in analysis['identified_patterns'][:5]:
        score = pattern_data['score']
        indicators = ', '.join(pattern_data['matched_indicators'][:3])
        print(f"   ✓ {pattern_name} (Score: {score}) - Indicators: {indicators}")
    
    print(f"\n📊 SYSTEM CHARACTERISTICS:")
    print(f"   • System Complexity: {analysis['system_complexity']}")
    print(f"   • Integration Complexity: {analysis['integration_complexity']}")  
    print(f"   • Security Posture: {analysis['security_posture']}")
    print(f"   • Quality Attributes: {', '.join(analysis['quality_attributes'][:4])}")
    
    # Generate and display the markdown report
    report = architect.generate_markdown_report(strategy)
    
    print("\n" + "=" * 60)
    print("📄 UNIVERSAL TESTING STRATEGY REPORT")
    print("=" * 60)
    print(report)
    
    # Show how the same engine works with different domains
    print("\n" + "🌐 DOMAIN ADAPTABILITY DEMONSTRATION" + "=" * 20)
    demo_other_domains(architect)

def demo_other_domains(architect):
    """Demonstrate the same engine working across different domains"""
    
    # E-commerce example
    ecommerce_requirements = """
    E-commerce Platform Requirements:
    - User registration and authentication with multiple roles (customer, admin, vendor)
    - Product catalog management with categories, pricing, and inventory
    - Shopping cart functionality with add, remove, update operations
    - Payment processing through multiple payment gateways (credit card, PayPal, digital wallets)
    - Order management with status tracking (pending, processing, shipped, delivered)
    - Integration with shipping providers for real-time rates and tracking
    - Customer review and rating system
    - Admin dashboard with sales analytics and reporting
    - Mobile responsive web interface
    - Email notifications for order confirmations and updates
    """
    
    # Healthcare example  
    healthcare_requirements = """
    Healthcare Management System Requirements:
    - Patient registration with personal and medical information
    - Appointment scheduling with doctor availability management
    - Electronic health records (EHR) with HIPAA compliance
    - Prescription management with drug interaction checks
    - Insurance verification and billing integration
    - Lab results integration with external laboratory systems
    - Secure messaging between patients and healthcare providers
    - Role-based access control (doctors, nurses, administrators, patients)
    - Audit trails for all patient data access and modifications
    - Mobile app for patient portal access
    - Integration with pharmacy systems for prescription fulfillment
    """
    
    domains = [
        ("E-commerce Platform", ecommerce_requirements),
        ("Healthcare Management", healthcare_requirements)
    ]
    
    for domain_name, requirements in domains:
        print(f"\n📱 {domain_name.upper()} ANALYSIS:")
        print("-" * 30)
        
        strategy = architect.generate_universal_testing_strategy(requirements)
        analysis = strategy['architecture_analysis']
        
        # Show top patterns identified
        print(f"Top Patterns: {', '.join([p[0] for p in analysis['identified_patterns'][:3]])}")
        print(f"Complexity: {analysis['system_complexity']} | Security: {analysis['security_posture']}")
        
        # Show key test recommendations  
        standard_tests = [test.test_type for test in strategy['standard_tests'][:3]]
        recommended_tests = [test.test_type for test in strategy['recommended_tests'][:3]]
        
        print(f"Standard Tests: {', '.join(standard_tests)}")
        print(f"Recommended Tests: {', '.join(recommended_tests)}")

def demo_pattern_universality():
    """Show how the same architectural patterns appear across domains"""
    
    print(f"\n🔬 UNIVERSAL PATTERN DEMONSTRATION")
    print("=" * 50)
    print("Same architectural patterns → Same test recommendations")
    print("(Regardless of business domain)")
    
    architect = DomainAgnosticTestArchitect()
    
    # Show how CRUD operations trigger the same tests everywhere
    examples = {
        "Financial Services": "Account creation, transaction processing, balance updates",
        "IoT Platform": "Device registration, sensor data collection, configuration management", 
        "HR System": "Employee onboarding, performance review management, payroll processing",
        "Subscription Management": "Subscription creation, charger association, payment processing"
    }
    
    print(f"\n📋 CRUD OPERATIONS PATTERN:")
    print("   Triggers → Functional Testing, Input Validation Testing")
    for domain, example in examples.items():
        print(f"   • {domain}: {example}")
    
    print(f"\n🔐 AUTHENTICATION & AUTHORIZATION PATTERN:")  
    print("   Triggers → Authentication Testing, Authorization Testing")
    for domain, _ in examples.items():
        print(f"   • {domain}: User roles, access control, session management")
    
    print(f"\n💰 FINANCIAL TRANSACTIONS PATTERN:")
    print("   Triggers → Security Testing, Audit Trail Testing")
    financial_examples = {
        "Banking": "Money transfers, loan processing",
        "E-commerce": "Payment processing, refunds", 
        "Subscription": "Billing, invoice generation",
        "Insurance": "Premium collection, claims"
    }
    for domain, example in financial_examples.items():
        print(f"   • {domain}: {example}")

if __name__ == "__main__":
    demo_subscription_management()
    demo_pattern_universality()
    
    print(f"\n🎉 CONCLUSION:")
    print("=" * 50)
    print("✅ The Domain-Agnostic Test Architect successfully:")
    print("   • Identifies universal architectural patterns")
    print("   • Generates testing strategies independent of business domain")  
    print("   • Provides rationale based on software engineering principles")
    print("   • Scales across Finance, Healthcare, IoT, E-commerce, and beyond")
    print(f"\n🚀 Ready for ANY domain requirements!")