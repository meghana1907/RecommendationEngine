"""
Unified Domain-Aware Test Recommendation Engine

This comprehensive engine analyzes BRD and User Stories content to generate:
1. Domain-specific test recommendations (EV Charging, IoT, FinTech, Healthcare, etc.)
2. Standard Testing Types (Must-haves for MVP/UAT) 
3. Recommended Testing Types (Advanced/Post-MVP)
4. Clear cluster attribution showing which content drove each recommendation
5. Contextual rationales based on actual business requirements
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class DomainType(Enum):
    EV_CHARGING = "ev_charging"
    IOT_SMART_HOME = "iot_smart_home"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "ecommerce"
    BUSINESS_MANAGEMENT = "business_management"
    GENERIC = "generic"


class TestCategory(Enum):
    STANDARD = "standard"
    RECOMMENDED = "recommended"


class TestType(Enum):
    # Standard Testing Types
    SMOKE = "smoke"
    FUNCTIONAL = "functional"
    ROLE_ACCESS = "role_access"
    API_FUNCTIONAL = "api_functional"
    UI_REGRESSION = "ui_regression"
    PAYMENT_WORKFLOW = "payment_workflow"
    SESSION_MANAGEMENT = "session_management"
    CONNECTIVITY = "connectivity"
    BROWSER_COMPATIBILITY = "browser_compatibility"
    ERROR_HANDLING = "error_handling"
    MOBILE_RESPONSIVE = "mobile_responsive"
    ANALYTICS = "analytics"
    INPUT_VALIDATION = "input_validation"
    
    # Recommended Testing Types
    CHAOS = "chaos"
    INTEROPERABILITY = "interoperability"
    USABILITY = "usability"
    API_CONTRACT = "api_contract"
    AI_VISUAL_REGRESSION = "ai_visual_regression"
    PAYMENT_SECURITY = "payment_security"
    CONCURRENCY = "concurrency"
    REAL_TIME_EVENT = "real_time_event"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"
    PWA = "pwa"
    PREDICTIVE_ANALYTICS = "predictive_analytics"


@dataclass
class DomainPattern:
    keywords: List[str]
    business_entities: List[str]
    processes: List[str]
    test_types: Dict[str, List[str]]  # standard vs recommended
    risk_areas: List[str]
    test_templates: List[Dict] = None  # Test templates for this domain
    
    def __post_init__(self):
        if self.test_templates is None:
            self.test_templates = []


@dataclass
class TestRecommendation:
    test_name: str
    test_description: str
    test_type: TestType
    category: TestCategory
    priority: str
    estimated_effort: str
    rationale: str  # Why this test is recommended based on content
    source_clusters: List[int]  # Which clusters contributed to this recommendation
    source_content: List[str]  # Specific content that triggered this recommendation
    business_impact: str = "Medium"
    focus_areas: List[str] = None
    domain_context: str = "generic"
    technical_requirements: List[str] = None
    source_story: str = None  # Which user story this test is based on
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = []
        if self.technical_requirements is None:
            self.technical_requirements = []


@dataclass
class ClusterAnalysis:
    cluster_id: int
    content_chunks: List[str]
    domain_elements: Dict[str, List[str]]  # business_rules, workflows, entities, etc.
    functional_areas: List[str]
    technical_components: List[str]
    risk_areas: List[str]
    representative_text: str


class DomainAwareTestEngine:
    def __init__(self, embedding_service=None):
        # Initialize domain-specific patterns
        self.domain_patterns = self._initialize_domain_patterns()
        
        # Store embedding service for semantic attribution (optional)
        self.embedding_service = embedding_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize hybrid recommender for advanced AI recommendations (lazy loading)
        self.hybrid_recommender = None
        self._hybrid_recommender_attempted = False
        
        # Generic patterns for extracting domain-agnostic information
        self.identifier_patterns = [
            r'[A-Z]{2,}-\d+',  # Generic pattern like XX-123, YY-456, etc.
            r'[A-Z][a-z]+ Story \d+',  # User Story 123, etc.
            r'[A-Z][a-z]+ Rule \d+',  # Business Rule 123, etc.
            r'Story-\d+',
            r'Rule-\d+',
            r'REQ-\d+',
            r'TC-\d+',
            r'ID-\d+'
        ]
        
        # Business rule indicators (not hardcoded rules)
        self.business_rule_indicators = [
            r'cannot be|must be|shall be|should be',
            r'is required|is mandatory|is optional',
            r'if\s+.*\s+then|when\s+.*\s+then',
            r'rule|policy|constraint|restriction',
            r'validation|requirement|condition'
        ]
        
        # Workflow and process indicators
        self.workflow_indicators = [
            r'workflow|process|step|stage|phase',
            r'approval|review|submit|validate',
            r'status|state|condition|trigger',
            r'sequence|order|priority|queue'
        ]
        
        # Technical component indicators  
        self.technical_indicators = [
            r'api|endpoint|service|microservice',
            r'database|storage|repository|cache',
            r'server|client|browser|mobile',
            r'integration|connector|adapter|gateway'
        ]
        
        # Security aspect indicators
        self.security_indicators = [
            r'authentication|authorization|access control',
            r'encryption|security|ssl|tls|https',
            r'permission|role|privilege|credential',
            r'audit|compliance|governance|policy'
        ]
        
        # Financial aspect indicators
        self.financial_indicators = [
            r'payment|billing|invoice|transaction',
            r'fee|cost|price|rate|tariff',
            r'subscription|purchase|order|revenue',
            r'financial|monetary|currency|amount'
        ]
        
        # Process workflow indicators
        self.process_indicators = [
            r'create|update|delete|modify|manage',
            r'generate|calculate|process|validate',
            r'send|receive|notify|alert|communicate',
            r'schedule|trigger|execute|complete'
        ]
        
    def _get_hybrid_recommender(self):
        """Lazy load hybrid recommender only when needed"""
        if self.hybrid_recommender is not None:
            return self.hybrid_recommender
            
        if self._hybrid_recommender_attempted:
            return None
            
        self._hybrid_recommender_attempted = True
        
        try:
            from .hybrid_test_recommender import HybridTestRecommender
            self.hybrid_recommender = HybridTestRecommender()
            self.logger.info("HybridTestRecommender initialized successfully")
            return self.hybrid_recommender
        except ImportError as e:
            self.logger.warning(f"HybridTestRecommender not available: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to initialize HybridTestRecommender: {e}")
            return None
    
    def _extract_story_references_from_content(self, content_chunks: List[str]) -> List[str]:
        """Extract user story references (ZB-X, Story-X, etc.) and BRD references from content chunks"""
        story_references = set()
        
        for chunk in content_chunks:
            # Look for common story ID patterns
            patterns = [
                r'\b(ZB-\d+)\b',      # ZB-1, ZB-2, etc.
                r'\b(Story-\d+)\b',   # Story-1, Story-2, etc.
                r'\b(US-\d+)\b',      # US-1, US-2, etc.
                r'\b(REQ-\d+)\b',     # REQ-1, REQ-2, etc.
                r'\b(BRD[_\-\s]*\d+)\b',  # BRD-1, BRD_1, BRD 1, etc.
                r'\b(BR[_\-\s]*\d+)\b',   # BR-1, BR_1, BR 1, etc.
                r'\b(Story[_\-\s]*story[_\-\s]*\d+)\b',  # Story_story_1, Story-story-2, etc.
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                # Clean up matches (remove spaces, normalize separators)
                for match in matches:
                    cleaned_match = re.sub(r'[_\s]+', '-', match.strip()).upper()
                    
                    # Filter out date patterns and other non-reference patterns
                    date_patterns = [
                        r'^(?:OCT|NOV|DEC|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP)-\d{4}$',
                        r'^(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)-\d{4}$',
                        r'^DATE-\d{4}$',
                        r'^TIME-\d{4}$',
                        r'^YEAR-\d{4}$'
                    ]
                    
                    is_date_pattern = any(re.match(date_pat, cleaned_match) for date_pat in date_patterns)
                    if not is_date_pattern:
                        story_references.add(cleaned_match)
            
            # Also look for contextual references like "As mentioned in BRD section X"
            contextual_patterns = [
                r'(?:in|from|per|according to)\s+(?:the\s+)?(?:BRD|Business Requirements?|User Stories?)[^.]*?(\w+[_\-\s]*\d+)',
                r'(?:requirement|story|section)\s+([A-Z]{1,3}[_\-\s]*\d+)',
                r'(?:As\s+(?:a|an)\s+\w+,?\s+I\s+want).*?(\w{2,3}[_\-]*\d+)',  # "As a user, I want... ZB-1"
            ]
            
            for pattern in contextual_patterns:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                for match in matches:
                    cleaned_match = re.sub(r'[_\s]+', '-', match.strip()).upper()
                    # Only add if it looks like a proper reference and is not a date
                    if re.match(r'\w{2,3}-\d+', cleaned_match):
                        date_patterns = [
                            r'^(?:OCT|NOV|DEC|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP)-\d{4}$',
                            r'^(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)-\d{4}$'
                        ]
                        is_date_pattern = any(re.match(date_pat, cleaned_match) for date_pat in date_patterns)
                        if not is_date_pattern:
                            story_references.add(cleaned_match)
        
        return sorted(list(story_references))

    def _find_triggering_stories_for_test(self, template: Dict, cluster_analysis: 'ClusterAnalysis') -> tuple[List[str], List[str]]:
        """
        Find SPECIFIC stories that triggered this specific test based on keyword and semantic matching.
        Returns: (story_references, relevant_content_chunks)
        """
        if not cluster_analysis or not cluster_analysis.content_chunks:
            return [], []
        
        # Extract key concepts from the test template
        test_keywords = self._extract_test_keywords(template)
        
        triggering_stories = []
        relevant_chunks = []
        
        # Process the content to split it into individual story chunks
        individual_story_chunks = self._split_content_into_story_chunks(cluster_analysis.content_chunks)
        
        for story_chunk in individual_story_chunks:
            chunk_lower = story_chunk.lower()
            
            # Extract story references from this specific chunk
            chunk_stories = self._extract_story_references_from_content([story_chunk])
            
            if not chunk_stories:
                continue
                
            # Check if this chunk contains content that would trigger this specific test
            relevance_score = self._calculate_chunk_test_relevance(chunk_lower, test_keywords, template)
            
            # Only include stories from chunks that are actually relevant to this test
            if relevance_score > 0.3:  # Threshold for relevance
                triggering_stories.extend(chunk_stories)
                relevant_chunks.append(story_chunk[:200] + "..." if len(story_chunk) > 200 else story_chunk)
                
                # Log the matching for debugging
                self.logger.debug(f"Test '{template['name']}' triggered by chunk with stories {chunk_stories} (score: {relevance_score:.2f})")
        
        # Remove duplicates while preserving order
        unique_triggering_stories = []
        seen = set()
        for story in triggering_stories:
            if story not in seen:
                unique_triggering_stories.append(story)
                seen.add(story)
        
        return unique_triggering_stories, relevant_chunks

    def _split_content_into_story_chunks(self, content_chunks: List[str]) -> List[str]:
        """
        Split content chunks into individual story-based chunks.
        Each returned chunk should contain content for one specific story/requirement.
        """
        individual_chunks = []
        
        for chunk in content_chunks:
            # Split on story/requirement boundaries
            # Look for patterns like "ZB-1:", "BRD-1:", etc.
            story_pattern = r'(\b(?:ZB|Story|US|REQ|BRD|BR)-\d+:)'
            
            # Split the chunk by story patterns
            parts = re.split(story_pattern, chunk, flags=re.IGNORECASE)
            
            if len(parts) <= 1:
                # No story patterns found, treat as single chunk
                if chunk.strip():
                    individual_chunks.append(chunk.strip())
            else:
                current_story_content = ""
                current_story_id = ""
                
                for i, part in enumerate(parts):
                    part = part.strip()
                    if not part:
                        continue
                        
                    # Check if this part is a story identifier
                    if re.match(r'\b(?:ZB|Story|US|REQ|BRD|BR)-\d+:', part, re.IGNORECASE):
                        # Save previous story content if exists
                        if current_story_content and current_story_id:
                            individual_chunks.append(f"{current_story_id} {current_story_content}".strip())
                        
                        # Start new story
                        current_story_id = part
                        current_story_content = ""
                    else:
                        # This is content for the current story
                        current_story_content += " " + part
                
                # Add the last story
                if current_story_content and current_story_id:
                    individual_chunks.append(f"{current_story_id} {current_story_content}".strip())
        
        return individual_chunks

    def _extract_test_keywords(self, template: Dict) -> List[str]:
        """Extract specific keywords that should trigger this test type"""
        test_name = template['name'].lower()
        test_type = template.get('type', '').lower() if hasattr(template.get('type', ''), 'lower') else str(template.get('type', '')).lower()
        
        # Define keyword mappings for different test types
        keyword_mappings = {
            'role-based access': ['login', 'authentication', 'auth', 'user', 'role', 'permission', 'access', 'signin', 'sign-in', 'credential'],
            'functional': ['create', 'update', 'delete', 'edit', 'modify', 'add', 'remove', 'manage', 'crud', 'operation'],
            'api functional': ['api', 'endpoint', 'service', 'backend', 'server', 'rest', 'json', 'request', 'response'],
            'ui regression': ['interface', 'ui', 'view', 'screen', 'page', 'display', 'render', 'visual', 'layout', 'component'],
            'session management': ['session', 'logout', 'timeout', 'expire', 'token', 'cookie', 'state'],
            'browser compatibility': ['browser', 'chrome', 'firefox', 'edge', 'safari', 'compatibility', 'cross-browser'],
            'usability': ['user experience', 'ux', 'ease', 'intuitive', 'friendly', 'navigation', 'workflow'],
            'concurrency': ['concurrent', 'multiple', 'simultaneous', 'parallel', 'many users', 'load'],
            'input validation': ['validation', 'input', 'field', 'form', 'required', 'constraint', 'limit', 'validate'],
            'predictive analytics': ['analytics', 'data', 'report', 'insight', 'forecast', 'prediction', 'intelligence'],
            'mobile responsiveness': ['mobile', 'responsive', 'tablet', 'phone', 'device', 'screen size'],
            'payment security': ['payment', 'billing', 'transaction', 'financial', 'money', 'cost', 'price', 'pay'],
            'device configuration': ['configuration', 'config', 'setup', 'setting', 'parameter', 'threshold'],
            'site management': ['site', 'location', 'management', 'admin', 'portal', 'manage']
        }
        
        # Get keywords for this specific test
        for test_pattern, keywords in keyword_mappings.items():
            if test_pattern in test_name:
                return keywords
        
        # Fallback: extract keywords from test name and type
        fallback_keywords = []
        
        # Split test name into meaningful words
        name_words = test_name.replace('-', ' ').replace('_', ' ').split()
        fallback_keywords.extend([word for word in name_words if len(word) > 3])
        
        # Add test type keywords
        if 'functional' in test_type:
            fallback_keywords.extend(['create', 'update', 'delete', 'manage'])
        elif 'access' in test_type or 'role' in test_type:
            fallback_keywords.extend(['login', 'authentication', 'permission'])
        elif 'ui' in test_type:
            fallback_keywords.extend(['interface', 'view', 'display'])
        
        return fallback_keywords

    def _calculate_chunk_test_relevance(self, chunk_lower: str, test_keywords: List[str], template: Dict) -> float:
        """Calculate how relevant a content chunk is to a specific test"""
        if not test_keywords:
            return 0.0
        
        relevance_score = 0.0
        total_possible_score = len(test_keywords)
        
        # Check for direct keyword matches
        for keyword in test_keywords:
            if keyword.lower() in chunk_lower:
                relevance_score += 1.0
        
        # Bonus for multiple keyword matches (indicating strong relevance)
        keyword_match_count = sum(1 for keyword in test_keywords if keyword.lower() in chunk_lower)
        if keyword_match_count >= 2:
            relevance_score += 0.5  # Bonus for multiple matches
        
        # Check for semantic patterns based on test focus
        test_focus = template.get('focus', '').lower()
        if test_focus == 'authentication' and any(auth_word in chunk_lower for auth_word in ['login', 'sign', 'auth', 'credential']):
            relevance_score += 1.0
        elif test_focus == 'api_operations' and any(api_word in chunk_lower for api_word in ['api', 'endpoint', 'service', 'backend']):
            relevance_score += 1.0
        elif test_focus == 'ui_components' and any(ui_word in chunk_lower for ui_word in ['interface', 'view', 'display', 'screen']):
            relevance_score += 1.0
        
        # Normalize score
        return min(relevance_score / total_possible_score, 1.0)
    def analyze_clusters(self, clusters_data: List[Dict]) -> List[ClusterAnalysis]:
        """Analyze each cluster to understand its domain content"""
        cluster_analyses = []
        
        for cluster in clusters_data:
            cluster_id = cluster.get('cluster_id', 0)
            content_chunks = cluster.get('content_chunks', [])
            
            # Combine all content for analysis
            combined_content = ' '.join(content_chunks).lower()
            
            # Extract domain elements
            domain_elements = self._extract_domain_elements(combined_content)
            
            # Identify functional areas
            functional_areas = self._identify_functional_areas(combined_content)
            
            # Identify technical components
            technical_components = self._identify_technical_components(combined_content)
            
            # Identify risk areas
            risk_areas = self._identify_risk_areas(combined_content)
            
            # Create representative text
            representative_text = self._create_representative_text(content_chunks, functional_areas)
            
            cluster_analysis = ClusterAnalysis(
                cluster_id=cluster_id,
                content_chunks=content_chunks,
                domain_elements=domain_elements,
                functional_areas=functional_areas,
                technical_components=technical_components,
                risk_areas=risk_areas,
                representative_text=representative_text
            )
            
            cluster_analyses.append(cluster_analysis)
        
        return cluster_analyses

    def _extract_domain_elements(self, content: str) -> Dict[str, List[str]]:
        """Dynamically extract business rules, workflows, entities from any domain content"""
        elements = {
            'identifiers': [],
            'business_rules': [],
            'workflows': [],
            'entities': [],
            'technical_aspects': [],
            'security_aspects': [],
            'financial_aspects': [],
            'processes': []
        }
        
        # Extract identifiers (Story IDs, Rule IDs, etc.)
        for pattern in self.identifier_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            elements['identifiers'].extend(matches)
        
        # Extract business rule indicators
        for pattern in self.business_rule_indicators:
            matches = re.findall(f'[^.]*{pattern}[^.]*', content, re.IGNORECASE)
            elements['business_rules'].extend([match.strip()[:100] for match in matches])
        
        # Extract workflow indicators
        for pattern in self.workflow_indicators:
            matches = re.findall(f'[^.]*{pattern}[^.]*', content, re.IGNORECASE)
            elements['workflows'].extend([match.strip()[:100] for match in matches])
        
        # Extract technical aspects
        for pattern in self.technical_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            elements['technical_aspects'].extend(matches)
        
        # Extract security aspects
        for pattern in self.security_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            elements['security_aspects'].extend(matches)
        
        # Extract financial aspects
        for pattern in self.financial_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            elements['financial_aspects'].extend(matches)
        
        # Extract process indicators
        for pattern in self.process_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            elements['processes'].extend(matches)
        
        # Extract entities (nouns that appear frequently and are capitalized)
        # Look for important domain entities by finding capitalized words
        entity_candidates = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        # Filter for entities that appear multiple times or are in business contexts
        entity_freq = {}
        for entity in entity_candidates:
            entity_freq[entity] = entity_freq.get(entity, 0) + 1
        
        # Include entities that appear more than once or are in business/technical contexts
        for entity, freq in entity_freq.items():
            if freq > 1 or any(keyword in entity.lower() for keyword in 
                              ['user', 'customer', 'system', 'service', 'manager', 'admin', 'role', 'account', 'profile']):
                elements['entities'].append(entity)
        
        # Remove duplicates and clean up
        for key in elements:
            elements[key] = list(set([item for item in elements[key] if item.strip()]))[:10]  # Limit to 10 per category
        
        return elements

    def _identify_functional_areas(self, content: str) -> List[str]:
        """Dynamically identify functional areas from any domain content"""
        functional_areas = []
        content_lower = content.lower()
        
        # Universal functional area patterns for any domain
        area_patterns = {
            'User Management': ['user', 'account', 'profile', 'registration', 'signup', 'member', 'customer', 'client'],
            'Authentication & Security': ['login', 'password', 'auth', 'security', 'permission', 'role', 'access', 'credential'],
            'Data Management': ['create', 'read', 'update', 'delete', 'crud', 'manage', 'data', 'record', 'storage'],
            'Transaction Processing': ['transaction', 'process', 'execute', 'commit', 'rollback', 'operation', 'business logic'],
            'Reporting & Analytics': ['report', 'analytics', 'dashboard', 'metric', 'statistic', 'chart', 'graph', 'insight'],
            'Communication': ['email', 'notification', 'message', 'alert', 'communication', 'contact', 'sms'],
            'Workflow Management': ['workflow', 'process', 'approval', 'review', 'status', 'state', 'step', 'stage'],
            'Integration Management': ['api', 'integration', 'sync', 'import', 'export', 'external', 'third-party', 'connector'],
            'Configuration Management': ['config', 'setting', 'preference', 'option', 'parameter', 'customize', 'setup'],
            'Search & Discovery': ['search', 'filter', 'query', 'find', 'lookup', 'browse', 'navigate', 'discover'],
            'Device Management': ['device', 'hardware', 'sensor', 'actuator', 'equipment', 'asset', 'inventory'],
            'Monitoring & Control': ['monitor', 'control', 'supervise', 'track', 'observe', 'measure', 'regulate'],
            'Content Management': ['content', 'document', 'file', 'media', 'publish', 'edit', 'version'],
            'Resource Management': ['resource', 'allocation', 'schedule', 'booking', 'reservation', 'capacity'],
            'Quality Management': ['quality', 'compliance', 'audit', 'standard', 'validation', 'certification'],
            'Performance Management': ['performance', 'optimization', 'efficiency', 'speed', 'throughput', 'latency'],
            'Event Management': ['event', 'trigger', 'handler', 'listener', 'subscriber', 'publisher', 'callback'],
            'Network Management': ['network', 'connectivity', 'protocol', 'communication', 'routing', 'topology'],
            # ADDED ADMINISTRATIVE/FINANCIAL CONFIGURATION
            'Financial Configuration': ['fee', 'cost', 'amount', 'billing', 'payout account', 'tax', 'rate', 'price', 'tariff'],
            # ADDED GEOSPATIAL/MAPPING  
            'Geospatial/Mapping': ['map', 'coordinate', 'latitude', 'longitude', 'address search', 'pin', 'site'],
            # ADDED REPORTING/DATA EXPORT
            'Reporting/Data Export': ['export', 'excel', 'download', 'report', 'listing', 'dashboard view']
        }
        
        # Look for functional areas based on content
        for area_name, keywords in area_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                # Count how many keywords match to prioritize
                matches = sum(1 for keyword in keywords if keyword in content_lower)
                if matches >= 2 or any(keyword in content_lower for keyword in keywords[:3]):  # High priority keywords
                    functional_areas.append(area_name)
        
        # Extract domain-specific functional areas from entities and processes
        entities = re.findall(r'\b[A-Z][a-z]+\b', content)
        processes = re.findall(r'\b(?:manage|process|handle|control|monitor|track|create|update|delete|validate)\s+([a-z]+(?:\s+[a-z]+)?)', content_lower)
        
        # Create functional areas from common entity + process combinations
        for entity in set(entities):
            if entity.lower() not in ['the', 'and', 'for', 'with', 'this', 'that']:
                entity_patterns = [f'{entity.lower()}', f'manage {entity.lower()}', f'{entity.lower()} management']
                if any(pattern in content_lower for pattern in entity_patterns):
                    functional_areas.append(f'{entity} Management')
        
        # Add process-based functional areas
        for process_match in processes:
            if len(process_match.strip()) > 2:
                functional_areas.append(f'{process_match.strip().title()} Processing')
        
        # Remove duplicates and limit
        functional_areas = list(set(functional_areas))[:8]
        
        # If no specific areas found, use generic ones based on technical indicators
        if not functional_areas:
            if any(term in content_lower for term in ['api', 'service', 'endpoint']):
                functional_areas.append('API Management')
            if any(term in content_lower for term in ['user', 'customer', 'client']):
                functional_areas.append('User Management')
            if any(term in content_lower for term in ['data', 'information', 'record']):
                functional_areas.append('Data Management')
        
        return functional_areas

    def _identify_technical_components(self, content: str) -> List[str]:
        """Dynamically identify technical components from content"""
        components = []
        content_lower = content.lower()
        
        # Dynamic component detection based on technical indicators (domain-agnostic)
        component_patterns = {
            'REST API': ['api', 'rest', 'endpoint', 'http', 'json', 'web service', 'microservice'],
            'Database': ['database', 'db', 'sql', 'nosql', 'storage', 'data store', 'repository', 'data layer'],
            'Authentication System': ['authentication', 'auth', 'login', 'signin', 'sso', 'oauth', 'token', 'identity'],
            'Web Application': ['portal', 'web', 'ui', 'interface', 'dashboard', 'frontend', 'webapp', 'website'],
            'Mobile Application': ['mobile', 'app', 'ios', 'android', 'native', 'hybrid', 'smartphone'],
            'Transaction System': ['transaction', 'processing', 'gateway', 'financial', 'commerce', 'order'],
            'Communication Service': ['email', 'notification', 'messaging', 'smtp', 'mail', 'sms', 'alert'],
            'External Integration': ['integration', 'external', 'third-party', 'api', 'webhook', 'sync', 'connector'],
            'Security System': ['security', 'encryption', 'ssl', 'tls', 'firewall', 'audit', 'compliance'],
            'Analytics System': ['analytics', 'reporting', 'metrics', 'tracking', 'monitoring', 'insights', 'dashboard'],
            'Search System': ['search', 'index', 'elasticsearch', 'solr', 'query', 'lookup', 'filter'],
            'File System': ['file', 'upload', 'storage', 'document', 'attachment', 'cdn', 'media'],
            'Background Service': ['background', 'queue', 'worker', 'scheduler', 'cron', 'job', 'batch'],
            'Cache System': ['cache', 'redis', 'memcached', 'session', 'temporary', 'buffer'],
            'Message System': ['queue', 'message', 'rabbitmq', 'kafka', 'broker', 'async', 'event'],
            'IoT Platform': ['iot', 'device', 'sensor', 'gateway', 'edge', 'telemetry', 'firmware', 'embedded'],
            'Real-time System': ['real-time', 'streaming', 'live', 'websocket', 'mqtt', 'publish', 'subscribe'],
            'Cloud Service': ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'container'],
            'AI/ML System': ['ai', 'ml', 'machine learning', 'neural', 'model', 'prediction', 'algorithm'],
            'Blockchain System': ['blockchain', 'crypto', 'smart contract', 'distributed ledger', 'consensus'],
            # ADDED GEOSPATIAL/DATA COMPONENTS
            'Geospatial Service': ['map', 'coordinate', 'address search', 'geocode', 'latitude', 'longitude', 'pin', 'site'],
            'Data Export Engine': ['export', 'excel', 'download', 'reporting', 'csv', 'pdf', 'file generation'],
            'Calculation Engine': ['calculate', 'fee', 'cost', 'percent', 'total', 'amount', 'net', 'computation']
        }
        
        # Check for each component type
        for component_name, keywords in component_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches >= 1:  # At least one keyword match
                components.append(component_name)
        
        # Extract technology-specific components
        tech_mentions = re.findall(r'\b(?:using|with|via|through)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', content)
        for tech in tech_mentions:
            if len(tech.strip()) > 2 and tech.strip() not in components:
                components.append(f'{tech.strip()} System')
        
        # Look for service/system mentions
        services = re.findall(r'\b([A-Z][a-zA-Z]+)\s+(?:service|system|component|module)', content, re.IGNORECASE)
        for service in services:
            service_name = f'{service.title()} Service'
            if service_name not in components and len(service) > 2:
                components.append(service_name)
        
        return list(set(components))[:10]  # Limit to 10 components

    def _identify_risk_areas(self, content: str) -> List[str]:
        """Dynamically identify areas that pose risks and need comprehensive testing"""
        risks = []
        content_lower = content.lower()
        
        # Financial/Monetary risks - generic terms
        financial_risk_terms = ['payment', 'billing', 'amount', 'money', 'cost', 'price', 'transaction', 'financial', 'purchase', 'order', 'invoice', 'revenue']
        if any(term in content_lower for term in financial_risk_terms):
            risks.append('Financial Transaction Risk')
        
        # Security and access risks
        security_risk_terms = ['security', 'access', 'authorization', 'authentication', 'permission', 'credential', 'token', 'password', 'encrypt']
        if any(term in content_lower for term in security_risk_terms):
            risks.append('Security Risk')
        
        # Data and privacy risks
        data_risk_terms = ['data', 'store', 'personal', 'private', 'sensitive', 'confidential', 'pii', 'gdpr', 'privacy', 'information']
        if any(term in content_lower for term in data_risk_terms):
            risks.append('Data Privacy Risk')
        
        # Integration and connectivity risks
        integration_risk_terms = ['integration', 'external', 'gateway', 'api', 'third-party', 'interface', 'connect', 'sync', 'import', 'export']
        if any(term in content_lower for term in integration_risk_terms):
            risks.append('Integration Risk')
        
        # Concurrency and performance risks
        concurrency_risk_terms = ['concurrent', 'multiple', 'simultaneous', 'parallel', 'performance', 'load', 'scale', 'throughput', 'multi-user']
        if any(term in content_lower for term in concurrency_risk_terms):
            risks.append('Concurrency Risk')
        
        # Network and connectivity risks
        network_risk_terms = ['network', 'connection', 'offline', 'connectivity', 'latency', 'timeout', 'bandwidth']
        if any(term in content_lower for term in network_risk_terms):
            risks.append('Network Risk')
        
        # Business logic and workflow risks
        workflow_risk_terms = ['workflow', 'process', 'business logic', 'rule', 'validation', 'approval', 'critical path']
        if any(term in content_lower for term in workflow_risk_terms):
            risks.append('Business Logic Risk')
        
        return risks

    def _create_representative_text(self, content_chunks: List[str], functional_areas: List[str]) -> str:
        """Create a representative description of the cluster"""
        if functional_areas:
            areas_text = ', '.join(functional_areas[:3])  # Top 3 areas
            return f"Content focused on: {areas_text}"
        elif content_chunks:
            # Use first meaningful chunk (truncated)
            first_chunk = content_chunks[0][:100] + "..." if len(content_chunks[0]) > 100 else content_chunks[0]
            return first_chunk
        else:
            return "Mixed content cluster"

    def generate_recommendations(self, cluster_analyses: List[ClusterAnalysis]) -> Tuple[List[TestRecommendation], List[TestRecommendation]]:
        """Generate Standard and Recommended test recommendations based on cluster analysis"""
        standard_tests = []
        recommended_tests = []
        
        # Detect overall domain from all cluster content
        all_content = ""
        for cluster in cluster_analyses:
            all_content += " ".join(cluster.content_chunks) + " "
        
        detected_domain = self.detect_domain(all_content)
        self.logger.info(f"Detected domain: {detected_domain.value}")
        
        # Perform gap analysis before generating recommendations
        gap_analysis = self.perform_gap_analysis(all_content, detected_domain)
        
        # If critical gaps are found, return empty recommendations with gap information
        if gap_analysis['has_gaps']:
            self.logger.warning(f"[GAP ANALYSIS] Critical gaps detected - blocking test recommendations: {gap_analysis['missing_requirements']}")
            
            # Create a special "gap notification" test recommendation to inform the user
            gap_notification = TestRecommendation(
                test_name="Missing Requirements Detected",
                test_description=f"Critical requirements are missing from the BRD/User Stories. Please address these gaps before generating test recommendations: {gap_analysis['gap_details']}",
                test_type=TestType.FUNCTIONAL,  # Use a generic type
                category=TestCategory.STANDARD,
                priority="Critical",
                estimated_effort="N/A",
                rationale="Gap analysis detected missing critical requirements that must be addressed before comprehensive testing can be planned.",
                source_clusters=[],
                source_content=[gap_analysis['gap_details']],
                business_impact="Critical",
                focus_areas=gap_analysis['missing_requirements'],
                domain_context=detected_domain.value,
                technical_requirements=[],
                source_story="Gap Analysis"
            )
            
            return [gap_notification], []  # Return gap notification in standard tests, empty recommended tests
        
        for cluster in cluster_analyses:
            # Generate domain-specific contextual tests first
            cluster_content = " ".join(cluster.content_chunks)
            contextual_tests = self.generate_contextual_tests(detected_domain, cluster_content, cluster)
            
            # Separate contextual tests by category
            for test in contextual_tests:
                if test.category == TestCategory.STANDARD:
                    standard_tests.append(test)
                else:
                    recommended_tests.append(test)
            
            # Generate standard tests based on functional areas
            standard_tests.extend(self._generate_standard_tests(cluster))
            
            # Generate recommended tests based on risk areas and technical complexity
            recommended_tests.extend(self._generate_recommended_tests(cluster))
        
        return standard_tests, recommended_tests

    def _generate_standard_tests(self, cluster: ClusterAnalysis) -> List[TestRecommendation]:
        """Generate domain-agnostic standard (must-have) test recommendations with deduplication logic"""
        tests = []
        
        # Track what specific tests have been generated to avoid generic duplicates
        specific_tests_generated = set()
        
        # First, generate domain-specific tests from templates
        content = ' '.join(cluster.content_chunks)
        domain = self.detect_domain(content)
        
        if domain != DomainType.GENERIC:
            contextual_tests = self.generate_contextual_tests(domain, content, cluster)
            tests.extend(contextual_tests)
            
            # Track specific test names to prevent generic duplicates
            for test in contextual_tests:
                if test.category == TestCategory.STANDARD:
                    specific_tests_generated.add(test.test_name)
                    # Also track base test types to prevent generic versions
                    if "OAuth" in test.test_name or "Authentication" in test.test_name:
                        specific_tests_generated.add("Authentication Testing")
                    if "CRUD" in test.test_name or "Operations" in test.test_name:
                        specific_tests_generated.add("Functional Testing")
                    if "Dashboard" in test.test_name:
                        specific_tests_generated.add("Analytics Visibility Check")
        
        # Always include smoke testing if there are workflows or functional areas
        if cluster.functional_areas or cluster.domain_elements.get('workflows'):
            workflow_context = ', '.join(cluster.functional_areas[:2]) if cluster.functional_areas else 'core system workflows'
            tests.append(TestRecommendation(
                test_name="Smoke Testing",
                test_description=f"Verify core user flows for {workflow_context}",
                test_type=TestType.SMOKE,
                category=TestCategory.STANDARD,
                priority="critical",
                estimated_effort="2-4 hours",
                rationale=f"Essential validation of {workflow_context} identified in requirements",
                source_clusters=[cluster.cluster_id],
                source_content=cluster.content_chunks[:2]
            ))
        
        # Functional testing - only if no specific functional tests were generated
        if cluster.functional_areas and "Functional Testing" not in specific_tests_generated:
            # Extract specific identifiers and business rules from content
            identifiers = cluster.domain_elements.get('identifiers', [])
            business_rules = cluster.domain_elements.get('business_rules', [])
            processes = cluster.domain_elements.get('processes', [])
            
            # Build dynamic rationale based on extracted content
            detailed_rationale = f"Validate core {', '.join(cluster.functional_areas[:3])} functionality"
            
            if identifiers:
                detailed_rationale += f". Reference requirements: {', '.join(identifiers[:2])}"
            
            if processes:
                main_processes = [p for p in processes if len(p) > 3][:3]
                if main_processes:
                    detailed_rationale += f". Key processes: {', '.join(main_processes)}"
            
            if business_rules:
                rule_summary = [rule[:50] + "..." if len(rule) > 50 else rule for rule in business_rules[:2]]
                detailed_rationale += f". Business rules: {'; '.join(rule_summary)}"
                
            # Create description based on actual functional areas
            functional_focus = ', '.join(cluster.functional_areas)
            tests.append(TestRecommendation(
                test_name="Functional Testing",
                test_description=f"Comprehensive validation of {functional_focus} including business logic and data flow verification",
                test_type=TestType.FUNCTIONAL,
                category=TestCategory.STANDARD,
                priority="high",
                estimated_effort="1-2 days",
                rationale=detailed_rationale,
                source_clusters=[cluster.cluster_id],
                source_content=[chunk for chunk in cluster.content_chunks if any(area.lower() in chunk.lower() for area in cluster.functional_areas)][:3]
            ))
        
        # Authentication testing - only if no specific auth tests were generated
        auth_components = [comp for comp in cluster.technical_components if any(keyword in comp.lower() for keyword in ['auth', 'security', 'portal', 'web'])]
        security_aspects = cluster.domain_elements.get('security_aspects', [])
        
        if (auth_components or security_aspects) and "Authentication Testing" not in specific_tests_generated:
            # Dynamically extract roles and entities from content
            entities = cluster.domain_elements.get('entities', [])
            roles_found = []
            
            # Look for role-like entities (words ending in common role suffixes or appearing in role contexts)
            role_context_patterns = [
                r'\b(\w+(?:er|or|ist|ant|ent))\s+(?:can|may|should|must|access|login)',
                r'\b(\w+)\s+(?:role|user|account|permission)',
                r'(?:as\s+a|the)\s+(\w+)',
                r'\b([A-Z]{2,5})\b'  # Common acronyms and abbreviations
            ]
            
            for chunk in cluster.content_chunks:
                for pattern in role_context_patterns:
                    matches = re.findall(pattern, chunk, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0] if match[0] else match[1]
                        if len(match) > 1 and match.lower() not in ['the', 'and', 'for', 'with']:
                            roles_found.append(match.title())
            
            # Also include entities that could be user types
            user_entities = [e for e in entities if any(keyword in e.lower() for keyword in ['user', 'admin', 'manager', 'customer', 'client'])]
            roles_found.extend(user_entities)
            
            roles_text = ', '.join(list(set(roles_found))[:4]) if roles_found else 'system users'
            
            # Extract access control requirements
            access_requirements = []
            for chunk in cluster.content_chunks:
                if any(word in chunk.lower() for word in ['login', 'access', 'permission', 'role', 'auth']):
                    sentences = re.split(r'[.!?]', chunk)
                    for sentence in sentences:
                        if any(word in sentence.lower() for word in ['login', 'access', 'permission', 'authenticate']):
                            clean_sentence = sentence.strip()
         
                            if len(clean_sentence) > 10:
                                access_requirements.append(clean_sentence[:80] + "..." if len(clean_sentence) > 80 else clean_sentence)
                                break
            
            detailed_rationale = f"Verify authentication and authorization for {roles_text}"
            if access_requirements:
                detailed_rationale += f". Key requirement: {access_requirements[0]}"
            if security_aspects:
                detailed_rationale += f". Security aspects: {', '.join(security_aspects[:2])}"
                
            tests.append(TestRecommendation(
                test_name="Authentication Testing",
                test_description=f"Validate user authentication and role-based access control for {roles_text} ensuring proper security controls",
                test_type=TestType.ROLE_ACCESS,
                category=TestCategory.STANDARD,
                priority="high",
                estimated_effort="1-2 days",
                rationale=detailed_rationale,
                source_clusters=[cluster.cluster_id],
                source_content=access_requirements[:2] if access_requirements else [chunk for chunk in cluster.content_chunks if any(keyword in chunk.lower() for keyword in ['auth', 'access', 'login', 'security'])][:2]
            ))
        
        # API testing if API components are identified
        api_components = [comp for comp in cluster.technical_components if 'api' in comp.lower()]
        technical_aspects = cluster.domain_elements.get('technical_aspects', [])
        
        if api_components or any('api' in aspect.lower() for aspect in technical_aspects):
            api_details = []
            for chunk in cluster.content_chunks:
                if any(keyword in chunk.lower() for keyword in ['api', 'endpoint', 'rest', 'http', 'json']):
                    # Extract API-related sentences
                    sentences = re.split(r'[.!?]', chunk)
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in ['api', 'endpoint', 'service']):
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 10:
                                api_details.append(clean_sentence[:100] + "..." if len(clean_sentence) > 100 else clean_sentence)
                                break
            
            api_focus = ', '.join(api_components) if api_components else 'system APIs'
            rationale = f"API components identified: {api_focus}."
            if api_details:
                rationale += f" Key integration: {api_details[0]}"
                
            tests.append(TestRecommendation(
                test_name="API Functional Testing",
                test_description=f"Validate {api_focus} including endpoints, data structure, and response handling",
                test_type=TestType.API_FUNCTIONAL,
                category=TestCategory.STANDARD,
                priority="high",
                estimated_effort="2-3 days",
                rationale=rationale,
                source_clusters=[cluster.cluster_id],
                source_content=api_details[:2] if api_details else [chunk for chunk in cluster.content_chunks if any(keyword in chunk.lower() for keyword in ['api', 'endpoint', 'service'])][:2]
            ))
        
        # CRITICAL CHANGE: Only add financial tests if EXPLICITLY required by complex calculations
        # Remove financial contamination - don't add financial tests unless BRD explicitly mentions complex formulas
        content_text = ' '.join(cluster.content_chunks).lower()
        has_complex_financial_calculations = any(term in content_text for term in [
            'fee calculation', 'complex formula', 'calculation logic', 'cno fee', 'csr fee', 
            'net total calculation', 'percentage calculation', 'tax calculation', 'commission calculation',
            'formula validation', 'arithmetic calculation', 'financial calculation'
        ])
        
        # Only add financial tests if there are ACTUAL financial calculations, NOT just "forecast revenue"
        if has_complex_financial_calculations:
            # Pre-process chunks to include source IDs
            cluster_chunks_with_source = [(chunk, f"Chunk_{i:03d}") for i, chunk in enumerate(cluster.content_chunks)]
            
            # Enhanced attribution for financial calculation testing
            rationale_query = "Verify the accuracy of complex fee calculation logic (CNO Fee, CSR Fee, Net CSO Total)"
            
            # Use the attribution function to find the best source
            best_rationale_text, source_id = self._find_best_rationale_match_with_source(rationale_query, cluster_chunks_with_source)
            
            # Explicitly use the extracted rationale and source ID
            tests.append(TestRecommendation(
                test_name="Financial Calculation Testing",
                test_description="Verify all configured fee formulas and net revenue distribution",
                test_type=TestType.PAYMENT_WORKFLOW,
                category=TestCategory.STANDARD,
                priority="critical",
                estimated_effort="2-3 days",
                rationale=f"Critical: {best_rationale_text}",
                source_clusters=[cluster.cluster_id],
                source_content=[source_id]  # Store only the source ID
            ))
        
        # Input validation testing (only for configuration-heavy systems)
        has_configuration_focus = any('configuration' in area.lower() for area in cluster.functional_areas)
        if has_configuration_focus or any('input' in chunk.lower() and 'validation' in chunk.lower() for chunk in cluster.content_chunks):
            # Pre-process chunks to include source IDs if not already done
            if not has_complex_financial_calculations:
                cluster_chunks_with_source = [(chunk, f"Chunk_{i:03d}") for i, chunk in enumerate(cluster.content_chunks)]
            
            rationale_query = "Verify all mandatory fields, character limits, and decimal constraints for location setup"
            
            # Use the attribution function to find the best source
            best_rationale_text, source_id = self._find_best_rationale_match_with_source(rationale_query, cluster_chunks_with_source)
            
            tests.append(TestRecommendation(
                test_name="Input Validation Testing",
                test_description="Verify all mandatory fields, character limits, and decimal constraints (e.g., Utility Cost)",
                test_type=TestType.FUNCTIONAL,
                category=TestCategory.STANDARD,
                priority="high",
                estimated_effort="1-2 days", 
                rationale=f"Mandatory: {best_rationale_text}",
                source_clusters=[cluster.cluster_id],
                source_content=[source_id]
            ))
        
        # UI testing if web/interface components are identified
        ui_components = [comp for comp in cluster.technical_components if any(keyword in comp.lower() for keyword in ['web', 'portal', 'ui', 'interface', 'dashboard', 'mobile', 'app'])]
        
        if ui_components:
            ui_details = []
            for chunk in cluster.content_chunks:
                ui_keywords = ['portal', 'dashboard', 'interface', 'ui', 'web', 'screen', 'page', 'form', 'button']
                if any(keyword in chunk.lower() for keyword in ui_keywords):
                    sentences = re.split(r'[.!?]', chunk)
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in ui_keywords):
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 10:
                                ui_details.append(clean_sentence[:80] + "..." if len(clean_sentence) > 80 else clean_sentence)
                                break
            
            ui_focus = ', '.join(ui_components)
            rationale = f"User interface components identified: {ui_focus}."
            if ui_details:
                rationale += f" Key interface: {ui_details[0]}"
                
            tests.append(TestRecommendation(
                test_name="UI Regression Testing",
                test_description=f"Validate {ui_focus} ensuring proper functionality and visual consistency",
                test_type=TestType.UI_REGRESSION,
                category=TestCategory.STANDARD,
                priority="medium",
                estimated_effort="1-2 days",
                rationale=rationale,
                source_clusters=[cluster.cluster_id],
                source_content=ui_details[:2] if ui_details else [chunk for chunk in cluster.content_chunks if any(keyword in chunk.lower() for keyword in ['portal', 'dashboard', 'interface', 'ui'])][:2]
            ))
        
        return tests

    def _generate_recommended_tests(self, cluster: ClusterAnalysis) -> List[TestRecommendation]:
        """Generate domain-agnostic recommended (advanced) test recommendations"""
        tests = []
        
        # Security testing for security-related components or aspects
        security_components = [comp for comp in cluster.technical_components if any(keyword in comp.lower() for keyword in ['security', 'auth', 'encryption'])]
        security_aspects = cluster.domain_elements.get('security_aspects', [])
        
        if security_components or security_aspects or 'Security Risk' in cluster.risk_areas:
            security_focus = ', '.join(security_aspects[:3]) if security_aspects else 'system security'
            security_details = []
            
            for chunk in cluster.content_chunks:
                security_keywords = ['security', 'encrypt', 'secure', 'compliance', 'audit', 'permission', 'access control']
                if any(keyword in chunk.lower() for keyword in security_keywords):
                    sentences = re.split(r'[.!?]', chunk)
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in security_keywords):
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 10:
                                security_details.append(clean_sentence[:100] + "..." if len(clean_sentence) > 100 else clean_sentence)
                                break
            
            # Extract story references from all content chunks
            story_refs = self._extract_story_references_from_content(cluster.content_chunks)
            source_content_with_refs = security_details[:2] if security_details else [chunk for chunk in cluster.content_chunks if any(keyword in chunk.lower() for keyword in ['security', 'encrypt', 'audit'])][:2]
            
            # Add story references to source content if found
            if story_refs:
                source_content_with_refs.extend([f"Referenced in: {', '.join(story_refs)}"])
            
            rationale = f"Security requirements identified: {security_focus}."
            if security_details:
                rationale += f" Key requirement: {security_details[0]}"
                
            tests.append(TestRecommendation(
                test_name="Advanced Security Testing",
                test_description=f"Comprehensive security validation including {security_focus} and compliance requirements",
                test_type=TestType.PAYMENT_SECURITY,
                category=TestCategory.RECOMMENDED,
                priority="high",
                estimated_effort="3-5 days",
                rationale=rationale,
                source_clusters=[cluster.cluster_id],
                source_content=source_content_with_refs
            ))
        
        # Concurrency testing for multi-user or concurrent access patterns
        concurrent_indicators = ['concurrent', 'simultaneous', 'multiple', 'parallel', 'shared', 'multi-user']
        has_concurrency_needs = (
            'Concurrency Risk' in cluster.risk_areas or
            any(indicator in ' '.join(cluster.content_chunks).lower() for indicator in concurrent_indicators)
        )
        
        if has_concurrency_needs:
            user_types = cluster.domain_elements.get('entities', [])
            user_focus = ', '.join(user_types[:3]) if user_types else 'system users'
            
            concurrent_scenarios = []
            for chunk in cluster.content_chunks:
                if any(indicator in chunk.lower() for indicator in concurrent_indicators):
                    sentences = re.split(r'[.!?]', chunk)
                    for sentence in sentences:
                        if any(indicator in sentence.lower() for indicator in concurrent_indicators):
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 10:
                                concurrent_scenarios.append(clean_sentence[:100] + "..." if len(clean_sentence) > 100 else clean_sentence)
                                break
            
            # Extract story references for concurrency testing
            story_refs = self._extract_story_references_from_content(cluster.content_chunks)
            source_content_with_refs = concurrent_scenarios[:2] if concurrent_scenarios else [chunk for chunk in cluster.content_chunks if any(indicator in chunk.lower() for indicator in concurrent_indicators)][:2]
            
            # Add story references to source content if found
            if story_refs:
                source_content_with_refs.extend([f"Referenced in: {', '.join(story_refs)}"])
            
            rationale = f"Multi-user access patterns identified for {user_focus}."
            if concurrent_scenarios:
                rationale += f" Key scenario: {concurrent_scenarios[0]}"
                
            tests.append(TestRecommendation(
                test_name="Concurrency Testing",
                test_description=f"Validate system behavior under concurrent access by {user_focus}",
                test_type=TestType.CONCURRENCY,
                category=TestCategory.RECOMMENDED,
                priority="medium",
                estimated_effort="2-4 days",
                rationale=rationale,
                source_clusters=[cluster.cluster_id],
                source_content=source_content_with_refs
            ))
        
        # Integration testing for external systems
        integration_components = [comp for comp in cluster.technical_components if any(keyword in comp.lower() for keyword in ['integration', 'external', 'third-party', 'api'])]
        
        if integration_components:
            integration_details = []
            for chunk in cluster.content_chunks:
                integration_keywords = ['integration', 'external', 'third-party', 'api', 'service', 'connect']
                if any(keyword in chunk.lower() for keyword in integration_keywords):
                    sentences = re.split(r'[.!?]', chunk)
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in integration_keywords):
                            clean_sentence = sentence.strip()
                            if len(clean_sentence) > 10:
                                integration_details.append(clean_sentence[:100] + "..." if len(clean_sentence) > 100 else clean_sentence)
                                break
            
            integration_focus = ', '.join(integration_components)
            rationale = f"External integration points identified: {integration_focus}."
            if integration_details:
                rationale += f" Key integration: {integration_details[0]}"
                
            tests.append(TestRecommendation(
                test_name="Integration Contract Testing",
                test_description=f"Validate {integration_focus} including data contracts and API compatibility",
                test_type=TestType.API_CONTRACT,
                category=TestCategory.RECOMMENDED,
                priority="medium",
                estimated_effort="1-2 days",
                rationale=rationale,
                source_clusters=[cluster.cluster_id],
                source_content=integration_details[:2] if integration_details else [chunk for chunk in cluster.content_chunks if any(keyword in chunk.lower() for keyword in ['integration', 'external', 'api'])][:2]
            ))
        
        # Chaos/Resilience testing for complex systems
        if len(cluster.technical_components) > 3 or len(cluster.functional_areas) > 4:
            system_complexity = f"{len(cluster.technical_components)} technical components and {len(cluster.functional_areas)} functional areas"
            
            # Extract story references for system resilience testing
            story_refs = self._extract_story_references_from_content(cluster.content_chunks)
            source_content_with_refs = cluster.content_chunks[:2]
            
            # Add story references to source content if found
            if story_refs:
                source_content_with_refs.extend([f"Referenced in: {', '.join(story_refs)}"])
            
            tests.append(TestRecommendation(
                test_name="System Resilience Testing",
                test_description=f"Validate system stability under stress including component failures and network disruptions",
                test_type=TestType.CHAOS,
                category=TestCategory.RECOMMENDED,
                priority="low",
                estimated_effort="3-5 days",
                rationale=f"Complex system architecture identified with {system_complexity}",
                source_clusters=[cluster.cluster_id],
                source_content=source_content_with_refs
            ))
        
        # Accessibility testing for user-facing interfaces
        ui_components = [comp for comp in cluster.technical_components if any(keyword in comp.lower() for keyword in ['web', 'portal', 'mobile', 'app', 'interface', 'ui'])]
        
        if ui_components:
            ui_focus = ', '.join(ui_components)
            
            # Extract story references for accessibility testing
            story_refs = self._extract_story_references_from_content(cluster.content_chunks)
            source_content_with_refs = [chunk for chunk in cluster.content_chunks if any(keyword in chunk.lower() for keyword in ['portal', 'interface', 'ui', 'web', 'user'])][:2]
            
            # Add story references to source content if found
            if story_refs:
                source_content_with_refs.extend([f"Referenced in: {', '.join(story_refs)}"])
            
            tests.append(TestRecommendation(
                test_name="Accessibility Compliance Testing",
                test_description=f"Validate {ui_focus} for accessibility standards including screen reader compatibility and keyboard navigation",
                test_type=TestType.ACCESSIBILITY,
                category=TestCategory.RECOMMENDED,
                priority="medium",
                estimated_effort="2-3 days",
                rationale=f"User interface components identified requiring accessibility compliance: {ui_focus}",
                source_clusters=[cluster.cluster_id],
                source_content=source_content_with_refs
            ))
        
        # HYBRID AI RECOMMENDATIONS: Use semantic similarity + rule-based approach
        hybrid_recommender = self._get_hybrid_recommender()
        if hybrid_recommender:
            try:
                # Combine all content for semantic analysis
                combined_content = ' '.join(cluster.content_chunks)
                
                # Get hybrid recommendations  
                hybrid_tests = hybrid_recommender.recommend_tests(combined_content)
                
                # Convert hybrid tests to TestRecommendation format with proper attribution
                for hybrid_test in hybrid_tests:
                    # Extract source attribution from rationale if available
                    source_content = [combined_content[:200] + "..."]
                    if hasattr(hybrid_test, 'rationale') and hybrid_test.rationale:
                        source_content = [hybrid_test.rationale[:200] + "..."]
                    
                    # Map hybrid test to our format
                    tests.append(TestRecommendation(
                        test_name=f"AI {hybrid_test.test_name}",
                        test_description=hybrid_test.description,
                        test_type=getattr(TestType, hybrid_test.test_type.upper(), TestType.FUNCTIONAL),
                        category=TestCategory.RECOMMENDED,
                        priority=hybrid_test.priority.lower(),
                        estimated_effort=hybrid_test.estimated_effort,
                        rationale=f"AI Analysis: {hybrid_test.rationale}",
                        source_clusters=[cluster.cluster_id],
                        source_content=source_content
                    ))
                
                self.logger.info(f"Added {len(hybrid_tests)} hybrid AI recommendations")
                
            except Exception as e:
                self.logger.warning(f"Hybrid recommender failed: {e}")
        
        return tests

    def format_recommendations(self, standard_tests: List[TestRecommendation], recommended_tests: List[TestRecommendation]) -> Dict[str, Any]:
        """Format recommendations for API response"""
        def format_test_list(tests: List[TestRecommendation]) -> List[Dict]:
            return [
                {
                    'test_name': test.test_name,
                    'test_description': test.test_description,
                    'test_category': test.test_type.value,
                    'priority': test.priority,
                    'estimated_effort': test.estimated_effort,
                    'rationale': test.rationale,
                    'source_clusters': test.source_clusters,
                    'source_content_preview': [content[:100] + "..." if len(content) > 100 else content 
                                            for content in test.source_content[:2]]  # Preview of source content
                }
                for test in tests
            ]
        
        return {
            'standard_testing_types': {
                'description': 'Must-haves for MVP / UAT',
                'total_tests': len(standard_tests),
                'tests': format_test_list(standard_tests)
            },
            'recommended_testing_types': {
                'description': 'Advanced / Post-MVP or Production Hardened',
                'total_tests': len(recommended_tests),
                'tests': format_test_list(recommended_tests)
            }
        }

    def _initialize_domain_patterns(self) -> Dict[DomainType, DomainPattern]:
        """Initialize domain-specific patterns for test recommendations."""
        return {
            DomainType.ECOMMERCE: DomainPattern(
                keywords=[
                    'ecommerce', 'online store', 'shopping cart', 'product catalog', 'checkout',
                    'payment gateway', 'order management', 'inventory', 'customer', 'cart',
                    'product', 'purchase', 'sale', 'revenue', 'discount', 'coupon', 'shipping'
                ],
                business_entities=[
                    'Product', 'Customer', 'Order', 'Cart', 'Payment', 'Inventory', 
                    'Category', 'Discount', 'Shipping', 'Review', 'Wishlist'
                ],
                processes=[
                    'Product Browsing', 'Cart Management', 'Checkout Process', 'Payment Processing',
                    'Order Fulfillment', 'Inventory Management', 'Customer Support'
                ],
                test_types={'standard': ['functional', 'payment_workflow'], 'recommended': ['usability', 'analytics']},
                risk_areas=['Payment Security', 'Performance', 'User Experience']
            ),
            DomainType.BUSINESS_MANAGEMENT: DomainPattern(
                keywords=[
                    'dashboard', 'CRM', 'sales', 'deals', 'kanban', 'contacts', 'forecast', 
                    'reports', 'analytics', 'management', 'personalized', 'AI chat', 'widgets',
                    'bulk import', 'filters', 'activity log', 'adoption', 'performance tracking',
                    'lead', 'won', 'lost', 'revenue', 'stakeholders', 'insights', 'oauth',
                    'authentication', 'google', 'logged-in user', 'workspace', 'business',
                    'manager', 'sales user', 'CRUD operations', 'network management'
                ],
                business_entities=[
                    'Dashboard', 'Contact', 'Deal', 'Lead', 'User', 'Report', 'Widget',
                    'Chat', 'Filter', 'Forecast', 'Activity', 'Stakeholder', 'Network'
                ],
                processes=[
                    'User Authentication', 'Dashboard Personalization', 'Contact Management',
                    'Deal Management', 'Report Generation', 'Data Import', 'Performance Tracking'
                ],
                test_types={'standard': ['functional', 'role_access'], 'recommended': ['usability', 'analytics']},
                risk_areas=['Data Security', 'Performance', 'User Experience']
            ),
            DomainType.EV_CHARGING: DomainPattern(
                keywords=[
                    'charging station', 'electric vehicle', 'EV', 'charger', 'OCPP', 'protocol',
                    'charging session', 'connector', 'charging point', 'power management',
                    'billing', 'payment', 'tariff', 'kWh', 'electricity', 'grid', 'energy',
                    'authentication', 'RFID', 'authorization', 'user account', 'session management',
                    'zuri', 'sales', 'dashboard', 'CNO', 'CSR', 'CSO', 'fee', 'formula',
                    'site owner', 'payout', 'revenue', 'location', 'charge session', 'states',
                    'transitions', 'network expansion', 'site configuration', 'utility cost',
                    'enhancement', 'business requirements', 'site management', 'financial calculation'
                ],
                business_entities=[
                    'Charging Station', 'User Account', 'Charging Session', 'Payment Method',
                    'Connector', 'Vehicle', 'Tariff', 'Energy Consumption', 'Grid Connection'
                ],
                processes=[
                    'User Authentication', 'Session Initiation', 'Charging Process',
                    'Payment Processing', 'Energy Monitoring', 'Grid Communication',
                    'Session Termination', 'Billing Calculation'
                ],
                test_types={'standard': ['session_management', 'functional'], 'recommended': ['payment_security', 'interoperability']},
                risk_areas=['Security', 'Performance', 'Compliance'],
                test_templates=[
                    # TIER 1: ADMINISTRATIVE/SETUP FOCUS (PRIORITIZED FOR CONFIG MODULES)
                    {
                        'name': 'Financial Calculation Testing',
                        'description': 'Verify complex fee calculation logic (CNO Fee, CSR Fee, Net CSO Total)',
                        'type': TestType.PAYMENT_WORKFLOW,
                        'category': TestCategory.STANDARD,
                        'priority': 'Critical',
                        'effort': '2-3 days',
                        'rationale': 'Critical: Verify the accuracy of all CNO/CSR/CSO fee formulas',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'Input Validation Testing',
                        'description': 'Verify all mandatory fields, character limits, and decimal constraints (e.g., Utility Cost)',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '1-2 days',
                        'rationale': 'Mandatory to ensure data consistency and integrity for location setup',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'Site Management Testing',
                        'description': 'Test admin portal for adding, editing site locations and mapping integration',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '2-4 days',
                        'rationale': 'Essential for network expansion and site configuration',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'Payout Account Configuration Testing',
                        'description': 'Verify admin ability to configure and manage site owner payout accounts and settlements',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '1-2 days',
                        'rationale': 'Required for site owner revenue distribution',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'Data Export Testing',
                        'description': 'Test admin ability to export transaction data, usage reports in Excel/CSV formats',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',
                        'effort': '1-2 days',
                        'rationale': 'Needed for business reporting and analysis',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    # TIER 2: REAL-TIME/OPERATIONAL FOCUS (DE-PRIORITIZED FOR CONFIG MODULES)
                    {
                        'name': 'Session Management Testing',
                        'description': 'Validate charging session lifecycle from authentication to billing',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',  # Downgraded priority for config modules
                        'effort': '3-5 days',
                        'rationale': 'Operational focus: Validate charge session states and transitions',
                        'tier': 2,
                        'focus': 'user_functionality'
                    },
                    # TIER 3: Advanced Integration & Security
                    {
                        'name': 'OCPP Protocol Compliance Testing',
                        'description': 'Verify OCPP message handling and protocol compliance',
                        'type': TestType.INTEROPERABILITY,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'Medium',
                        'effort': '5-7 days',
                        'rationale': 'Required for interoperability with charging networks',
                        'tier': 3,
                        'focus': 'integration'
                    },
                    {
                        'name': 'Payment Security Testing',
                        'description': 'Validate payment processing security and PCI compliance',
                        'type': TestType.PAYMENT_SECURITY,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'High',
                        'effort': '4-6 days',
                        'rationale': 'Critical for financial transaction security',
                        'tier': 3,
                        'focus': 'security'
                    }
                ]
            ),
            DomainType.IOT_SMART_HOME: DomainPattern(
                keywords=[
                    'smart home', 'IoT', 'device', 'sensor', 'automation', 'smart device',
                    'home automation', 'connected device', 'wireless', 'bluetooth', 'wifi',
                    'app control', 'remote control', 'scheduling', 'energy management',
                    'device management', 'monitoring', 'control', 'dashboard', 'interface',
                    'hardware', 'equipment', 'asset', 'inventory', 'configuration'
                ],
                business_entities=[
                    'Smart Device', 'User Profile', 'Home Network', 'Automation Rule',
                    'Sensor Data', 'Device Group', 'Energy Usage', 'Security System'
                ],
                processes=[
                    'Device Pairing', 'Automation Setup', 'Remote Control', 'Data Collection',
                    'Energy Monitoring', 'Security Management', 'Firmware Updates'
                ],
                test_types={'standard': ['connectivity', 'functional'], 'recommended': ['usability', 'analytics']},
                risk_areas=['Connectivity', 'Security', 'Usability'],
                test_templates=[
                    # TIER 1: ADMINISTRATIVE/SETUP FOCUS (PRIORITIZED FOR CONFIG MODULES)
                    {
                        'name': 'Device Configuration Testing',
                        'description': 'Verify admin ability to configure device settings, thresholds, and operational parameters',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'Critical',
                        'effort': '2-3 days',
                        'rationale': 'Critical: Ensure proper device configuration for optimal performance',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'Input Validation Testing',
                        'description': 'Verify all mandatory fields, limits, and constraints in device setup forms',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '1-2 days',
                        'rationale': 'Mandatory to ensure data consistency and integrity for device setup',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'User Account Management Testing',
                        'description': 'Validate admin ability to create, modify user accounts and assign device permissions',
                        'type': TestType.ROLE_ACCESS,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '2-4 days',
                        'rationale': 'Critical for user access control and system security',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    {
                        'name': 'Data Export and Reporting Testing',
                        'description': 'Test admin ability to export device data, usage analytics, and system reports',
                        'type': TestType.ANALYTICS,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',
                        'effort': '1-2 days',
                        'rationale': 'Required for business intelligence and compliance reporting',
                        'tier': 1,
                        'focus': 'administrative'
                    },
                    # TIER 2: REAL-TIME/OPERATIONAL FOCUS (DE-PRIORITIZED FOR CONFIG MODULES)
                    {
                        'name': 'Device Connectivity Testing',
                        'description': 'Validate device pairing and network connectivity across protocols',
                        'type': TestType.CONNECTIVITY,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',  # Downgraded priority for config modules
                        'effort': '2-4 days',
                        'rationale': 'Operational focus: Validate device communication and pairing',
                        'tier': 2,
                        'focus': 'user_functionality'
                    },
                    {
                        'name': 'Automation Rule Testing',
                        'description': 'Verify automation logic and trigger conditions work correctly',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',
                        'effort': '3-5 days',
                        'rationale': 'Operational focus: Core value proposition of smart home systems',
                        'tier': 2,
                        'focus': 'user_functionality'
                    },
                    # TIER 3: Advanced Features
                    {
                        'name': 'Cross-Platform Integration Testing',
                        'description': 'Test integration with third-party platforms and protocols',
                        'type': TestType.INTEROPERABILITY,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'Medium',
                        'effort': '4-6 days',
                        'rationale': 'Important for ecosystem compatibility',
                        'tier': 3,
                        'focus': 'integration'
                    }
                ]
            ),
            DomainType.FINTECH: DomainPattern(
                keywords=[
                    'payment', 'transaction', 'financial', 'banking', 'account', 'balance',
                    'transfer', 'deposit', 'withdrawal', 'credit', 'debit', 'fraud', 'security'
                ],
                business_entities=[
                    'Account', 'Transaction', 'Payment Method', 'User Wallet', 'Merchant'
                ],
                processes=[
                    'Payment Processing', 'Account Management', 'Fraud Detection', 'Compliance'
                ],
                test_types={'standard': ['payment_workflow', 'functional'], 'recommended': ['payment_security']},
                risk_areas=['Security', 'Compliance', 'Fraud'],
                test_templates=[]
            ),
            DomainType.HEALTHCARE: DomainPattern(
                keywords=[
                    'patient', 'medical', 'health', 'doctor', 'appointment', 'prescription',
                    'diagnosis', 'treatment', 'hospital', 'clinic', 'HIPAA', 'privacy'
                ],
                business_entities=[
                    'Patient', 'Doctor', 'Appointment', 'Medical Record', 'Prescription'
                ],
                processes=[
                    'Patient Registration', 'Appointment Scheduling', 'Medical Records', 'Privacy'
                ],
                test_types={'standard': ['functional', 'role_access'], 'recommended': ['accessibility']},
                risk_areas=['Privacy', 'Compliance', 'Security'],
                test_templates=[]
            ),
            DomainType.ECOMMERCE: DomainPattern(
                keywords=[
                    'product', 'cart', 'checkout', 'order', 'inventory', 'shipping',
                    'customer', 'catalog', 'search', 'payment', 'delivery'
                ],
                business_entities=[
                    'Product', 'Customer', 'Order', 'Cart', 'Inventory', 'Shipping'
                ],
                processes=[
                    'Product Search', 'Cart Management', 'Checkout Process', 'Order Fulfillment'
                ],
                test_types={'standard': ['functional', 'payment_workflow'], 'recommended': ['usability', 'analytics']},
                risk_areas=['Performance', 'Security', 'Usability'],
                test_templates=[]
            ),
            DomainType.BUSINESS_MANAGEMENT: DomainPattern(
                keywords=[
                    'dashboard', 'CRM', 'sales', 'deals', 'kanban', 'contacts', 'forecast', 
                    'reports', 'analytics', 'management', 'personalized', 'AI chat', 'widgets',
                    'bulk import', 'filters', 'activity log', 'adoption', 'performance tracking',
                    'lead', 'won', 'lost', 'revenue', 'stakeholders', 'insights', 'oauth',
                    'authentication', 'google', 'logged-in user', 'workspace', 'business',
                    'manager', 'sales user', 'CRUD operations', 'network management'
                ],
                business_entities=[
                    'Dashboard', 'Contact', 'Deal', 'Lead', 'User', 'Report', 'Widget',
                    'Chat', 'Filter', 'Forecast', 'Activity', 'Stakeholder', 'Network'
                ],
                processes=[
                    'User Authentication', 'Dashboard Personalization', 'Contact Management',
                    'Deal Management', 'Report Generation', 'Data Import', 'Performance Tracking'
                ],
                test_types={'standard': ['functional', 'role_access'], 'recommended': ['usability', 'analytics']},
                risk_areas=['Data Security', 'Performance', 'User Experience'],
                test_templates=[
                    # Standard Tests for Business Management
                    {
                        'name': 'Role-Based Access Testing',
                        'description': 'Verify users can authenticate and access system based on their assigned roles and permissions',
                        'type': TestType.ROLE_ACCESS,
                        'category': TestCategory.STANDARD,
                        'priority': 'Critical',
                        'effort': '1-2 days',
                        'rationale': 'Critical: Validate access control across different user roles (Owner, Manager, Admin)',
                        'focus': 'authentication'
                    },
                    {
                        'name': 'Functional Testing',
                        'description': 'Validate core business workflows and user interface interactions',
                        'type': TestType.FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '2-3 days',
                        'rationale': 'High: Test front-end form flows, data operations, and core business logic',
                        'focus': 'core_workflows'
                    },
                    {
                        'name': 'API Functional Testing',
                        'description': 'Validate JSON structure, correct data flow, and API status codes',
                        'type': TestType.API_FUNCTIONAL,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '2-4 days',
                        'rationale': 'High: Ensure API endpoints handle CRUD operations correctly with proper validation',
                        'focus': 'api_operations'
                    },
                    {
                        'name': 'UI Regression Testing',
                        'description': 'Ensure no broken components or visual bugs in user interface',
                        'type': TestType.UI_REGRESSION,
                        'category': TestCategory.STANDARD,
                        'priority': 'High',
                        'effort': '2-3 days',
                        'rationale': 'High: Verify UI components render correctly across different views and interactions',
                        'focus': 'ui_components'
                    },
                    {
                        'name': 'Session Management Testing',
                        'description': 'Test session expiry, logout functionality, and multi-tab handling',
                        'type': TestType.SESSION_MANAGEMENT,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',
                        'effort': '2-3 days',
                        'rationale': 'Medium: Ensure proper session handling and security across user interactions',
                        'focus': 'session_security'
                    },
                    {
                        'name': 'Browser Compatibility Testing',
                        'description': 'Verify application works correctly across Chrome, Firefox, Edge (latest versions)',
                        'type': TestType.BROWSER_COMPATIBILITY,
                        'category': TestCategory.STANDARD,
                        'priority': 'Medium',
                        'effort': '1-2 days',
                        'rationale': 'Medium: Ensure cross-browser functionality for all user types',
                        'focus': 'browser_support'
                    },
                    # Recommended Tests
                    {
                        'name': 'Usability Testing',
                        'description': 'Real users interacting with the system for UX feedback and workflow validation',
                        'type': TestType.USABILITY,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'Medium',
                        'effort': '2-3 days',
                        'rationale': 'Recommended: Optimize user experience through real user feedback',
                        'focus': 'user_experience'
                    },
                    {
                        'name': 'Concurrency Testing',
                        'description': 'Multiple users accessing the same resources concurrently',
                        'type': TestType.CONCURRENCY,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'Medium',
                        'effort': '3-4 days',
                        'rationale': 'Recommended: Validate system stability under concurrent user load',
                        'focus': 'concurrency'
                    },
                    {
                        'name': 'Predictive Analytics Testing',
                        'description': 'Data model validation, usage forecasts, and anomaly detection flags',
                        'type': TestType.PREDICTIVE_ANALYTICS,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'Low',
                        'effort': '2-4 days',
                        'rationale': 'Recommended: Validate accuracy of predictive models and insights',
                        'focus': 'analytics'
                    },
                    {
                        'name': 'Mobile Responsiveness Testing',
                        'description': 'Web views render properly on phones and tablets',
                        'type': TestType.MOBILE_RESPONSIVE,
                        'category': TestCategory.RECOMMENDED,
                        'priority': 'Low',
                        'effort': '2-3 days',
                        'rationale': 'Recommended: Ensure mobile accessibility for all user scenarios',
                        'focus': 'mobile'
                    }
                ]
            ),
            DomainType.GENERIC: DomainPattern(
                keywords=[],
                business_entities=[],
                processes=[],
                test_types={'standard': [], 'recommended': []},
                risk_areas=[],
                test_templates=[]
            )
        }

    def detect_domain(self, content: str) -> DomainType:
        """Detect the primary domain based on content analysis."""
        content_lower = content.lower()
        domain_scores = {}
        
        for domain_type, pattern in self.domain_patterns.items():
            if domain_type == DomainType.GENERIC:
                continue
                
            score = 0
            for keyword in pattern.keywords:
                # Count keyword occurrences with some fuzzy matching
                keyword_count = content_lower.count(keyword.lower())
                if keyword_count > 0:
                    # Higher weight for business management domain keywords
                    weight = 3 if domain_type == DomainType.BUSINESS_MANAGEMENT else 1
                    score += keyword_count * (len(keyword.split()) + 1) * weight
            
            domain_scores[domain_type] = score
        
        # Log domain detection results for debugging
        self.logger.info(f"[DOMAIN DETECTION] Scores: {domain_scores}")
        
        # Return domain with highest score, or GENERIC if no clear winner
        if not domain_scores or max(domain_scores.values()) < 3:
            return DomainType.GENERIC
            
        detected_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
        self.logger.info(f"[DOMAIN DETECTION] Detected domain: {detected_domain.value}")
        return detected_domain

    def perform_gap_analysis(self, content: str, domain: DomainType) -> Dict[str, Any]:
        """
        Perform comprehensive gap analysis to detect missing requirements.
        Returns dict with 'has_gaps', 'missing_requirements', and 'gap_details'.
        """
        if domain == DomainType.GENERIC or domain not in self.domain_patterns:
            # For generic domains, perform basic content analysis
            missing_requirements = []
            
            # Check for basic requirements in any domain
            basic_checks = {
                "User Authentication": ['login', 'signin', 'auth', 'authentication', 'user account'],
                "Data Management": ['create', 'update', 'delete', 'manage', 'data', 'crud'],
                "User Interface": ['ui', 'interface', 'dashboard', 'screen', 'page', 'view'],
                "Error Handling": ['error', 'validation', 'exception', 'handling', 'failure']
            }
            
            content_lower = content.lower()
            
            for req_name, keywords in basic_checks.items():
                if not any(keyword in content_lower for keyword in keywords):
                    missing_requirements.append(req_name)
            
            # For generic domains, be more lenient
            has_gaps = len(missing_requirements) > 2  # Only flag if many requirements are missing
            
            return {
                'has_gaps': has_gaps,
                'missing_requirements': missing_requirements,
                'gap_details': f"Basic analysis - {len(missing_requirements)} potential gaps identified" if has_gaps else "Basic analysis - content appears adequate"
            }
            
        pattern = self.domain_patterns[domain]
        missing_requirements = []
        gap_details = []
        content_lower = content.lower()
        
        # Define critical requirements per domain
        critical_requirements = self._get_critical_requirements_for_domain(domain)
        
        # Track found requirements for better analysis
        total_critical_requirements = 0
        found_requirements = 0
        
        # Check for missing critical requirements
        for req_category, requirements in critical_requirements.items():
            category_found = 0
            category_total = len(requirements)
            total_critical_requirements += category_total
            
            missing_in_category = []
            
            for req in requirements:
                # Check if requirement keywords are present in content
                req_keywords = req.get('keywords', [])
                req_found = any(keyword.lower() in content_lower for keyword in req_keywords)
                
                if req_found:
                    found_requirements += 1
                    category_found += 1
                else:
                    missing_in_category.append(req['name'])
                    missing_requirements.append(f"{req_category}: {req['name']}")
            
            if missing_in_category:
                gap_details.append(f"Missing {req_category}: {', '.join(missing_in_category)}")
            else:
                gap_details.append(f"Complete {req_category}: All requirements found")
        
        # Calculate coverage percentage
        coverage_ratio = found_requirements / total_critical_requirements if total_critical_requirements > 0 else 1.0
        
        # Determine if gaps are critical enough to block testing recommendations
        # More lenient threshold - only block if less than 50% coverage
        has_critical_gaps = coverage_ratio < 0.5
        
        if not has_critical_gaps and not missing_requirements:
            gap_summary = "All critical requirements are adequately covered"
        else:
            gap_summary = "; ".join(gap_details) if gap_details else "No critical gaps detected"
        
        self.logger.info(f"[GAP ANALYSIS] Domain: {domain.value}, Coverage: {coverage_ratio:.2f}, Critical gaps: {has_critical_gaps}, Missing: {len(missing_requirements)}")
        
        return {
            'has_gaps': has_critical_gaps,
            'missing_requirements': missing_requirements,
            'gap_details': gap_summary,
            'coverage_ratio': coverage_ratio,
            'total_requirements_checked': total_critical_requirements,
            'found_requirements': found_requirements
        }

    def _get_critical_requirements_for_domain(self, domain: DomainType) -> Dict[str, List[Dict]]:
        """Get critical requirements that must be present for each domain"""
        
        critical_requirements = {
            DomainType.BUSINESS_MANAGEMENT: {
                'Authentication': [
                    {'name': 'User Authentication', 'keywords': ['login', 'signin', 'auth', 'authentication', 'oauth', 'sso']},
                    {'name': 'User Authorization', 'keywords': ['role', 'permission', 'access control', 'authorization']}
                ],
                'Core Business Logic': [
                    {'name': 'Data Management', 'keywords': ['create', 'update', 'delete', 'manage', 'crud', 'data']},
                    {'name': 'User Interface', 'keywords': ['ui', 'interface', 'dashboard', 'screen', 'page', 'view']}
                ]
            },
            DomainType.EV_CHARGING: {
                'Hardware Integration': [
                    {'name': 'Charging Station Control', 'keywords': ['charging station', 'charger', 'ev charger', 'charging point']},
                    {'name': 'Power Management', 'keywords': ['power', 'electricity', 'current', 'voltage', 'kw', 'charging speed']}
                ],
                'Core Functionality': [
                    {'name': 'Charging Session Management', 'keywords': ['charging session', 'start charging', 'stop charging', 'session']},
                    {'name': 'Payment Processing', 'keywords': ['payment', 'billing', 'cost', 'price', 'tariff', 'fee']}
                ]
            },
            DomainType.FINTECH: {
                'Financial Operations': [
                    {'name': 'Transaction Processing', 'keywords': ['transaction', 'payment', 'transfer', 'financial']},
                    {'name': 'Account Management', 'keywords': ['account', 'balance', 'wallet', 'bank']}
                ],
                'Compliance & Security': [
                    {'name': 'Security Controls', 'keywords': ['security', 'encryption', 'secure', 'ssl', 'tls']},
                    {'name': 'Regulatory Compliance', 'keywords': ['compliance', 'regulation', 'audit', 'kyc', 'aml']}
                ]
            },
            DomainType.IOT_SMART_HOME: {
                'Device Integration': [
                    {'name': 'Device Connectivity', 'keywords': ['device', 'sensor', 'iot', 'connectivity', 'wireless']},
                    {'name': 'Device Control', 'keywords': ['control', 'command', 'actuator', 'switch', 'automation']}
                ],
                'Core Features': [
                    {'name': 'Monitoring & Alerts', 'keywords': ['monitor', 'alert', 'notification', 'status', 'sensor data']},
                    {'name': 'User Interface', 'keywords': ['ui', 'interface', 'dashboard', 'mobile app', 'control panel']}
                ]
            },
            DomainType.HEALTHCARE: {
                'Patient Management': [
                    {'name': 'Patient Records', 'keywords': ['patient', 'medical record', 'health record', 'ehr', 'emr']},
                    {'name': 'Medical Data', 'keywords': ['medical data', 'diagnosis', 'treatment', 'medication', 'clinical']}
                ],
                'Compliance & Security': [
                    {'name': 'HIPAA Compliance', 'keywords': ['hipaa', 'privacy', 'confidential', 'patient privacy']},
                    {'name': 'Data Security', 'keywords': ['security', 'encryption', 'access control', 'audit trail']}
                ]
            },
            DomainType.ECOMMERCE: {
                'Core Commerce': [
                    {'name': 'Product Management', 'keywords': ['product', 'catalog', 'inventory', 'item', 'merchandise']},
                    {'name': 'Shopping Cart', 'keywords': ['cart', 'basket', 'checkout', 'purchase', 'order']}
                ],
                'Transaction Processing': [
                    {'name': 'Payment Processing', 'keywords': ['payment', 'billing', 'transaction', 'checkout', 'pay']},
                    {'name': 'Order Management', 'keywords': ['order', 'fulfillment', 'shipping', 'delivery', 'tracking']}
                ]
            }
        }
        
        return critical_requirements.get(domain, {})

    def generate_contextual_tests(self, domain: DomainType, content: str, 
                                 cluster_analysis: 'ClusterAnalysis') -> List[TestRecommendation]:
        """Generate contextual test recommendations based on detected domain."""
        if domain == DomainType.GENERIC or domain not in self.domain_patterns:
            return []
            
        pattern = self.domain_patterns[domain]
        recommendations = []
        
        for template in pattern.test_templates:
            # Check if this test template is relevant to the content
            if self._is_test_relevant(template, content, pattern):
                # Find SPECIFIC stories that triggered this specific test
                specific_story_refs, relevant_content_chunks = self._find_triggering_stories_for_test(
                    template, cluster_analysis
                )
                
                # Only create recommendation if we found specific triggering stories
                if specific_story_refs:
                    enhanced_source_content = relevant_content_chunks[:2] if relevant_content_chunks else []
                    
                    # Add specific story references that actually triggered this test
                    enhanced_source_content.append(f"Referenced in: {', '.join(specific_story_refs)}")
                    
                    recommendation = TestRecommendation(
                        test_name=template['name'],
                        test_description=template['description'],
                        test_type=template['type'],
                        category=template['category'],
                        priority=template['priority'],
                        estimated_effort=template['effort'],
                        rationale=template['rationale'],
                        source_clusters=[cluster_analysis.cluster_id] if cluster_analysis else [],
                        source_content=enhanced_source_content,
                        business_impact="High" if template['priority'] == 'High' else "Medium",
                        focus_areas=self._extract_focus_areas(content, pattern),
                        domain_context=domain.value,
                        technical_requirements=self._extract_technical_requirements(content, pattern),
                        source_story=template.get('source_story', None)
                    )
                    recommendations.append(recommendation)
        
        return recommendations

    def _is_test_relevant(self, template: Dict, content: str, pattern: DomainPattern) -> bool:
        """Check if a test template is relevant to the given content."""
        content_lower = content.lower()
        template_name_lower = template['name'].lower()
        
        # Check for direct keyword matches
        for keyword in pattern.keywords:
            if keyword.lower() in content_lower:
                # Check if the test template relates to this keyword
                if any(word in template_name_lower for word in keyword.lower().split()):
                    return True
        
        # Check for business entity matches
        for entity in pattern.business_entities:
            if entity.lower() in content_lower:
                return True
                
        # Check for process matches
        for process in pattern.processes:
            if process.lower() in content_lower:
                return True
        
        return False

    def _extract_focus_areas(self, content: str, pattern: DomainPattern) -> List[str]:
        """Extract focus areas from content based on domain patterns."""
        focus_areas = []
        content_lower = content.lower()
        
        # Check which business entities are mentioned
        for entity in pattern.business_entities:
            if entity.lower() in content_lower:
                focus_areas.append(entity)
        
        # Check which processes are mentioned
        for process in pattern.processes:
            if process.lower() in content_lower:
                focus_areas.append(process)
        
        return list(set(focus_areas))  # Remove duplicates

    def _extract_technical_requirements(self, content: str, pattern: DomainPattern) -> List[str]:
        """Extract technical requirements from content."""
        requirements = []
        content_lower = content.lower()
        
        # Look for technical keywords specific to the domain
        technical_keywords = {
            'api': 'API Integration Required',
            'database': 'Database Testing Required', 
            'security': 'Security Testing Required',
            'performance': 'Performance Testing Required',
            'integration': 'Integration Testing Required',
            'protocol': 'Protocol Compliance Testing Required',
            'compliance': 'Compliance Validation Required',
            'authentication': 'Authentication Testing Required',
            'encryption': 'Encryption Testing Required'
        }
        
        for keyword, requirement in technical_keywords.items():
            if keyword in content_lower:
                requirements.append(requirement)
        
        return requirements

    def _find_best_rationale_match_with_source(self, rationale_query: str, cluster_content_chunks: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Simulates finding the best matching sentence and its source citation marker.
        
        Args:
            rationale_query: The specific question/query for the rationale (e.g., "Test accuracy of fee calculation").
            cluster_content_chunks: List of (content_text, source_identifier) tuples.
            
        Returns:
            (best_matching_sentence, source_identifier)
        """
        # *** REAL IMPLEMENTATION requires EmbeddingService.calculate_similarity ***
        # For now, we use simple keyword matching to demonstrate attribution logic:
        
        query_keywords = set(rationale_query.lower().split())
        best_score = -1
        best_match = ("", "Source N/A")
        
        for content_text, source_id in cluster_content_chunks:
            score = sum(1 for word in query_keywords if word in content_text.lower())
            
            if score > best_score:
                # Find the most relevant sentence (simple heuristic)
                sentences = re.split(r'[.!?]', content_text)
                relevant_sentence = next((s.strip() for s in sentences if score > 0 and any(w in s.lower() for w in query_keywords)), content_text.strip())
                
                best_score = score
                best_match = (relevant_sentence[:200] + "..." if len(relevant_sentence) > 200 else relevant_sentence, source_id)

        # Fallback to the initial query if no good match is found
        if best_score < 1:
             return (f"Contextual match not found. Rationale based on: {rationale_query}", "Source N/A")
             
        return best_match

    def _find_best_rationale_match(self, test_template: Dict, content_chunks: List[str]) -> Tuple[str, str]:
        """
        Perform semantic back-check to find the best content snippet that justifies this test.
        Returns enhanced rationale and source attribution.
        """
        if not self.embedding_service or not content_chunks:
            # Fallback to template rationale if no embedding service
            return test_template.get('rationale', 'Test recommended based on domain analysis'), 'Domain pattern analysis'
        
        try:
            # Create a query based on test focus areas
            test_focus = test_template.get('focus', 'general')
            test_name_lower = test_template['name'].lower()
            
            # Generate semantic query based on test type and focus
            if 'configuration' in test_name_lower or 'management' in test_name_lower:
                query_terms = ['admin', 'configure', 'manage', 'setup', 'portal', 'dashboard']
            elif 'fee' in test_name_lower or 'payout' in test_name_lower:
                query_terms = ['fee', 'cost', 'payment', 'billing', 'payout', 'revenue']
            elif 'site' in test_name_lower or 'location' in test_name_lower:
                query_terms = ['site', 'location', 'address', 'map', 'coordinate', 'pin']
            elif 'export' in test_name_lower or 'report' in test_name_lower:
                query_terms = ['export', 'report', 'data', 'excel', 'download', 'analytics']
            else:
                query_terms = test_template['name'].split()[:3]  # Use first 3 words of test name
            
            # Create query embedding
            query_text = ' '.join(query_terms)
            query_embedding = self.embedding_service.create_embedding(query_text)
            
            # Find most similar content chunks
            best_match = None
            best_similarity = 0.0
            
            for chunk in content_chunks:
                if len(chunk.strip()) < 20:  # Skip very short chunks
                    continue
                    
                chunk_embedding = self.embedding_service.create_embedding(chunk)
                similarity = self.embedding_service.calculate_similarity(query_embedding, chunk_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = chunk
            
            if best_match and best_similarity > 0.3:  # Reasonable similarity threshold
                # Extract key phrases from best matching content
                enhanced_rationale = self._create_enhanced_rationale(test_template, best_match)
                source_attribution = f"Based on BRD content: '{best_match[:100]}...'" if len(best_match) > 100 else f"Based on BRD content: '{best_match}'"
                return enhanced_rationale, source_attribution
            else:
                # No good semantic match found
                return test_template.get('rationale', 'Test recommended based on domain analysis'), 'Domain pattern analysis'
                
        except Exception as e:
            self.logger.warning(f"Semantic back-check failed: {e}")
            return test_template.get('rationale', 'Test recommended based on domain analysis'), 'Domain pattern analysis (fallback)'

    def _create_enhanced_rationale(self, test_template: Dict, matching_content: str) -> str:
        """Create enhanced rationale by combining template rationale with specific BRD content."""
        base_rationale = test_template.get('rationale', '')
        test_tier = test_template.get('tier', 2)
        test_focus = test_template.get('focus', 'general')
        
        # Extract relevant business terms from matching content
        business_terms = self._extract_business_terms(matching_content)
        
        # Create contextual rationale based on tier and focus
        if test_tier == 1 and test_focus == 'administrative':
            context_phrase = f"BRD indicates administrative requirements for {', '.join(business_terms[:2])}"
        elif test_focus == 'user_functionality':
            context_phrase = f"User stories require functionality related to {', '.join(business_terms[:2])}"
        else:
            context_phrase = f"Content analysis identifies needs for {', '.join(business_terms[:2])}"
        
        # Combine with original rationale
        if business_terms:
            enhanced_rationale = f"{base_rationale}. {context_phrase}."
        else:
            enhanced_rationale = f"{base_rationale}. Referenced in business requirements."
        
        return enhanced_rationale

    def _extract_business_terms(self, content: str) -> List[str]:
        """Extract key business terms from content for rationale enhancement."""
        import re
        
        # Look for business-relevant terms (capitalize first letter for better presentation)
        business_patterns = [
            r'\b(?:admin|administrator|administration)\b',
            r'\b(?:manage|management|manager)\b', 
            r'\b(?:configure|configuration|config)\b',
            r'\b(?:portal|dashboard|interface)\b',
            r'\b(?:fee|fees|cost|costs|billing)\b',
            r'\b(?:site|sites|location|locations)\b',
            r'\b(?:payout|payouts|settlement|settlements)\b',
            r'\b(?:export|exports|report|reports|reporting)\b',
            r'\b(?:user|users|account|accounts)\b',
            r'\b(?:device|devices|sensor|sensors)\b'
        ]
        
        found_terms = []
        content_lower = content.lower()
        
        for pattern in business_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                # Capitalize first letter for presentation
                formatted_term = match.capitalize()
                if formatted_term not in found_terms:
                    found_terms.append(formatted_term)
        
        return found_terms[:3]  # Return up to 3 most relevant terms

    def enhance_recommendations_with_attribution(self, recommendations: List[TestRecommendation], 
                                                content_chunks: List[str]) -> List[TestRecommendation]:
        """
        Enhance existing recommendations with better rationales and source attribution.
        This method can be called after generate_contextual_tests to improve the results.
        """
        enhanced_recommendations = []
        
        for recommendation in recommendations:
            # Create a mock template for attribution logic
            mock_template = {
                'name': recommendation.test_name,
                'rationale': recommendation.rationale,
                'tier': getattr(recommendation, 'tier', 2),  # Default to tier 2 if not set
                'focus': getattr(recommendation, 'focus', 'general')  # Default focus
            }
            
            # Get enhanced rationale and attribution
            enhanced_rationale, source_attribution = self._find_best_rationale_match(
                mock_template, content_chunks
            )
            
            # Create enhanced recommendation
            enhanced_recommendation = TestRecommendation(
                test_name=recommendation.test_name,
                test_description=recommendation.test_description, 
                test_type=recommendation.test_type,
                category=recommendation.category,
                priority=recommendation.priority,
                estimated_effort=recommendation.estimated_effort,
                rationale=enhanced_rationale,
                source_clusters=recommendation.source_clusters,
                source_content=recommendation.source_content,
                business_impact=recommendation.business_impact,
                focus_areas=recommendation.focus_areas,
                domain_context=recommendation.domain_context,
                technical_requirements=recommendation.technical_requirements
            )
            
            # Add source attribution as metadata if available
            if hasattr(enhanced_recommendation, 'source_attribution'):
                enhanced_recommendation.source_attribution = source_attribution
            
            enhanced_recommendations.append(enhanced_recommendation)
        
        return enhanced_recommendations