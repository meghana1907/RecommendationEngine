from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio

from app.models.schemas import (
    DocumentResponse, DocumentStatusResponse, UploadResponse,
    JiraImportRequest, JiraImportResponse, ProcessingStatus, DocumentType
)
from app.services.jira_service import jira_service
from app.services.supabase_service import supabase_service
from app.services.document_processor import document_processor
from app.core.logger import debug_logger

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.REQUIREMENTS)
):
    """Upload a document file for processing"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Check file type
        allowed_extensions = ['.txt', '.doc', '.docx', '.pdf']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Log upload
        debug_logger.log_file_upload(file.filename, len(content), file.content_type or "unknown")
        
        # Create document record
        document_id = str(uuid.uuid4())
        document_data = {
            "id": document_id,
            "filename": file.filename,
            "content": content.decode('utf-8', errors='ignore'),
            "content_type": file.content_type or "application/octet-stream",
            "file_size": len(content),
            "document_type": document_type.value,
            "processing_status": ProcessingStatus.PROCESSING.value,
            "upload_timestamp": datetime.now(),
            "created_at": datetime.now()
        }
        
        # Store in database
        await supabase_service.insert_document(document_data)
        
        # Start background processing
        asyncio.create_task(process_document_background(document_id, content.decode('utf-8', errors='ignore'), file.filename))
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            message="Document uploaded successfully. Processing started.",
            status=ProcessingStatus.PROCESSING
        )
        
    except Exception as e:
        debug_logger.log_error("document_upload", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-text", response_model=UploadResponse)
async def upload_text_content(
    content: str = Form(...),
    filename: str = Form("pasted-content.txt"),
    document_type: DocumentType = Form(DocumentType.REQUIREMENTS)
):
    """Upload text content directly"""
    try:
        if len(content.strip()) < 100:
            raise HTTPException(status_code=400, detail="Content must be at least 100 characters")
        
        # Log upload
        debug_logger.log_file_upload(filename, len(content), "text/plain")
        
        # Create document record
        document_id = str(uuid.uuid4())
        document_data = {
            "id": document_id,
            "filename": filename,
            "content": content,
            "content_type": "text/plain",
            "file_size": len(content),
            "document_type": document_type.value,
            "processing_status": ProcessingStatus.PROCESSING.value,
            "upload_timestamp": datetime.now(),
            "created_at": datetime.now()
        }
        
        # Store in database
        await supabase_service.insert_document(document_data)
        
        # Start background processing
        asyncio.create_task(process_document_background(document_id, content, filename))
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            message="Content uploaded successfully. Processing started.",
            status=ProcessingStatus.PROCESSING
        )
        
    except Exception as e:
        debug_logger.log_error("text_upload", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-jira", response_model=JiraImportResponse)
async def import_from_jira(request: JiraImportRequest):
    """Import user stories from Jira"""
    try:
        # Test Jira connection
        if not jira_service.authenticate(request.credentials):
            raise HTTPException(status_code=400, detail="Failed to authenticate with Jira")
        
        # Search for user stories
        user_stories = jira_service.search_user_stories(
            project_key=request.project_key,
            jql_query=request.jql_query,
            include_subtasks=request.include_subtasks
        )
        
        if not user_stories:
            return JiraImportResponse(
                success=False,
                message="No user stories found matching the criteria"
            )
        
        # Format as document
        document_content = jira_service.format_stories_as_document(user_stories, request.project_key)
        
        # Create document record
        document_id = str(uuid.uuid4())
        filename = f"jira_import_{request.project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        document_data = {
            "id": document_id,
            "filename": filename,
            "content": document_content,
            "content_type": "text/plain",
            "file_size": len(document_content),
            "document_type": DocumentType.JIRA_IMPORT.value,
            "processing_status": ProcessingStatus.PROCESSING.value,
            "upload_timestamp": datetime.now(),
            "created_at": datetime.now()
        }
        
        # Store in database
        await supabase_service.insert_document(document_data)
        
        # Start background processing
        asyncio.create_task(process_document_background(document_id, document_content, filename))
        
        return JiraImportResponse(
            success=True,
            document_id=document_id,
            imported_stories=len(user_stories),
            message=f"Successfully imported {len(user_stories)} user stories from Jira"
        )
        
    except Exception as e:
        debug_logger.log_error("jira_import", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jira/projects")
async def get_jira_projects(
    base_url: str,
    username: str, 
    api_token: str
):
    """Get accessible Jira projects"""
    try:
        from app.models.schemas import JiraCredentials
        credentials = JiraCredentials(
            base_url=base_url,
            username=username,
            api_token=api_token
        )
        
        if not jira_service.authenticate(credentials):
            raise HTTPException(status_code=400, detail="Failed to authenticate with Jira")
        
        projects = jira_service.get_projects()
        return {"projects": projects}
        
    except Exception as e:
        debug_logger.log_error("get_jira_projects", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jira/test-connection")
async def test_jira_connection(request: JiraImportRequest):
    """Test Jira connection"""
    try:
        result = jira_service.test_connection(request.credentials)
        return result
        
    except Exception as e:
        debug_logger.log_error("test_jira_connection", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """Get document processing status"""
    try:
        document = await supabase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Calculate progress percentage
        status_progress = {
            ProcessingStatus.PENDING: 5,
            ProcessingStatus.PROCESSING: 20,
            ProcessingStatus.CHUNKING: 35,
            ProcessingStatus.EMBEDDING: 50,
            ProcessingStatus.CLUSTERING: 70,
            ProcessingStatus.GENERATING_TESTS: 90,
            ProcessingStatus.COMPLETED: 100,
            ProcessingStatus.FAILED: 0
        }
        
        progress = status_progress.get(ProcessingStatus(document["processing_status"]), 0)
        
        return DocumentStatusResponse(
            document_id=document_id,
            status=ProcessingStatus(document["processing_status"]),
            total_chunks=document.get("total_chunks", 0),
            upload_timestamp=document["upload_timestamp"],
            progress_percentage=progress
        )
        
    except Exception as e:
        debug_logger.log_error("get_document_status", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_documents():
    """List all documents"""
    try:
        documents = await supabase_service.list_documents()
        return {"documents": documents}
        
    except Exception as e:
        debug_logger.log_error("list_documents", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all related data"""
    try:
        success = await supabase_service.delete_document(document_id)
        if success:
            return {"success": True, "message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        debug_logger.log_error("delete_document", e)
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_background(document_id: str, content: str, filename: str):
    """Background task for document processing"""
    try:
        debug_logger.log_progress(1, 5, "Starting document processing")
        
        # Process the document
        result = await document_processor.process_document(document_id, content, filename)
        
        if result["success"]:
            await supabase_service.update_document_status(document_id, ProcessingStatus.COMPLETED)
            debug_logger.log_progress(5, 5, "Document processing completed successfully")
        else:
            await supabase_service.update_document_status(document_id, ProcessingStatus.FAILED)
            debug_logger.log_error("document_processing", Exception(result.get("error", "Unknown error")))
            
    except Exception as e:
        debug_logger.log_error("background_processing", e)
        await supabase_service.update_document_status(document_id, ProcessingStatus.FAILED)