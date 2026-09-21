# Day 3 — RAG & Knowledge-Based Agents · Notes

> How agents access enterprise knowledge that is not in the LLM's training.

---

## 1. Why RAG?

LLMs have three structural limitations on enterprise knowledge:

1. **Knowledge cutoff** — the model doesn't know anything published after
   its training date.
2. **No private data** — the model never saw your internal docs.
3. **No real-time data** — the model cannot fetch a number that changed
   five minutes ago.

RAG solves all three by retrieving external documents at inference time
and grounding the answer on them.

```text
User: "What is our latest travel policy?"
LLM alone: ❌ "I don't have access to your company's policies."
LLM + RAG: ✅ "Per travel-policy.pdf v2.3, employees are reimbursed up to $150/night..."
```

---

## 2. RAG Architecture

### Offline (ingestion)

```text
Documents
 ↓
Parsing
 ↓
Chunking
 ↓
Embeddings (vector per chunk)
 ↓
Vector Database (chunks + vectors + metadata)
```

### Online (retrieval)

```text
User Question
 ↓
Embedding (same model)
 ↓
Vector Search (top-k nearest)
 ↓
Relevant Chunks + Metadata
 ↓
Prompt = System + Chunks + Question
 ↓
LLM
 ↓
Grounded Answer
```

---

## 3. Document Ingestion

Inputs we routinely see in enterprise RAG:

- PDFs (contracts, policies, manuals)
- Word / Google Docs (internal writeups)
- HTML / wikis (Confluence, Notion)
- Markdown (READMEs, design docs)
- CSV / Excel (catalogs, FAQs)
- Web pages (external docs, FAQs)

**Per-format gotchas:**

| Format | Gotcha |
|--------|--------|
| PDF | Two-column layout, headers/footers, scanned (OCR needed), tables |
| DOCX | Embedded images, comments, tracked changes |
| HTML | Navigation chrome, ads, scripts |
| CSV | Schema drift, mixed types, encoding |
| Markdown | Embedded code blocks, image refs |

Use a parser per format. Don't try to write a universal one.

---

## 4. Chunking

Chunking is the most underrated lever in RAG. Bad chunks → bad retrieval →
hallucinated answers.

### Strategies

| Strategy | When to use |
|----------|-------------|
| **Fixed-size** | Quickstart. Uniform. Loses semantic boundaries. |
| **Recursive** | Splits on paragraphs → sentences → words. Better than fixed. |
| **Semantic** | Splits when embedding similarity drops. Best quality, slower. |
| **Heading-based** | Markdown, legal docs with clear sections. |
| **Document-aware** | Per-format parser (e.g. `unstructured` library). |

### Parameters

- **Chunk size** — typically 200–800 tokens. Smaller = more precise, more chunks.
- **Overlap** — typically 10–20% of chunk size. Prevents losing context at boundaries.
- **Metadata** — always store: source file, section, version, ingestion date,
  access-control tags.

### Failure mode: too-small chunks

If chunks are too small, the embedding loses context ("25 vacation days"
without "full-time employees per year" → wrong retrieval). Add overlapping
context windows or store parent-document context.

---

## 5. Embeddings

```text
"VPN password reset"
        ↓
Embedding Model (e.g. text-embedding-3-small)
        ↓
[0.12, -0.44, 0.81, ...]   (1536 dimensions)
```

Similar meaning → similar vector. Cosine similarity measures "how close
in meaning" two texts are.

### Properties to know

- **Same model for indexing and querying.** Mismatched models = random retrieval.
- **Multilingual models** exist; pick one if your corpus mixes languages.
- **Dimension size** matters: larger = more expressive, more storage.
- **Cost** is per million tokens embedded. Cache embeddings; never re-embed
  the same text twice.

---

## 6. Vector Databases

| Database | Notes |
|----------|-------|
| **Astra DB** | Managed, multi-cloud |
| **PostgreSQL + pgvector** | Reuses existing Postgres ops |
| **OpenSearch** | Hybrid search built in |
| **Pinecone** | Managed, fast |
| **Weaviate** | Open source, hybrid search |
| **Milvus** | Open source, scales to billions |
| **Qdrant** | Open source, fast |
| **Chroma** | Best for prototyping and notebooks |

Each stores:

```text
Vector (embedding)
+
Text (the chunk)
+
Metadata (source, version, ACL, ...)
```

Metadata filters are critical for enterprise security (see §8).

---

## 7. Retrieval

### Similarity search

