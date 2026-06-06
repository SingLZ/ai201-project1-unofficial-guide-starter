# query.py

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer


CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "south_san_jose_housing_chunks"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

TOP_K = 4
MAX_ACCEPTABLE_DISTANCE = 0.60


@dataclass(frozen=True)
class RetrievedChunk:
    rank: int
    chunk_id: str
    text: str
    distance: float
    metadata: dict[str, Any]


_model: SentenceTransformer | None = None
_groq_client: Groq | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _model


def get_groq_client() -> Groq:
    global _groq_client

    if _groq_client is None:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "Missing GROQ_API_KEY. Add it to .env before running generation."
            )

        _groq_client = Groq(api_key=api_key)

    return _groq_client


def get_collection():
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            "Missing data/chroma. Run: python scripts/embed_and_retrieve.py --build --test"
        )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME)


def retrieve(query: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
    question = query.strip()

    if not question:
        return []

    model = get_embedding_model()
    query_embedding = model.encode(
        [question],
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()

    collection = get_collection()
    result = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for rank, (chunk_id, text, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        chunks.append(
            RetrievedChunk(
                rank=rank,
                chunk_id=str(chunk_id),
                text=str(text),
                metadata=dict(metadata or {}),
                distance=float(distance),
            )
        )

    return chunks


def should_decline(chunks: list[RetrievedChunk]) -> bool:
    if not chunks:
        return True

    best_distance = chunks[0].distance
    return best_distance > MAX_ACCEPTABLE_DISTANCE


def format_context(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []

    for chunk in chunks:
        source_title = chunk.metadata.get("source_title", "Unknown source")
        url = chunk.metadata.get("url", "")
        chunk_index = chunk.metadata.get("chunk_index", "")

        parts.append(
            "\n".join(
                [
                    f"[S{chunk.rank}]",
                    f"Source: {source_title}",
                    f"URL: {url}",
                    f"Chunk index: {chunk_index}",
                    f"Distance: {chunk.distance:.4f}",
                    "Text:",
                    chunk.text,
                ]
            )
        )

    return "\n\n---\n\n".join(parts)


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    context = format_context(chunks)

    system_prompt = (
        "You are a grounded RAG assistant for an unofficial South San Jose housing guide. "
        "Answer using ONLY the provided retrieved document chunks. "
        "Do not use outside knowledge. "
        "If the retrieved chunks do not explicitly contain the answer, say exactly: "
        "\"I don't have enough information on that from the collected documents.\" "
        "When answering, cite the relevant source labels like [S1] or [S2]. "
        "Do not invent apartment facts, prices, safety claims, policies, or recommendations."
    )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Retrieved document chunks:\n{context}\n\n"
        "Answer format:\n"
        "Answer: <grounded answer with source labels>\n"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def unique_sources(chunks: list[RetrievedChunk]) -> list[str]:
    seen: set[str] = set()
    sources: list[str] = []

    for chunk in chunks:
        title = str(chunk.metadata.get("source_title", "Unknown source"))
        url = str(chunk.metadata.get("url", ""))
        chunk_index = chunk.metadata.get("chunk_index", "")
        item = f"{title} | chunk {chunk_index} | distance {chunk.distance:.4f} | {url}"

        if item not in seen:
            sources.append(item)
            seen.add(item)

    return sources


def ask(question: str, top_k: int = TOP_K) -> dict[str, Any]:
    clean_question = question.strip()

    if not clean_question:
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "chunks": [],
        }

    chunks = retrieve(clean_question, top_k=top_k)

    if should_decline(chunks):
        return {
            "answer": "I don't have enough information on that from the collected documents.",
            "sources": unique_sources(chunks),
            "chunks": [chunk.__dict__ for chunk in chunks],
        }

    client = get_groq_client()
    model_name = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    completion = client.chat.completions.create(
        model=model_name,
        messages=build_prompt(clean_question, chunks),
        temperature=0,
        max_completion_tokens=500,
    )

    answer = completion.choices[0].message.content or ""
    answer = answer.strip()

    if not answer:
        answer = "I don't have enough information on that from the collected documents."

    if chunks and "[S" not in answer:
        answer = (
            f"{answer}\n\n"
            "Sources used: "
            + ", ".join(f"[S{chunk.rank}]" for chunk in chunks[:2])
        )

    return {
        "answer": answer,
        "sources": unique_sources(chunks),
        "chunks": [chunk.__dict__ for chunk in chunks],
    }


def print_result(question: str) -> None:
    result = ask(question)

    print("\n" + "=" * 88)
    print(f"QUESTION: {question}")
    print("=" * 88)
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(f"- {source}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask grounded questions over the housing guide.")
    parser.add_argument("question", nargs="*", help="Question to ask.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    question = " ".join(args.question).strip()

    if question:
        print_result(question)
        return 0

    test_questions = [
        "What is the estimated budget for 1B1B in San Jose?",
        "What is the estimated budget for 2B2B in San Jose?",
        "In Santa Teresa Apartments listing, what bedroom options are available?",
        "What do the documents say about apartments in New York City?",
    ]

    for test_question in test_questions:
        print_result(test_question)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())