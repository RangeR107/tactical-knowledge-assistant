"""RAG pipeline using LangChain LCEL (LangChain Expression Language)."""

import time
from typing import Any, Generator

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from app.config import config
from app.llm import get_llm
from app.logger import logger
from app.retriever import get_retriever


RAG_PROMPT_TEMPLATE = """\
You are a Tactical Knowledge Assistant. Answer the user's question using ONLY the context provided below.

If the context does not contain enough information to answer the question, respond with:
"I don't have enough information in the knowledge base to answer this question."

Do not make up information. Be concise, accurate, and professional.
Format your answer clearly — use bullet points or numbered lists where appropriate.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer:"""


def _format_docs(docs: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        parts.append(f"[{i}] Source: {source}\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def _format_chat_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for turn in history[-config.chat.get("max_history", 10):]:
        lines.append(f"Human: {turn['human']}")
        lines.append(f"Assistant: {turn['assistant']}")
    return "\n".join(lines)


class RAGChain:
    """Orchestrates retrieval-augmented generation using LangChain LCEL."""

    def __init__(
        self,
        vector_store: Any,
        model_name: str | None = None,
        temperature: float | None = None,
        top_k: int | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.retriever = get_retriever(vector_store, top_k=top_k)
        self.llm = get_llm(model_name=model_name, temperature=temperature)
        self.prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=RAG_PROMPT_TEMPLATE,
        )
        self._build_chain()

    def _build_chain(self) -> None:
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
        """Run the full RAG chain and return the complete answer (non-streaming)."""
        history = chat_history or []
        start = time.perf_counter()
        logger.info(f"RAG query: '{question[:80]}…'")
        retrieved_docs = self.retriever.invoke(question)
        answer = self._chain.invoke({"question": question, "chat_history": history})
        elapsed = time.perf_counter() - start
        logger.info(f"RAG response generated in {elapsed:.2f}s")
        return {"answer": answer, "source_documents": retrieved_docs, "latency_seconds": elapsed}

    def stream(
        self,
        question: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> tuple[list[Document], Generator]:
        """Retrieve docs and return a token stream for progressive display.

        Returns:
            (retrieved_docs, token_generator) — render docs after streaming.
        """
        history = chat_history or []
        logger.info(f"RAG stream query: '{question[:80]}…'")
        retrieved_docs = self.retriever.invoke(question)
        inputs = {"question": question, "chat_history": history}
        return retrieved_docs, self._chain.stream(inputs)
