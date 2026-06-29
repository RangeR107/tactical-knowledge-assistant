# 🎯 Tactical Knowledge Assistant

A **fully offline, production-quality AI assistant** built with Python, LangChain, Streamlit, FAISS, and Ollama. Upload any combination of PDF, DOCX, TXT, or Markdown documents to build a persistent local knowledge base, then ask questions in natural language and receive accurate, context-grounded answers — with zero cloud dependencies.

---

## 📸 Screenshots

> *(Add screenshots after running the app)*

| Feature | Screenshot |
|---------|-----------|
| Main chat interface | `docs/screenshots/chat.png` |
| Sidebar & KB controls | `docs/screenshots/sidebar.png` |
| Retrieved context | `docs/screenshots/context.png` |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   STREAMLIT UI (main.py)                     │
│   ┌────────────────┐    ┌──────────────────────────────────┐ │
│   │    Sidebar     │    │         Chat Interface            │ │
│   │ • File upload  │    │  • Message history               │ │
│   │ • Build/Reset  │    │  • Query input                   │ │
│   │ • Stats        │    │  • Answer + sources + context    │ │
│   │ • Settings     │    │  • Response latency              │ │
│   └────────────────┘    └──────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────┘
                                   │
         ┌─────────────────────────▼───────────────────────────┐
         │                   RAG CHAIN                          │
         │  LangChain LCEL: Retriever → Prompt → LLM → Parser  │
         └────────────┬────────────────────┬────────────────────┘
                      │                    │
         ┌────────────▼──────┐  ┌──────────▼──────────┐
         │   FAISS Vector    │  │    Ollama LLM        │
         │   Store (local)   │  │   qwen2.5:3b (local) │
         └────────────┬──────┘  └─────────────────────┘
                      │
         ┌────────────▼──────────────────────────────────────┐
         │           DOCUMENT PIPELINE                        │
         │  Loader → Chunker → SentenceTransformer Embedder  │
         │  (PDF / DOCX / TXT / Markdown)                    │
         └────────────────────────────────────────────────────┘
