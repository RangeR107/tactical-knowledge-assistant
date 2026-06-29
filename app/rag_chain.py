"""RAG pipeline using LangChain LCEL (LangChain Expression Language)."""

import time
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from app.config import config
from app.llm import get_llm
from app.logger import logger
from app.retriever import get_retriever


# ── Prompt template ─────────────────────────────────────────────────────────

RAG_PROMPT_TEMPLATE = """\
You are a Tactical Knowledge Assistant. Answer the user's question using ONLY the context provided below.

If the context does not contain enough information to answer the question, respond with:
"I don't have enough information in the knowledge base to answer this question."

Do not make up information. Be concise, accurate, and professional.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer:"""


def _format_docs(docs: list[Document]) -> str:
    """Format retrieved documents into a single context string."""
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        parts.append(f"[{i}] Source: {source}\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def _format_chat_history(history: list[dict[str, str]]) -> str:
    """Format chat history into a readable string for the prompt."""
    if not history:
        return "No previous conversation."
    lines = []
    for turn in history[-config.chat.get("max_history", 10):]:
        lines.append(f"Human: {turn['human']}")
        lines.append(f"Assistant: {turn['assistant']}")
    return "\n".join(lines)


# ── RAG Chain ────────────────────────────────────────────────────────────────

class RAGChain:
    """Orchestrates retrieval-augmented generation using LangChain LCEL."""

    def __init__(self, vector_store: FAISS) -> None:
        self.vector_store = vector_store
        self.retriever = get_retriever(vector_store)
        self.llm = get_llm()
        self.prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=RAG_PROMPT_TEMPLATE,
        )
        self._build_chain()

    def _build_chain(self) -> None:
        """Build the LCEL chain: retrieve → format → prompt → LLM → parse."""
        # Extract the question string before hitting the retriever
        extract_question = RunnableLambda(lambda x: x["question"])
        extract_history = RunnableLambda(
            lambda x: _format_chat_history(x.get("chat_history", []))
        )

        self._chain = (
            {
                "context": extract_question | self.retriever | _format_docs,
                "chat_history": extract_history,
                "question": extract_question,
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def run(
        self,
        question: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Execute the RAG chain for a given question.

        Args:
            question: The user's natural language question.
            chat_history: List of previous turns as [{"human": ..., "assistant": ...}].

        Returns:
            Dict with keys: answer, source_documents, latency_seconds.
        """
        history = chat_history or []
        start = time.perf_counter()

        logger.info(f"RAG query: '{question[:80]}…'")

        # Retrieve relevant documents separately so we can surface them in the UI
        retrieved_docs = self.retriever.invoke(question)

        inputs = {"question": question, "chat_history": history}
        answer = self._chain.invoke(inputs)

        elapsed = time.perf_counter() - start
        logger.info(f"RAG response generated in {elapsed:.2f}s")

        return {
            "answer": answer,
            "source_documents": retrieved_docs,
            "latency_seconds": elapsed,
        }
