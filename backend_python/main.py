from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import json
import logging
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
import asyncio
import traceback
import time
import re
from pathlib import Path
from dotenv import load_dotenv

# Optional Supabase import with error handling
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    Client = None
    print(f"Warning: Supabase not available: {e}")
    # Continue without Supabase - it's optional
except Exception as e:
    SUPABASE_AVAILABLE = False
    Client = None
    print(f"Warning: Supabase import failed: {e}")
    # Continue without Supabase - it's optional

from jira import JIRA
from openai import OpenAI
from langgraph.graph import StateGraph
import requests
from requests.auth import HTTPBasicAuth

# Import services
from services.domain_aware_test_engine import ClusterAnalysis

# Add necessary imports for handling different file types
try:
    import docx
    import PyPDF2
    HAS_PDF_DOCX = True
except ImportError:
    HAS_PDF_DOCX = False

try:
    import textract
    HAS_TEXTRACT = True
except ImportError:
    HAS_TEXTRACT = False

HAS_TEXT_EXTRACTION = HAS_PDF_DOCX or HAS_TEXTRACT

# Import our services
from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService  
from services.clustering_service import ClusteringService
from services.domain_aware_test_engine import DomainAwareTestEngine
from services.universal_test_architect import DomainAgnosticTestArchitect

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recommendation_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Initialize Supabase (with error handling)
supabase = None
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    else:
        logger.warning("Supabase credentials not found in environment variables")
except Exception as e:
    logger.warning(f"Failed to initialize Supabase client: {str(e)}")

# Initialize OpenAI (with error handling)
openai_api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_TEXT = "gpt-4o-mini"  # For text generation

if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info("OpenAI API key configured successfully")
    except Exception as e:
        logger.warning(f"Failed to configure OpenAI: {str(e)}")
else:
    logger.warning("OpenAI API key not found in environment variables")

# Create directory for BRD storage
BRD_UPLOADS_DIR = Path("uploads")
BRD_UPLOADS_DIR.mkdir(exist_ok=True, parents=True)

# Pydantic models
class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    filename: str
    processing_status: str

class ProcessingRequest(BaseModel):
    document_ids: List[str]
    jira_stories: Optional[List[Dict]] = []

class UserStoriesUploadResponse(BaseModel):
    success: bool
    message: str
    user_stories_id: str
    filename: str
    stories_count: int

class TextUploadRequest(BaseModel):
    content: str

class TestGenerationRequest(BaseModel):
    brd_document_id: str
    user_stories_document_id: str

class TestGenerationResponse(BaseModel):
    success: bool
    message: str
    recommendations: List[Dict[str, Any]]
    processing_details: Dict[str, Any]
    
class TestRecommendationResponse(BaseModel):
    success: bool
    clusters: List[Dict[str, Any]]
    standard_tests: List[Dict[str, Any]]
    ai_recommended_tests: List[Dict[str, Any]]
    processing_log: List[str]

# New Pydantic models from app.py for Jira and BRD functionality
class JiraConfig(BaseModel):
    email: str
    token: str
    project_name: str
    sprint_id: Optional[str] = None
    assigned_to_me: bool = False
    epic: Optional[str] = None

class JiraAuthRequest(BaseModel):
    email: str
    apiToken: str
    jiraUrl: str
    project: str
    domain: Optional[str] = None
    filterByAssignee: Optional[bool] = True
    sprint: str  # Required
    epic: Optional[str] = None  # Optional
    issueType: Optional[str] = None  # New field for issue type filter

class ComparisonRequest(BaseModel):
    brd_content: str
    jira_config: Optional[JiraConfig] = None
    user_stories: Optional[List[dict]] = None

