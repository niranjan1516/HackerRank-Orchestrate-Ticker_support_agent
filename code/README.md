# Support Triage Agent

A multi-domain support ticket triage agent using RAG and local LLMs (Ollama).

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install and run Ollama (free, local)

**Download Ollama:** https://ollama.ai

Then pull a model (one-time):
```bash
ollama pull mistral:7b
```

Run the Ollama server (in a separate terminal):
```bash
ollama serve
```

It will start on `http://localhost:11434` (the agent connects here automatically).

> **Note:** First time takes ~5-10 min to download model. After that it's instant.

### 3. Build the vector database (one-time)
```bash
python ingest.py
```

This builds the Chroma vector DB from the support corpus in `data/`.

## Running the agent

Process support tickets from `support_tickets.csv` and write to `output.csv`:
```bash
python main.py
```

The agent will process each ticket and output triage decisions.

## Architecture

- **ingest.py**: Loads support docs, chunks them, builds Chroma vector DB
- **retriever.py**: Retrieves relevant context from vector DB using semantic search
- **agent.py**: Uses local Ollama LLM to triage tickets (status, category, response, etc.)
- **main.py**: Orchestrates the pipeline over CSV input

## How it works

1. Read ticket from CSV (issue, company, subject)
2. Retrieve relevant support docs from vector DB
3. Send context + ticket to local LLM (Ollama) for triage decision
4. Output: status, product_area, response, justification, request_type

## Available models (free)

- `mistral:7b` ← **Recommended** (fast, good quality, 4.1GB)
- `llama2:7b` (8.2GB)
- `neural-chat:7b` (4.1GB)
- `orca-mini:3b` (1.3GB) ← Smallest, fastest

Change model in `agent.py` line 5.

## Testing

Test just the retriever:
```bash
python test_retriever.py
```

Run unit tests on sample tickets:
```bash
python test_logic.py
```

## Troubleshooting

**"Connection refused" error?**  
Ollama server isn't running. Start it in another terminal: `ollama serve`

**Slow inference?**  
Switch to a smaller model (`orca-mini:3b`). Or use a GPU if available (Ollama auto-detects).

**Out of memory?**  
Try `orca-mini:3b` or reduce context window in main.py.

