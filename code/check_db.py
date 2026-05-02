import sys
sys.path.insert(0, '.')
from retriever import SupportRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Check what embeddings model is being used
print("=== Checking Embeddings ===")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print(f"Embeddings model: all-MiniLM-L6-v2")

# Check the database directly
print("\n=== Checking Vector DB ===")
DB_PATH = "./db"
db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

# Get collection info
try:
    collection = db._collection
    print(f"Collection count: {collection.count()}")
except Exception as e:
    print(f"Error getting count: {e}")

# Try raw search (no filter)
print("\n=== Raw Search (no filter) ===")
results = db.similarity_search("password reset", k=3)
print(f"Raw search results: {len(results)}")
for r in results:
    print(f"  - {r.page_content[:100]}...")

# Try with filter
print("\n=== Search with filter ===")
try:
    results = db.similarity_search("password reset", k=3, filter={"company": "HackerRank"})
    print(f"Filtered search results: {len(results)}")
except Exception as e:
    print(f"Filtered search error: {e}")

# Check what metadata fields exist in the DB
print("\n=== Checking Metadata ===")
try:
    # Get a sample to see metadata structure
    results = db.get() 
    print(f"Total documents in DB: {len(results.get('ids', []))}")
    if results.get('metadatas'):
        print(f"Sample metadata: {results['metadatas'][0] if results['metadatas'] else 'None'}")
except Exception as e:
    print(f"Error: {e}")
