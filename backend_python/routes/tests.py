from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid

from models.schemas import TestRecommendationResponse, TestGenerationRequest
from services.supabase_service import supabase_service
from services.document_processor import document_processor
from core.logger import get_logger

router = APIRouter(prefix="/tests", tags=["tests"])
logger = get_logger(__name__)

@router.get("/{document_id}/recommendations", response_model=TestRecommendationResponse)
async def get_test_recommendations(document_id: str):
    """Get test recommendations for a document"""
    try:
        logger.info(f"Getting test recommendations for document: {document_id}")
        
        # Validate document exists
        document = await supabase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get recommendations
        recommendations = await supabase_service.get_test_recommendations(document_id)
        
        return TestRecommendationResponse(
            document_id=document_id,
            status=document.get("status", "unknown"),
            recommendations=recommendations,
            total_tests=sum(len(rec.get("tests", [])) for rec in recommendations),
            clusters_count=len(recommendations)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/clusters/{cluster_id}/regenerate")
async def regenerate_cluster_tests(document_id: str, cluster_id: str):
    """Regenerate tests for a specific cluster"""
    try:
        logger.info(f"Regenerating tests for cluster {cluster_id} in document {document_id}")
        
        # Validate document exists
        document = await supabase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Regenerate tests
        new_tests = await document_processor.regenerate_cluster_tests(document_id, cluster_id)
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "tests_generated": len(new_tests),
            "recommendations": new_tests
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating cluster tests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/generate")
async def generate_tests_for_type(document_id: str, request: TestGenerationRequest):
    """Generate specific types of tests for a document"""
    try:
        logger.info(f"Generating {request.test_types} tests for document: {document_id}")
        
        # Validate document exists
        document = await supabase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # This would be implemented to generate specific test types
        # For now, return a placeholder response
        
        return {
            "success": True,
            "document_id": document_id,
            "test_types": request.test_types,
            "message": "Specific test type generation not yet implemented"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating specific test types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/export")
async def export_tests(document_id: str, format: str = "json"):
    """Export test recommendations in various formats"""
    try:
        logger.info(f"Exporting tests for document {document_id} in {format} format")
        
        # Validate document exists
        document = await supabase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get recommendations
        recommendations = await supabase_service.get_test_recommendations(document_id)
        
        if format.lower() == "json":
            return {
                "document_id": document_id,
                "export_format": format,
                "recommendations": recommendations
            }
        else:
            # Other formats would be implemented here
            raise HTTPException(status_code=400, detail=f"Export format '{format}' not supported")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting tests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))