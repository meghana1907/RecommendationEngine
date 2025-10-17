from typing import List, Dict, Any
import os
import logging
import time
import numpy as np
from dotenv import load_dotenv

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

load_dotenv()
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.is_available = False
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading sentence transformer model: {model_name}")
                self.model = SentenceTransformer(model_name)
                self.is_available = True
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.is_available = False
        else:
            logger.warning("sentence-transformers not available")
            self.is_available = False
    
    def get_embedding_dimension(self) -> int:
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 384
    
    def generate_embeddings_text(self, texts: List[str]) -> List[List[float]]:
        if not self.is_available or not texts:
            # Use deterministic dummy embeddings based on text hash
            logger.warning("[FALLBACK] Model not available or no texts, generating deterministic dummy embeddings")
            dummy_embeddings = []
            for i, text in enumerate(texts):
                # Create deterministic dummy embedding based on text content hash
                text_hash = hash(text) % (2**31)  # Ensure positive hash
                np.random.seed(text_hash)  # Set seed based on text content
                dummy_embedding = np.random.rand(384).tolist()
                dummy_embeddings.append(dummy_embedding)
            return dummy_embeddings
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            # Use deterministic fallback
            dummy_embeddings = []
            for i, text in enumerate(texts):
                text_hash = hash(text) % (2**31)
                np.random.seed(text_hash)
                dummy_embedding = np.random.rand(384).tolist()
                dummy_embeddings.append(dummy_embedding)
            return dummy_embeddings
    
    async def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Starting embedding generation for {len(chunks)} chunks")
        embeddings = []
        
        try:
            texts = []
            for chunk in chunks:
                text_content = chunk.get('content', chunk.get('text', ''))
                if text_content:
                    texts.append(text_content)
            
            if self.is_available and texts:
                embedding_vectors = self.generate_embeddings_text(texts)
                
                for i, (chunk, embedding_vector) in enumerate(zip(chunks, embedding_vectors)):
                    embedding_data = {
                        'chunk_id': chunk.get('chunk_id', f"chunk_{i}"),
                        'content': chunk.get('content', chunk.get('text', '')),
                        'embedding': embedding_vector,
                        'metadata': chunk.get('metadata', {}),
                        'document_id': chunk.get('document_id'),
                        'chunk_index': i
                    }
                    embeddings.append(embedding_data)
            else:
                for i, chunk in enumerate(chunks):
                    # Generate deterministic dummy embedding based on content
                    text_content = chunk.get('content', chunk.get('text', ''))
                    text_hash = hash(text_content) % (2**31)
                    np.random.seed(text_hash)
                    dummy_embedding = np.random.rand(384).tolist()
                    embedding_data = {
                        'chunk_id': chunk.get('chunk_id', f"chunk_{i}"),
                        'content': chunk.get('content', chunk.get('text', '')),
                        'embedding': dummy_embedding,
                        'metadata': chunk.get('metadata', {}),
                        'document_id': chunk.get('document_id'),
                        'chunk_index': i
                    }
                    embeddings.append(embedding_data)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise Exception(f"Embedding generation failed: {e}")
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def find_similar_chunks(self, query_embedding: List[float], chunk_embeddings: List[Dict], threshold: float = 0.7) -> List[Dict]:
        similar_chunks = []
        
        for chunk in chunk_embeddings:
            chunk_embedding = chunk.get('embedding', [])
            if chunk_embedding:
                similarity = self.calculate_similarity(query_embedding, chunk_embedding)
                if similarity >= threshold:
                    chunk['similarity'] = similarity
                    similar_chunks.append(chunk)
        
        similar_chunks.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_chunks
