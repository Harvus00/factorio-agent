from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict
import numpy as np
from tqdm import tqdm
import os

class EmbeddingProcessor:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        
    def process_chunks(self, chunks: List[Dict], batch_size: int = 32) -> List[Dict]:
        """process chunks and add embeddings"""
        texts = [chunk["content"] for chunk in chunks]

        # batch generate embeddings
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch_texts, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)
        
        # add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()
            
        return chunks

def main():
    # define file paths
    input_file = os.path.join("data", "processed", "chunks", "api_chunks.json")
    output_file = os.path.join("data", "processed", "embeddings", "api_chunks_with_embeddings.json")
    
    # load chunks
    print(f"Loading chunks from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # process embeddings
    print("Processing embeddings...")
    processor = EmbeddingProcessor()
    chunks_with_embeddings = processor.process_chunks(chunks)
    
    print(f"Saving chunks with embeddings to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_with_embeddings, f, indent=2, ensure_ascii=False)
    
    print("Done!")

if __name__ == "__main__":
    main() 