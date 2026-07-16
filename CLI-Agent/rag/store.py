import os
from pathlib import Path
from typing import Optional, cast, Any
import chromadb
from chromadb.utils import embedding_functions

class VectorStoreManager:
    def __init__(self, db_dir: Optional[Path] = None):
        """
        Initializes the local persistent vector database.
        If no path is provided, it defaults to a hidden directory in a user's home folder.
        ensuring global availability across any auidited repository.
        """
        if db_dir is None:
            #Resolves to C:\Users\<username>\.auditor\vectorstore in windows
            self.db_dir = Path.home() / ".auditor" / "vectorstore"
        else:
            self.db_dir = Path(db_dir)

        #Ensure the directory exists in the machine
        self.db_dir.mkdir(parents=True, exist_ok=True)

        #Initialize thr chromaDB's persistent disk client
        self.client = chromadb.PersistentClient(path=str(self.db_dir))

        # Configure a lightweight, locally executed embedding model
        # This translates text/code into a dense 384-dimensional vector space

        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )


    def get_or_create_knowledge_collection(self):
        """
        Fetches or instantiates the core collection ( the vector equivalent of a database table) 
        dedicated to storing security and code quality standards.
        """

        return self.client.get_or_create_collection(
            name="kb_standards",
            embedding_function=cast(Any,self.embedding_fn),
            metadata={"hnsw:space": "cosine"} # Use cosine similarity to calculate conceptual distance
        )
    
    def upsert_document_chunks(self, ids: list, documents: list, metadatas: list):
        """
        Safely inserts or updates vector records. 
        If an ID already exists, it updates the record; otherwise, it inserts a new one.
        """
        collection = self.get_or_create_knowledge_collection()
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Successfully synchronized {len(ids)} documentation chunks to the vector database.")