from retriever import SupportRetriever

retriever = SupportRetriever()

# Test HackerRank retrieval
context = retriever.get_context("How do I reset my password?", "HackerRank")
print("=== HackerRank Query ===")
print(f"Context length: {len(context)} chars")
print(f"Found context: {'NO RELEVANT' not in context}\n")

# Test Claude retrieval
context = retriever.get_context("How do I access Claude API?", "Claude")
print("=== Claude Query ===")
print(f"Context length: {len(context)} chars")
print(f"Found context: {'NO RELEVANT' not in context}\n")

# Test Visa retrieval
context = retriever.get_context("How do I use my Visa card?", "Visa")
print("=== Visa Query ===")
print(f"Context length: {len(context)} chars")
print(f"Found context: {'NO RELEVANT' not in context}\n")

print("SUCCESS: Retriever is working!")
