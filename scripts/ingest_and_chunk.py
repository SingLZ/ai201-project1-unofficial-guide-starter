# scripts/ingest_and_chunk.py

from __future__ import annotations

import argparse
import html
import json
import random
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup


RAW_OUT = Path("data/raw/documents.jsonl")
CLEAN_OUT = Path("data/clean/clean_documents.jsonl")
CHUNKS_OUT = Path("data/chunks/chunks.jsonl")


@dataclass(frozen=True)
class Source:
    source_id: int
    source_title: str
    source_type: str
    url: str
    local_path: str

SOURCES: list[Source] = [
    Source(
        1,
        "Reddit / r/SanJose — 1b1b Apartment Recommendations near south San Jose",
        "Reddit thread",
        "https://www.reddit.com/r/SanJose/comments/1j0k6gn/1b1b_apartment_recommendations_near_south_san_jose/",
        "data/sources/source1.txt",
    ),
    Source(
        2,
        "Reddit / r/SanJose — 2 bedroom 2 bath Apartment Recommendations South San Jose",
        "Reddit thread",
        "https://www.reddit.com/r/SanJose/comments/1m0s17v/2_bedroom_2_bath_apartment_recommendations_south/",
        "data/sources/source2.txt",
    ),
    Source(
        3,
        "Reddit / r/SanJose — Recommended neighborhoods to rent an apartment?",
        "Reddit thread",
        "https://www.reddit.com/r/SanJose/comments/1s39tcf/recommended_neighborhoods_to_rent_an_apartment/",
        "data/sources/source3.txt",
    ),
    Source(
        4,
        "Reddit / r/SanJose — Any apartment complexes that don’t suck?",
        "Reddit thread",
        "https://www.reddit.com/r/SanJose/comments/zfdbmt/any_apartment_complexes_that_dont_suck/",
        "data/sources/source4.txt",
    ),
    Source(
        5,
        "Reddit / r/SanJose — Apartment Reviews Advice",
        "Reddit thread",
        "https://www.reddit.com/r/SanJose/comments/vxoux5/apartment_reviews_advice/",
        "data/sources/source5.txt",
    ),
    Source(
        6,
        "Reddit / r/SanJose — Apartments that are Modern and Safe?",
        "Reddit thread",
        "https://www.reddit.com/r/SanJose/comments/1fu57xx/apartments_that_are_modern_and_safe/",
        "data/sources/source6.txt",
    ),
    Source(
        7,
        "San José State University — Off Campus Housing Resources",
        "University housing resource page",
        "https://www.sjsu.edu/housing/how-we-can-help/off-campus-housing-resources.php",
        "data/sources/source7.txt",
    ),
    Source(
        8,
        "Apartments.com — 5 Best Neighborhoods in San Jose, CA for Renters",
        "Neighborhood guide",
        "https://www.apartments.com/blog/best-neighborhoods-in-san-jose-for-renters",
        "data/sources/source8.txt",
    ),
    Source(
        9,
        "Apartments.com — Santa Teresa Apartments, San Jose, CA",
        "Apartment listing / reviews page",
        "https://www.apartments.com/santa-teresa-apartments-san-jose-ca/0tn5k10/",
        "data/sources/source9.txt",
    ),
    Source(
        10,
        "Apartments.com — The Woods Apartments, San Jose, CA",
        "Apartment listing / reviews page",
        "https://www.apartments.com/the-woods-apartments-san-jose-ca/75d8npw/",
        "data/sources/source10.txt",
    ),
]


BOILERPLATE_PATTERNS = [
    r"^\s*cookie[s]?\s",
    r"^\s*accept all",
    r"^\s*privacy policy",
    r"^\s*terms of use",
    r"^\s*advertise",
    r"^\s*share\s*$",
    r"^\s*read more\s*$",
    r"^\s*skip to main content",
    r"^\s*log in\s*$",
    r"^\s*sign up\s*$",
    r"^\s*menu\s*$",
    r"^\s*©",
]


def source_metadata(source: Source, stage: str) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "source_title": source.source_title,
        "source_type": source.source_type,
        "url": source.url,
        "local_path": source.local_path,
        "stage": stage,
    }


def request_text(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 UnofficialGuideStudentProject/1.0 "
            "(educational document collection)"
        )
    }
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()
    return response.text


def reddit_json_url(url: str) -> str:
    clean_url = url.rstrip("/")
    return f"{clean_url}.json"


