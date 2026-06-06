## Troubleshooting

### Docker cannot see the GPU

Run:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

If the second command fails, check your NVIDIA Container Toolkit installation.

---

### Ollama runs out of VRAM

Try:

* Use a smaller quantized model
* Reduce context size
* Use only one concurrent request
* Stop other GPU workloads
* Use `all-minilm` instead of larger embedding models

---

### Documents are not ingested

Check:

```bash
docker compose logs -f rag-api
```

Confirm that files are in:

```text
./data/inbox
```

Confirm that file extensions are supported:

```text
.txt
.md
.pdf
.docx
```

---

### PDF text is empty

The PDF may be scanned or image-based.

Current parser support assumes text-based PDFs. OCR can be added later as a separate processing step.

---