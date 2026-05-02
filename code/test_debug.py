import sys
sys.path.insert(0, '.')
from retriever import SupportRetriever

retriever = SupportRetriever()

# Test with various issues
test_cases = [
    ("How do I reset my HackerRank password?", "HackerRank"),
    ("Test Active in the system", "HackerRank"),
    ("How to reinvite candidate", "HackerRank"),
]

for issue, company in test_cases:
    print(f"\n=== TEST ===")
    print(f"Issue: {issue}")
    print(f"Company: {company}")
    context = retriever.get_context(issue, company)
    print(f"Context length: {len(context)}")
    print(f"Context preview: {context[:300]}..." if len(context) > 300 else context)
    print(f"Has NO RELEVANT: {'NO RELEVANT CONTEXT FOUND' in context}")
    print("-" * 50)
