import httpx

from app.config import settings
from app.embeddings import embed_texts
from app.vectorstore import search


SYSTEM_PROMPT = """You are a local AI assistant using retrieved context.

Rules:
- Answer using the provided context when relevant.
- If the context does not contain the answer, say so.
- Do not invent citations.
- Keep the answer concise and practical.
"""


def build_prompt(query: str, results) -> str:
    context_blocks = []

    for index, result in enumerate(results, start=1):
        payload = result.payload or {}
        context_blocks.append(
            f"""[Source {index}]
Filename: {payload.get("filename")}
Chunk ID: {payload.get("chunk_id")}
Content:
{payload.get("chunk_text")}
"""
        )

    context = "\n\n".join(context_blocks)

    return f"""
Context:
{context}

User question:
{query}

Answer:
"""


async def answer_query(query: str) -> dict:
    query_embedding = (await embed_texts([query]))[0]
    results = search(query_embedding, settings.top_k)

    prompt = build_prompt(query, results)

    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

    sources = []
    for result in results:
        payload = result.payload or {}
        sources.append(
            {
                "filename": payload.get("filename"),
                "chunk_id": payload.get("chunk_id"),
                "score": result.score,
            }
        )

    return {
        "answer": data["message"]["content"],
        "sources": sources,
    }