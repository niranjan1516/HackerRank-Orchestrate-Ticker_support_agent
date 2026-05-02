import os
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# FIXED PATH: Based on your terminal, 'data' is inside your project root, not above it.
# We use absolute paths to be 100% safe.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")

def build_vector_db():
    print("Starting Ingestion Pipeline...")
    print(f"Searching for data in: {CORPUS_DIR}")

    # Clean old DB to avoid corruption/empty collections
    if os.path.exists(DB_DIR):
        print(f"Removing old database at {DB_DIR}...")
        shutil.rmtree(DB_DIR)
    os.makedirs(DB_DIR, exist_ok=True)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    all_chunks = []

    company_map = {'hackerrank': 'HackerRank', 'claude': 'Claude', 'visa': 'Visa'}

    for dir_name, display_name in company_map.items():
        path = os.path.join(CORPUS_DIR, dir_name)
        if not os.path.exists(path):
            print(f"WARNING: Directory {path} not found. Skipping.")
            continue

        print(f"Loading documents for {display_name}...")

        loader = DirectoryLoader(path, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'}, silent_errors=True)
        docs = loader.load()

        if not docs:
            print(f"  ERROR: No .md files found in {path}")
            continue

        print(f"  Loaded {len(docs)} documents")
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        chunks = splitter.split_documents(docs)

        for chunk in chunks:
            chunk.metadata['company'] = display_name

        all_chunks.extend(chunks)
        print(f"  Created {len(chunks)} chunks")

    if not all_chunks:
        print("ERROR: No documents were processed. Check your file extensions and paths.")
        return

    print(f"\nGenerating embeddings for {len(all_chunks)} chunks...")
    
    # Create vectorstore and explicitly persist
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    vectorstore.persist()
    
    print(f"SUCCESS: Vector database built with {len(all_chunks)} chunks in {DB_DIR}!")
    
    # Verify the database was created properly
    print("\nVerifying database...")
    verify_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    count = verify_db._collection.count()
    print(f"Verified: Database contains {count} documents")

if __name__ == "__main__":
    build_vector_db()
