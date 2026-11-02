# CLARIS Experimental Plan

## 1. Research questions

The evaluation should answer:

1. What are the proof-generation and verification costs of reports, claims, and selected links?
2. Does the ordinary eight-block disclosure proof keep its additional proof size independent of ring size?
3. How do costs scale with ring size N and selected-report count s?
4. What is the measured difference between Anchor and Bridge in a matched ablation?
5. How does CLARIS compare with relevant claimable-ring-signature and user-controlled-linking constructions when instantiated at a compatible security target?
6. What are the full evidence-transfer costs after including original reports, manifest, report references, application payload, and certificates?

## 2. Benchmark matrix

Primary ring sizes: N = 16, 64, 256, 1024.

Selected report counts: s = 2, 3, 5, 10, 20.

For each supported cell, target at least 30 measured repetitions after warm-up. Retain every raw sample. If a configuration is unsupported or exceeds a resource limit, record the reason rather than omitting it.

## 3. Operations to measure separately

- Key generation / enrollment.
- Report signing.
- Original ring-report verification.
- Claim generation.
- Claim verification (additional proof only and full verification).
- Link generation.
- Link verification (additional proof only and full verification).
- Anchor and Bridge variants under the same implementation and parameter set.
- Peak resident memory and proof/certificate byte length.

Report median, mean, standard deviation, and p95 for latency. Record peak memory in bytes or MiB and clearly identify the measurement method.

## 4. Existing manuscript results: do not mislabel

The manuscript reports an ordinary claim/link proof size of 49,208 bytes and a three-report link core proof size of 98,416 bytes. It reports functional checks at N = 64 and N = 1024.

The Anchor/Bridge timing table is a separate matched ablation of the earlier repeated-OR implementation. It uses three measured runs per cell after one warm-up, for N = 64 and 1024 and s = 2, 3, 5. Those timings must not be presented as ordinary-pair implementation latency.

The manuscript states that ordinary-pair latency and peak memory remain unmeasured. These are priority experiments.

## 5. External comparison strategy

Prioritize these construction families from the manuscript's related-work discussion:

- Park–Sealfon generic claimability transformation.
- Fiore et al. RS-UCL / RS-UCAL and AKRS compiler.
- Chiang et al. AES/VOLE threshold ring-signature construction.
- DualRing-PRF post-quantum ring signatures with public linkability.
- SPRING lattice ring signatures with designated opening / accountability.
- TalosLogic as an engineering reference where a reproducible implementation is available.

Do not put all schemes into one timing chart by default. First build a feature/security-model table. For concrete timing, implement matched baselines over a compatible underlying ring-signature implementation and equivalent security targets. Mark unavailable or non-equivalent operations as N/A, not zero.

## 6. Communication accounting

Report separately:

- Original report size.
- Claim proof and wrapper size.
- Single link-edge proof size.
- Multi-report link certificate size.
- Manifest size.
- Complete evidence package size.

The manuscript's proposed packed transfer profile gives analytical formulas:
- Link certificate: 44 + 32s + (s - 1)pG bytes.
- Claim certificate: 76 + pG bytes.
- pG = 49,208 bytes in the reported prototype.

These are encoding-based calculations, not measured network traffic. Keep this distinction in every table and figure.

## 7. Environment metadata

Every result file must identify:
- Git commit SHA and dirty/clean status.
- CPU model and core configuration.
- RAM.
- OS and kernel.
- Compiler and version.
- Build type and flags (the manuscript's described build enables -O2, AVX2, AES, and PCLMUL).
- Dependency revisions.
- Parameter set and random seed policy.
- Warm-up count and measured repetition count.

## 8. Acceptance criteria for a publishable comparison

- Raw samples are committed or archived with checksums.
- Tables are generated from raw data, not manually transcribed.
- Figures state units and repetition counts.
- Every external baseline has a citation, implementation source, pinned revision, and parameter mapping.
- Security/functionality comparisons distinguish native functionality from functionality added by a compiler.
- No performance-superiority claim is made from incomparable implementations or security levels.
