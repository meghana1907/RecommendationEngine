import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Create colored level name
        record.colored_levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)

class DebugLogger:
    """Comprehensive logging system for the Dynamic Test Recommendation Engine"""
    
    def __init__(self):
        self.logger = logging.getLogger("test_recommendation_engine")
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(colored_levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for all logs
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def log_file_upload(self, filename: str, size: int, content_type: str):
        """Log file upload details"""
        self.logger.info(f"FILE UPLOAD STARTED: {filename} ({size/1024:.2f} KB, {content_type})")
    
    def log_jira_import(self, project_key: str, stories_count: int):
        """Log Jira import details"""
        self.logger.info(f"JIRA IMPORT: Project {project_key} - {stories_count} stories imported")
    
    def log_chunking(self, filename: str, total_chunks: int, avg_tokens: int):
        """Log text chunking completion"""
        self.logger.info(f"TEXT CHUNKING: {filename} - {total_chunks} chunks (avg {avg_tokens} tokens)")
    
    def log_embedding_generation(self, chunk_id: str, chunk_preview: str, dimensions: int):
        """Log embedding generation"""
        self.logger.info(f"EMBEDDING GENERATED: {chunk_id} - {chunk_preview[:50]}... ({dimensions}D)")
    
    def log_clustering(self, total_embeddings: int, clusters_found: int, distribution: Dict[str, Any]):
        """Log clustering completion"""
        self.logger.info(f"CLUSTERING COMPLETE: {total_embeddings} embeddings -> {clusters_found} clusters")
        self.logger.debug(f"Cluster distribution: {json.dumps(distribution, indent=2)}")
    
    def log_llm_call(self, model: str, prompt_preview: str, response_preview: str, tokens_used: int = None):
        """Log LLM API calls"""
        token_info = f" ({tokens_used} tokens)" if tokens_used else ""
        self.logger.info(f"LLM CALL ({model}): {prompt_preview[:100]}...{token_info}")
        self.logger.debug(f"LLM Response preview: {response_preview[:200]}...")
    
    def log_database_operation(self, operation: str, table: str, record_id: str, success: bool):
        """Log database operations"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"DB {operation.upper()}: {table}.{record_id} - {status}")
    
    def log_test_recommendation(self, cluster_id: int, standard_count: int, recommended_count: int):
        """Log test recommendation generation"""
        self.logger.info(f"TESTS GENERATED: Cluster {cluster_id} - {standard_count} standard, {recommended_count} recommended")
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user actions"""
        detail_str = f" - {json.dumps(details)}" if details else ""
        self.logger.info(f"👤 USER ACTION: {user_id} - {action}{detail_str}")
    
    def log_payment_event(self, user_id: str, event: str, amount: float = None, plan: str = None):
        """Log payment events"""
        amount_str = f" ${amount:.2f}" if amount else ""
        plan_str = f" ({plan})" if plan else ""
        self.logger.info(f"PAYMENT: {user_id} - {event}{amount_str}{plan_str}")
    
    def log_email_sent(self, recipient: str, subject: str, success: bool):
        """Log email sending"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"EMAIL: {recipient} - {subject} - {status}")
    
    def log_export(self, document_id: str, format: str, file_size: int):
        """Log export operations"""
        self.logger.info(f"EXPORT: {document_id} -> {format} ({file_size/1024:.2f} KB)")
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any] = None):
        """Log errors with context"""
        context_str = f" Context: {json.dumps(context)}" if context else ""
        self.logger.error(f"ERROR in {operation}: {str(error)}{context_str}")
        self.logger.debug(f"Error traceback:", exc_info=True)
    
    def log_progress(self, step: int, total_steps: int, operation: str):
        """Log progress updates"""
        percentage = int((step / total_steps) * 100)
        self.logger.info(f"PROGRESS: Step {step}/{total_steps} ({percentage}%) - {operation}")
    
    def log_api_request(self, method: str, endpoint: str, user_id: str = None, response_time: float = None):
        """Log API requests"""
        user_str = f" (User: {user_id})" if user_id else ""
        time_str = f" - {response_time:.3f}s" if response_time else ""
        self.logger.info(f"🌐 API: {method} {endpoint}{user_str}{time_str}")
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None):
        """Log cache operations"""
        hit_str = " HIT" if hit is True else " MISS" if hit is False else ""
        self.logger.debug(f"🗄️ CACHE {operation.upper()}: {key}{hit_str}")
    
    def log_security_event(self, event: str, user_id: str = None, ip_address: str = None, severity: str = "INFO"):
        """Log security events"""
        user_str = f" User: {user_id}" if user_id else ""
        ip_str = f" IP: {ip_address}" if ip_address else ""
        
        if severity.upper() == "WARNING":
            self.logger.warning(f"🛡️ SECURITY WARNING: {event}{user_str}{ip_str}")
        elif severity.upper() == "ERROR":
            self.logger.error(f"🛡️ SECURITY ALERT: {event}{user_str}{ip_str}")
        else:
            self.logger.info(f"🛡️ SECURITY: {event}{user_str}{ip_str}")

# Create global logger instance
debug_logger = DebugLogger()

# Create logs directory if it doesn't exist
import os
os.makedirs("logs", exist_ok=True)