For a query vector `q`, return the `k` chunks with the highest cosine
similarity to `q`.

### Hybrid search

Combine dense (embedding) similarity with sparse (BM25 keyword) similarity.
Best for queries that mix concepts ("VPN") with rare terms ("INC-12345").

### Reranking

After retrieving top-k (e.g. k=50), apply a cross-encoder reranker to
produce the final top-n (e.g. n=5). Cross-encoders are slower but more
accurate. Common models: Cohere Rerank, bge-reranker.

### Common failure modes

| Failure | Symptom | Fix |
|---------|---------|-----|
| Query too short | Wrong chunks retrieved | Query expansion (LLM rephrases) |
| Query too long | Embedding diluted | LLM-generated hypothetical answer (HyDE) |
| Vocabulary mismatch | "VPN" query, chunk says "virtual private network" | Better embeddings, query expansion |
| No metadata filter | Wrong-version doc returned | Filter on `version` |
| Wrong ACL | User sees restricted content | Filter on `user_clearance` |

---

## 8. Metadata Filtering (Enterprise RAG)

```json
{
  "department": "HR",
  "region": "US",
  "classification": "internal",
  "version": "3.2",
  "ingested_at": "2025-01-15"
}
```

The retrieval must respect authorization:

```text
User Permissions
 ↓
Metadata Filter
 ↓
Vector Search (filtered)
 ↓
Relevant Documents
```

**This is non-negotiable in enterprise RAG.** A user without HR clearance
must never see HR-restricted chunks, even if they are the most similar.

### Implementation

- Tag every chunk at ingestion with its access tags.
- At retrieval, intersect the user's permissions with the chunk's tags.
- Use a metadata filter on the vector query — don't filter in post.

---

## 9. RAG vs Fine-Tuning

| Concern | RAG | Fine-Tuning |
|---------|-----|-------------|
| **What it changes** | Runtime knowledge | Model behavior / style |
| **Best for** | Frequently changing info | Stable task adaptation |
| **Returns citations** | Yes (source documents) | No (intrinsic to weights) |
| **Update cost** | Re-ingest chunks | Retrain ($) |
| **Latency** | Higher (retrieval step) | Lower (no retrieval) |
| **Hallucination risk** | Lower (grounded) | Higher (no grounding) |

**Rule:** if the answer changes because a doc was updated, use RAG. If the
*behavior* needs to change (always respond in JSON, always use a specific
style), fine-tune.

The two are complementary. Many production systems do both.

---

## 10. RAG + Agents

The agent decides when retrieval is needed. RAG is just another tool:

```text
User
 ↓
Agent
 ↓
LLM
 ↓
"Should I retrieve?"
 ├── No → answer from conversation history
 └── Yes → Knowledge Tool → RAG → Vector DB → Documents → LLM → Response
```

This is why **RAG fits inside the agent loop**: the LLM treats it as a tool
and decides on its own whether to call it.

### When to retrieve vs not

- ✅ User asks about a specific policy, ticket, or product → retrieve.
- ❌ User says "Hi" or "Thanks" → don't retrieve.
- ✅ User references a doc ("per the handbook...") → retrieve.
- ❌ User asks a general knowledge question → use the LLM's training data.

The LLM's tool-calling decision is the answer to "when." You don't need
a separate classifier.

---

## 11. Evaluation

What to measure:

| Metric | How |
|--------|-----|
| **Retrieval relevance** | Top-k chunks contain the answer? (human-labeled) |
| **Answer correctness** | Answer matches a reference? (LLM-as-judge) |
| **Groundedness** | Answer claims are supported by chunks? (LLM-as-judge) |
| **Citation accuracy** | Citations point to chunks that contain the cited claim? |
| **Retrieval latency** | p50/p95/p99 of retrieval step |
| **Token usage** | Total tokens per query (prompt + completion) |

---

## Project: Enterprise Policy Agent

```text
User
 ↓
Policy Agent
 ↓
Knowledge Tool
 ↓
RAG
 ↓
Vector DB
 ↓
Relevant Documents
 ↓
LLM
 ↓
Grounded Answer (with citations)
```

Hands-on builds: chunker → embedder → vector store → retriever → agent
tool. Then queries the system and inspects citations.

---

## Bridge to Day 4

Today we built RAG with raw OpenAI + Chroma. Tomorrow we layer
**frameworks** on top: LangChain (composable primitives), LangGraph
(stateful workflows), CrewAI (role-based agents), MCP (standard tool
protocol). The RAG pipeline becomes a node in a LangGraph workflow.
