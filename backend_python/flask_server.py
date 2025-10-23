"""
Simple Test Server for Intelligent Test Generation

This creates a minimal server to test the intelligent test generation
without the full FastAPI complexity.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.universal_test_architect import DomainAgnosticTestArchitect
from services.domain_aware_test_engine import DomainAwareTestEngine

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Initialize the intelligent engines
universal_architect = DomainAgnosticTestArchitect()
domain_engine = DomainAwareTestEngine()

# Simple storage for uploaded documents (for testing)
document_storage = {}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Intelligent Test Recommendation Engine is running",
        "version": "2.0 - AI Enhanced"
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        "status": "healthy",
        "engines": {
            "universal_architect": "ready",
            "domain_aware_engine": "ready"
        }
    })

@app.route('/api/documents/upload-text', methods=['POST'])
def upload_text():
    """Simple text upload endpoint for testing"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        document_id = f"doc_{len(document_storage) + 1}"
        
        document_storage[document_id] = {
            'raw_content': content,
            'filename': data.get('filename', f'document_{document_id}.txt')
        }
        
        return jsonify({
            "success": True,
            "document_id": document_id,
            "message": "Document uploaded successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tests/generate-intelligent', methods=['POST'])
def generate_intelligent_tests():
    """Generate intelligent test recommendations using domain-aware and universal analysis"""
    try:
        data = request.get_json()
        brd_document_id = data.get('brd_document_id')
        user_stories_document_id = data.get('user_stories_document_id')
        
        print(f"🧠 Starting INTELLIGENT test generation for BRD: {brd_document_id}, User Stories: {user_stories_document_id}")
        
        # For testing purposes, use sample subscription management content if documents not found
        if brd_document_id not in document_storage or user_stories_document_id not in document_storage:
            combined_content = """
            Business Requirements Document (BRD) - Module: Subscription Management
            
            The Subscription Module is designed for Charge Network Operators (CNOs) to manage and 
            administer annual subscriptions for Charge Station Operators (CSOs).

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
            - Security: All organizational, payment, and contact data must be securely handled
            - Auditability: Every action must be logged for traceability and compliance
            - Performance: Invoice generation and payment updates should reflect in real time
            
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
        else:
            brd_doc = document_storage[brd_document_id]
            user_stories_doc = document_storage[user_stories_document_id]
            combined_content = f"{brd_doc['raw_content']}\n\n{user_stories_doc['raw_content']}"
        
        print(f"📄 Processing combined content with intelligent engines: {len(combined_content)} characters")
        
        # STEP 1: Universal Architecture Analysis
        print("🏗️ Step 1: Universal Architecture Analysis")
        universal_strategy = universal_architect.generate_universal_testing_strategy(combined_content)
        arch_analysis = universal_strategy['architecture_analysis']
        
        # STEP 2: Domain-Aware Analysis (using simulated clusters)
        print("🧠 Step 2: Domain-Aware Content Analysis")
        
        # Create simulated clusters for domain analysis
        clusters_data = [
            {
                'cluster_id': 1,
                'cluster_name': 'Business Rules & Validation',
                'content_chunks': [
                    'BR-01: A charger cannot be associated with more than one Active or Pending subscription',
                    'BR-02: Only Operational chargers can be included (Decommissioned/Uncommissioned excluded)',
                    'BR-03: Subscription submission requires a valid reseller and billing contact',
                    'BR-04: Amount field is system-calculated and not user-editable'
                ]
            },
            {
                'cluster_id': 2,
                'cluster_name': 'User Workflows & Operations',
                'content_chunks': [
                    'CNO can log in and access Subscription Management',
                    'System filters Organization Selection to only CSO types',
                    'CNO can select specific chargers to include in the subscription',
                    'CNO can set the subscription Term and manually input Total Ports count'
                ]
            },
            {
                'cluster_id': 3,
                'cluster_name': 'Payment & Financial Processing',
                'content_chunks': [
                    'Amount field is auto-calculated and read-only',
                    'System auto-generates an invoice upon submission',
                    'Status updates automatically to Paid upon payment receipt',
                    'Invoice generation and payment updates should reflect in real time'
                ]
            }
        ]
        
        # Analyze clusters with domain-aware engine
        cluster_analyses = domain_engine.analyze_clusters(clusters_data)
        domain_standard_tests, domain_recommended_tests = domain_engine.generate_recommendations(cluster_analyses)
        
        # STEP 3: Integrate Results
        print("🔀 Step 3: Intelligent Integration")
        
        # Combine and categorize tests
        all_tests = []
        
        # Add universal architecture tests
        for test in universal_strategy['standard_tests']:
            all_tests.append({
                'name': test.test_type,
                'test_type': test.test_type,
                'category': 'Standard',
                'priority': 'High',
                'rationale': test.rationale,
                'source': 'Universal Architecture',
                'business_impact': test.business_impact,
                'focus_areas': test.focus_areas,
                'cluster_attribution': 'Architecture Pattern Analysis',
                'effort_estimate': '2-4 hours' if test.complexity_level == 'Low' else '1-2 days'
            })
        
        for test in universal_strategy['recommended_tests']:
            all_tests.append({
                'name': test.test_type,
                'test_type': test.test_type,
                'category': 'Recommended',
                'priority': 'Medium',
                'rationale': test.rationale,
                'source': 'Universal Architecture',
                'business_impact': test.business_impact,
                'focus_areas': test.focus_areas,
                'cluster_attribution': 'Architecture Pattern Analysis',
                'effort_estimate': '3-5 days' if test.complexity_level == 'High' else '1-3 days'
            })
        
        # Format domain-aware tests
        domain_formatted = domain_engine.format_recommendations(domain_standard_tests, domain_recommended_tests)
        
        # Add domain-aware tests
        for test in domain_formatted['standard_testing_types']['tests']:
            # Check if already exists from universal analysis
            existing = next((t for t in all_tests if t['test_type'] == test['test_name']), None)
            if existing:
                existing['source'] += ' + Domain Analysis'
                existing['category'] = 'Standard'  # Upgrade to standard if both agree
            else:
                all_tests.append({
                    'name': test['test_name'],
                    'test_type': test['test_name'],
                    'category': 'Standard',
                    'priority': test['priority'].title(),
                    'rationale': test['rationale'],
                    'source': 'Domain Analysis',
                    'business_impact': 'High',
                    'focus_areas': [test['test_category']],
                    'cluster_attribution': f"Domain Content: {', '.join(test['source_clusters'])}",
                    'effort_estimate': test['estimated_effort']
                })
        
        for test in domain_formatted['recommended_testing_types']['tests']:
            existing = next((t for t in all_tests if t['test_type'] == test['test_name']), None)
            if existing:
                existing['source'] += ' + Domain Analysis'
            else:
                all_tests.append({
                    'name': test['test_name'],
                    'test_type': test['test_name'],
                    'category': 'Recommended',
                    'priority': test['priority'].title(),
                    'rationale': test['rationale'],
                    'source': 'Domain Analysis',
                    'business_impact': 'Medium',
                    'focus_areas': [test['test_category']],
                    'cluster_attribution': f"Domain Content: {', '.join(test['source_clusters'])}",
                    'effort_estimate': test['estimated_effort']
                })
        
        # Calculate metrics
        standard_tests = [t for t in all_tests if t['category'] == 'Standard']
        recommended_tests = [t for t in all_tests if t['category'] == 'Recommended']
        multi_source_tests = [t for t in all_tests if '+' in t['source']]
        
        confidence_score = round((len(multi_source_tests) / len(all_tests)) * 100, 1) if all_tests else 0
        
        print(f"✅ Intelligent analysis complete: {len(standard_tests)} Standard + {len(recommended_tests)} Recommended tests")
        
        return jsonify({
            "success": True,
            "message": f"Generated {len(all_tests)} intelligent test recommendations with {confidence_score}% confidence",
            "recommendations": all_tests,
            "processing_details": {
                "brd_document_id": brd_document_id,
                "user_stories_document_id": user_stories_document_id,
                "analysis_method": "Domain-Aware + Universal Architecture Analysis",
                "standard_tests": len(standard_tests),
                "recommended_tests": len(recommended_tests),
                "confidence_score": confidence_score,
                "architectural_patterns": len(arch_analysis['identified_patterns']),
                "system_complexity": arch_analysis['system_complexity'],
                "security_posture": arch_analysis['security_posture'],
                "multi_source_validation": len(multi_source_tests)
            }
        })
        
    except Exception as e:
        print(f"❌ Intelligent test generation failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Intelligent test generation failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Intelligent Test Recommendation Engine (Flask)")
    print("🧠 Domain-Aware + Universal Architecture Analysis Ready")
    app.run(host='0.0.0.0', port=8000, debug=True)