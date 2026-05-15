# 🔍 Self-RAG: Self-Reflective Retrieval-Augmented Generation Agent

A production-grade **Self-RAG** pipeline built with **LangGraph** and **Google Gemini**. Unlike standard RAG systems that blindly retrieve and generate, this agent makes intelligent decisions at each stage — deciding *when* to retrieve, *whether* the retrieved content is useful, and *whether* the final answer is actually grounded in facts.

---

## 🧠 What is Self-RAG?

Standard RAG pipelines have two fundamental weaknesses:
1. They **always retrieve**, even when the LLM already knows the answer.
2. They **blindly trust** whatever documents are retrieved, even irrelevant ones.

**Self-RAG** addresses both by introducing reflection checkpoints:

| Checkpoint | Question Asked |
|---|---|
| **Adaptive Retrieval** | Should I even retrieve? |
| **Relevance Grading** | Is what I retrieved actually useful? |
| **Hallucination Check** | Is my answer faithful to the evidence? |

---

## 🏗️ Architecture

```
User Query
    │
    ▼
[Route Question] ──── General/Greeting ──▶ [Direct Answer] ──▶ END
    │
    │ Domain-Specific
    ▼
[Retrieve from VectorStore]
    │
    ▼
[Grade Documents]
    │
    ├── All Irrelevant ──▶ [Web Search Fallback]
    │                           │
    │ Relevant docs found       │
    ├───────────────────────────┘
    ▼
[Generate Answer]
    │
    ▼
[Check Hallucination]
    │
    ├── Grounded ──▶ END
    │
    └── Hallucination Detected ──▶ [Increment Retries] ──▶ [Generate Answer]
                                         (max 3 retries)
```

---

## 📁 Project Structure

```
selfRAG/
├── self_rag_agent.py       # Main entry point — run this to start the agent
├── graph.py                # LangGraph StateGraph: all nodes, edges, routing logic
├── tools.py                # Tool definitions with @tool decorator and Pydantic validation
├── evaluation_results.md   # 5 test cases with execution traces and final responses
├── Data_share/             # Knowledge base PDF documents
│   ├── CS_Department_Catalog.pdf
│   ├── EE_Department_Catalog.pdf
│   ├── BBA_Department_Catalog.pdf
│   ├── University_Academic_Policies.pdf
│   └── Faculty_Directory.pdf
├── .env.example            # Example environment variable file
└── README.md
```

---

## ⚙️ How It Works

### 1. Knowledge Base Setup
All 5 PDF documents are ingested via `PyPDFLoader`, chunked using `RecursiveCharacterTextSplitter` (1000 tokens, 200 overlap) to preserve document structure, and embedded with `GoogleGenerativeAIEmbeddings`. Chunks are stored in a local **ChromaDB** vector store with meaningful metadata:
- `department`: CS / EE / BBA / University
- `doc_type`: course_catalog / faculty / policies

### 2. Adaptive Retrieval (Router Node)
The agent uses a structured-output Gemini call to classify the query:
- `direct_answer` → Greetings, general knowledge (no retrieval needed)
- `vectorstore` → Domain-specific questions (retrieval required)

### 3. Relevance Grading
Each retrieved document is individually scored as `yes/no` for relevance. Irrelevant documents are discarded. If **all** documents are irrelevant, `web_fallback = True` is set, triggering the web search node.

### 4. Web Search Fallback
Uses **DuckDuckGo** (via `langchain_community`) to fetch real-time web results when the knowledge base fails. Web results are injected into the context as a `Document` object.

### 5. Hallucination Self-Check
After generation, the agent checks if the response is grounded in the source context. If hallucination is detected:
- The agent **retries** generation (up to 3 times).
- After max retries, the agent explicitly states it could not verify the information.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **LLM** | Google Gemini 2.5 Flash |
| **Embeddings** | Google Gemini Embedding 001 |
| **Orchestration** | LangGraph (StateGraph) |
| **Vector Store** | ChromaDB |
| **PDF Parsing** | LangChain PyPDFLoader |
| **Web Search** | DuckDuckGo (langchain_community) |
| **Validation** | Pydantic v2 |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A Google AI Studio API key ([Get one here](https://aistudio.google.com/))

### Installation

```bash
git clone https://github.com/Tajhoonmain/selfRAG.git
cd selfRAG

pip install langchain langgraph langchain-community langchain-google-genai \
            chromadb pypdf python-dotenv duckduckgo-search
```

### Configuration

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

### Run

```bash
python self_rag_agent.py
```

The agent will:
1. Ingest all 5 PDFs and build the ChromaDB vector store (first run only).
2. Start an interactive terminal session.

---

## 🧪 Test Scenarios

Five scenarios are pre-documented in [`evaluation_results.md`](./evaluation_results.md):

| # | Scenario | Path Taken |
|---|---|---|
| 1 | Greeting / General Knowledge | → Direct Answer (no retrieval) |
| 2 | Specific domain query (relevant docs) | → Retrieve → Grade → Generate |
| 3 | Off-topic query (irrelevant docs) | → Retrieve → Grade → Web Search → Generate |
| 4 | Hallucination-inducing query | → Retrieve → Generate → Retry → Generate |
| 5 | Multi-document synthesis | → Retrieve → Grade (multiple) → Generate |

---

## 🔑 Key Design Decisions

- **No blind trust**: Documents must pass a relevance gate before being used for generation.
- **No silent hallucinations**: Every response is checked against source evidence.
- **Graceful degradation**: When the KB fails, web search keeps the agent functional.
- **Retry with a limit**: The agent never loops indefinitely — max 3 hallucination retries.

---

## 📄 License

MIT License
