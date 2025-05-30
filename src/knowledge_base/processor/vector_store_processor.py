import json
from typing import List, Dict
import numpy as np
from tqdm import tqdm
import faiss
import pickle

class VectorStoreProcessor:
    def __init__(self):
        self.index = None
        self.chunks = None
        self.dimension = None
        
    def create_index(self, chunks: List[Dict]):
        """create FAISS index"""
        # get embedding dimension
        self.dimension = len(chunks[0]["embedding"])
        print(f"Embedding dimension: {self.dimension}")
        
        # create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # prepare vectors
        vectors = np.array([chunk["embedding"] for chunk in chunks]).astype('float32')
        
        # add to index
        self.index.add(vectors)
        
        # save chunks data
        self.chunks = chunks
        
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """search most similar chunks"""
        # convert query vector
        query_vector = np.array([query_embedding]).astype('float32')
        
        # search
        distances, indices = self.index.search(query_vector, k)
        
        # return results
        results = []
        similarity_scores = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # FAISS may return -1 to indicate invalid results
                chunk = self.chunks[idx].copy()
                # chunk["similarity_score"] = float(1 / (1 + distances[0][i]))  # convert distance to similarity score
                results.append(chunk)
                similarity_scores.append(float(1 / (1 + distances[0][i])))
        return similarity_scores, results
    
    def save(self, index_path: str, chunks_path: str):
        """save index and chunks data"""
        # save FAISS index
        faiss.write_index(self.index, index_path)
        
        # save chunks data
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
            
    def load(self, index_path: str, chunks_path: str):
        """load index and chunks data"""
        # load FAISS index
        self.index = faiss.read_index(index_path)
        
        # load chunks data
        with open(chunks_path, 'rb') as f:
            self.chunks = pickle.load(f)

def main():
    # define file paths
    input_file = "data/processed/embeddings/api_chunks_with_embeddings.json"
    index_file = "data/processed/embeddings/faiss_index.bin"
    chunks_file = "data/processed/embeddings/chunks_data.pkl"
    
    # load chunks
    print(f"Loading chunks from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # create vector store
    print("Creating vector store...")
    processor = VectorStoreProcessor()
    processor.create_index(chunks)
    
    # save vector store
    print("Saving vector store...")
    processor.save(index_file, chunks_file)
    
    print("Done!")

if __name__ == "__main__":
    main() 