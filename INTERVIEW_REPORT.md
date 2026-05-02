# HackerRank Orchestrate - Project Report for AI Interview

## 1. Project Overview

This is a **Multi-Domain Support Triage Challenge** - building a terminal-based support agent that can handle support tickets across three ecosystems:
- HackerRank (hiring/assessment platform)
- Claude (AI assistant)
- Visa (payment/card services)

### What the Agent Does:
For each support ticket, the agent must:
- Identify the request type (product_issue, feature_request, bug, invalid)
- Classify into product area
- Assess urgency and risk
- Decide whether to reply directly or escalate to human
- Retrieve relevant support documentation
- Generate grounded, helpful response

---

## 2. Architecture & Design Decisions

### Component Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (Orchestrator)                  │
│  - Loads CSV, loops through tickets                      │
│  - Calls retriever → agent → saves output               │
└─────────────────────────────────────────────────────────────┘
          │                        │
          ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐
│  SupportRetriever   │  │    TriageAgent       │
│  - Chroma DB       │  │  - LLM (Ollama)     │
│  - RAG retrieval  │  │  - Rules + JSON    │
└─────────────────────┘  └─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  ingest.py         │
│  - Loads .md files│
│  - Chunks & embeds │
└─────────────────────┘
```

### Design Decisions Explained:

#### 1. **RAG (Retrieval-Augmented Generation) Approach**
- **Why:** The problem required grounded answers from the corpus, not parametric knowledge
- **Trade-off:** Adds complexity but ensures responses are traceable to documentation
- **Alternative considered:** Pure rule-based (rejected - too many edge cases)

#### 2. **Vector Store: Chroma + HuggingFace Embeddings**
- **Why:** Open-source, easy to set up, integrates with LangChain
- **Alternative considered:** Pinecone/Weaviate (too expensive), FAISS (no filtering)
- **Decision:** Use local Chroma to avoid external dependencies

#### 3. **LLM: Ollama with gemma3:1b**
- **Why:** Local inference, privacy-safe, no API costs
- **Trade-off:** Smaller model, less capable, risk of 500 errors
- **Alternative considered:** GPT-4 API (rejected - privacy concerns)

#### 4. **Hybrid Architecture (Rules + LLM)**
- Rules for obvious cases (out-of-scope, bugs, escalations)
- LLM for nuanced FAQ responses
- **Why:** Reliability + scalability tradeoff

---

## 3. Technical Implementation Details

### Code Structure:

| File | Purpose | Key Functions |
|------|---------|---------------|
| `ingest.py` | Build vector DB | `build_vector_db()` - loads .md files, chunks, embeds |
| `retriever.py` | RAG retrieval | `get_context(query, company, subject)` |
| `agent.py` | Decision logic | `process_ticket(issue, company, context)` |
| `main.py` | Orchestration | Main loop, CSV I/O |

### Data Pipeline:

1. **Ingestion** (ingest.py):
   - Load .md files from `data/{company}/` folders
   - Split with RecursiveCharacterTextSplitter (800 chars, 150 overlap)
   - Tag chunks with company metadata
   - Store in Chroma vector DB

2. **Retrieval** (retriever.py):
   - Company-filtered similarity search
   - Fallback to global search
   - Context truncation (1200 chars) to prevent LLM errors

3. **Agent Decision** (agent.py):
   - Pre-process rules (escalation signals)
   - LLM prompt engineering with examples
   - JSON extraction + validation
   - Fallback handling

---

## 4. Challenges Faced and Solutions

### Challenge 1: Empty Vector Database
**Symptom:** All tickets returned "No relevant context found"

**Root Cause:** Chroma persistence issue - DB created but not saving documents

**Solution:** 
- Modified ingest.py to explicitly call `persist()`
- Clean DB directory before rebuild
- Added verification step

### Challenge 2: Ollama 500 Errors
**Symptom:** LLM returns 500 Internal Server Error for many tickets

**Root Cause:** gemma3:1b running out of memory/context on longer prompts

**Solutions Tried:**
- Reduced k from 5 → 3 context chunks
- Truncated context to 1200 chars max
- Shortened system prompt
- Added delay between requests
- Added retry logic with exponential backoff

**Outcome:** Partial success - some tickets work, others fail

### Challenge 3: Path Resolution Issues
**Symptom:** Relative paths not working correctly

**Solution:** Use absolute paths based on `__file__` location

---

## 5. Evaluation Criteria Coverage

### 1. Agent Design (Code Quality)
✅ Architecture: Clear separation (retriever, agent, main)
✅ RAG approach: Uses provided corpus
✅ Escalation logic: Rule-based pre-processing
⚠️ Reproducibility: Depends on local Ollama

### 2. Output CSV (Results)
The output should contain:
- `status`: "replied" or "escalated"
- `product_area`: Support category
- `response`: Grounded answer
- `justification`: Decision reasoning
- `request_type`: product_issue/feature_request/bug/invalid

### 3. AI Fluency (Chat Transcript)
The log.txt should show:
- Scoped prompts
- Evidence of critique/verification
- Human steering architecture decisions

---

## 6. What the AI Judge Might Ask

### Design Questions:
1. "Why did you choose RAG over pure rule-based?"
2. "What are the failure modes of your system?"
3. "How would you improve the escalation logic?"
4. "What trade-offs did you make between reliability and quality?"

### Technical Questions:
1. "How does the retrieval filtering work?"
2. "What happens when the LLM returns invalid JSON?"
3. "How do you handle the 500 error problem?"
4. "Why chunk size 800?"

### AI Collaboration Questions:
1. "What prompts did you use with AI tools?"
2. "How did you verify AI-generated code?"
3. "What decisions did the AI suggest that you rejected?"

---

## 7. Key Files Reference

### Requirements:
```
langchain
langchain-community
langchain-huggingface
chromadb
sentence-transformers
pandas
requests
```

### Run Commands:
```bash
# Rebuild vector DB
python code/ingest.py

# Run pipeline
python code/main.py

# Test retrieval
python code/test_debug.py
```

### Expected Output:
- Input: `support_tickets/support_tickets.csv` (29 tickets)
- Output: `support_tickets/output.csv` (5 columns)

---

## 8. Known Issues & Future Improvements

### Current Limitations:
1. Ollama 500 errors on some tickets
2. No graceful fallback to rule-based when LLM fails
3. LLM response quality varies

### Would Improve:
1. Switch to chat endpoint instead of generate
2. Add more comprehensive rules for fallback
3. Use larger model if available
4. Add confidence scoring
5. Better error handling for malformed outputs

---

## Interview Preparation Tips

1. **Know your architecture** - Be able to explain each component
2. **Know your trade-offs** - Why RAG? Why local LLM?
3. **Know failure modes** - What breaks and how to fix
4. **Be honest about AI help** - Clearly distinguish AI-generated from designed

Good luck with your interview! 🍀
