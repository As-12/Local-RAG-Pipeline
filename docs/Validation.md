# Validation

Use a document with a few **unique facts that the model would not already know**, then query those facts. That proves the answer came from RAG retrieval, not the base model.

Create this test document:

# RAG Test Document: Project Moonstone

Project Moonstone is an internal home-lab experiment created by Thanaphon to test a local Retrieval-Augmented Generation pipeline.

The project mascot is a blue fox named Nimbo.

The secret validation phrase for this document is: "pineapple circuit delta".

The preferred backup window for Project Moonstone is every Saturday at 03:15 local time.

The primary vector database used by Project Moonstone is Qdrant.

The ingestion rule is that duplicate files should be detected using a SHA-256 content hash.

The expected embedding model for the first prototype is all-minilm.

The expected local chat model for the first prototype is qwen2.5:7b-instruct-q4_K_M.

If a document fails ingestion, it should be moved to the failed directory.

If a document succeeds ingestion, it should be moved to the processed directory.

Project Moonstone should never call an external API during inference. All embedding generation, vector search, and chat responses should run locally.

Save it into your inbox:

```bash
cat > ./data/inbox/rag-test-moonstone.md <<'EOF'
# RAG Test Document: Project Moonstone

Project Moonstone is an internal home-lab experiment created by Thanaphon to test a local Retrieval-Augmented Generation pipeline.

The project mascot is a blue fox named Nimbo.

The secret validation phrase for this document is: "pineapple circuit delta".

The preferred backup window for Project Moonstone is every Saturday at 03:15 local time.

The primary vector database used by Project Moonstone is Qdrant.

The ingestion rule is that duplicate files should be detected using a SHA-256 content hash.

The expected embedding model for the first prototype is all-minilm.

The expected local chat model for the first prototype is qwen2.5:7b-instruct-q4_K_M.

If a document fails ingestion, it should be moved to the failed directory.

If a document succeeds ingestion, it should be moved to the processed directory.

Project Moonstone should never call an external API during inference. All embedding generation, vector search, and chat responses should run locally.
EOF
```

Trigger ingestion:

```bash
curl -X POST http://localhost:8080/ingest
```

Check that it moved:

```bash
ls ./data/processed
ls ./data/failed
```

Now test RAG retrieval:

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the secret validation phrase for Project Moonstone?"}'
```

Expected answer should include:

```text
pineapple circuit delta
```

Try a few more:

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the mascot of Project Moonstone?"}'
```

Expected:

```text
blue fox named Nimbo
```

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "When is the preferred backup window for Project Moonstone?"}'
```

Expected:

```text
Saturday at 03:15 local time
```

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What should happen to a document after successful ingestion?"}'
```

Expected:

```text
It should be moved to the processed directory.
```

The strongest proof is the secret phrase test, because the base model cannot know `"pineapple circuit delta"` unless retrieval is working.
