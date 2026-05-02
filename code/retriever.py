import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Absolute path to DB directory (same as ingest.py)
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")

class SupportRetriever:
    def __init__(self, db_path=None):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # Use absolute path to avoid cwd mismatch
        path = db_path if db_path else DB_DIR
        self.db = Chroma(persist_directory=path, embedding_function=self.embeddings)


    def get_context(self, query: str, company: str, subject: str = "", k: int = 5) -> str:
        """
        Retrieve relevant context from vector DB.
        Handles company filtering and falls back to global search if needed.
        """
        raw_company = str(company).strip()

        # Map variations to canonical company names
        company_map = {
            'hackerrank': 'HackerRank',
            'hackrrank': 'HackerRank',
            'claude': 'Claude',
            'visa': 'Visa',
            'none': None,
            'nan': None,
            '': None
        }

        canonical_company = company_map.get(raw_company.lower(), raw_company)

        # Combine subject + issue for better retrieval if subject is meaningful
        search_query = query
        # Ensure subject is a string before trying to strip it
        if isinstance(subject, str) and subject.lower() != 'nan' and len(subject.strip()) > 3:
            search_query = f"{subject.strip()}. {query}"

        results = []
        if canonical_company:
            try:
                results = self.db.similarity_search(search_query, k=3, filter={"company": canonical_company})
            except Exception as e:
                print(f"  Filtered search error: {e}")

        # Fallback to global search if no company match or filtered search failed
        if not results:
            try:
                results = self.db.similarity_search(search_query, k=3)
            except Exception as e:
                print(f"  Global search error: {e}")


        if not results:
            return "NO RELEVANT CONTEXT FOUND."

        context = "\n---\n".join([doc.page_content for doc in results])
        
        # Truncate to ~1200 chars to prevent Ollama 500 errors with small models
        max_len = 1200
        if len(context) > max_len:
            context = context[:max_len].rsplit('\n', 1)[0] + "\n..."
        
        return context
