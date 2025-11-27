"""
Semantic Search Module for FAQ Knowledge Base

This module provides semantic search capabilities using vector embeddings
and FAISS for efficient similarity search. It enables finding similar
questions even with different wording.

Features:
- Vector embeddings using sentence transformers
- FAISS-based similarity search
- Multi-language support
- Similarity threshold tuning
- Thread-safe operations
"""
import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    SentenceTransformer = None
    faiss = None

from config.settings import settings


class SemanticSearchEngine:
    """
    Semantic search engine for FAQ knowledge base using vector embeddings.
    
    Uses sentence-transformers for embeddings and FAISS for efficient
    similarity search. Supports multi-language queries and automatic
    index management.
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.5,
        top_k: int = 5,
        index_path: Optional[Path] = None
    ):
        """
        Initialize semantic search engine.
        
        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity score (0-1)
            top_k: Number of top results to return
            index_path: Path to save/load FAISS index
        """
        if not SEMANTIC_SEARCH_AVAILABLE:
            raise ImportError(
                "Semantic search dependencies not installed. "
                "Please install: pip install sentence-transformers faiss-cpu"
            )
        
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.index_path = index_path or Path(__file__).parent.parent / "data" / "faq_index"
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.Lock()
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.Index] = None
        self._faq_data: List[Dict] = []
        self._dimension: int = 384  # Default for all-MiniLM-L6-v2
        self._model_initialized: bool = False
        
        # Don't initialize model here - use lazy loading when actually needed
        # This prevents downloading/loading the model if semantic search isn't used
    
    def _initialize_model(self) -> None:
        """Initialize the sentence transformer model."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
                # Get actual dimension from model
                test_embedding = self._model.encode(["test"])
                self._dimension = test_embedding.shape[1]
            except Exception as e:
                raise RuntimeError(f"Failed to load model {self.model_name}: {str(e)}")
    
    def build_index(self, faqs: List[Dict]) -> None:
        """
        Build FAISS index from FAQ data.
        
        Args:
            faqs: List of FAQ dictionaries with 'question' and 'answer' fields
        """
        # Ensure model is loaded before building index
        self._ensure_model_loaded()
        
        if not faqs:
            raise ValueError("FAQ list cannot be empty")
        
        with self._lock:
            self._faq_data = faqs
            
            # Extract questions for embedding
            questions = [faq.get("question", "") for faq in faqs]
            
            # Generate embeddings
            embeddings = self._model.encode(questions, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Create FAISS index (Inner Product for cosine similarity)
            self._index = faiss.IndexFlatIP(self._dimension)
            self._index.add(embeddings)
            
            # Save index and metadata
            self._save_index()
    
    def _save_index(self) -> None:
        """Save FAISS index and FAQ data to Supabase Storage or disk."""
        if self._index is None:
            return
        
        # Try Supabase Storage first
        if self._save_index_to_supabase():
            return
        
        # Fallback to local disk
        try:
            # Save FAISS index
            index_file = self.index_path / "faq_index.faiss"
            faiss.write_index(self._index, str(index_file))
            
            # Save FAQ metadata
            metadata_file = self.index_path / "faq_metadata.pkl"
            with open(metadata_file, 'wb') as f:
                pickle.dump({
                    'faq_data': self._faq_data,
                    'dimension': self._dimension,
                    'model_name': self.model_name
                }, f)
        except Exception as e:
            # Log error but don't fail
            print(f"Warning: Failed to save index: {str(e)}")
    
    def _save_index_to_supabase(self) -> bool:
        """Save FAISS index to Supabase Storage."""
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if not SUPABASE_ENABLED:
                return False
            
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            import tempfile
            
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                return False
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Save index to temporary file first (FAISS needs a file path, not BytesIO)
            tmp_index_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.faiss') as tmp_file:
                    tmp_index_path = tmp_file.name
                
                # Write index to temporary file
                faiss.write_index(self._index, tmp_index_path)
                
                # Read the file content
                with open(tmp_index_path, 'rb') as f:
                    index_data = f.read()
                
                # Upload to Supabase Storage bucket "Storage"
                try:
                    # Try upload with upsert
                    result = supabase.storage.from_("Storage").upload(
                        "faq_index.faiss",
                        index_data,
                        file_options={"content-type": "application/octet-stream", "upsert": "true"}
                    )
                except Exception as e:
                    error_str = str(e).lower()
                    # If file exists, try to update it
                    if "already exists" in error_str or "duplicate" in error_str or "409" in error_str:
                        try:
                            supabase.storage.from_("Storage").update(
                                "faq_index.faiss",
                                index_data,
                                file_options={"content-type": "application/octet-stream"}
                            )
                        except Exception as e2:
                            # If update also fails, try remove then upload
                            try:
                                supabase.storage.from_("Storage").remove(["faq_index.faiss"])
                                supabase.storage.from_("Storage").upload(
                                    "faq_index.faiss",
                                    index_data,
                                    file_options={"content-type": "application/octet-stream"}
                                )
                            except Exception as e3:
                                raise e3
                    else:
                        # Check if it's a permission error
                        if "403" in str(e) or "unauthorized" in error_str or "row-level security" in error_str:
                            print(f"\n⚠️  Permission Error: Make sure you're using SERVICE_ROLE key in .env")
                            print(f"   Current key starts with: {supabase_key[:20]}...")
                            print(f"   Go to Supabase Dashboard → Settings → API → Copy SERVICE_ROLE key")
                            raise
                        raise
            finally:
                # Clean up temporary file
                if tmp_index_path and os.path.exists(tmp_index_path):
                    try:
                        os.unlink(tmp_index_path)
                    except Exception:
                        pass
            
            # Save metadata
            metadata = {
                'faq_data': self._faq_data,
                'dimension': self._dimension,
                'model_name': self.model_name
            }
            metadata_bytes = pickle.dumps(metadata)
            
            try:
                supabase.storage.from_("Storage").upload(
                    "faq_metadata.pkl",
                    metadata_bytes,
                    file_options={"content-type": "application/octet-stream", "upsert": "true"}
                )
            except Exception as e:
                # If file exists, try to update it
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    supabase.storage.from_("Storage").update(
                        "faq_metadata.pkl",
                        metadata_bytes,
                        file_options={"content-type": "application/octet-stream"}
                    )
                else:
                    raise
            
            print("✅ FAQ index saved to Supabase Storage")
            return True
        except Exception as e:
            error_msg = str(e)
            # Check if it's a permission error
            if "403" in error_msg or "unauthorized" in error_msg.lower() or "row-level security" in error_msg.lower():
                print(f"\n⚠️  PERMISSION ERROR - Supabase Storage")
                print(f"   Error: {error_msg}")
                print(f"\n   Solutions:")
                print(f"   1. Use SERVICE_ROLE key (recommended):")
                print(f"      - Go to Supabase Dashboard → Settings → API")
                print(f"      - Copy the 'service_role' key (NOT 'anon' key)")
                print(f"      - Update .env: SUPABASE_KEY=your_service_role_key")
                print(f"   2. Or configure RLS policies:")
                print(f"      - Run sql/setup_storage_permissions.sql in Supabase SQL Editor")
                print(f"      - Or make bucket public in Storage settings")
            else:
                print(f"Warning: Failed to save index to Supabase Storage: {error_msg}")
            return False
        finally:
            # Clean up temporary file
            try:
                if 'tmp_index_path' in locals() and os.path.exists(tmp_index_path):
                    os.unlink(tmp_index_path)
            except Exception:
                pass
    
    def load_index(self) -> bool:
        """
        Load FAISS index from Supabase Storage or disk.
        
        Returns:
            True if index loaded successfully, False otherwise
        """
        # Try Supabase Storage first
        if self._load_index_from_supabase():
            return True
        
        # Fallback to local disk
        index_file = self.index_path / "faq_index.faiss"
        metadata_file = self.index_path / "faq_metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            return False
        
        try:
            with self._lock:
                # Load FAISS index
                self._index = faiss.read_index(str(index_file))
                
                # Load metadata
                with open(metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                    self._faq_data = metadata.get('faq_data', [])
                    self._dimension = metadata.get('dimension', self._dimension)
                    saved_model = metadata.get('model_name', self.model_name)
                    
                    # Check if model matches
                    if saved_model != self.model_name:
                        print(f"Warning: Saved model ({saved_model}) differs from current ({self.model_name})")
                        return False
                
                return True
        except Exception as e:
            print(f"Warning: Failed to load index: {str(e)}")
            return False
    
    def _load_index_from_supabase(self) -> bool:
        """Load FAISS index from Supabase Storage."""
        try:
            from utils.supabase_client import SUPABASE_ENABLED
            if not SUPABASE_ENABLED:
                return False
            
            from supabase import create_client
            import os
            from dotenv import load_dotenv
            import io
            
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                return False
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Download index from Supabase Storage bucket "Storage"
            try:
                index_data = supabase.storage.from_("Storage").download("faq_index.faiss")
            except Exception as e:
                # File doesn't exist in Storage
                return False
            
            # FAISS requires a file path, not bytes directly
            # Save to temporary file first, then load
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.faiss') as tmp_file:
                tmp_index_path = tmp_file.name
                tmp_file.write(index_data)
            
            try:
                # Load index from temporary file
                self._index = faiss.read_index(tmp_index_path)
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_index_path)
                except:
                    pass
            
            # Download metadata
            try:
                metadata_data = supabase.storage.from_("Storage").download("faq_metadata.pkl")
            except Exception as e:
                print(f"Warning: Metadata not found in Supabase Storage: {str(e)}")
                return False
            
            # Load metadata
            metadata = pickle.loads(metadata_data)
            self._faq_data = metadata.get('faq_data', [])
            self._dimension = metadata.get('dimension', self._dimension)
            saved_model = metadata.get('model_name', self.model_name)
            
            # Check if model matches
            if saved_model != self.model_name:
                print(f"Warning: Saved model ({saved_model}) differs from current ({self.model_name})")
                return False
            
            print("✅ FAQ index loaded from Supabase Storage")
            return True
        except Exception as e:
            print(f"Warning: Failed to load index from Supabase Storage: {str(e)}")
            return False
    
    def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded (lazy initialization)."""
        if not self._model_initialized:
            with self._lock:
                if not self._model_initialized:
                    self._initialize_model()
                    self._model_initialized = True
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar FAQs using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return (overrides default)
            similarity_threshold: Minimum similarity score (overrides default)
            
        Returns:
            List of tuples (FAQ dict, similarity score) sorted by score
        """
        # Ensure model is loaded (lazy initialization)
        self._ensure_model_loaded()
        
        if self._index is None or not self._faq_data:
            return []
        
        top_k = top_k or self.top_k
        threshold = similarity_threshold or self.similarity_threshold
        
        # Generate query embedding
        query_embedding = self._model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        with self._lock:
            scores, indices = self._index.search(query_embedding, min(top_k, len(self._faq_data)))
        
        # Filter by threshold and return results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._faq_data) and score >= threshold:
                results.append((self._faq_data[idx], float(score)))
        
        return results
    
    def get_suggestions(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """
        Get auto-suggestions based on partial query.
        
        Args:
            partial_query: Partial query string
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested question strings
        """
        if not partial_query or len(partial_query.strip()) < 2:
            return []
        
        # Search for similar questions
        results = self.search(partial_query, top_k=max_suggestions * 2, similarity_threshold=0.3)
        
        # Extract questions and deduplicate
        suggestions = []
        seen = set()
        for faq, score in results:
            question = faq.get("question", "")
            if question and question.lower() not in seen:
                suggestions.append(question)
                seen.add(question.lower())
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions
    
    def is_index_loaded(self) -> bool:
        """Check if index is loaded and ready."""
        return self._index is not None and len(self._faq_data) > 0
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the current index."""
        return {
            "num_faqs": len(self._faq_data),
            "dimension": self._dimension,
            "model_name": self.model_name,
            "index_loaded": self.is_index_loaded()
        }


# Global semantic search engine instance
_semantic_engine: Optional[SemanticSearchEngine] = None
_engine_lock = threading.Lock()


def get_semantic_engine() -> Optional[SemanticSearchEngine]:
    """
    Get or create global semantic search engine instance.
    
    Returns:
        SemanticSearchEngine instance or None if dependencies not available
    """
    global _semantic_engine
    
    if not SEMANTIC_SEARCH_AVAILABLE:
        return None
    
    if _semantic_engine is None:
        with _engine_lock:
            if _semantic_engine is None:
                try:
                    # Get settings from config
                    model_name = getattr(settings, 'semantic_model_name', 'all-MiniLM-L6-v2')
                    similarity_threshold = getattr(settings, 'semantic_threshold', 0.5)
                    top_k = getattr(settings, 'semantic_top_k', 5)
                    
                    _semantic_engine = SemanticSearchEngine(
                        model_name=model_name,
                        similarity_threshold=similarity_threshold,
                        top_k=top_k
                    )
                    
                    # Try to load existing index automatically
                    if not _semantic_engine.is_index_loaded():
                        _semantic_engine.load_index()
                        
                except Exception as e:
                    print(f"Warning: Failed to initialize semantic search: {str(e)}")
                    return None
    
    return _semantic_engine

