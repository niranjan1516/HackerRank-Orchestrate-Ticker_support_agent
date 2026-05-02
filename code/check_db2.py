import sys
sys.path.insert(0, '.')
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Check project root db folder
DB_PATH1 = "../db"
DB_PATH2 = "./db"

for db_path in [DB_PATH1, DB_PATH2]:
    full_path = os.path.abspath(db_path)
    print(f"\n=== Checking: {full_path} ===")
    if not os.path.exists(full_path):
        print("  Does not exist!")
        continue
    
    # List files
    files = os.listdir(full_path)
    print(f"  Files: {files}")
    
    try:
        db = Chroma(persist_directory=full_path, embedding_function=embeddings)
        collection = db._collection
        count = collection.count()
        print(f"  Document count: {count}")
        
        if count > 0:
            print(f"  FOUND DATA IN: {full_path}")
            # Try a search
            results = db.similarity_search("password reset", k=1)
            print(f"  Sample search: {len(results)} results")
            if results:
                print(f"  First result: {results[0].page_content[:200]}...")
    except Exception as e:
        print(f"  Error: {e}")
