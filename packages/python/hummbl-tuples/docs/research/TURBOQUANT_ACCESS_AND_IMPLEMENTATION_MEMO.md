# TurboQuant Access And Implementation Memo

Date: 2026-03-27
Status: draft

## Question

What is Google's TurboQuant, how do you access it, and what is the most practical path to implementation?

## Bottom Line

TurboQuant is real, but it is not a public Google Cloud feature or hosted API.

As of 2026-03-27, the practical way to access it is:

1. read the official Google Research blog and paper
2. treat it as a research algorithm, not a product
3. start from the official `QJL` repo plus third-party TurboQuant implementations or forks
4. benchmark it against adjacent KV-cache quantization baselines rather than assuming the blog claims will transfer directly to your stack

## Official Sources

- Google Research blog  
  https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
- TurboQuant paper  
  https://arxiv.org/abs/2504.19874
- ICLR 2026 OpenReview paper page  
  https://openreview.net/pdf?id=tO3ASKZlok

## What TurboQuant Actually Is

TurboQuant is a vector-quantization method aimed at:

- KV-cache compression for LLM inference
- vector compression for search and retrieval

The paper describes a two-stage design:

1. a high-quality compression stage based on random rotation and scalar quantization
2. a residual correction stage using a 1-bit Quantized Johnson-Lindenstrauss transform

The core research claim is near-optimal distortion with negligible overhead, plus practical gains for KV-cache compression and vector search.

From the paper:

- near-optimal distortion rate within a small constant factor
- quality neutrality reported around 3.5 bits per channel for KV-cache settings
- marginal degradation at 2.5 bits per channel

Sources:

- paper abstract and results  
  https://arxiv.org/abs/2504.19874
- Google blog overview  
  https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/

## What I Did Not Find

I did not find:

- a Google Cloud TurboQuant API
- a Vertex AI feature named TurboQuant
- an official Google-maintained TurboQuant repository

So the clean answer is:

- TurboQuant is currently a paper and blog-backed research method
- not an access-controlled Google product

## Best Open-Source Starting Points

### 1. Official Adjacent Repo: QJL

This is the strongest starting point because it comes from the same research line and is directly used in TurboQuant's residual-error stage.

- QJL repo  
  https://github.com/amirzandieh/QJL

Why it matters:

- official author repo
- includes CUDA kernel work
- directly relevant to KV-cache quantization
- provides a more trustworthy substrate than an unvetted full reimplementation

### 2. Third-Party TurboQuant Library

- Zig implementation  
  https://github.com/botirk38/turboquant

What it appears to provide:

- encode / decode / dot-product API
- SIMD-oriented implementation
- packaged library surface

Why to treat it carefully:

- third-party, not Google-maintained
- still early and lightly adopted

### 3. Third-Party llama.cpp Integration Work

- llama.cpp TurboQuant fork / branch  
  https://github.com/TheTom/llama-cpp-turboquant/tree/experiment/speed-optimization

Why it matters:

- closest path to real local-inference usage
- useful for understanding serving-level integration tradeoffs

Why to treat it carefully:

- experimental branch
- not a canonical upstream implementation

## Best Practical Access Path

### If You Want To Understand The Method

Start with:

1. Google blog
2. TurboQuant paper
3. QJL paper and repo
4. PolarQuant paper from the blog's linked references

### If You Want To Build With It

Start with:

1. `QJL`
2. compare against `KIVI`, `KVQuant`, and adjacent KV-cache methods
3. only then look at third-party TurboQuant ports

Useful adjacent baselines:

- KIVI  
  https://arxiv.org/abs/2402.02750
- KVQuant  
  https://github.com/SqueezeAILab/KVQuant

## Recommended Integration Strategy

If the target is your stack, the cleanest sequence is:

1. prototype a vector-only implementation
   - encode
   - approximate dot product
   - measure distortion
2. validate against paper-style vector-search settings
3. then test KV-cache compression in one inference runtime
   - MLX
   - llama.cpp
   - or a Hugging Face inference path
4. compare against QJL-only and other KV baselines

Do not start by assuming the full TurboQuant stack will drop cleanly into your inference runtime.

## Best Fit For You

Given your current research direction, TurboQuant is most relevant for:

- memory-aware reasoning systems
- long-context inference efficiency
- governed retrieval and vector search
- studying when compression changes trace or operator quality

It is less relevant as a first implementation target than your current reasoning-trace and bio-governance work, but it is a very good adjacent technical lane.

## Recommendation

If you want a real next step:

1. read the paper carefully
2. inspect QJL code first
3. choose one runtime target
4. build a narrow evaluation memo before implementing

For your environment, the most plausible targets are:

- local `llama.cpp`
- local `MLX`
- or a vector-search prototype

## Confidence

High on the access answer. Medium-high on the implementation path because the open-source landscape is still shifting quickly.
