# local-models

Type: research
Status: resolved
Blocked by: -

## Question

Which free local search, re-ordering and summary models run well on an ordinary laptop, with what quality and speed, for the fully local Mode?

## Answer

Findings in `research/08-local-models.md`. Local defaults: bge-small-en-v1.5 for embeddings (nomic-embed-text-v1.5 is the upgrade for long text), ms-marco-MiniLM-L-6-v2 for re-ordering, and a 3-4B 4-bit model (Qwen3-4B-Instruct-2507 or Phi-4-mini) via Ollama or llama.cpp for summaries. Hosted embeddings score about the same. CPU speed and RAM were not measured; MTEB scores are the model owners' own.
