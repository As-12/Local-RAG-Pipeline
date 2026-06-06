import asyncio
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

from app.config import settings
from app.ingest import ingest_file
from app.rag import answer_query
from app.vectorstore import ensure_collection


app = FastAPI(title="Local RAG API")

documents_ingested = Counter("rag_documents_ingested_total", "Documents ingested")
documents_failed = Counter("rag_documents_failed_total", "Documents failed")
query_latency = Histogram("rag_query_latency_seconds", "RAG query latency")
ingestion_latency = Histogram("rag_ingestion_latency_seconds", "Document ingestion latency")
inbox_queue_size = Gauge("rag_inbox_queue_size", "Number of files waiting in inbox")


class QueryRequest(BaseModel):
    query: str


@app.on_event("startup")
async def startup():
    ensure_collection()
    asyncio.create_task(inbox_loop())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")


@app.post("/query")
@query_latency.time()
async def query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return await answer_query(request.query)


@app.post("/ingest")
@ingestion_latency.time()
async def ingest_now():
    return await scan_inbox_once()


async def inbox_loop():
    while True:
        await scan_inbox_once()
        await asyncio.sleep(10)


async def scan_inbox_once():
    inbox = Path(settings.inbox_dir)
    failed = Path(settings.failed_dir)

    inbox.mkdir(parents=True, exist_ok=True)
    failed.mkdir(parents=True, exist_ok=True)

    files = [
        path for path in inbox.iterdir()
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}
    ]

    inbox_queue_size.set(len(files))

    results = []

    for path in files:
        try:
            result = await ingest_file(path)
            documents_ingested.inc()
            results.append(result)
        except Exception as exc:
            documents_failed.inc()
            failed_path = failed / path.name
            shutil.move(str(path), str(failed_path))
            results.append(
                {
                    "filename": path.name,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    return {"results": results}