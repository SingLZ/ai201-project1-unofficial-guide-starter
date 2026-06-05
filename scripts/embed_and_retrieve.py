# scripts/embed_and_retrieve.py

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


CHUNKS_PATH = Path("data/chunks/chunks.jsonl")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "south_san_jose_housing_chunks"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


DEFAULT_TEST_QUERIES = [
    "What is the estimated budget for 1B1B in san jose?",
    "What is the estimated budget for 2B2B in san jose?",
    "In Santa Teresa Apartments listing, what bedroom options are available?",
]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, str | int | float | bool]


def load_chunks(path: Path = CHUNKS_PATH) -> list[Chunk]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing chunks file: {path}. Run `python scripts/ingest_and_chunk.py` first."
        )

    chunks: list[Chunk] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}") from exc

            chunk_id = str(row.get("chunk_id", "")).strip()
            text = str(row.get("text", "")).strip()

            if not chunk_id:
                raise ValueError(f"Missing chunk_id on line {line_number}")
            if not text:
                continue

            metadata: dict[str, str | int | float | bool] = {
                "source_id": int(row.get("source_id", -1)),
                "source_title": str(row.get("source_title", "")),
                "source_type": str(row.get("source_type", "")),
                "url": str(row.get("url", "")),
                "local_path": str(row.get("local_path", "")),
                "chunk_index": int(row.get("chunk_index", -1)),
                "token_count": int(row.get("token_count", 0)),
            }

            chunks.append(Chunk(chunk_id=chunk_id, text=text, metadata=metadata))

    if not chunks:
        raise ValueError(f"No valid chunks found in {path}")

    return chunks


def batched(items: list[Any], batch_size: int) -> list[list[Any]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def reset_chroma_dir() -> None:
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def build_vector_store(batch_size: int = 32, rebuild: bool = True) -> None:
    if rebuild:
        reset_chroma_dir()
    else:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Loaded chunks: {len(chunks)}")
    print(f"Embedding model: {EMBEDDING_MODEL_NAME}")
    print(f"Chroma path: {CHROMA_DIR}")
    print(f"Collection: {COLLECTION_NAME}")

    for batch in batched(chunks, batch_size):
        texts = [chunk.text for chunk in batch]
        ids = [chunk.chunk_id for chunk in batch]
        metadatas = [chunk.metadata for chunk in batch]

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    print(f"Stored vectors: {collection.count()}")


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME)


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode(
        [query],
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()

    collection = get_collection()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    rows: list[dict[str, Any]] = []
    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        rows.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "distance": float(distance),
                "text": document,
                "metadata": metadata,
            }
        )

    return rows


def print_retrieval_results(query: str, top_k: int) -> None:
    rows = retrieve(query=query, top_k=top_k)

    print("\n" + "=" * 88)
    print(f"QUERY: {query}")
    print("=" * 88)

    for row in rows:
        metadata = row["metadata"]
        text = row["text"]

        print(f"\n--- Result {row['rank']} ---")
        print(f"Distance: {row['distance']:.4f}")
        print(f"Chunk ID: {row['chunk_id']}")
        print(f"Source: {metadata.get('source_title')}")
        print(f"URL: {metadata.get('url')}")
        print(f"Chunk index: {metadata.get('chunk_index')}")
        print("Text:")
        print(text[:1200])


def run_test_queries(top_k: int) -> None:
    for query in DEFAULT_TEST_QUERIES:
        print_retrieval_results(query=query, top_k=top_k)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed chunks into ChromaDB and test retrieval."
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build/rebuild the ChromaDB vector store from data/chunks/chunks.jsonl.",
    )
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help="Do not delete the existing vector store before building.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the default retrieval test queries.",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Run one custom retrieval query.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.build and not args.test and not args.query:
        print(
            "Nothing to do. Use one of:\n"
            "  python scripts/embed_and_retrieve.py --build --test\n"
            "  python scripts/embed_and_retrieve.py --query \"your question\""
        )
        return 0

    if args.build:
        build_vector_store(batch_size=args.batch_size, rebuild=not args.no_rebuild)

    if args.test:
        run_test_queries(top_k=args.top_k)

    if args.query:
        print_retrieval_results(query=args.query, top_k=args.top_k)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())