def extract_reddit_comment_bodies(children: list[dict[str, Any]]) -> list[str]:
    comments: list[str] = []

    for child in children:
        if child.get("kind") != "t1":
            continue

        data = child.get("data", {})
        body = data.get("body", "")
        author = data.get("author", "unknown")
        score = data.get("score", 0)

        if body and body not in {"[deleted]", "[removed]"}:
            comments.append(f"[COMMENT]\nAuthor: {author}\nScore: {score}\nText: {body}")

        replies = data.get("replies")
        if isinstance(replies, dict):
            reply_children = (
                replies.get("data", {})
                .get("children", [])
            )
            comments.extend(extract_reddit_comment_bodies(reply_children))

    return comments


def fetch_reddit_text(source: Source) -> str:
    payload = json.loads(request_text(reddit_json_url(source.url)))

    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Unexpected Reddit JSON structure")

    post_data = payload[0]["data"]["children"][0]["data"]
    title = post_data.get("title", source.source_title)
    selftext = post_data.get("selftext", "")

    comments = extract_reddit_comment_bodies(payload[1]["data"].get("children", []))

    sections = [
        f"THREAD TITLE: {title}",
        f"POST TEXT:\n{selftext}" if selftext else "POST TEXT: [No post body]",
        "COMMENTS:",
        *comments,
    ]
    return "\n\n".join(sections)


def remove_noncontent_nodes(soup: BeautifulSoup) -> None:
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "button",
        ]
    ):
        tag.decompose()

    noisy_selector = re.compile(
        r"(cookie|banner|advert|ad-|ads|footer|header|navbar|nav|sidebar|share|social|modal|popup|newsletter)",
        re.IGNORECASE,
    )

    for tag in soup.find_all(True):
        tag_id = " ".join(
            [
                str(tag.get("id", "")),
                " ".join(tag.get("class", [])) if isinstance(tag.get("class"), list) else str(tag.get("class", "")),
            ]
        )
        if noisy_selector.search(tag_id):
            tag.decompose()


def extract_html_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    remove_noncontent_nodes(soup)

    candidate = soup.find("main") or soup.find("article") or soup.body or soup

    pieces: list[str] = []
    for node in candidate.find_all(["h1", "h2", "h3", "p", "li"]):
        text = node.get_text(" ", strip=True)
        if text:
            pieces.append(text)

    if not pieces:
        pieces = [candidate.get_text("\n", strip=True)]

    return "\n\n".join(pieces)


def fetch_source_text(source: Source) -> str:
    local_text = load_local_text(source)

    if local_text is not None:
        return local_text

    if source.source_type.lower().startswith("reddit"):
        return fetch_reddit_text(source)

    return extract_html_text(request_text(source.url))


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[\u200b\u200c\u200d]", "", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in BOILERPLATE_PATTERNS):
            continue

        if len(line) <= 2:
            continue

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return cleaned.strip()


def token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def split_words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def chunk_by_tokens(text: str, max_tokens: int, overlap: int) -> list[str]:
    words = split_words(text)
    if not words:
        return []

    if len(words) <= max_tokens:
        return [" ".join(words)]

    chunks: list[str] = []
    step = max(1, max_tokens - overlap)

    for start in range(0, len(words), step):
        end = start + max_tokens
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break

    return chunks


