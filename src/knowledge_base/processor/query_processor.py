from sentence_transformers import SentenceTransformer
from typing import List, Dict, Set
from src.knowledge_base.processor.vector_store_processor import VectorStoreProcessor
from collections import defaultdict
import numpy as np
import json

class QueryProcessor:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.vector_store = VectorStoreProcessor()
        
    def load_vector_store(self, index_path: str, chunks_path: str):
        self.vector_store.load(index_path, chunks_path)
        
    def query(self, query_text: str, k: int = 5) -> List[Dict]:
        # First search: semantic similarity search
        query_embedding = self.model.encode(query_text, convert_to_numpy=True)
        similarity_scores, initial_results = self.vector_store.search(query_embedding.tolist(), k=20)
        
        # Group results by metadata and find all related chunks
        metadata_groups = self._gather_by_metadata(similarity_scores, initial_results)
        
        # Process each group
        final_results = []
        for i, group_results in enumerate(metadata_groups.values()):
            # Combine content from all chunks in the group
            combined_content = "\n".join(result['content'] for result in group_results)
            
            # Create aggregated result using first result's metadata and similarity
            aggregated_result = {
                'type': group_results[0]['type'],
                'name': group_results[0]['name'],
                'content': combined_content,
                'metadata': group_results[0]['metadata'],
                'similarity_score': similarity_scores[i],
                'chunk_count': len(group_results)
            }
            
            final_results.append(aggregated_result)
            
        return final_results[:k]
    
    def _gather_by_metadata(self, similarity_scores: List[float], results: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group results by metadata and find all related chunks from original data.
        
        Args:
            results: List of search results with similarity scores
            
        Returns:
            Dict mapping metadata keys to lists of results, where:
            - Each group contains ALL chunks with matching metadata from original data
            - Groups are ordered by the similarity score of their first matching result
        """
        # First, group initial results by metadata
        metadata_groups = defaultdict(list)
        for result in results:
            metadata_groups[json.dumps(result['metadata'])].append(result)
        
        # Find all chunks with matching metadata in original data
        for chunk in self.vector_store.chunks:
            if json.dumps(chunk['metadata']) in metadata_groups and chunk not in metadata_groups[json.dumps(chunk['metadata'])]:
                metadata_groups[json.dumps(chunk['metadata'])].append(chunk)
            
        return metadata_groups

def main():
    # define file paths
    index_file = "data/processed/faiss_index.bin"
    chunks_file = "data/processed/chunks_data.pkl"
    
    # create query processor
    processor = QueryProcessor()
    
    # load vector store
    print("Loading vector store...")
    processor.load_vector_store(index_file, chunks_file)
    
    # test query
    while True:
        query = input("\n请输入查询（输入'q'退出）: ")
        if query.lower() == 'q':
            break
            
        results = processor.query(query)
        for result in results:
            print(result['similarity_score'])
            print(result['name'])
            print(result['content'])
            print("-" * 80)

if __name__ == "__main__":
    main() 