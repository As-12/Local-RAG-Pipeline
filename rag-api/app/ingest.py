import hashlib
import shutil
import time
import uuid
from pathlib import Path

from qdrant_client.models import PointStruct

from app.config import settings
from app.parser import parse_document
from app.chunking import chunk_text
from app.embeddings import embed_texts
from app.vectorstore import delete_by_file_hash, upsert_chunks


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


async def ingest_file(path: Path) -> dict:
    started = time.time()
    content_hash = file_hash(path)

    text = parse_document(path)
    chunks = chunk_text(
        text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )

    if not chunks:
        raise ValueError("No text extracted from document")

    embeddings = await embed_texts(chunks)

    # Duplicate policy: overwrite old vectors with same content hash.
    delete_by_file_hash(content_hash)

    file_id = str(uuid.uuid4())
    now = int(time.time())

    points = []
    for i, embedding in enumerate(embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "file_id": file_id,
                    "filename": path.name,
                    "source_path": str(path),
                    "content_hash": content_hash,
                    "chunk_id": i,
                    "chunk_text": chunks[i],
                    "created_at": int(path.stat().st_ctime),
                    "ingested_at": now,
                    "mime_type": path.suffix.lower(),
                },
            )
        )

    upsert_chunks(points)

    processed_path = Path(settings.processed_dir) / path.name
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(processed_path))

    return {
        "filename": path.name,
        "chunks": len(chunks),
        "elapsed_seconds": round(time.time() - started, 3),
        "status": "ingested",
    }