# Create FastAPI app
app = FastAPI(
    title="Test Recommendation Engine API",
    description="AI-powered test recommendation system with clustering",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
embedding_service = EmbeddingService()
domain_aware_engine = DomainAwareTestEngine(embedding_service)  # Pass embedding service for attribution
universal_architect = DomainAgnosticTestArchitect()
clustering_service = ClusteringService()

# Note: openai_service and test_generator seem to be undefined - let's use the services we have

# Global storage for processing results
processing_results = {}
# Global storage for user stories  
user_stories_storage = {}

# Helper function for text extraction from different file types
def extract_text_from_file(file_path):
    """
    Extract text from various file types
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # Text files - read directly
        if file_ext in ['.txt', '.md', '.csv', '.json']:
            with open(file_path, "r", encoding='utf-8', errors='replace') as f:
                return f.read()
        
        # Only attempt extraction if we have the required libraries
        if not HAS_TEXT_EXTRACTION:
            return f"To view content from {file_ext} files, install required packages: pip install python-docx PyPDF2 textract"
        
        # Microsoft Word documents
        if file_ext in ['.doc', '.docx']:
            if file_ext == '.docx':
                # Use python-docx for .docx
                doc = docx.Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            else:
                # Use textract for .doc
                return textract.process(file_path).decode('utf-8', errors='replace')
        
        # PDF documents
        elif file_ext == '.pdf':
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            return text
            
        else:
            return f"Unsupported file format: {file_ext}. Please upload a text-based file."
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return f"Could not extract text from file. Error: {str(e)}"

# LangGraph Agent for BRD Analysis
def create_comparison_agent():
    # Define the state schema for StateGraph
    class ComparisonState(TypedDict, total=False):
        brd_content: str
        jira_config: dict
        brd_analysis: str
        user_stories: List[dict]
        comparison_result: str
        error: Optional[str]
        warning: Optional[str]

    def analyze_brd(state):
        brd_content = state.get("brd_content", "")
        logger.info("Analyzing BRD content with OpenAI")
        
        try:
            # Configure the OpenAI model
            
            # Enhanced prompt for BRD analysis that focuses on actual features
            prompt = f"""
            You are a business analyst. Extract only the key functional requirements, features, and acceptance criteria that are explicitly written in the BRD.
            
            Critical Instructions:
            1. Extract ONLY what is explicitly mentioned in the document
            2. Do NOT add any requirements, features, or suggestions that are not clearly stated
            3. Do NOT assume or infer additional requirements based on industry standards
            4. Focus ONLY on actual product functionality, features, and requirements as written
            5. Ignore document structure, headings, formatting, or any non-requirement content
            6. Organize your analysis by feature categories as they appear in the document
            7. Present requirements as a numbered list for clarity
            8. Only include concrete, implementable requirements that are explicitly stated
            
            Analyze this BRD and extract only the explicitly stated requirements:
            
            {brd_content}
            """
            
            # Generate response with deterministic settings for perfect consistency
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL_TEXT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Perfect deterministic output for consistent results
                max_tokens=2048,
                top_p=1.0,
                n=1  # Always return exactly one response
            )
            
            state["brd_analysis"] = response.choices[0].message.content
            logger.info("BRD analysis completed successfully with OpenAI")
            return state
        except Exception as e:
            error_msg = f"OpenAI API error during BRD analysis: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            return state

    def fetch_jira_stories(state):
        if "error" in state:
            return state
            
        jira_config = state.get("jira_config")
        logger.info(f"Fetching Jira stories from project: {jira_config['project_name']}")
        
        try:
            jira_server = f"https://{jira_config['project_name']}.atlassian.net"
            logger.info(f"Connecting to Jira server: {jira_server}")
            
            jira = JIRA(
                server=jira_server,
                basic_auth=(jira_config['email'], jira_config['token'])
            )
            
            jql = f"project = {jira_config['project_name']}"
            
            if jira_config.get('sprint_id'):
                jql += f" AND sprint = {jira_config['sprint_id']}"
            
            if jira_config.get('assigned_to_me'):
                jql += f" AND assignee = '{jira_config['email']}'"
            
            if jira_config.get('epic'):
                jql += f" AND 'Epic Link' = '{jira_config['epic']}'"
            
            logger.info(f"Executing JQL query: {jql}")
            issues = jira.search_issues(jql, maxResults=100)
            logger.info(f"Found {len(issues)} issues in Jira")
            
            user_stories = []
            for issue in issues:
                assignee_name = "Unassigned"
                if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                    assignee_name = issue.fields.assignee.displayName
                
                user_stories.append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "description": issue.fields.description or "",
                    "status": issue.fields.status.name,
                    "assignee": assignee_name
                })
            
            state["user_stories"] = user_stories
            logger.info("Successfully fetched and processed Jira stories")
            return state
            
        except Exception as e:
            error_msg = f"Failed to fetch Jira stories: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            state["error"] = error_msg
            return state

    def compare_brd_stories(state):
        if "error" in state:
            return state
            
        brd_analysis = state.get("brd_analysis", "")
        user_stories = state.get("user_stories", [])
        
        logger.info("Comparing BRD analysis with user stories using OpenAI")
        
        if not user_stories:
            warning_msg = "No user stories found for comparison"
            logger.warning(warning_msg)
            state["warning"] = warning_msg

        stories_text = "\n".join([
            f"Story {story['id'] if 'id' in story else 'Unknown'}: {story['title'] if 'title' in story else story.get('summary', 'Untitled')}\nDescription: {story.get('description', '')}\n"
            for story in user_stories
        ])
        
        try:
            # Enhanced prompt that focuses only on actual features and requirements
            prompt = f"""
            You will compare the functional requirements and features from a BRD (Business Requirements Document) with Jira user stories. 
            
            CRITICAL COMPARISON RULES:
            1. ONLY compare what is explicitly written in the BRD vs what is explicitly described in the user stories
            2. DO NOT add, suggest, or infer any requirements that are not clearly stated in the BRD
            3. DO NOT apply industry standards, best practices, or assumptions
            4. If a BRD requirement is explicitly covered by a user story, mark it as covered
            5. If a BRD requirement has no corresponding user story, mark it as missing
            6. DO NOT flag missing requirements unless they are explicitly stated in the BRD
            
            Important Formatting Requirements:
            1. Use minimal line spacing - avoid blank lines between items in the same list
            2. Use ## for main section headers only (never include section headers in numbered lists)
            3. Use **bold text** syntax for emphasis
            4. For numbered lists, use "1. " format with NO blank lines between items
            5. Only include a blank line BEFORE a heading or between major sections
            
            Content Requirements:
            1. Focus ONLY on comparing actual features and functional requirements as explicitly written
            2. Ignore document structure, headings, or any non-requirement content
            3. Only analyze substantive content representing actual product functionality as stated
            
            Your analysis must be structured into two distinct sections:

            ## COVERED REQUIREMENTS
            
            Under this heading, provide a point-by-point comparison for each BRD requirement that IS covered by one or more user stories.
            - For each BRD requirement, list it clearly.
            - Underneath it, list the specific user story or stories that cover it.
            - Use a format like this for each covered requirement:
              1. **BRD Requirement:** [The requirement from the BRD]
                 - **Covered by:** [Story ID or description]

            ## MISSING REQUIREMENTS

            Under this heading, include a numbered list of specific functional requirements from the BRD that are NOT addressed in any user story.
            - Each missing requirement must be an actual feature or capability explicitly stated in the BRD.
            - If no requirements are missing, state "No missing requirements found."
            - DO NOT include requirements that are not explicitly mentioned in the BRD.

            BRD Analysis:
            {brd_analysis}
            
            User Stories:
            {stories_text}
            
            Remember: Only compare what is explicitly written. Do not add intelligence or assumptions.
            """
            
            # Generate response with deterministic settings for perfect consistency
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL_TEXT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Perfect deterministic output for consistent results
                max_tokens=2048,
                top_p=1.0,
                n=1  # Always return exactly one response
            )
            
            # Process the response to ensure we have a structured missing requirements section
            result_text = response.choices[0].message.content
            if "## MISSING REQUIREMENTS" not in result_text:
                # Add the section header if it's missing
                result_text += "\n## MISSING REQUIREMENTS\n\n"
                result_text += "No specific missing requirements identified. The user stories appear to cover the BRD requirements adequately."
        
            state["comparison_result"] = result_text
            
            # Extract and structure missing requirements separately with improved handling
            try:
                missing_reqs_section = result_text.split("## MISSING REQUIREMENTS")[1].strip()
                missing_reqs = []
                
                # Split by numbered items (1., 2., etc.)
                import re
                req_items = re.split(r'\n\s*\d+\.\s+', '\n' + missing_reqs_section)
                
                # Process each item
                for item in req_items[1:]:  # Skip first empty item
                    if item.strip() and not item.strip().lower().startswith('no specific'):
                        missing_reqs.append(item.strip())
                
                # Store separately for easier access in frontend
                state["missing_requirements"] = missing_reqs
                logger.info(f"Successfully extracted {len(missing_reqs)} missing requirements")
            except Exception as e:
                logger.warning(f"Failed to extract structured missing requirements: {str(e)}")
                
            logger.info("Comparison analysis completed successfully with Gemini")
            return state
        except Exception as e:
            error_msg = f"Gemini API error during comparison: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            return state

    # Create LangGraph workflow
    try:
        logger.info("Creating LangGraph workflow")
        # Initialize StateGraph with the required state_schema parameter
        workflow = StateGraph(state_schema=ComparisonState)
        workflow.add_node("analyze_brd", analyze_brd)
        workflow.add_node("fetch_jira", fetch_jira_stories)
        workflow.add_node("compare", compare_brd_stories)
        
        workflow.add_edge("analyze_brd", "fetch_jira")
        workflow.add_edge("fetch_jira", "compare")
        workflow.set_entry_point("analyze_brd")
        
        logger.info("LangGraph workflow created successfully")
        return workflow.compile()
    except Exception as e:
        logger.error(f"Failed to create LangGraph workflow: {str(e)}")
        raise

def create_direct_comparison_agent():
    """
    Create a comparison agent that skips Jira fetch and directly compares BRD with provided user stories
    """
    # Define the state schema for StateGraph
    class ComparisonState(TypedDict, total=False):
        brd_content: str
        user_stories: List[dict]
        brd_analysis: str
        comparison_result: str
        error: Optional[str]
        warning: Optional[str]

    def analyze_brd(state):
        brd_content = state.get("brd_content", "")
        logger.info("Analyzing BRD content with OpenAI (direct comparison)")
        
        try:
            # Create prompt for BRD analysis
            prompt = f"""
            You are a business analyst. Extract key requirements, features, and acceptance criteria from the BRD.
            
            Analyze this BRD and extract key requirements:
            
            {brd_content}
            """
            
            # Generate response with deterministic settings for perfect consistency
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL_TEXT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Perfect deterministic output for consistent results
                max_tokens=2048,
                top_p=1.0,
                n=1  # Always return exactly one response
            )
            
            state["brd_analysis"] = response.choices[0].message.content
            logger.info("BRD analysis completed successfully with OpenAI")
            return state
        except Exception as e:
            error_msg = f"OpenAI API error during BRD analysis: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            return state

    def compare_brd_stories(state):
        if "error" in state:
            return state
            
        brd_analysis = state.get("brd_analysis", "")
        user_stories = state.get("user_stories", [])
        0
        logger.info("Comparing BRD analysis with pre-processed user stories using OpenAI")
        
        if not user_stories:
            warning_msg = "No user stories found for comparison"
            logger.warning(warning_msg)
            state["warning"] = warning_msg

        stories_text = "\n".join([
            f"Story {story['id']}: {story['title']}\nDescription: {story['description']}\n"
            for story in user_stories
        ])
        
        try:
            # Enhanced prompt for concise, well-formatted markdown with minimal spacing
            prompt = f"""
            You will compare the functional requirements and features from a BRD (Business Requirements Document) with Jira user stories. 
            
            CRITICAL COMPARISON RULES:
            1. ONLY compare what is explicitly written in the BRD vs what is explicitly described in the user stories
            2. DO NOT add, suggest, or infer any requirements that are not clearly stated in the BRD
            3. DO NOT apply industry standards, best practices, or assumptions
            4. If a BRD requirement is explicitly covered by a user story, mark it as covered
            5. If a BRD requirement has no corresponding user story, mark it as missing
            6. DO NOT flag missing requirements unless they are explicitly stated in the BRD
            
            Important Formatting Requirements:
            1. Use minimal line spacing - avoid blank lines between items in the same list
            2. Use ## for main section headers only (never include section headers in numbered lists)
            3. Use **bold text** syntax for emphasis
            4. For numbered lists, use "1. " format with NO blank lines between items
            5. Only include a blank line BEFORE a heading or between major sections
            
            Content Requirements:
            1. Focus ONLY on comparing actual features and functional requirements as explicitly written
            2. Ignore document structure, headings, or any non-requirement content
            3. Only analyze substantive content representing actual product functionality as stated
            
            Your analysis must be structured into two distinct sections:

            ## COVERED REQUIREMENTS
            
            Under this heading, provide a point-by-point comparison for each BRD requirement that IS covered by one or more user stories.
            - For each BRD requirement, list it clearly.
            - Underneath it, list the specific user story or stories that cover it.
            - Use a format like this for each covered requirement:
              1. **BRD Requirement:** [The requirement from the BRD]
                 - **Covered by:** [Story ID or description]

            ## MISSING REQUIREMENTS

            Under this heading, include a numbered list of specific functional requirements from the BRD that are NOT addressed in any user story.
            - Each missing requirement must be an actual feature or capability explicitly stated in the BRD.
            - If no requirements are missing, state "No missing requirements found."
            - DO NOT include requirements that are not explicitly mentioned in the BRD.

            BRD Analysis:
            {brd_analysis}
            
            User Stories:
            {stories_text}
            
            Remember to keep your formatting clean with minimal spacing between items in lists.
            """
            
            # Generate response with deterministic settings for perfect consistency
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL_TEXT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Perfect deterministic output for consistent results
                max_tokens=2048,
                top_p=1.0,
                n=1  # Always return exactly one response
            )
            
            # Process the response to ensure we have a structured missing requirements section
            result_text = response.choices[0].message.content
            if "## MISSING REQUIREMENTS" not in result_text:
                # Add the section header if it's missing
                result_text += "\n## MISSING REQUIREMENTS\n\n"
                result_text += "No specific missing requirements identified. The user stories appear to cover the BRD requirements adequately."
            
            state["comparison_result"] = result_text
            
            # Extract and structure missing requirements separately with improved handling
            try:
                missing_reqs_section = result_text.split("## MISSING REQUIREMENTS")[1].strip()
                missing_reqs = []
                
                # Split by numbered items (1., 2., etc.)
                import re
                req_items = re.split(r'\n\s*\d+\.\s+', '\n' + missing_reqs_section)
                
                # Process each item
                for item in req_items[1:]:  # Skip first empty item
                    if item.strip() and not item.strip().lower().startswith('no specific'):
                        missing_reqs.append(item.strip())
                
                # Store separately for easier access in frontend
                state["missing_requirements"] = missing_reqs
                logger.info(f"Successfully extracted {len(missing_reqs)} missing requirements")
            except Exception as e:
                logger.warning(f"Failed to extract structured missing requirements: {str(e)}")
                
            logger.info("Comparison analysis completed successfully with Gemini")
            return state
        except Exception as e:
            error_msg = f"Gemini API error during comparison: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            return state

    # Create LangGraph workflow
    try:
        logger.info("Creating direct comparison workflow")
        # Initialize StateGraph with the required state_schema parameter
        workflow = StateGraph(state_schema=ComparisonState)
        workflow.add_node("analyze_brd", analyze_brd)
        workflow.add_node("compare", compare_brd_stories)
        
        workflow.add_edge("analyze_brd", "compare")
        workflow.set_entry_point("analyze_brd")
        
        logger.info("Direct comparison workflow created successfully")
        return workflow.compile()
    except Exception as e:
        logger.error(f"Failed to create direct comparison workflow: {str(e)}")
        raise

# Helper function to parse user stories from text content
async def parse_user_stories_content(content: str) -> List[Dict[str, Any]]:
    """Parse user stories from uploaded text content"""
    stories = []
    
    # Split content into potential stories
    # Look for common user story patterns like "As a...", "Given...", numbered items, etc.
    lines = content.split('\n')
    current_story = ""
    story_counter = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line starts a new user story
        is_new_story = (
            line.lower().startswith('as a') or
            line.lower().startswith('as an') or
            line.lower().startswith('user story') or
            line.lower().startswith('story') or
            line.startswith(f'{story_counter}.') or
            line.startswith(f'{story_counter})')
        )
        
        if is_new_story and current_story:
            # Save previous story
            stories.append({
                'id': f'story_{len(stories) + 1}',
                'title': f'User Story {len(stories) + 1}',
                'description': current_story.strip(),
                'type': 'user_story',
                'priority': 'Medium'
            })
            current_story = line
            story_counter += 1
        else:
            if current_story:
                current_story += f"\n{line}"
            else:
                current_story = line
    
    # Add the last story
    if current_story:
        stories.append({
            'id': f'story_{len(stories) + 1}',
            'title': f'User Story {len(stories) + 1}',
            'description': current_story.strip(),
            'type': 'user_story',
            'priority': 'Medium'
        })
    
    # If no structured stories found, create one big story from all content
    if not stories:
        stories.append({
            'id': 'story_1',
            'title': 'Extracted User Requirements',
            'description': content.strip(),
            'type': 'requirements',
            'priority': 'High'
        })
    
    return stories

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Test Recommendation Engine API v2.0",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Document Processing",
            "Semantic Chunking", 
            "Embedding Generation",
            "Clustering Analysis",
            "AI Test Generation"
        ]
    }

@app.get("/api/health")
async def health_check():
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "test-recommendation-engine",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# BRD-specific upload and management routes
@app.post("/upload-brd")
async def upload_brd(file: UploadFile = File(...)):
    try:
        # Generate a unique filename to avoid conflicts
        file_ext = os.path.splitext(file.filename)[1]
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = BRD_UPLOADS_DIR / unique_filename
        
        # Save the file to disk
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text content from the file
        file_content = extract_text_from_file(file_path)
            
        logger.info(f"BRD file saved to: {file_path}")
        
        return {
            "message": "BRD uploaded successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "content": file_content
        }
    
    except Exception as e:
        error_msg = f"Error uploading BRD: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/brd-files")
async def list_brd_files():
    try:
        files = []
        for file_path in BRD_UPLOADS_DIR.glob("*"):
            if file_path.is_file():
                stats = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": stats.st_size,
                    "created": datetime.fromtimestamp(stats.st_ctime).isoformat()
                })
        
        # Sort files by upload time (newest first)
        files.sort(key=lambda x: x["path"], reverse=True)
        return {"files": files}
    
    except Exception as e:
        error_msg = f"Error listing BRD files: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/brd-file/{filename}")
async def get_brd_file(filename: str):
    try:
        file_path = BRD_UPLOADS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Extract the text content from the file
        content = extract_text_from_file(file_path)
            
        return {
            "filename": filename,
            "content": content,
            "size": file_path.stat().st_size
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error reading BRD file: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# Document routes with full processing pipeline
@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document through the complete pipeline"""
    logger.info(f"Starting document upload: {file.filename}")
    try:
        # Step 1: Process the uploaded file
        logger.info("Step 1: Processing uploaded file")
        document_data = await document_processor.process_file(file)
        document_id = document_data['document_id']
        logger.info(f"Document processed successfully: {document_id}")
        return DocumentUploadResponse(
            success=True,
            message="Document uploaded and ready for processing",
            document_id=document_id,
            filename=file.filename,
            processing_status="uploaded"
        )
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/user-stories/upload", response_model=UserStoriesUploadResponse)
async def upload_user_stories(file: UploadFile = File(...)):
    """Upload user stories file (temporary replacement for Jira integration)"""
    logger.info(f"Starting user stories upload: {file.filename}")
    try:
        # Process the user stories file
        logger.info("Processing user stories file")
        user_stories_data = await document_processor.process_file(file)
        user_stories_id = f"stories_{user_stories_data['document_id']}"
        
        # Extract and parse user stories from the content
        content = user_stories_data['raw_content']
        stories = await parse_user_stories_content(content)
        
        # Store user stories
        user_stories_storage[user_stories_id] = {
            'stories': stories,
            'filename': file.filename,
            'created_at': datetime.now().isoformat(),
            'raw_content': content
        }
        
        logger.info(f"User stories processed successfully: {user_stories_id} with {len(stories)} stories")
        
        return UserStoriesUploadResponse(
            success=True,
            message="User stories uploaded successfully",
            user_stories_id=user_stories_id,
            filename=file.filename,
            stories_count=len(stories)
        )
    except Exception as e:
        logger.error(f"User stories upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User stories upload failed: {str(e)}")

@app.post("/api/documents/process/{document_id}")
async def process_document(document_id: str, user_stories_id: Optional[str] = None):
    """Process document through complete clustering and test generation pipeline"""
    logger.info(f"Starting complete processing pipeline for document: {document_id}")
    processing_log = []
    
    # Get user stories if provided
    jira_stories = []
    if user_stories_id and user_stories_id in user_stories_storage:
        jira_stories = user_stories_storage[user_stories_id]['stories']
        logger.info(f"Using {len(jira_stories)} user stories from {user_stories_id}")
        processing_log.append(f"Using {len(jira_stories)} user stories from uploaded file")
    
    try:
        # Step 1: Get document content
        logger.info("Step 1: Retrieving document content")
        processing_log.append("Retrieving document content")
        document_content = await document_processor.get_document_content(document_id)
        # Step 2: Semantic chunking
        logger.info("Step 2: Performing semantic chunking")
        processing_log.append("Breaking document into semantic chunks")
        chunks = await document_processor.semantic_chunk(document_content, document_id)
        logger.info(f"Created {len(chunks)} semantic chunks")
        processing_log.append(f"Created {len(chunks)} semantic chunks")
        # Step 3: Generate embeddings for chunks
        logger.info("Step 3: Generating embeddings for chunks")
        processing_log.append("Generating semantic embeddings")
        embeddings = await embedding_service.generate_embeddings(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")
        processing_log.append(f"Generated {len(embeddings)} embeddings")
        # Step 4: Cluster embeddings into feature groups
        logger.info("Step 4: Clustering embeddings into feature groups")
        processing_log.append("Clustering into feature groups")
        clusters = await clustering_service.cluster_embeddings(embeddings, chunks)
        logger.info(f"Created {len(clusters)} feature clusters")
        processing_log.append(f"Created {len(clusters)} feature clusters")
        # Step 5: Analyze clusters with domain-aware engine
        logger.info("Step 5: Analyzing cluster contents")
        processing_log.append("Analyzing cluster contents with domain-aware engine")
        cluster_analyses = domain_aware_engine.analyze_clusters(clusters)
        logger.info(f"Analyzed {len(cluster_analyses)} clusters")
        processing_log.append(f"Analyzed {len(cluster_analyses)} clusters")
        # Step 6: Generate test recommendations
        logger.info("Step 6: Generating AI test recommendations")
        processing_log.append("Generating test recommendations")
        standard_tests, recommended_tests = domain_aware_engine.generate_recommendations(cluster_analyses)
        test_recommendations = domain_aware_engine.format_recommendations(standard_tests, recommended_tests)
        # Log detailed results
        logger.info(f"Generated {len(test_recommendations['standard_testing_types']['tests'])} standard tests")
        logger.info(f"Generated {len(test_recommendations['recommended_testing_types']['tests'])} AI recommended tests")
        processing_log.append(f"Generated {len(test_recommendations['standard_testing_types']['tests'])} standard tests")
        processing_log.append(f"Generated {len(test_recommendations['recommended_testing_types']['tests'])} AI tests")
        # Store results
        processing_results[document_id] = {
            "clusters": clusters,
            "test_recommendations": test_recommendations,
            "processing_log": processing_log,
            "timestamp": datetime.now().isoformat()
        }
        logger.info("Complete processing pipeline finished successfully")
        processing_log.append("Processing completed successfully")
        return TestRecommendationResponse(
            success=True,
            clusters=clusters,
            standard_tests=test_recommendations['standard_testing_types']['tests'],
            ai_recommended_tests=test_recommendations['recommended_testing_types']['tests'],
            processing_log=processing_log
        )
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        logger.error(f"{error_msg}")
        processing_log.append(f"{error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/documents/")
async def list_documents():
    """List all processed documents"""
    logger.info("Listing all documents")
    return {
        "documents": list(processing_results.keys()),
        "total": len(processing_results)
    }

@app.get("/api/documents/{document_id}/results")
async def get_document_results(document_id: str):
    """Get processing results for a specific document"""
    logger.info(f"Getting results for document: {document_id}")
    
    if document_id not in processing_results:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return processing_results[document_id]

# User Stories routes
@app.get("/api/user-stories")
async def list_user_stories():
    """List all uploaded user stories"""
    logger.info("Listing all user stories")
    
    stories_list = []
    for stories_id, stories_data in user_stories_storage.items():
        stories_list.append({
            "user_stories_id": stories_id,
            "filename": stories_data["filename"],
            "stories_count": len(stories_data["stories"]),
            "created_at": stories_data["created_at"]
        })
    
    return {
        "success": True,
        "user_stories": stories_list,
        "total_count": len(stories_list)
    }

@app.get("/api/user-stories/{user_stories_id}")
async def get_user_stories(user_stories_id: str):
    """Get specific user stories by ID"""
    logger.info(f"Getting user stories: {user_stories_id}")
    
    if user_stories_id not in user_stories_storage:
        raise HTTPException(status_code=404, detail="User stories not found")
    
    return {
        "success": True,
        "user_stories_id": user_stories_id,
        "data": user_stories_storage[user_stories_id]
    }

# Jira integration routes
@app.post("/api/jira/test-connection")
async def test_jira_connection(url: str, username: str, api_token: str):
    """Test Jira connection"""
    logger.info(f"Testing Jira connection to: {url}")
    # Implementation would go here
    return {
        "success": True,
        "message": "Connection successful"
    }

@app.post("/api/jira/projects")  
async def get_jira_projects(url: str, username: str, api_token: str):
    """Get Jira projects"""
    logger.info(f"Getting Jira projects from: {url}")
    # Implementation would go here
    return {
        "success": True,
        "projects": []
    }

@app.get("/api/debug/processing-log/{document_id}")
async def get_processing_log(document_id: str):
    """Get detailed processing log for debugging"""
    logger.info(f"🔍 Getting processing log for: {document_id}")
    
    if document_id not in processing_results:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document_id,
        "processing_log": processing_results[document_id].get("processing_log", []),
        "timestamp": processing_results[document_id].get("timestamp")
    }

@app.post("/api/documents/upload-text")
async def upload_text_content(request: TextUploadRequest):
    """Upload text content directly without file"""
    try:
        logger.info(f"[UPLOAD] Uploading text content: {len(request.content)} characters")
        
        # Create a document ID
        document_id = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Store the document
        from services.document_processor import document_storage
        document_storage[document_id] = {
            'document_id': document_id,
            'filename': 'text_content.txt',
            'content_type': 'text/plain',
            'raw_content': request.content,
            'file_size': len(request.content.encode()),
            'created_at': datetime.now().isoformat(),
            'status': 'uploaded'
        }
        
        logger.info(f"[SUCCESS] Text content uploaded successfully: {document_id}")
        
        return DocumentUploadResponse(
            success=True,
            message="Text content uploaded successfully",
            document_id=document_id,
            filename="text_content.txt",
            processing_status="uploaded"
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Text upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text upload failed: {str(e)}")

@app.post("/api/tests/generate")
async def generate_comprehensive_tests(request: TestGenerationRequest):
    """Generate comprehensive test recommendations from BRD and User Stories"""
    try:
        logger.info(f"🧪 Starting test generation for BRD: {request.brd_document_id}, User Stories: {request.user_stories_document_id}")
        
        # Get documents from storage
        from services.document_processor import document_storage
        
        if request.brd_document_id not in document_storage:
            raise HTTPException(status_code=404, detail="BRD document not found")
        
        if request.user_stories_document_id not in document_storage:
            raise HTTPException(status_code=404, detail="User Stories document not found")
        
        brd_doc = document_storage[request.brd_document_id]
        user_stories_doc = document_storage[request.user_stories_document_id]
        
        # Combine content for processing
        combined_content = f"""
BRD Content:
{brd_doc['raw_content']}

User Stories Content:
{user_stories_doc['raw_content']}
"""
        
        logger.info(f"[PROCESS] Processing combined content: {len(combined_content)} characters")
        
        # Process through our comprehensive pipeline
        result = await document_processor.process_document(
            document_id=f"combined_{request.brd_document_id}_{request.user_stories_document_id}",
            content=combined_content
        )
        
        logger.info(f"[SUCCESS] Test generation completed: {result['total_tests']} tests generated")
        
        return TestGenerationResponse(
            success=True,
            message=f"Generated {result['total_tests']} comprehensive test recommendations",
            recommendations=result['recommendations'],
            processing_details={
                'brd_document_id': request.brd_document_id,
                'user_stories_document_id': request.user_stories_document_id,
                'clusters_generated': result['clusters_generated'],
                'total_tests': result['total_tests'],
                'processing_method': 'Rule-based clustering + comprehensive test engine'
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Test generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")

@app.post("/api/tests/generate-intelligent")
async def generate_intelligent_tests(request: TestGenerationRequest):
    """Generate intelligent test recommendations using domain-aware and universal analysis"""
    try:
        logger.info(f"[INTELLIGENT] Starting INTELLIGENT test generation for BRD: {request.brd_document_id}, User Stories: {request.user_stories_document_id}")
        
        # Get documents from storage
        from services.document_processor import document_storage
        
        if request.brd_document_id not in document_storage:
            raise HTTPException(status_code=404, detail="BRD document not found")
        
        if request.user_stories_document_id not in document_storage:
            raise HTTPException(status_code=404, detail="User Stories document not found")
        
        brd_doc = document_storage[request.brd_document_id]
        user_stories_doc = document_storage[request.user_stories_document_id]
        
        # Combine content for processing
        combined_content = f"""
BRD Content:
{brd_doc['raw_content']}

User Stories Content:
{user_stories_doc['raw_content']}
"""
        
        logger.info(f"[PROCESS] Processing combined content with intelligent engines: {len(combined_content)} characters")
        
        # STEP 1: Universal Architecture Analysis
        logger.info("[STEP1] Step 1: Universal Architecture Analysis")
        universal_strategy = universal_architect.generate_universal_testing_strategy(combined_content)
        arch_analysis = universal_strategy['architecture_analysis']
        
        # STEP 2: Enhanced Domain-Specific Analysis
        logger.info("[STEP2] Step 2: Domain-Aware Content Analysis")
        
        # Use consolidated domain-aware engine for contextual analysis
        logger.info(f"[DOMAIN-AWARE] Analyzing content with consolidated Domain-Aware Engine: {len(combined_content)} characters")
        
        # Run intelligent clustering pipeline for domain-aware analysis
        document_id = f"intelligent_{request.brd_document_id}_{request.user_stories_document_id}"
        chunks = await document_processor.semantic_chunk(combined_content, document_id)
        logger.info(f"Created {len(chunks)} semantic chunks for clustering analysis")
        
        # Generate embeddings for clustering
        valid_chunks = [chunk for chunk in chunks if chunk.get('content', '').strip()]
        logger.info(f"Prepared {len(valid_chunks)} valid chunks for embedding generation")
        
        # Generate embeddings for all chunks at once
        embeddings = await embedding_service.generate_embeddings(valid_chunks)
        logger.info(f"Generated embeddings for {len(embeddings)} chunks")
        
        # Perform clustering if we have enough content
        cluster_analyses = []
        if len(embeddings) >= 2:
            clusters = await clustering_service.cluster_embeddings(embeddings, valid_chunks)
            logger.info(f"Created {len(clusters)} content clusters")
            
            # Analyze all clusters with domain-aware engine
            cluster_analyses = domain_aware_engine.analyze_clusters(clusters)
        else:
            # Create single cluster analysis for small content
            single_cluster = {
                'cluster_id': 0,
                'chunks': valid_chunks,
                'centroid': embeddings[0] if embeddings else [],
                'representative_text': valid_chunks[0]['content'] if valid_chunks else combined_content[:500],
                'size': len(valid_chunks),
                'content_chunks': [chunk.get('content', '') for chunk in valid_chunks]
            }
            cluster_analyses = domain_aware_engine.analyze_clusters([single_cluster])
        
        # Generate domain-aware test recommendations
        domain_standard_tests, domain_recommended_tests = domain_aware_engine.generate_recommendations(cluster_analyses)
        
        # Check if gap analysis detected missing requirements
        gap_detected = (len(domain_standard_tests) == 1 and 
                       domain_standard_tests[0].test_name == "Missing Requirements Detected" and
                       len(domain_recommended_tests) == 0)
        
        if gap_detected:
            logger.warning("[GAP ANALYSIS] Missing requirements detected - returning gap analysis instead of test recommendations")
            gap_info = domain_standard_tests[0]
            
            return {
                "success": True,
                "has_gap_issues": True,
                "gap_analysis": {
                    "has_gaps": True,
                    "missing_requirements": gap_info.focus_areas,
                    "gap_details": gap_info.test_description,
                    "domain": gap_info.domain_context
                },
                "message": "Missing critical requirements detected. Please address these gaps before generating test recommendations.",
                "recommendations": [],
                "standard_testing_types": [],
                "recommended_testing_types": []
            }
        
        logger.info(f"[DOMAIN-AWARE] Generated {len(domain_standard_tests)} domain-specific standard tests")
        logger.info(f"[DOMAIN-AWARE] Generated {len(domain_recommended_tests)} domain-specific recommended tests")
        
        # STEP 2.5: Enhance with Source Attribution
        logger.info("[ATTRIBUTION] Enhancing recommendations with source attribution")
        
        # Extract all content for attribution
        all_content_chunks = [combined_content[i:i+500] for i in range(0, len(combined_content), 500)]  # Split into 500-char chunks
        
        # Enhance standard tests with attribution
        if domain_standard_tests:
            domain_standard_tests = domain_aware_engine.enhance_recommendations_with_attribution(
                domain_standard_tests, all_content_chunks
            )
            logger.info(f"[ATTRIBUTION] Enhanced {len(domain_standard_tests)} standard tests with source attribution")
        
        # Enhance recommended tests with attribution  
        if domain_recommended_tests:
            domain_recommended_tests = domain_aware_engine.enhance_recommendations_with_attribution(
                domain_recommended_tests, all_content_chunks
            )
            logger.info(f"[ATTRIBUTION] Enhanced {len(domain_recommended_tests)} recommended tests with source attribution")
        
        # STEP 3: Integrate Results
        logger.info("[STEP3] Step 3: Intelligent Integration")
        
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
        domain_formatted = domain_aware_engine.format_recommendations(domain_standard_tests, domain_recommended_tests)
        
        # Add domain-aware tests
        for test in domain_formatted['standard_testing_types']['tests']:
            # Check if already exists from universal analysis
            existing = next((t for t in all_tests if t['test_type'] == test['test_name']), None)
            if existing:
                existing['source'] += ' + Domain Analysis'
                existing['category'] = 'Standard'  # Upgrade to standard if both agree
                # Enhance rationale with domain-specific content
                if test.get('source_content_preview'):
                    existing['rationale'] += f" | BRD Context: {test['source_content_preview'][0] if test['source_content_preview'] else 'N/A'}"
            else:
                # Create detailed rationale with specific BRD/User Story references
                detailed_rationale = test['rationale']
                if test.get('source_content_preview') and test['source_content_preview']:
                    detailed_rationale += f" | Referenced from BRD/User Stories: '{test['source_content_preview'][0]}'"
                
                all_tests.append({
                    'name': test['test_name'],
                    'test_type': test['test_name'],
                    'category': 'Standard',
                    'priority': test['priority'].title(),
                    'rationale': detailed_rationale,
                    'description': test.get('test_description', test['test_name']),
                    'source': 'Domain Analysis',
                    'business_impact': 'High',
                    'focus_areas': [test['test_category']],
                    'cluster_attribution': f"Clusters {', '.join(str(c) for c in test.get('source_clusters', []))} - {test.get('test_description', 'Content-based analysis')}",
                    'effort_estimate': test.get('estimated_effort', '1-2 days'),
                    'source_content': test.get('source_content_preview', [])
                })
        
        for test in domain_formatted['recommended_testing_types']['tests']:
            existing = next((t for t in all_tests if t['test_type'] == test['test_name']), None)
            if existing:
                existing['source'] += ' + Domain Analysis'
                # Enhance rationale with domain-specific content
                if test.get('source_content_preview'):
                    existing['rationale'] += f" | BRD Context: {test['source_content_preview'][0] if test['source_content_preview'] else 'N/A'}"
            else:
                # Create detailed rationale with specific BRD/User Story references
                detailed_rationale = test['rationale']
                if test.get('source_content_preview') and test['source_content_preview']:
                    detailed_rationale += f" | Referenced from BRD/User Stories: '{test['source_content_preview'][0]}'"
                
                all_tests.append({
                    'name': test['test_name'],
                    'test_type': test['test_name'],
                    'category': 'Recommended',
                    'priority': test['priority'].title(),
                    'rationale': detailed_rationale,
                    'description': test.get('test_description', test['test_name']),
                    'source': 'Domain Analysis',
                    'business_impact': 'Medium',
                    'focus_areas': [test['test_category']],
                    'cluster_attribution': f"Clusters {', '.join(str(c) for c in test.get('source_clusters', []))} - {test.get('test_description', 'Content-based analysis')}",
                    'effort_estimate': test.get('estimated_effort', '1-2 days'),
                    'source_content': test.get('source_content_preview', [])
                })
        
        # Calculate metrics
        standard_tests = [t for t in all_tests if t['category'] == 'Standard']
        recommended_tests = [t for t in all_tests if t['category'] == 'Recommended']
        multi_source_tests = [t for t in all_tests if '+' in t['source']]
        
        confidence_score = round((len(multi_source_tests) / len(all_tests)) * 100, 1) if all_tests else 0
        
        logger.info(f"[COMPLETE] Intelligent analysis complete: {len(standard_tests)} Standard + {len(recommended_tests)} Recommended tests")
        
        # Format the response to match the expected cluster structure
        cluster_recommendations = []
        
        # ENHANCED: Use only domain-specific tests (remove universal generic tests)
        total_tests = list(domain_standard_tests + domain_recommended_tests)
        
        # Skip universal tests - they're too generic and not relevant to specific user stories
        logger.info(f"[DEBUG] Using only domain-specific tests: {len(total_tests)} tests")
        
        logger.info(f"[DEBUG] Total tests to distribute: {len(total_tests)}")
        
        # Use the REAL cluster analyses from domain-aware engine (remove mock data)
        # cluster_analyses was already created earlier from real clustering results
        logger.info(f"[DEBUG] Using {len(cluster_analyses)} real clusters from domain analysis")
        
        # Distribute tests across clusters more evenly
        # FIXED: Instead of distributing tests across clusters (causing duplicates),
        # consolidate all unique tests into a single response
        all_cluster_tests = []
        
        # Collect all tests without duplication
        seen_test_names = set()
        for test in total_tests:
            test_key = f"{test.test_name}_{test.category.value if hasattr(test.category, 'value') else str(test.category)}"
            if test_key not in seen_test_names:
                seen_test_names.add(test_key)
                all_cluster_tests.append({
                    'name': test.test_name,
                    'test_type': test.test_type.value if hasattr(test.test_type, 'value') else str(test.test_type),
                    'category': test.category.value.title() if hasattr(test.category, 'value') else str(test.category).title(),
                    'priority': str(test.priority).title(),
                    'rationale': test.rationale,
                    'description': getattr(test, 'test_description', test.rationale),
                    'source': 'Enhanced Domain Analysis',
                    'business_impact': getattr(test, 'business_impact', 'High'),
                    'focus_areas': getattr(test, 'focus_areas', []),
                    'estimated_effort': test.estimated_effort,
                    'source_content': test.source_content[:2] if test.source_content else [],
                    'domain_context': getattr(test, 'domain_context', 'context_based'),
                    'source_story': getattr(test, 'source_story', None),
                    'technical_requirements': getattr(test, 'technical_requirements', [])
                })
        
        logger.info(f"[DEBUG] Consolidated {len(all_cluster_tests)} unique tests (removed duplicates)")
        
        # Helper function to extract user story references from content
        def extract_user_story_references(test_data):
            """Extract ZB-X, Story-X, BRD references, or similar from test content"""
            references = set()
            
            # Check source_story field first
            if test_data.get('source_story'):
                references.add(test_data['source_story'])
            
            # Enhanced patterns to match the domain aware engine
            patterns = [
                r'\b(ZB-\d+)\b',      # ZB-1, ZB-2, etc.
                r'\b(Story-\d+)\b',   # Story-1, Story-2, etc.
                r'\b(US-\d+)\b',      # US-1, US-2, etc.
                r'\b(REQ-\d+)\b',     # REQ-1, REQ-2, etc.
                r'\b(BRD[_\-\s]*\d+)\b',  # BRD-1, BRD_1, BRD 1, etc.
                r'\b(BR[_\-\s]*\d+)\b',   # BR-1, BR_1, BR 1, etc.
            ]
            
            # Check rationale for story references
            rationale = test_data.get('rationale', '')
            for pattern in patterns:
                matches = re.findall(pattern, rationale, re.IGNORECASE)
                for match in matches:
                    cleaned_match = re.sub(r'[_\s]+', '-', match.strip()).upper()
                    
                    # Filter out date patterns
                    date_patterns = [
                        r'^(?:OCT|NOV|DEC|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP)-\d{4}$',
                        r'^(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)-\d{4}$',
                        r'^DATE-\d{4}$',
                        r'^TIME-\d{4}$'
                    ]
                    
                    is_date_pattern = any(re.match(date_pat, cleaned_match) for date_pat in date_patterns)
                    if not is_date_pattern:
                        references.add(cleaned_match)
            
            # Check source_content for story references
            source_content = test_data.get('source_content', [])
            if isinstance(source_content, list):
                for content in source_content:
                    if isinstance(content, str):
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                cleaned_match = re.sub(r'[_\s]+', '-', match.strip()).upper()
                                
                                # Filter out date patterns
                                date_patterns = [
                                    r'^(?:OCT|NOV|DEC|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP)-\d{4}$',
                                    r'^(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)-\d{4}$',
                                    r'^DATE-\d{4}$',
                                    r'^TIME-\d{4}$'
                                ]
                                
                                is_date_pattern = any(re.match(date_pat, cleaned_match) for date_pat in date_patterns)
                                if not is_date_pattern:
                                    references.add(cleaned_match)
            
            # Return comma-separated list or fallback to "From: BRD Analysis" for better attribution
            if references:
                return ', '.join(sorted(references))
            else:
                return 'From: BRD Analysis'
        
        # Convert tests to expected format for single consolidated response
        formatted_tests = []
        for test in all_cluster_tests:
            logger.info(f"[DEBUG] Test '{test['name']}' has source_story: {test.get('source_story', 'None')}")
            
            # Extract user story references for this test
            cluster_attribution = extract_user_story_references(test)
            
            formatted_tests.append({
                'test_name': test['name'],
                'test_description': test.get('description', test['rationale']),
                'test_category': test['category'],
                'test_classification': 'STANDARD' if test['category'] == 'Standard' else 'RECOMMENDED',
                'priority': test['priority'],
                'estimated_effort': test.get('estimated_effort', '1-2 days'),
                'rationale': test['rationale'],
                'source_content': test.get('source_content', []),
                'cluster_attribution': cluster_attribution,
                'business_impact': test.get('business_impact', 'Medium'),
                'source': test.get('source', 'Analysis Engine'),
                'source_story': test.get('source_story', None)
            })
        
        # Create single consolidated cluster recommendation
        cluster_recommendations.append({
            'cluster_id': 0,
            'feature_name': 'Consolidated Test Recommendations',
            'cluster_info': {
                'functional_areas': list(set().union(*[ca.functional_areas for ca in cluster_analyses])) if cluster_analyses else [],
                'technical_components': list(set().union(*[ca.technical_components for ca in cluster_analyses])) if cluster_analyses else [],
                'risk_areas': list(set().union(*[ca.risk_areas for ca in cluster_analyses])) if cluster_analyses else [],
                'content_chunks': sum(len(ca.content_chunks) for ca in cluster_analyses) if cluster_analyses else 0
            },
            'tests': formatted_tests,
            'test_coverage': {
                'total_tests': len(formatted_tests),
                'standard_tests': len([t for t in formatted_tests if t['test_classification'] == 'STANDARD']),
                'recommended_tests': len([t for t in formatted_tests if t['test_classification'] == 'RECOMMENDED']),
                'by_category': {}
            }
        })
        
        return TestGenerationResponse(
            success=True,
            message=f"Generated {len(all_tests)} intelligent test recommendations with {confidence_score}% confidence",
            recommendations=cluster_recommendations,
            processing_details={
                'brd_document_id': request.brd_document_id,
                'user_stories_document_id': request.user_stories_document_id,
                'analysis_method': 'Domain-Aware + Universal Architecture Analysis',
                'standard_tests': len(standard_tests),
                'recommended_tests': len(recommended_tests),
                'confidence_score': confidence_score,
                'architectural_patterns': len(arch_analysis['identified_patterns']),
                'system_complexity': arch_analysis['system_complexity'],
                'security_posture': arch_analysis['security_posture'],
                'multi_source_validation': len(multi_source_tests)
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Intelligent test generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intelligent test generation failed: {str(e)}")

# BRD-Jira Comparison endpoints
@app.post("/compare")
async def compare_brd_stories(request: ComparisonRequest):
    try:
        logger.info("Received comparison request")
        if not request.brd_content:
            raise HTTPException(status_code=400, detail="BRD content is required")
        
        # Check if user stories were provided directly
        if request.user_stories:
            logger.info(f"Using {len(request.user_stories)} pre-processed user stories for comparison")
            
            # Create the initial state with BRD content and pre-processed user stories
            initial_state = {
                "brd_content": request.brd_content,
                "user_stories": request.user_stories
            }
            
            # Create and invoke an agent that skips the Jira fetch step
            comparison_agent = create_direct_comparison_agent()
            result = comparison_agent.invoke(initial_state)
            
        elif request.jira_config:
            # Original flow: fetch stories from Jira
            logger.info(f"Creating comparison agent for project: {request.jira_config.project_name}")
            agent = create_comparison_agent()
            
            initial_state = {
                "brd_content": request.brd_content,
                "jira_config": request.jira_config.dict()
            }
            
            logger.info("Invoking comparison agent with Jira fetch")
            result = agent.invoke(initial_state)
        else:
            raise HTTPException(status_code=400, detail="Either Jira config or user stories must be provided")
        
        if "error" in result:
            logger.error(f"Agent returned error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info("Storing comparison results in Supabase")
        try:
            if supabase:
                # Store comparison result
                comparison_data = {
                    'brd_analysis': result.get('brd_analysis'),
                    'user_stories': result.get('user_stories'),
                    'comparison_result': result.get('comparison_result'),
                    'jira_config': request.jira_config.dict() if request.jira_config else None
                }
                
                supabase.table('comparisons').insert(comparison_data).execute()
                logger.info("Comparison results stored successfully")
            else:
                logger.warning("Supabase not available, skipping storage")
        except Exception as e:
            logger.error(f"Failed to store comparison results: {str(e)}")
            # Continue even if storage fails
        
        # When preparing response, include missing requirements if available
        response_data = {
            "brd_analysis": result.get('brd_analysis'),
            "user_stories": result.get('user_stories', []),
            "comparison_result": result.get('comparison_result'),
            "missing_requirements": result.get('missing_requirements', [])
        }
        
        # Perform comprehensive gap analysis and coverage calculation
        try:
            logger.info("Performing comprehensive gap analysis and coverage calculation")
            combined_content = request.brd_content
            user_stories_text = ""
            if result.get('user_stories'):
                # Safely extract descriptions from user stories, ensuring all items are strings
                user_story_descriptions = []
                for story in result.get('user_stories', []):
                    if isinstance(story, dict):
                        description = story.get('description', story.get('summary', ''))
                        if description and isinstance(description, str):
                            user_story_descriptions.append(description)
                    elif isinstance(story, str):
                        user_story_descriptions.append(story)
                    # Skip any other types
                
                user_stories_text = "\n".join(user_story_descriptions)
                combined_content += "\n" + user_stories_text
            
            # Create content hash for debugging determinism
            import hashlib
            content_hash = hashlib.md5(combined_content.encode()).hexdigest()[:8]
            logger.info(f"Gap analysis content hash: {content_hash}")
            
            # Detect domain and perform gap analysis with error handling
            try:
                domain = domain_aware_engine.detect_domain(combined_content)
                # Skip intelligent gap analysis - only use basic comparison
                gap_analysis = {
                    "has_gaps": False,
                    "missing_requirements": [],
                    "gap_details": "Direct BRD to User Stories comparison only - no additional intelligence applied"
                }
                logger.info("Using direct comparison mode - no AI intelligence added")
            except Exception as gap_error:
                logger.warning(f"Gap analysis failed, using fallback: {str(gap_error)}")
                domain = domain_aware_engine.DomainType.GENERIC
                gap_analysis = {
                    "has_gaps": False,
                    "missing_requirements": [],
                    "gap_details": "Gap analysis not available due to processing error"
                }
            
            # Calculate coverage percentage based on missing requirements
            missing_reqs = result.get('missing_requirements', [])
            logger.debug(f"missing_reqs type: {type(missing_reqs)}, content: {missing_reqs}")
            
            # Filter out generic "no specific" entries from both missing_reqs and gap_analysis
            if missing_reqs:
                # Ensure all items are strings before filtering
                missing_reqs = [str(req) for req in missing_reqs if req]  # Convert to string and filter out empty items
                actual_missing_reqs = [req for req in missing_reqs if not req.lower().startswith('no specific')]
            else:
                actual_missing_reqs = []
            
            # Also check gap_analysis missing requirements
            gap_missing_reqs = gap_analysis.get("missing_requirements", [])
            logger.debug(f"gap_missing_reqs type: {type(gap_missing_reqs)}, content: {gap_missing_reqs}")
            if gap_missing_reqs:
                # Ensure all items are strings before filtering
                gap_missing_reqs = [str(req) for req in gap_missing_reqs if req]  # Convert to string and filter out empty items
                gap_actual_missing = [req for req in gap_missing_reqs if not req.lower().startswith('no specific')]
            else:
                gap_actual_missing = []
            
            # Use the larger set of missing requirements for accurate calculation
            all_missing_reqs = list(set(actual_missing_reqs + gap_actual_missing))
            
            # Check if the comparison result explicitly states no missing requirements
            comparison_text = result.get('comparison_result', '').lower()
            has_no_missing_statement = any(phrase in comparison_text for phrase in [
                'no missing requirements found',
                'no specific missing requirements',
                'all brd functional requirements are addressed',
                'all requirements appear to be covered',
                'no missing requirements identified',
                'all requirements are met',
                'complete coverage',
                'fully covered',
                'no gaps identified',
                'requirements appear to cover the brd requirements adequately'
            ])
            
            # Enhanced logic for perfect coverage detection
            if has_no_missing_statement or (len(all_missing_reqs) == 0 and comparison_text):
                missing_count = 0
                coverage_percentage = 100
                all_missing_reqs = []  # Clear the list as analysis indicates no missing requirements
                logger.info("Perfect coverage detected - no missing requirements found")
            else:
                missing_count = len(all_missing_reqs)
                
                # Simple coverage calculation - don't use domain-specific intelligence
                # Just base it on the number of missing requirements found
                if missing_count == 0:
                    coverage_percentage = 100  # Perfect coverage when no missing requirements
                    total_brd_requirements = 1  # Assume at least 1 requirement was analyzed
                else:
                    # Estimate based on missing count (conservative approach)
                    total_brd_requirements = missing_count + 5  # Conservative estimate
                    coverage_percentage = max(0, round(((total_brd_requirements - missing_count) / total_brd_requirements) * 100))
            
            # Determine coverage status and message
            if coverage_percentage == 100:
                coverage_status = "complete"
                coverage_message = "Perfect coverage! All BRD requirements are addressed by user stories."
                has_gaps_final = False  # Override gap analysis if coverage is perfect
            elif coverage_percentage >= 80:
                coverage_status = "good"
                coverage_message = f"Good coverage with {missing_count} missing requirement(s) to address."
                has_gaps_final = True
            elif coverage_percentage >= 60:
                coverage_status = "moderate"
                coverage_message = f"Moderate coverage with {missing_count} missing requirement(s) requiring attention."
                has_gaps_final = True
            else:
                coverage_status = "poor"
                coverage_message = f"Poor coverage with {missing_count} critical missing requirement(s)."
                has_gaps_final = True
            
            response_data["gap_analysis"] = {
                "has_gaps": has_gaps_final,
                "missing_requirements": all_missing_reqs,  # Use consolidated missing requirements
                "gap_details": gap_analysis["gap_details"],
                "domain": domain.value,
                "content_hash": content_hash,
                "coverage_percentage": coverage_percentage,
                "coverage_status": coverage_status,
                "coverage_message": coverage_message,
                "total_requirements_found": total_brd_requirements,
                "missing_count": missing_count
            }
            
            logger.info(f"Gap analysis completed - hash: {content_hash}, coverage: {coverage_percentage}%, missing: {missing_count}")
            
        except Exception as e:
            logger.error(f"Gap analysis failed: {str(e)}")
            # Don't fail the entire comparison if gap analysis fails
            response_data["gap_analysis"] = {
                "has_gaps": False,
                "missing_requirements": [],
                "gap_details": "Gap analysis not available",
                "domain": "unknown",
                "coverage_percentage": 0,
                "coverage_status": "unknown",
                "coverage_message": "Gap analysis not available",
                "total_requirements_found": 0,
                "missing_count": 0
            }
        
        if "warning" in result:
            response_data["warning"] = result["warning"]
            
        logger.info("Comparison completed successfully")
        return response_data
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        logger.error(f"HTTP exception in comparison: {e.detail}")
        raise
    except Exception as e:
        error_msg = f"Error in comparison: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/jira-auth")
async def jira_auth(request: JiraAuthRequest):
    """
    Authenticate with Jira using email and API token and fetch issues based on filters
    """
    try:
        logger.info(f"Authenticating with Jira for project: {request.project}, epic: {request.epic}, sprint: {request.sprint}, issueType: {request.issueType}")
        
        # Validate required fields
        if not request.project or not request.sprint:
            missing_fields = []
            if not request.project:
                missing_fields.append("project")
            if not request.sprint:
                missing_fields.append("sprint")
                
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Prepare authentication
        auth = HTTPBasicAuth(request.email, request.apiToken)
        
        # Define headers for Jira API
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Construct base URL - ensure a valid Jira URL is used
        if not request.jiraUrl:
            raise HTTPException(
                status_code=400,
                detail="Jira URL is required. Please provide your complete Atlassian URL (e.g., https://your-domain.atlassian.net)"
            )
            
        if request.jiraUrl.endswith('/'):
            base_url = request.jiraUrl[:-1]
        else:
            base_url = request.jiraUrl

        # First validate auth token by checking the current user endpoint
        validate_auth_endpoint = f"{base_url}/rest/api/3/myself"
        logger.info(f"Validating Jira authentication with endpoint: {validate_auth_endpoint}")
        
        try:
            auth_response = requests.get(
                validate_auth_endpoint,
                headers=headers,
                auth=auth,
                timeout=10
            )
            
            if not auth_response.ok:
                if auth_response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication failed. Please check your email and API token."
                    )
                elif auth_response.status_code == 403:
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied. Please check your permissions for this Jira instance."
                    )
                else:
                    raise HTTPException(
                        status_code=auth_response.status_code,
                        detail=f"Jira API error: {auth_response.text}"
                    )
            
            logger.info("Jira authentication successful")
            
            # Build simple query with project and sprint
            sprint_value = request.sprint.strip()
            jql = f'project = "{request.project}" AND sprint = "{sprint_value}"'
            
            # Add epic filter if provided
            if request.epic and request.epic.strip():
                jql += f' AND "Epic Link" = "{request.epic.strip()}"'
            
            # Add issue type filter if provided
            if request.issueType and request.issueType.strip():
                jql += f' AND issuetype = "{request.issueType.strip()}"'
            
            # Add assignee filter if requested
            if request.filterByAssignee:
                jql += f' AND assignee = "{request.email}"'
            
            logger.info(f"Using JQL query: {jql}")
            
            # Fetch issues
            search_endpoint = f"{base_url}/rest/api/3/search/jql"
            
            response = requests.post(
                search_endpoint,
                headers=headers,
                json={
                    'jql': jql,
                    'maxResults': 200,
                    'fields': ['key', 'summary', 'status', 'assignee', 'created', 'updated', 'issuetype', 'description', 'priority', 'labels', 'reporter', 'components', 'parent']
                },
                auth=auth,
                timeout=30
            )
            
            if not response.ok:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch Jira issues: {response.text}"
                )
            
            data = response.json()
            issues = data.get('issues', [])
            
            logger.info(f"Successfully fetched {len(issues)} Jira issues")
            
            return {
                "success": True,
                "message": f"Successfully fetched {len(issues)} issues from Jira",
                "issues": issues,
                "project": request.project,
                "sprint": request.sprint,
                "epic": request.epic,
                "total_count": len(issues)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when authenticating with Jira: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Connection error to Jira API: {str(e)}")
            
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when authenticating with Jira: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Connection error to Jira API: {str(e)}")
    except Exception as e:
        logger.error(f"Error authenticating with Jira: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with Jira: {str(e)}")

@app.post("/api/process-jira-issues")
async def process_jira_issues(data: dict = Body(...)):
    """
    Process Jira issues and convert them to user stories
    """
    try:
        session_id = data.get("session_id")
        issues = data.get("issues", [])
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
            
        if not issues:
            raise HTTPException(status_code=400, detail="Issues data is required")
            
        logger.info(f"Processing {len(issues)} Jira issues for session {session_id}")
        
        # Convert Jira issues to user stories
        user_stories = []
        for i, issue in enumerate(issues):
            fields = issue.get('fields', {})
            
            # Extract assignee information
            assignee = fields.get('assignee')
            assignee_name = "Unassigned"
            if assignee:
                assignee_name = assignee.get('displayName', assignee.get('name', 'Unknown'))
            
            # Extract status
            status = fields.get('status', {})
            status_name = status.get('name', 'Unknown')
            
            # Extract issue type
            issuetype = fields.get('issuetype', {})
            issue_type = issuetype.get('name', 'Story')
            
            # Create user story object
            user_story = {
                'id': f'story_{i+1}',
                'jira_key': issue.get('key', ''),
                'title': fields.get('summary', 'Untitled Story'),
                'description': fields.get('description', '') or f"Jira Issue: {issue.get('key', '')}",
                'status': status_name,
                'assignee': assignee_name,
                'issue_type': issue_type,
                'priority': fields.get('priority', {}).get('name', 'Medium'),
                'labels': fields.get('labels', []),
                'created': fields.get('created', ''),
                'updated': fields.get('updated', '')
            }
            
            user_stories.append(user_story)
        
        logger.info(f"Converted {len(user_stories)} Jira issues to user stories")
        
        return {
            "user_stories": user_stories,
            "metadata": {
                "projectKey": data.get("project", ""),
                "sprintName": data.get("sprint", ""),
                "epicName": data.get("epic", ""),
                "totalIssues": len(issues)
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing Jira issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process Jira issues: {str(e)}")