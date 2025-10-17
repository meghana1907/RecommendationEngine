import logging
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class ClusteringService:
    """Service for clustering embeddings into feature/functionality groups - OPTIMIZED for fewer, more meaningful clusters"""
    
    def __init__(self):
        self.min_clusters = 2
        self.max_clusters = 6  # REDUCED from 10 to create fewer, larger clusters
        self.optimal_cluster_method = "silhouette"  # or "elbow"
        logger.info("Clustering service initialized with OPTIMIZED parameters for fewer API calls")
    
    async def cluster_embeddings(self, embeddings: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cluster embeddings into feature groups using KMeans with optimal cluster detection"""
        logger.info(f"[CLUSTERING] Starting clustering process for {len(embeddings)} embeddings")
        
        if len(embeddings) < 2:
            logger.warning("[CLUSTERING] Not enough embeddings for clustering, creating single cluster")
            return self._create_single_cluster(embeddings, chunks)
        
        try:
            # Extract embedding vectors
            logger.info("[CLUSTERING] Extracting embedding vectors...")
            embedding_vectors = [emb['embedding'] for emb in embeddings]
            embedding_matrix = np.array(embedding_vectors)
            logger.info(f"[CLUSTERING] Embedding matrix shape: {embedding_matrix.shape}")
            
            # Find optimal number of clusters
            logger.info("[CLUSTERING] Finding optimal number of clusters...")
            optimal_k = self._find_optimal_clusters(embedding_matrix)
            logger.info(f"[CLUSTERING] Optimal number of clusters determined: {optimal_k}")
            
            # Perform KMeans clustering
            logger.info(f"[CLUSTERING] Performing KMeans clustering with k={optimal_k}")
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embedding_matrix)
            logger.info(f"[CLUSTERING] KMeans clustering completed. Cluster labels: {cluster_labels}")
            
            # Create cluster groups
            logger.info("[CLUSTERING] Creating cluster groups...")
            clusters = self._create_cluster_groups(embeddings, chunks, cluster_labels, kmeans)
            
            # Log clustering results
            logger.info("[CLUSTERING] Logging clustering results...")
            self._log_clustering_results(clusters, embedding_matrix, cluster_labels)
            
            logger.info(f"[CLUSTERING] Successfully created {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"[CLUSTERING] Clustering failed: {e}")
            logger.info("[CLUSTERING] Falling back to single cluster")
            return self._create_single_cluster(embeddings, chunks)
    
    def _find_optimal_clusters(self, embedding_matrix: np.ndarray) -> int:
        """Find optimal number of clusters using silhouette analysis"""
        logger.info("[CLUSTERING] Finding optimal number of clusters using silhouette analysis")
        n_samples = len(embedding_matrix)
        max_k = min(self.max_clusters, n_samples - 1)
        
        if max_k < self.min_clusters:
            logger.warning(f"[CLUSTERING] Not enough samples for multiple clusters, using k=2")
            return 2
            
        logger.info(f"[CLUSTERING] Testing cluster counts from {self.min_clusters} to {max_k}")
        
        best_k = self.min_clusters
        best_score = -1
        scores = {}
        
        try:
            for k in range(self.min_clusters, max_k + 1):
                logger.info(f"[CLUSTERING] Testing k={k}")
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(embedding_matrix)
                # Calculate silhouette score
                score = silhouette_score(embedding_matrix, cluster_labels)
                scores[k] = score
                logger.info(f"[CLUSTERING] k={k}, silhouette_score={score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_k = k
                    
            logger.info(f"[CLUSTERING] Optimal k={best_k} with silhouette score={best_score:.3f}")
            logger.info(f"[CLUSTERING] All scores: {scores}")
            return best_k
            
        except Exception as e:
            logger.error(f"[CLUSTERING] Optimal cluster detection failed: {e}")
            logger.info(f"[CLUSTERING] Using default k={self.min_clusters}")
            return self.min_clusters
    
    def _create_cluster_groups(self, embeddings: List[Dict], chunks: List[Dict], cluster_labels: np.ndarray, kmeans) -> List[Dict]:
        """Create cluster groups with metadata"""
        logger.info("[CLUSTERING] Creating cluster groups")
        clusters = {}
        
        # Group embeddings by cluster
        logger.info(f"[CLUSTERING] Grouping {len(embeddings)} embeddings into clusters...")
        for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
            cluster_id = int(cluster_labels[i])
            
            if cluster_id not in clusters:
                logger.info(f"[CLUSTERING] Creating new cluster {cluster_id}")
                clusters[cluster_id] = {
                    'cluster_id': cluster_id,
                    'chunks': [],
                    'embeddings': [],
                    'centroid': kmeans.cluster_centers_[cluster_id].tolist(),
                    'size': 0
                }
                
            clusters[cluster_id]['chunks'].append(chunk)
            clusters[cluster_id]['embeddings'].append(embedding)
            clusters[cluster_id]['size'] += 1
            
        logger.info(f"[CLUSTERING] Created {len(clusters)} clusters")
        for cluster_id, cluster_data in clusters.items():
            logger.info(f"[CLUSTERING] Cluster {cluster_id}: {cluster_data['size']} chunks")
        
        # Convert to list and add metadata
        cluster_list = []
        for cluster_id, cluster_data in clusters.items():
            # Extract representative content
            chunk_contents = [chunk.get('content', chunk.get('text', '')) for chunk in cluster_data['chunks']]
            cluster_info = {
                'cluster_id': cluster_id,
                'size': cluster_data['size'],
                'chunks': cluster_data['chunks'],
                'content_chunks': chunk_contents,  # Changed from chunk_contents to content_chunks
                'centroid': cluster_data['centroid'],
                'representative_text': self._get_representative_text(chunk_contents),
                'metadata': {
                    'total_characters': sum(len(content) for content in chunk_contents),
                    'avg_chunk_length': np.mean([len(content) for content in chunk_contents]) if chunk_contents else 0,
                    'chunk_count': len(chunk_contents)
                }
            }
            cluster_list.append(cluster_info)
            logger.debug(f"Cluster {cluster_id}: {cluster_data['size']} chunks, avg_length={cluster_info['metadata']['avg_chunk_length']:.1f}")
        # Sort clusters by size (largest first)
        cluster_list.sort(key=lambda x: x['size'], reverse=True)
        logger.info(f"Created {len(cluster_list)} clusters")
        return cluster_list
    
    def _get_representative_text(self, chunk_contents: List[str]) -> str:
        """Get representative text from cluster chunks"""
        if not chunk_contents:
            return ""
        
        # For now, return the longest chunk as representative
        # Could be enhanced with more sophisticated selection
        longest_chunk = max(chunk_contents, key=len) if chunk_contents else ""
        
        # Truncate if too long
        if len(longest_chunk) > 500:
            longest_chunk = longest_chunk[:500] + "..."
        
        return longest_chunk
    
    def _create_single_cluster(self, embeddings: List[Dict], chunks: List[Dict]) -> List[Dict]:
        """Create a single cluster when clustering is not possible"""
        logger.info("Creating single cluster fallback")
        chunk_contents = []
        for chunk in chunks:
            content = chunk.get('content', chunk.get('text', ''))
            if content:
                chunk_contents.append(content)
        single_cluster = {
            'cluster_id': 0,
            'size': len(chunks),
            'chunks': chunks,
            'content_chunks': chunk_contents,  # Changed from chunk_contents to content_chunks
            'centroid': None,
            'representative_text': self._get_representative_text(chunk_contents),
            'metadata': {
                'total_characters': sum(len(content) for content in chunk_contents),
                'avg_chunk_length': np.mean([len(content) for content in chunk_contents]) if chunk_contents else 0,
                'chunk_count': len(chunk_contents),
                'note': 'Single cluster created due to insufficient data for clustering'
            }
        }
        return [single_cluster]
    
    def _log_clustering_results(self, clusters: List[Dict], embedding_matrix: np.ndarray, cluster_labels: np.ndarray):
        """Log detailed clustering results for debugging"""
        logger.info("Clustering Results Summary:")
        logger.info(f"   - Total clusters: {len(clusters)}")
        logger.info(f"   - Total data points: {len(embedding_matrix)}")
        # Cluster size distribution
        sizes = [cluster['size'] for cluster in clusters]
        logger.info(f"   - Cluster sizes: {sizes}")
        logger.info(f"   - Largest cluster: {max(sizes)} chunks")
        logger.info(f"   - Smallest cluster: {min(sizes)} chunks")
        logger.info(f"   - Average cluster size: {np.mean(sizes):.1f} chunks")
        # Log sample content from each cluster
        for i, cluster in enumerate(clusters[:5]):  # Show first 5 clusters
            sample_text = cluster['representative_text'][:100] + "..." if len(cluster['representative_text']) > 100 else cluster['representative_text']
            logger.info(f"   - Cluster {cluster['cluster_id']} ({cluster['size']} chunks): {sample_text}")
        # Calculate and log silhouette score
        try:
            if len(set(cluster_labels)) > 1:  # Need at least 2 clusters for silhouette score
                silhouette_avg = silhouette_score(embedding_matrix, cluster_labels)
                logger.info(f"   - Overall silhouette score: {silhouette_avg:.3f}")
        except Exception as e:
            logger.debug(f"Could not calculate silhouette score: {e}")
    
    def get_cluster_keywords(self, cluster: Dict[str, Any]) -> List[str]:
        """Extract keywords from cluster content (placeholder for future enhancement)"""
        # This could be enhanced with TF-IDF or other keyword extraction methods
        content = cluster.get('representative_text', '')
        
        # Simple keyword extraction (could be enhanced)
        words = content.lower().split()
        keywords = [word for word in words if len(word) > 4][:10]  # Get first 10 long words
        
        return keywords