def paragraph_chunks(text: str, max_tokens: int, overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        p_tokens = token_count(paragraph)

        if p_tokens > max_tokens:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_tokens = 0
            chunks.extend(chunk_by_tokens(paragraph, max_tokens, overlap))
            continue

        if current and current_tokens + p_tokens > max_tokens:
            chunks.append("\n\n".join(current).strip())

            overlap_words = split_words(chunks[-1])[-overlap:] if overlap > 0 else []
            current = [" ".join(overlap_words)] if overlap_words else []
            current_tokens = len(overlap_words)

        current.append(paragraph)
        current_tokens += p_tokens

    if current:
        chunks.append("\n\n".join(current).strip())

    return [chunk for chunk in chunks if token_count(chunk) > 0]


def reddit_comment_chunks(text: str, max_tokens: int, overlap: int) -> list[str]:
    blocks = [block.strip() for block in re.split(r"(?=\[COMMENT\])", text) if block.strip()]
    chunks: list[str] = []

    for block in blocks:
        if token_count(block) <= max_tokens:
            chunks.append(block)
        else:
            chunks.extend(chunk_by_tokens(block, max_tokens, overlap))

    return [chunk for chunk in chunks if len(chunk.strip()) >= 40]


def make_chunks(
    cleaned_doc: dict[str, Any],
    max_tokens: int,
    overlap: int,
) -> list[dict[str, Any]]:
    source_type = str(cleaned_doc["source_type"]).lower()
    text = cleaned_doc["text"]

    if source_type.startswith("reddit"):
        texts = reddit_comment_chunks(text, max_tokens=max_tokens, overlap=overlap)
    else:
        texts = paragraph_chunks(text, max_tokens=max_tokens, overlap=overlap)

    rows: list[dict[str, Any]] = []
    for index, chunk_text in enumerate(texts):
        source_id = cleaned_doc["source_id"]
        rows.append(
            {
                "chunk_id": f"source-{source_id}-chunk-{index}",
                "chunk_index": index,
                "text": chunk_text,
                "token_count": token_count(chunk_text),
                "source_id": cleaned_doc["source_id"],
                "source_title": cleaned_doc["source_title"],
                "source_type": cleaned_doc["source_type"],
                "url": cleaned_doc["url"],
                "local_path": cleaned_doc["local_path"],
                "stage": "chunk",
            }
        )

    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_sample_chunks(chunks: list[dict[str, Any]], sample_size: int) -> None:
    if not chunks:
        print("\nNo chunks produced.")
        return

    random.seed(42)
    sample = random.sample(chunks, k=min(sample_size, len(chunks)))

    print("\n=== Representative chunks ===")
    for i, chunk in enumerate(sample, start=1):
        print(f"\n--- Chunk sample {i} ---")
        print(f"Source: {chunk['source_title']}")
        print(f"URL: {chunk['url']}")
        print(f"Token count: {chunk['token_count']}")
        print(chunk["text"][:1200])


def run(max_tokens: int, overlap: int, sample_size: int) -> int:
    raw_docs: list[dict[str, Any]] = []

    for source in SOURCES:
        print(f"Loading source {source.source_id}: {source.source_title}")

        try:
            text = fetch_source_text(source)
            error = None
        except Exception as exc:
            text = ""
            error = f"{type(exc).__name__}: {exc}"

        row = {
            **source_metadata(source, "raw"),
            "text": text,
            "fetch_error": error,
        }
        raw_docs.append(row)

    write_jsonl(RAW_OUT, raw_docs)

    clean_docs: list[dict[str, Any]] = []
    for row in raw_docs:
        cleaned = clean_text(row["text"])

        clean_docs.append(
    {
        **{
            key: row[key]
            for key in ["source_id", "source_title", "source_type", "url", "local_path"]
        },
        "stage": "clean",
        "text": cleaned,
        "fetch_error": row.get("fetch_error"),
    }
)

    write_jsonl(CLEAN_OUT, clean_docs)

    all_chunks: list[dict[str, Any]] = []
    for doc in clean_docs:
        if not doc["text"]:
            continue
        all_chunks.extend(make_chunks(doc, max_tokens=max_tokens, overlap=overlap))

    all_chunks = [
        chunk
        for chunk in all_chunks
        if chunk["text"].strip()
        and not re.search(r"<[^>]+>|&nbsp;|&amp;", chunk["text"], flags=re.IGNORECASE)
    ]

    write_jsonl(CHUNKS_OUT, all_chunks)

    loaded = sum(1 for row in raw_docs if row["text"])
    cleaned = sum(1 for row in clean_docs if row["text"])

    print("\n=== Summary ===")
    print(f"Documents attempted: {len(SOURCES)}")
    print(f"Documents loaded: {loaded}")
    print(f"Cleaned documents: {cleaned}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Raw output: {RAW_OUT}")
    print(f"Clean output: {CLEAN_OUT}")
    print(f"Chunks output: {CHUNKS_OUT}")

    failed = [row for row in raw_docs if row.get("fetch_error")]
    if failed:
        print("\n=== Fetch warnings ===")
        for row in failed:
            print(f"- Source {row['source_id']}: {row['fetch_error']}")

    if len(all_chunks) < 50:
        print("\nWARNING: Fewer than 50 chunks were produced. Check whether pages were blocked or chunks are too large.")
    elif len(all_chunks) > 2000:
        print("\nWARNING: More than 2000 chunks were produced. Chunks may be too small.")

    print_sample_chunks(all_chunks, sample_size=sample_size)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest, clean, and chunk South San Jose housing documents.")
    parser.add_argument("--max-tokens", type=int, default=450, help="Maximum tokens per chunk.")
    parser.add_argument("--overlap", type=int, default=50, help="Token overlap for longer documents.")
    parser.add_argument("--sample-size", type=int, default=5, help="Number of representative chunks to print.")
    return parser.parse_args()

def load_local_text(source: Source) -> str | None:
    path = Path(source.local_path)

    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8").strip()

    if not text:
        return None

    return text

if __name__ == "__main__":
    args = parse_args()

    if args.overlap >= args.max_tokens:
        print("ERROR: --overlap must be smaller than --max-tokens.", file=sys.stderr)
        raise SystemExit(2)

    raise SystemExit(run(max_tokens=args.max_tokens, overlap=args.overlap, sample_size=args.sample_size))
