
import os
import json
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

class LlamaIndexingService:
    def __init__(self, config_path="config/search_config.json", index_path="config/faiss_index"):
        self.config_path = config_path
        self.index_path = index_path
        self._initialize_embedder()

    def _initialize_embedder(self):
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def _load_search_paths(self):
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                return [path for path in data.get("search_paths", []) if os.path.exists(path)]
        except Exception as e:
            print(f"[ERROR] Failed to load search paths: {e}")
            return []

    def build_and_save_index(self):
        search_paths = self._load_search_paths()
        if not search_paths:
            print("[INFO] No valid search paths found. Aborting indexing.")
            return

        print("[INFO] Loading documents from specified paths...")
        all_documents = []
        for path in search_paths:
            try:
                documents = SimpleDirectoryReader(input_dir=path).load_data()
                all_documents.extend(documents)
                print(f"[INFO] Loaded {len(documents)} documents from {path}")
            except Exception as e:
                print(f"[WARN] Failed to load documents from {path}: {e}")
        
        documents = all_documents
        
        if not documents:
            print("[INFO] No documents found to index.")
            return

        print(f"[INFO] Loaded {len(documents)} documents. Now creating FAISS index...")
        # Get embedding dimension by creating a dummy embedding
        dummy_embedding = Settings.embed_model.get_text_embedding("dummy query")
        d = len(dummy_embedding)

        faiss_index = faiss.IndexFlatL2(d)
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )

        print(f"[INFO] Index created successfully. Saving to {self.index_path}...")
        index.storage_context.persist(persist_dir=self.index_path)
        print("[INFO] Indexing complete.")


