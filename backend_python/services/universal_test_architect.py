"""
Domain-Agnostic Test Strategy Architect Implementation

This module implements a universal test recommendation engine that analyzes 
software requirements based on architectural patterns rather than domain content.
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class ArchitecturalPattern:
    """Represents a universal software architecture pattern"""
    pattern_name: str
    indicators: List[str]  # Keywords/phrases that indicate this pattern
    description: str
    quality_attributes: List[str]  # Security, Performance, etc.


@dataclass
class UniversalTestRecommendation:
    """Domain-agnostic test recommendation"""
    test_type: str
    category: str  # Standard or Recommended
    rationale: str  # Must be domain-agnostic
    focus_areas: List[str]
    triggered_by_patterns: List[str]
    quality_attributes: List[str]
    complexity_level: str  # Low, Medium, High
    business_impact: str  # Critical, High, Medium, Low


class DomainAgnosticTestArchitect:
    """
    Universal Test Strategy Architect that generates testing recommendations
    based on architectural patterns rather than domain-specific content.
    """
    
    def __init__(self):
        self.architectural_patterns = self._initialize_architectural_patterns()
        self.quality_attributes = self._initialize_quality_attributes()
        self.universal_test_catalog = self._initialize_universal_test_catalog()
    
    def _initialize_architectural_patterns(self) -> List[ArchitecturalPattern]:
        """Initialize universal architectural patterns found in software systems"""
        return [
            # Data Processing Patterns
            ArchitecturalPattern(
                pattern_name="CRUD Operations",
                indicators=["create", "update", "delete", "retrieve", "manage", "add", "edit", "remove"],
                description="Standard Create-Read-Update-Delete operations on business entities",
                quality_attributes=["Data Integrity", "Performance", "Usability"]
            ),
            
            ArchitecturalPattern(
                pattern_name="Workflow Management",
                indicators=["workflow", "process", "step", "stage", "approval", "review", "submit"],
                description="Multi-step business processes with state transitions",
                quality_attributes=["Reliability", "Auditability", "Performance"]
            ),
            
            ArchitecturalPattern(
                pattern_name="Data Validation Rules",
                indicators=["validate", "validation", "rule", "constraint", "requirement", "must", "cannot", "should"],
                description="Business rules and constraints that govern data integrity",
                quality_attributes=["Data Integrity", "Security", "Reliability"]
            ),
            
            # Security Patterns
            ArchitecturalPattern(
                pattern_name="Authentication & Authorization",
                indicators=["login", "auth", "user", "role", "permission", "access", "credential"],
                description="User identity verification and access control mechanisms",
                quality_attributes=["Security", "Compliance", "Auditability"]
            ),
            
            ArchitecturalPattern(
                pattern_name="Sensitive Data Handling",
                indicators=["payment", "financial", "personal", "confidential", "encrypted", "secure"],
                description="Processing and storage of sensitive or regulated data",
                quality_attributes=["Security", "Compliance", "Privacy"]
            ),
            
            # Integration Patterns  
            ArchitecturalPattern(
                pattern_name="External System Integration",
                indicators=["api", "service", "integration", "gateway", "external", "third-party"],
                description="Communication with external systems and services",
                quality_attributes=["Reliability", "Performance", "Interoperability"]
            ),
            
            ArchitecturalPattern(
                pattern_name="Real-time Communication",
                indicators=["notification", "email", "alert", "message", "real-time", "live"],
                description="Asynchronous messaging and notification systems",
                quality_attributes=["Reliability", "Performance", "Usability"]
            ),
            
            # User Interface Patterns
            ArchitecturalPattern(
                pattern_name="Multi-User System",
                indicators=["multiple", "concurrent", "simultaneous", "shared", "collaboration"],
                description="Systems supporting multiple concurrent users",
                quality_attributes=["Performance", "Scalability", "Concurrency"]
            ),
            
            ArchitecturalPattern(
                pattern_name="Web Portal Interface",
                indicators=["portal", "dashboard", "interface", "web", "browser", "ui"],
                description="Web-based user interfaces and dashboards",
                quality_attributes=["Usability", "Accessibility", "Performance"]
            ),
            
            # Business Logic Patterns
            ArchitecturalPattern(
                pattern_name="Financial Transactions",
                indicators=["payment", "billing", "invoice", "transaction", "amount", "cost"],
                description="Financial processing and transaction management",
                quality_attributes=["Security", "Compliance", "Auditability", "Data Integrity"]
            ),
            
            ArchitecturalPattern(
                pattern_name="Status Management",
                indicators=["status", "state", "pending", "active", "complete", "cancelled"],
                description="Entity lifecycle and state management systems",
                quality_attributes=["Data Integrity", "Reliability", "Auditability"]
            )
        ]
    
    def _initialize_quality_attributes(self) -> Dict[str, List[str]]:
        """Initialize quality attribute categories"""
        return {
            "Security": ["authentication", "authorization", "encryption", "access control", "data protection"],
            "Performance": ["response time", "throughput", "scalability", "load handling", "resource usage"],
            "Reliability": ["error handling", "fault tolerance", "data consistency", "backup", "recovery"],
            "Usability": ["user experience", "accessibility", "interface design", "user workflows"],
            "Compliance": ["audit trails", "regulatory requirements", "data privacy", "standards compliance"],
            "Data Integrity": ["validation", "constraints", "consistency", "accuracy", "completeness"],
            "Auditability": ["logging", "tracking", "history", "traceability", "accountability"],
            "Interoperability": ["integration", "data exchange", "protocol compliance", "standards"]
        }
    
    def _initialize_universal_test_catalog(self) -> Dict[str, Dict]:
        """Initialize catalog of universal test types mapped to architectural patterns"""
        return {
            "Functional Testing": {
                "category": "Standard",
                "triggered_by": ["CRUD Operations", "Workflow Management", "Data Validation Rules"],
                "description": "Validate core business functionality and user workflows",
                "rationale_template": "Required for any system with {patterns} to ensure correct functionality"
            },
            
            "Authentication Testing": {
                "category": "Standard", 
                "triggered_by": ["Authentication & Authorization"],
                "description": "Verify user login, logout, and session management",
                "rationale_template": "Essential for any system requiring user authentication and access control"
            },
            
            "Authorization Testing": {
                "category": "Standard",
                "triggered_by": ["Authentication & Authorization", "Multi-User System"],
                "description": "Validate role-based permissions and access restrictions", 
                "rationale_template": "Critical for multi-user systems with role-based access control mechanisms"
            },
            
            "Input Validation Testing": {
                "category": "Standard",
                "triggered_by": ["Data Validation Rules", "CRUD Operations"],
                "description": "Test data validation rules and input constraints",
                "rationale_template": "Mandatory for any system with data input and business rule validation"
            },
            
            "Integration Testing": {
                "category": "Standard",
                "triggered_by": ["External System Integration", "Real-time Communication"],
                "description": "Verify communication with external systems and services",
                "rationale_template": "Required for systems with external dependencies and third-party integrations"
            },
            
            "UI/UX Testing": {
                "category": "Standard",
                "triggered_by": ["Web Portal Interface"],
                "description": "Validate user interface functionality and user experience",
                "rationale_template": "Essential for any system with web-based user interfaces"
            },
            
            "Negative Testing": {
                "category": "Recommended",
                "triggered_by": ["Data Validation Rules", "Authentication & Authorization"],
                "description": "Test system behavior with invalid inputs and unauthorized actions",
                "rationale_template": "Critical for enforcing business rules and security constraints"
            },
            
            "Security Testing": {
                "category": "Recommended",
                "triggered_by": ["Sensitive Data Handling", "Financial Transactions"],
                "description": "Validate data protection, encryption, and security controls",
                "rationale_template": "Required for any system handling sensitive data or financial transactions"
            },
            
            "Performance Testing": {
                "category": "Recommended",
                "triggered_by": ["Multi-User System", "External System Integration"],
                "description": "Test system performance under load and stress conditions",
                "rationale_template": "Important for systems with concurrent users or high-volume operations"
            },
            
            "Concurrency Testing": {
                "category": "Recommended", 
                "triggered_by": ["Multi-User System", "Status Management"],
                "description": "Test concurrent access to shared resources and data",
                "rationale_template": "Critical for multi-user systems with shared data and state management"
            },
            
            "Audit Trail Testing": {
                "category": "Recommended",
                "triggered_by": ["Financial Transactions", "Status Management", "Sensitive Data Handling"],
                "description": "Verify logging and traceability of system actions",
                "rationale_template": "Essential for systems requiring compliance and audit accountability"
            },
            
            "API Testing": {
                "category": "Recommended",
                "triggered_by": ["External System Integration"],
                "description": "Test API endpoints, data formats, and error handling",
                "rationale_template": "Required for systems with RESTful APIs or web services"
            },
            
            "Accessibility Testing": {
                "category": "Recommended",
                "triggered_by": ["Web Portal Interface"],
                "description": "Verify compliance with accessibility standards (WCAG)",
                "rationale_template": "Important for web applications to ensure inclusive user access"
            },
            
            "Data Migration Testing": {
                "category": "Recommended",
                "triggered_by": ["External System Integration", "CRUD Operations"],
                "description": "Test data import, export, and migration processes",
                "rationale_template": "Required for systems with data integration or migration requirements"
            },
            
            "Backup and Recovery Testing": {
                "category": "Recommended",
                "triggered_by": ["Financial Transactions", "Sensitive Data Handling"],
                "description": "Verify data backup and disaster recovery procedures",
                "rationale_template": "Critical for systems with important business data and continuity requirements"
            }
        }
    
    def analyze_requirements(self, requirements_text: str) -> Dict[str, Any]:
        """
        Analyze requirements text to identify universal architectural patterns
        """
        text_lower = requirements_text.lower()
        
        # Identify architectural patterns
        identified_patterns = []
        pattern_scores = {}
        
        for pattern in self.architectural_patterns:
            score = 0
            matched_indicators = []
            
            for indicator in pattern.indicators:
                if indicator.lower() in text_lower:
                    score += 1
                    matched_indicators.append(indicator)
            
            if score > 0:
                pattern_scores[pattern.pattern_name] = {
                    'score': score,
                    'pattern': pattern,
                    'matched_indicators': matched_indicators
                }
        
        # Sort patterns by relevance
        identified_patterns = sorted(pattern_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # Analyze system characteristics
        system_complexity = self._assess_system_complexity(identified_patterns)
        integration_complexity = self._assess_integration_complexity(text_lower)
        security_posture = self._assess_security_posture(text_lower)
        
        return {
            'identified_patterns': identified_patterns,
            'system_complexity': system_complexity,
            'integration_complexity': integration_complexity,
            'security_posture': security_posture,
            'quality_attributes': self._extract_quality_attributes(text_lower)
        }
    
    def generate_universal_testing_strategy(self, requirements_text: str) -> Dict[str, Any]:
        """
        Generate domain-agnostic testing strategy based on architectural analysis
        """
        analysis = self.analyze_requirements(requirements_text)
        
        # Generate test recommendations
        standard_tests = []
        recommended_tests = []
        
        identified_pattern_names = [pattern[0] for pattern in analysis['identified_patterns']]
        
        for test_type, test_config in self.universal_test_catalog.items():
            # Check if this test type is triggered by identified patterns
            if any(trigger in identified_pattern_names for trigger in test_config['triggered_by']):
                
                # Generate rationale based on identified patterns
                relevant_patterns = [p for p in test_config['triggered_by'] if p in identified_pattern_names]
                rationale = test_config['rationale_template'].format(
                    patterns=', '.join(relevant_patterns[:2])  # Limit to 2 patterns for readability
                )
                
                test_recommendation = UniversalTestRecommendation(
                    test_type=test_type,
                    category=test_config['category'],
                    rationale=rationale,
                    focus_areas=[test_config['description']],
                    triggered_by_patterns=relevant_patterns,
                    quality_attributes=self._get_quality_attributes_for_patterns(relevant_patterns),
                    complexity_level=self._determine_test_complexity(relevant_patterns),
                    business_impact=self._determine_business_impact(test_config['category'], relevant_patterns)
                )
                
                if test_config['category'] == 'Standard':
                    standard_tests.append(test_recommendation)
                else:
                    recommended_tests.append(test_recommendation)
        
        # Generate comprehensive report
        return {
            'architecture_analysis': analysis,
            'standard_tests': standard_tests,
            'recommended_tests': recommended_tests,
            'testing_strategy_summary': self._generate_strategy_summary(analysis, standard_tests, recommended_tests)
        }
    
    def _assess_system_complexity(self, patterns: List) -> str:
        """Assess overall system complexity based on identified patterns"""
        pattern_count = len(patterns)
        if pattern_count >= 8:
            return "High"
        elif pattern_count >= 5:
            return "Medium" 
        else:
            return "Low"
    
    def _assess_integration_complexity(self, text: str) -> str:
        """Assess integration complexity based on external system indicators"""
        integration_keywords = ['api', 'gateway', 'service', 'external', 'third-party', 'integration']
        count = sum(1 for keyword in integration_keywords if keyword in text)
        
        if count >= 4:
            return "Complex"
        elif count >= 2:
            return "Moderate"
        else:
            return "Simple"
    
    def _assess_security_posture(self, text: str) -> str:
        """Assess security requirements based on data sensitivity indicators"""
        security_keywords = ['financial', 'payment', 'sensitive', 'personal', 'confidential', 'secure', 'encrypted']
        compliance_keywords = ['audit', 'compliance', 'regulation', 'standard']
        
        security_count = sum(1 for keyword in security_keywords if keyword in text)
        compliance_count = sum(1 for keyword in compliance_keywords if keyword in text)
        
        if security_count >= 3 or compliance_count >= 2:
            return "Critical"
        elif security_count >= 2 or compliance_count >= 1:
            return "Enhanced"
        else:
            return "Basic"
    
    def _extract_quality_attributes(self, text: str) -> List[str]:
        """Extract relevant quality attributes from requirements"""
        found_attributes = []
        for attribute, keywords in self.quality_attributes.items():
            if any(keyword in text for keyword in keywords):
                found_attributes.append(attribute)
        return found_attributes
    
    def _get_quality_attributes_for_patterns(self, patterns: List[str]) -> List[str]:
        """Get quality attributes associated with architectural patterns"""
        attributes = set()
        for pattern_name in patterns:
            for pattern in self.architectural_patterns:
                if pattern.pattern_name == pattern_name:
                    attributes.update(pattern.quality_attributes)
        return list(attributes)
    
    def _determine_test_complexity(self, patterns: List[str]) -> str:
        """Determine test complexity based on patterns involved"""
        complex_patterns = ['External System Integration', 'Financial Transactions', 'Multi-User System']
        if any(pattern in complex_patterns for pattern in patterns):
            return "High"
        elif len(patterns) >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _determine_business_impact(self, category: str, patterns: List[str]) -> str:
        """Determine business impact based on test category and patterns"""
        critical_patterns = ['Financial Transactions', 'Sensitive Data Handling', 'Authentication & Authorization']
        
        if category == 'Standard':
            return "Critical" if any(pattern in critical_patterns for pattern in patterns) else "High"
        else:
            return "High" if any(pattern in critical_patterns for pattern in patterns) else "Medium"
    
    def _generate_strategy_summary(self, analysis: Dict, standard_tests: List, recommended_tests: List) -> Dict[str, Any]:
        """Generate executive summary of testing strategy"""
        return {
            'total_test_types': len(standard_tests) + len(recommended_tests),
            'standard_test_count': len(standard_tests),
            'recommended_test_count': len(recommended_tests),
            'primary_patterns': [p[0] for p in analysis['identified_patterns'][:3]],
            'system_complexity': analysis['system_complexity'],
            'integration_complexity': analysis['integration_complexity'], 
            'security_posture': analysis['security_posture'],
            'quality_focus_areas': analysis['quality_attributes'][:5]
        }
    
    def generate_markdown_report(self, strategy: Dict[str, Any]) -> str:
        """Generate formatted markdown report"""
        analysis = strategy['architecture_analysis']
        standard_tests = strategy['standard_tests']
        recommended_tests = strategy['recommended_tests']
        summary = strategy['testing_strategy_summary']
        
        report = f"""# Universal Testing Strategy Report