```

### LangChain Components Used

| Component | LangChain Class | Purpose |
|-----------|----------------|---------|
| Document Loaders | `PyPDFLoader`, `Docx2txtLoader`, `TextLoader`, `UnstructuredMarkdownLoader` | Multi-format document ingestion |
| Text Splitter | `RecursiveCharacterTextSplitter` | Intelligent document chunking |
| Embeddings | `HuggingFaceEmbeddings` (SentenceTransformers) | Local vector representations |
| Vector Store | `FAISS` | Similarity search and persistence |
| Retriever | `VectorStoreRetriever` | Relevant chunk retrieval |
| Prompt Template | `PromptTemplate` | Structured RAG prompt |
| LLM | `OllamaLLM` | Local language model inference |
| Chain | LCEL (`RunnablePassthrough`, `RunnableLambda`) | Chain orchestration |
| Output Parser | `StrOutputParser` | Clean string output |

---

## ✨ Features

- **Multi-format document upload** — PDF, DOCX, TXT, Markdown
- **Intelligent chunking** — Recursive character splitting with configurable size/overlap
- **Local embeddings** — `all-MiniLM-L6-v2` via SentenceTransformers (no API required)
- **Persistent knowledge base** — FAISS index saved to disk, auto-loaded on restart
- **Natural language Q&A** — Full RAG pipeline with conversation memory
- **Retrieved context display** — See exactly which chunks informed each answer
- **Source attribution** — Document names shown for every response
- **Chat history** — Multi-turn conversation with configurable window
- **Knowledge base management** — Build, reset, and rebuild without restarting
- **Real-time status** — Ollama/model availability badges
- **Response latency** — Shown for every query
- **Application logs** — Live log viewer in sidebar
- **Fully offline** — Zero cloud dependencies after initial setup

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | LangChain 0.3 + LCEL |
| UI | Streamlit 1.45 |
| Vector Store | FAISS (CPU) |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| LLM | Ollama + Qwen2.5:3B |
| Document Parsing | PyPDF, python-docx, UnstructuredMarkdown |
| Config | PyYAML |

---

## 📁 Folder Structure

```
tactical-knowledge-assistant/
├── app/                        # Core application modules
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── logger.py               # Centralised logging
│   ├── document_loader.py      # Multi-format document loading
│   ├── chunker.py              # Text splitting/chunking
│   ├── embeddings.py           # SentenceTransformer embeddings
│   ├── vector_store.py         # FAISS persistence & management
│   ├── retriever.py            # Retrieval logic
│   ├── llm.py                  # Ollama LLM interface
│   ├── rag_chain.py            # LCEL RAG pipeline
│   ├── chat_history.py         # Conversation memory
│   └── utils.py                # Utility functions
├── ui/                         # Streamlit UI components
│   ├── __init__.py
│   ├── styles.py               # Custom CSS
│   ├── sidebar.py              # Sidebar (upload, controls, stats)
│   └── chat.py                 # Chat interface
├── data/
│   ├── sample_docs/            # Example documents to get started
│   └── vector_store/           # Persisted FAISS index (auto-created)
├── logs/                       # Application logs (auto-created)
├── .streamlit/
│   └── config.toml             # Streamlit dark-theme config
├── main.py                     # Application entry point
├── config.yaml                 # All app settings
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.12
- [Ollama](https://ollama.ai) installed on your machine

### Step 1 — Clone the repository

```bash
git clone <your-repo-url>
cd tactical-knowledge-assistant
```

### Step 2 — Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> The first run will also download the `all-MiniLM-L6-v2` embedding model (~90 MB) automatically.

### Step 4 — Download the local LLM

```bash
ollama pull qwen2.5:3b
```

> This downloads the Qwen2.5 3B parameter model (~2 GB). Only required once.

### Step 5 — Start Ollama (if not already running)

```bash
ollama serve
```

### Step 6 — Launch the application

```bash
streamlit run main.py
```

The app will open at **http://localhost:8501** in your browser.

---

## 💡 Example Workflow

1. **Start the app** — `streamlit run main.py`
2. **Upload documents** — Use the sidebar file uploader (PDF, DOCX, TXT, or MD)
3. **Build the knowledge base** — Click **⚡ Build KB** in the sidebar
4. **Ask a question** — Type in the chat input and press **Send**
5. **Review the answer** — See the response, sources, and retrieved context
6. **Continue the conversation** — The assistant remembers previous turns
7. **Reset when done** — Click **🗑️ Reset KB** to start fresh with new documents

---

## ⚙️ Configuration

All settings are in [`config.yaml`](config.yaml):

```yaml
llm:
  model: "qwen2.5:3b"      # Change to any Ollama model
  temperature: 0.1          # Response creativity

chunking:
  chunk_size: 800           # Characters per chunk
  chunk_overlap: 150        # Overlap between chunks

retrieval:
  top_k: 5                  # Chunks retrieved per query
```

---

## 🤖 Model Choice

**Qwen2.5:3B** was chosen because:
- Excellent instruction following at 3B parameters
- Strong multilingual capability
- Low memory footprint (~2 GB VRAM / runs on CPU)
- Consistently outperforms similarly-sized models on reasoning tasks
- Fully supported by Ollama

Alternative models (change in `config.yaml`):
- `phi3:mini` — Microsoft, very fast on CPU
- `mistral:7b` — Higher quality, requires more RAM
- `llama3.2:3b` — Meta's 3B model, comparable performance

---

## 🔮 Future Improvements

- [ ] Multi-modal support (image documents via vision models)
- [ ] Hybrid search (BM25 + vector similarity)
- [ ] Document metadata filtering in retrieval
- [ ] Export chat history to PDF/Markdown
- [ ] Docker containerisation for easy deployment
- [ ] Support for additional file formats (CSV, XLSX, HTML)
- [ ] Streaming responses for improved UX
- [ ] User authentication and multi-tenant knowledge bases
- [ ] Graph-based knowledge representation
- [ ] Automatic model selection based on available hardware

---

## 📄 License

This project is created for educational and internship demonstration purposes.

---

*Built with ❤️ using LangChain, Streamlit, FAISS, SentenceTransformers, and Ollama*
