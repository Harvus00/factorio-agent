from sentence_transformers import SentenceTransformer
import json
import os
from typing import List, Dict

def test_tokenization(input_texts: List[str]):
    """Test tokenization and token count for sentence-transformers/all-MiniLM-L6-v2 model"""
    
    # Initialize the model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print(model.max_seq_length)
    # Test texts with different lengths
    test_texts = input_texts
    
    print("Testing tokenization for sentence-transformers/all-MiniLM-L6-v2")
    print("=" * 60)
    
    for i, text in enumerate(test_texts, 1):
        # Tokenize the text
        tokenizer = model.tokenizer
        tokens = tokenizer.tokenize(text)
        token_ids = tokenizer.encode(text)
        
        # Get token count
        token_count = len(token_ids)
        
        print(f"\nTest {i}:")
        print(f"Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"Character count: {len(text)}")
        print(f"Token count: {token_count}")
        print(f"Tokens: {tokens[:20]}{'...' if len(tokens) > 20 else ''}")
        
        # Check if text exceeds model's max sequence length
        max_seq_length = model.max_seq_length
        if token_count > max_seq_length:
            print(f"⚠️  WARNING: Token count ({token_count}) exceeds max sequence length ({max_seq_length})")
        else:
            print(f"✅ Token count within limits (max: {max_seq_length})")
    
    # Test with actual API chunk data if available
    try:
        chunks_file = os.path.join("data", "processed", "chunks", "api_chunks.json")
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"\n\nTesting with actual API chunks (first 5 chunks)")
        print("=" * 60)
        
        for i, chunk in enumerate(chunks[:5]):
            content = chunk.get("content", "")
            tokens = model.tokenizer.encode(content)
            token_count = len(tokens)
            
            print(f"\nChunk {i+1} ({chunk.get('type', 'unknown')}):")
            print(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")
            print(f"Token count: {token_count}")
            
            if token_count > model.max_seq_length:
                print(f"⚠️  WARNING: Exceeds max length")
            else:
                print(f"✅ Within limits")
                
    except FileNotFoundError:
        print("\n📝 Note: API chunks file not found, skipping chunk analysis")
    
    print(f"\n\nModel Information:")
    print(f"Model name: {model.model_name}")
    print(f"Max sequence length: {model.max_seq_length}")
    print(f"Embedding dimension: {model.get_sentence_embedding_dimension()}")

if __name__ == "__main__":
    input_texts = ["- position (MapPosition): Where to create the entity.\n- preserve_ghosts_and_corpses (boolean)[Optional]: If true, colliding ghosts and corpses will not be removed by the creation of some entity types. Defaults to `false`.\n- quality (QualityID)[Optional]: Quality of the entity to be created. Defaults to `normal`.\n- raise_built (boolean)[Optional]: If true; [defines.events.script_raised_built](runtime:defines.events.script_raised_built) will be fired on successful entity creation. Defaults to `false`."]
    test_tokenization(input_texts)