## System Architecture Analysis
- **Primary Patterns Identified**: {', '.join(summary['primary_patterns'])}
- **Integration Complexity**: {summary['integration_complexity']} (based on external dependencies)
- **Security Posture**: {summary['security_posture']} (based on data sensitivity)
- **System Complexity**: {summary['system_complexity']} (based on architectural patterns)

## Testing Strategy Matrix

| Testing Type | Category | Rationale & Focus Areas (Generalized Requirements) |
|--------------|----------|---------------------------------------------------|
"""
        
        # Add standard tests
        for test in standard_tests:
            report += f"| {test.test_type} | {test.category} | {test.rationale} |\n"
        
        # Add recommended tests
        for test in recommended_tests:
            report += f"| {test.test_type} | {test.category} | {test.rationale} |\n"
        
        report += f"""
## Risk-Based Testing Priorities
1. **Critical Path**: Core business workflows identified in primary patterns
2. **Security Vectors**: Authentication, data protection, and access control points
3. **Integration Points**: External dependencies and failure scenarios  
4. **Performance Bottlenecks**: High-volume operations and resource constraints

## Execution Recommendations
- **MVP Testing Focus**: {summary['standard_test_count']} Standard tests covering core functionality
- **Post-MVP Enhancements**: {summary['recommended_test_count']} Recommended tests for production readiness
- **Quality Focus Areas**: {', '.join(summary['quality_focus_areas'])}

## Architecture Pattern Summary
"""
        
        for pattern_name, pattern_data in analysis['identified_patterns'][:5]:
            pattern = pattern_data['pattern']
            report += f"- **{pattern_name}**: {pattern.description}\n"
        
        return report