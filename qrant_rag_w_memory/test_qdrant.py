from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    url = os.getenv('QDRANT_URL')
    api_key = os.getenv('QDRANT_API_KEY')
    
    print(f"URL: {url}")
    print(f"API Key: {'SET' if api_key else 'NOT SET'}")
    
    if not url or not api_key:
        print("❌ Missing URL or API key in environment variables")
        return False
    
    try:
        client = QdrantClient(url=url, api_key=api_key)
        
        # Test connection
        collections = client.get_collections()
        print("✅ Connection successful!")
        print(f"Existing collections: {collections}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()