from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import uuid

from app.core.config import settings
from app.core.logger import debug_logger
from app.routes import documents, tests, auth, payments
from app.models.schemas import ErrorResponse

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered test recommendation engine for BRD and User Stories",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", settings.HOST]
)

# Request ID and logging middleware
@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """Add request ID and log API requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Log incoming request
    debug_logger.log_api_request(
        method=request.method,
        endpoint=str(request.url.path),
        user_id=getattr(request.state, 'user_id', None)
    )
    
    response = await call_next(request)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log response
    debug_logger.log_api_request(
        method=request.method,
        endpoint=str(request.url.path),
        user_id=getattr(request.state, 'user_id', None),
        response_time=response_time
    )
    
    return response

# Include routers
app.include_router(documents.router)
app.include_router(tests.router)
app.include_router(auth.router)
app.include_router(payments.router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    debug_logger.log_user_action("system", "health_check")
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation not available in production"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    debug_logger.log_error(
        operation=f"{request.method} {request.url.path}",
        error=exc,
        context={"request_id": request_id}
    )
    
    # Don't expose internal errors in production
    if not settings.DEBUG:
        error_message = "An internal error occurred"
    else:
        error_message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message=error_message
        ).dict()
    )

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=exc.detail
        ).dict(),
        headers={"X-Request-ID": request_id}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    debug_logger.logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    debug_logger.logger.info(f"🌐 Server running on {settings.HOST}:{settings.PORT}")
    debug_logger.logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    
    # Initialize services
    try:
        from app.services.supabase_service import supabase_service
        await supabase_service.initialize()
        debug_logger.logger.info("✅ Supabase service initialized")
    except Exception as e:
        debug_logger.log_error("supabase_initialization", e)
    
    try:
        from app.services.openai_service import openai_service
        await openai_service.initialize()
        debug_logger.logger.info("✅ OpenAI service initialized")
    except Exception as e:
        debug_logger.log_error("openai_initialization", e)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    debug_logger.logger.info(f"🛑 Shutting down {settings.APP_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )