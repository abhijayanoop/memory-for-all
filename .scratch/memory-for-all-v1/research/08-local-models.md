# 08 local-models: free local models for the fully local Mode

Question: which free local embedding, re-ordering (rerank) and summary models run well on a no-GPU laptop (8-16 GB RAM)?

Tags: **verified** = read on the owning page during this research; **secondary** = reported by a page that is not the model owner, or a number the page gave only indirectly; **inferred** = my reasoning, not stated by any source. No speed was measured on a real laptop; all speed claims below are sourced from model/library pages or inferred from size.

## Summary and recommendation (inferred unless cited below)

- Embeddings: keep `BAAI/bge-small-en-v1.5` as default (tiny, MIT, already in prototype). Upgrade candidate: `nomic-ai/nomic-embed-text-v1.5` (8192-token context, similar MTEB, 4x larger) if Chunks exceed 512 tokens.
- Rerank: keep `Xenova/ms-marco-MiniLM-L-6-v2` (80 MB). Upgrade candidate: `BAAI/bge-reranker-base` (about 1 GB on disk, slower).
- Summary / key decisions: a 3-4B instruct model in 4-bit via Ollama or llama.cpp (Qwen3-4B-Instruct-2507, Apache-2.0, is the cleanest licence; Phi-4-mini is MIT; Llama 3.2 3B has a custom licence). 1.7B-class models are the low-RAM fallback.
- Hosted: OpenAI has embeddings; Anthropic has none (points to Voyage). Both plug in as a swap of the "embed" and "summarise" functions behind the Mode setting.

## (a) Embeddings

| Model | Size | Dim | Max tokens | MTEB avg | Licence |
|---|---|---|---|---|---|
| BAAI/bge-small-en-v1.5 | 33.4M params, 0.067 GB | 384 | 512 | 62.17 | MIT |
| nomic-embed-text-v1.5 | 0.1B params; 0.52 GB (0.13 GB quantised) | 768 (truncate to 64-512) | 8192 | 62.28 at 768, 61.04 at 256 | Apache-2.0 |
| BAAI/bge-m3 | size not stated on card | 1024 | 8192 | not stated on card | MIT |
| OpenAI text-embedding-3-small (hosted) | n/a | 1536 | 8192 | 62.3% | proprietary API |
| OpenAI text-embedding-3-large (hosted) | n/a | 3072 | 8192 | 64.6% | proprietary API |

Claims:
- bge-small: MIT, 33.4M params, 384 dim, 512 tokens, MTEB 62.17 over 56 datasets; query instruction optional in v1.5, never needed for passages. [verified] https://huggingface.co/BAAI/bge-small-en-v1.5
- nomic v1.5: Apache-2.0, 0.1B params, 8192 sequence length, Matryoshka dims 768/512/256/128/64 with MTEB 62.28/61.96/61.04/59.34/56.10; requires prefixes `search_document:` and `search_query:`; runs in sentence-transformers. [verified] https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
- bge-m3: MIT, 1024 dim, 8192 tokens, 100+ languages, no parameter count on card. [verified] https://huggingface.co/BAAI/bge-m3 . It is not in fastembed's supported list. [verified] https://qdrant.github.io/fastembed/examples/Supported_Models/
- fastembed supported list (size GB, licence): bge-small-en-v1.5 0.067 MIT; bge-base-en-v1.5 0.21 MIT; nomic-embed-text-v1.5 0.52 Apache-2.0 and a `-Q` quantised build 0.13; jina-embeddings-v2-small-en 0.12 Apache-2.0; snowflake-arctic-embed-s 0.13 Apache-2.0. [verified] https://qdrant.github.io/fastembed/examples/Supported_Models/
- fastembed uses ONNX Runtime and is described as light and fast; the page gives no GPU requirement and no speed comparison. [verified] https://qdrant.github.io/fastembed/
- Ollama serves `nomic-embed-text` (274 MB) with a 2K context window via `POST /api/embed`. [verified] https://ollama.com/library/nomic-embed-text . Note: Ollama's 2K window is lower than the 8192 on the HF card, so long Chunks are truncated there. [inferred from the two pages]
- MTEB leaderboard itself could not be read (page is a JS app, no static scores). Numbers above are the model owners' own reported figures. [verified that the page is not scrapable] https://huggingface.co/spaces/mteb/leaderboard

Long chat text: bge-small caps at 512 tokens (about 350-400 words, [inferred]); a Chunk that keeps a question with its answer may exceed this and be silently truncated. nomic (8192) and bge-m3 (8192) avoid that but cost 4x+ the size and slower CPU encoding [inferred]. Cheaper alternative: keep Chunks under about 400 tokens. [inferred]

Matryoshka truncation lets nomic shrink stored vectors with small loss (62.28 to 61.04 at 256 dim). [verified] https://huggingface.co/nomic-ai/nomic-embed-text-v1.5

## (b) Re-ordering (cross-encoder rerank)

| Model | Size | Licence | Quality / speed |
|---|---|---|---|
| ms-marco-MiniLM-L-6-v2 (Xenova ONNX) | 0.08 GB | Apache-2.0 | NDCG@10 TREC DL19 74.30, MRR@10 39.01, 1800 docs/s on a V100 GPU |
| ms-marco-MiniLM-L-12-v2 | 0.12 GB | Apache-2.0 | 74.31 / 39.02, 960 docs/s (V100); almost no gain over L-6 |
| jina-reranker-v1-tiny-en / turbo-en | 0.13 / 0.15 GB | Apache-2.0 | no figures fetched |
| BAAI/bge-reranker-base | 1.04 GB (about 0.3B params) | MIT | reported on Chinese benchmarks only (avg 65.42 vs 66.09 for large) |
| jina-reranker-v2-base-multilingual | 1.11 GB | CC-BY-NC-4.0 (non-commercial) | - |

Claims:
- MiniLM-L6 figures and family table: [verified] https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 (V100 GPU speed; CPU speed will be much lower, [inferred]).
- The Xenova repo is an ONNX conversion of that cross-encoder; the card states no licence or size. [verified] https://huggingface.co/Xenova/ms-marco-MiniLM-L-6-v2 . Licence and 0.08 GB come from fastembed's table. [verified] https://qdrant.github.io/fastembed/examples/Supported_Models/
- bge-reranker-base: MIT, about 0.3B params, examples truncate at 512, intended to rerank the top-k from an embedder; its published numbers are Chinese-language, so they say little about English chat. [verified] https://huggingface.co/BAAI/bge-reranker-base
- jina-reranker-v2 is non-commercial: [verified] fastembed table above.

Long chat text: MS MARCO cross-encoders were trained on short passages; the card gives no max length (512 is typical for MiniLM, [inferred]). Rerank only the top 20-50 hits, cheap on CPU. [inferred] Raw scores are unbounded logits; the prototype's sigmoid is a sensible squashing but is not a calibrated Match Score. [inferred]

## (c) Summary / key-decisions generation

| Model | Params | Context | Licence | Reported quality |
|---|---|---|---|---|
| Qwen3-4B-Instruct-2507 | 4.0B | 262,144 native | Apache-2.0 | IFEval 83.4, MMLU-Redux 84.2 |
| Qwen3-1.7B | 1.7B | 32,768 | Apache-2.0 | thinking on by default; disable with `enable_thinking=False` |
| Phi-4-mini-instruct | 3.8B | 128K | MIT | MMLU 67.3; English-leaning, 23 languages |
| Llama-3.2-3B-Instruct | 3.21B | 128K (quantised variants 8K) | Llama 3.2 Community Licence (attribution, AUP, 700M MAU cap) | IFEval 77.4, TLDR9+ summarisation ROUGE-L 19.0 |

Claims:
- Qwen3-4B-Instruct-2507: [verified] https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 (page says Ollama, LM Studio, MLX-LM, llama.cpp support it).
- Qwen3-1.7B: [verified] https://huggingface.co/Qwen/Qwen3-1.7B
- Phi-4-mini: [verified] https://huggingface.co/microsoft/Phi-4-mini-instruct (card's hardware notes are GPU/Flash-Attention oriented; CPU use goes through GGUF runtimes, [inferred]).
- Llama 3.2 3B: [verified] https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
- RAM: a 4B model at 4-bit is roughly 2.5-3 GB of weights, so it fits 8 GB with a modest context; 16 GB is comfortable. [inferred, standard quantisation arithmetic, not from a fetched page]
- CPU speed: expect roughly single-digit to low-teens tokens/second for 3-4B at 4-bit on a typical laptop CPU. [inferred, unmeasured; benchmark on the target machine before promising anything]
- No head-to-head summarisation benchmark between these models was found in primary sources; IFEval is only a proxy for "follows a key-decisions format". [inferred]

Long chat text: the Context Pack input (top Chunks) is small, so even 8K context suffices. Ollama defaults to 4096 tokens, changeable via `OLLAMA_CONTEXT_LENGTH` or `num_ctx`; larger context raises memory use (KV cache), and Flash Attention with `OLLAMA_KV_CACHE_TYPE=q8_0` roughly halves it. [verified] https://raw.githubusercontent.com/ollama/ollama/main/docs/faq.mdx . Silent truncation at 4096 is a real risk when stuffing many Chunks. [inferred]

## How to run

- fastembed: Python, ONNX Runtime, embeddings and cross-encoder rerankers, no torch needed. Best fit for (a) and (b); already used by the prototype. [verified] https://qdrant.github.io/fastembed/
- sentence-transformers: needed for models outside fastembed's list (bge-m3, bge-reranker via `CrossEncoder`); pulls in PyTorch (large install). [verified usage] model cards above; install weight [inferred]
- Ollama: local HTTP server; one tool for both generation (Qwen3, Llama, Phi) and embeddings (`/api/embed`). Easiest packaging for end users. [verified] https://ollama.com/library/nomic-embed-text and the FAQ above
- llama.cpp: runs GGUF quantised models on CPU; Qwen3 card lists it as supported. Ollama is built on it, so use it directly only if embedding the runtime. [verified for Qwen3 support; "Ollama builds on llama.cpp" is inferred from memory, not fetched]

## Hosted option beside the local models

- OpenAI embeddings: text-embedding-3-small (1536 dim, 8192 tokens, MTEB 62.3%) and -3-large (3072 dim, 64.6%); `dimensions` parameter can shorten vectors. Price per 1M tokens not on that page; the page's figures imply about $0.02 and $0.13 [secondary, derived by the fetcher; check the pricing page]. https://developers.openai.com/api/docs/guides/embeddings
- Note: text-embedding-3-small's MTEB (62.3) is about equal to bge-small-en-v1.5 (62.17) and nomic v1.5 (62.28) on the owners' own numbers, so hosted embeddings buy little quality here. [inferred; different MTEB versions/subsets may not be strictly comparable]
- Anthropic: "does not offer its own embedding model"; recommends Voyage AI (voyage-4 family, 32,000-token context, rerank-3 reranker; also the open-weight Apache-2.0 `voyage-4-nano`, not served via the API). [verified] https://platform.claude.com/docs/en/build-with-claude/embeddings
- Summary generation hosted: OpenAI or Claude chat APIs take the same Chunk text; not researched further (no primary page fetched this run).
- Integration (inferred): define three narrow functions, `embed(texts, kind)`, `rerank(query, docs)`, `summarise(request, chunks)`; the Mode setting picks the local or hosted implementation. Vectors from different embedding models are not interchangeable, so switching Mode (or any embedding model) means re-embedding the whole Knowledge Base; store the model name with the index. Query/document prefixes differ per model (bge optional, nomic mandatory, Voyage `input_type`), so wrap them inside `embed`.

## Open points

- Real CPU latency and RAM on the target laptop are unmeasured; run the prototype's Test Set with each candidate to decide.
- bge-m3 size/MTEB and OpenAI per-token price not confirmed from primary pages.
- Test whether bge-small's 512-token cap truncates real Chunks before paying for a bigger embedder.
