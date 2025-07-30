import os
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from pathlib import Path

class LlamaFileSearchService:
    def __init__(self, index_path="config/faiss_index"):
        self.index_path = index_path
        self.index = None
        self._initialize_embedder()
        self._load_index()

    def _initialize_embedder(self):
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def _load_index(self):
        if not os.path.exists(self.index_path):
            print(f"[INFO] Index path {self.index_path} does not exist. Run indexing first.")
            return

        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.index_path)
            self.index = load_index_from_storage(storage_context)
            print("[INFO] FAISS index loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load index: {e}")
            self.index = None

    def search(self, query: str, top_k: int = 10):
        if self.index is None:
            return {
                "exact_matches": [],
                "fuzzy_matches": [],
                "content_matches": [],
                "all_results": []
            }

        try:
            # Query the index
            query_engine = self.index.as_query_engine(similarity_top_k=top_k)
            response = query_engine.query(query)
            
            # Extract file paths from source nodes
            file_paths = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                        file_path = node.node.metadata.get('file_path', '')
                        if file_path and file_path not in file_paths:
                            file_paths.append(file_path)
            
            # For compatibility with the existing handler, classify results
            # In this vector-based approach, all results are essentially "content matches"
            return {
                "exact_matches": [],  # Vector search doesn't do exact filename matching
                "fuzzy_matches": [],  # Vector search doesn't do fuzzy filename matching  
                "content_matches": file_paths,
                "all_results": file_paths
            }
            
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return {
                "exact_matches": [],
                "fuzzy_matches": [],
                "content_matches": [],
                "all_results": []
            }

    def is_index_available(self):
        return self.index is not None

