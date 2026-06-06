from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings


client = QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    collections = client.get_collections().collections
    names = {collection.name for collection in collections}

    if settings.collection_name not in names:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(
                size=settings.vector_size,
                distance=Distance.COSINE,
            ),
        )


def delete_by_file_hash(content_hash: str) -> None:
    client.delete(
        collection_name=settings.collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="content_hash",
                    match=MatchValue(value=content_hash),
                )
            ]
        ),
    )


def upsert_chunks(points: list[PointStruct]) -> None:
    client.upsert(
        collection_name=settings.collection_name,
        points=points,
    )


def search(vector: list[float], top_k: int):
    return client.search(
        collection_name=settings.collection_name,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )