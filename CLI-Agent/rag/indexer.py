# rag/indexer.py
import re
from pathlib import Path
from typing import List, Dict, Any
from rag.store import VectorStoreManager

class KnowledgeIndexer:
    def __init__(self, store_manager: VectorStoreManager):
        self.store = store_manager

    def chunk_text(self, text: str, max_chars: int = 1000, overlap: int = 200) -> List[str]:
        """
        Splits a large document string into smaller overlapping paragraphs.
        This guarantees that semantic contexts aren't cut off mid-sentence.
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + max_chars
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move our window forward by max_chars minus the overlap
            start += (max_chars - overlap)
            
        return chunks

    def index_markdown_file(self, file_path: Path) -> None:
        """
        Reads a single documentation file, parses it into semantic chunks,
        and pushes it directly into our local ChromaDB vector store collection.
        """
        if not file_path.exists():
            print(f"Error: Target documentation file {file_path} does not exist.")
            return

        # 1. Read document text safely
        content = file_path.read_text(encoding="utf-8")
        
        # 2. Extract metadata elements from the document title or filename
        doc_title = file_path.stem.replace("_", " ").title()
        
        # 3. Process raw file text into smaller windows
        text_chunks = self.chunk_text(content)
        
        ids = []
        documents = []
        metadatas = []
        
        # 4. Loop over chunks to create unique IDs and structural mapping coordinates
        for idx, chunk in enumerate(text_chunks):
            chunk_id = f"{file_path.stem}_chunk_{idx}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "source_file": file_path.name,
                "document_title": doc_title,
                "chunk_index": idx
            })
            
        # 5. Commit these processed entries directly to the vector store database
        self.store.upsert_document_chunks(ids=ids, documents=documents, metadatas=metadatas)