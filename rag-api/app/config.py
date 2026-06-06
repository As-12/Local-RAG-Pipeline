from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://ollama:11434"
    qdrant_url: str = "http://qdrant:6333"

    collection_name: str = "local_docs"
    embedding_model: str = "all-minilm"
    llm_model: str = "qwen2.5:7b-instruct-q4_K_M"

    vector_size: int = 384

    inbox_dir: str = "/data/inbox"
    processed_dir: str = "/data/processed"
    failed_dir: str = "/data/failed"

    chunk_size: int = 700
    chunk_overlap: int = 120
    top_k: int = 5


settings = Settings()