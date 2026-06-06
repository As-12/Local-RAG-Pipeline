# Reset Database

## Option 1: Reset only Qdrant data

From your project directory:

```bash
docker compose stop rag-api qdrant
sudo rm -rf ./data/qdrant/*
docker compose up -d qdrant rag-api
```

Then confirm the services are healthy:

```bash
docker compose ps
curl http://localhost:8080/health
```

This removes all vectors, collections, and payload metadata.

## Option 2: Delete the collection through Qdrant API

This is cleaner if Qdrant is running.

```bash
curl -X DELETE http://localhost:6333/collections/local_docs
```

Then restart `rag-api`, which should recreate the collection on startup:

```bash
docker compose restart rag-api
```

Check Qdrant collections:

```bash
curl http://localhost:6333/collections
```

## Option 3: Full local RAG data reset

This removes vector DB data and processed/failed/inbox files:

```bash
docker compose down

sudo rm -rf ./data/qdrant/*
sudo rm -rf ./data/inbox/*
sudo rm -rf ./data/processed/*
sudo rm -rf ./data/failed/*

docker compose up -d
```

This does **not** delete Ollama models, because those are usually stored in:

```text
./data/ollama
```

## After reset, re-ingest a test document

```bash
cat > ./data/inbox/rag-test-moonstone.md <<'EOF'
# RAG Test Document: Project Moonstone

The secret validation phrase for this document is: pineapple circuit delta.

The project mascot is a blue fox named Nimbo.

The primary vector database used by Project Moonstone is Qdrant.
EOF
```

Trigger ingestion:

```bash
curl -X POST http://localhost:8080/ingest
```

Test retrieval:

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the secret validation phrase for Project Moonstone?"}'
```

Expected answer should include:

```text
pineapple circuit delta
```

For normal development, I would use **Option 2**. For a guaranteed clean slate, use **Option 1**.
