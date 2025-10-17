from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Test Recommendation Engine API",
    description="AI-powered test recommendation system",
    version="1.0.0"
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

@app.get("/")
async def root():
    return {
        "message": "Test Recommendation Engine API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "test-recommendation-engine",
        "version": "1.0.0"
    }

# Document routes - simplified for testing
@app.post("/api/documents/upload-text")
async def upload_text(content: str, filename: str = "text_document.txt"):
    """Upload text content directly"""
    document_id = f"doc_test_123"
    
    return {
        "success": True,
        "message": "Text content uploaded successfully",
        "document_id": document_id,
        "filename": filename
    }

@app.get("/api/documents/")
async def list_documents():
    """List all documents"""
    return {
        "documents": [],
        "total": 0
    }

# Jira routes - simplified for testing
@app.post("/api/jira/test-connection")
async def test_jira_connection(url: str, username: str, api_token: str):
    """Test Jira connection"""
    return {
        "success": True,
        "message": "Connection successful"
    }

@app.post("/api/jira/projects")  
async def get_jira_projects(url: str, username: str, api_token: str):
    """Get Jira projects"""
    return {
        "success": True,
        "projects": []
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )