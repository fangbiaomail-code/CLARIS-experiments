# CLARIS source artifact

This offline source package accompanies **CLARIS: Claimable and selectively linkable ring signatures from VOLE-in-the-head**. The default profile is **CLARIS-Q-v2-G-v1**: Q uses the revised OR batching, while the ordinary eight-block G backend remains identical to v1. It builds both proofs from C/assembly source. No existing object files, executables, signing keys, or generated proofs are shipped.

## Requirements

- Python 3.8 or newer, standard library only.
- A C11 compiler. Apple Clang is tested on macOS; the build driver also selects Linux x86_64 flags, but Linux is not validated in this artifact's local validation record.
- x86_64 execution with AVX2, AES-NI and PCLMUL. Apple Silicon requires an already installed Rosetta environment. A native ARM backend is not included.
- No Git checkout, package download, Python package, or network connection is needed to build and run the included checks.

## Build and smoke check

Run from this directory; choose a new, empty build directory outside the package:

```sh
python3 verify_sources.py
python3 build.py --output /tmp/claris-build --ring-sizes 64 1024
python3 smoke.py --build /tmp/claris-build --ring-size 64 --result /tmp/claris-smoke64.json
python3 smoke.py --build /tmp/claris-build --ring-size 1024 --result /tmp/claris-smoke1024.json
python3 checks/check_sbox.py
python3 checks/check_namespaces.py --build /tmp/claris-build --result /tmp/claris-namespaces.json
python3 checks/check_batching_algebra.py
python3 checks/check_opening_bound.py
python3 checks/check_selector_transcripts.py --build /tmp/claris-build --result /tmp/claris-selector-transcripts.json
```

The build records exact compiler commands, source hashes, executable hashes, and parameter metadata in `build_manifest.json`. It refuses a nonempty destination so stale objects cannot be reused. Source integrity hashes are in `provenance/source_inventory.json`.

The smoke check generates new registry keys and reports, checks a valid claim and selected link, attempts altered identities, reports, selection orders and mixed-owner certificates, then launches independent verifiers using public material. Its temporary witness files have mode 0600 and are removed after each proving operation and on driver cleanup. The temporary output directory is deleted at completion. These checks establish functional behavior for the sampled cases; they do not establish cryptographic security.

The selector transcript check uses an intentionally duplicated low-level ring so every AES branch is true, then changes one or both selector dimensions from one-hot to three-hot. This isolates the selector checks in actual Q transcripts. The strict application registry rejects such duplicated rings; this diagnostic is not an end-to-end application forgery test. An optional `--legacy-build /path/to/pre-or-batch-build` checks the archived N=64 profile for comparison.

## Main implementation benchmark

The build additionally produces `ordinary/ordinary_worker` and `ring_n64/ordinary_benchmark` (and N=1024). From a new result directory, run:

For an automated sequential run with raw samples, descriptive statistics and public verification:

```sh
python3 benchmark.py --build /tmp/claris-build --output /tmp/claris-results --repeats 30 --warmups 3 --ring-sizes 64 1024
```

The equivalent single-configuration manual invocation is:

```sh
mkdir /tmp/claris-results64
cd /tmp/claris-results64
/tmp/claris-build/ring_n64/ordinary_benchmark /tmp/claris-build/ordinary/ordinary_worker 30 3
/tmp/claris-build/ring_n64/ordinary_benchmark /tmp/claris-build/ordinary/ordinary_worker verify
```

The last two numeric arguments are measured repetitions and discarded warmups. For a short pilot, use `1 1`. Repeat in another result directory with `ring_n1024` for the larger ring. Do not run both configurations concurrently when collecting latency evidence. The runner summarizes median, mean, range, sample standard deviation, quartiles and the interpolated 95th percentile; these are descriptive statistics for this host and workload.

`reports.json` contains the original report generation/verification samples. `claim_s1.json`, `anchor_s{2,3,5}.json`, and `bridge_s{2,3,5}.json` contain ordinary proof generation/verification samples. The matching `*.originals.json` files record original-report validation separately. The worker receives the witness through a pipe and times in-memory witness expansion, randomness, proving/retries, and verification; process launch, file I/O, and public request preparation are excluded. Report timers include their wrapper work. Timings from these different scopes must be labeled separately.

All methods use the same generated reports and ordinary eight-block backend. Anchor needs s-1 proofs; the hash-constrained bridge needs s proofs, plus its public bridge data. This is a controlled comparison of two constructions within this artifact, not a measured comparison against an external published implementation. The benchmark stores experiment-native public structures to enable a separate verification process. They are ABI-dependent fixtures, not a portable network serialization. Core proof bytes can be compared directly; full communication claims must separately specify framing, identifiers and tuple encoding.

## Source origin and changes

`vendor/p01/` contains a flattened source subset from:

- P01: <https://github.com/jachiang/PQ-Threshold-Ring-Sigs-from-VOLEitH>, commit `fa540fa152303a23b55a0a63efe20977076a6e15`.
- XKCP: <https://github.com/XKCP/XKCP>, commit `64404beeeb261b08a1076fe2f076e4e28dd9b040`.

These pins come from the original acquisition manifest. `provenance/upstream.json` maps each shipped file to its upstream relative path and hash; the generated configuration is identified separately. The archive is self-contained, so a build does not depend on those repositories remaining available.

Changes are applied to fresh build copies:

1. Replace one byte-buffer `aligned_alloc(1, ...)` with `malloc(...)`, for Darwin compatibility (`patches/01-byte-alignment.diff`).
2. For the ordinary proof only, use eight AES blocks and a 256-byte public statement (`patches/02-ordinary-eight-blocks.diff`). The AES constraint algorithm is retained.
3. For Q only, apply `patches/patch_ring_batching_v2.py`: use independent branch and outer batching keys, include each selector equation separately in the outer batch, and encode distinct selector labels. The stage-4 challenge expands from 104 to 208 bytes. Proof/witness layouts are unchanged. Each Q build records `ring_batching_v2.json`.
4. Apply `patches/patch_transcript_domains.py`: bind a CLARIS version string, proof kind Q/G, parameter digest and stage identifier to backend proof hashes, including the scalar/vectorized grinding paths. The Q namespace is v2 and its digest covers the revised constraint source; G keeps exactly its v1 namespace. Public report/context hash interfaces remain unchanged. Each build records `transcript_namespace.json`.
5. Select a ring of 64 or 1024 entries through the generated configuration.

The default Q-v2 namespace changes report transcript values. Regenerate reports and dependent report IDs, contexts and certificates for v2 measurements. Proof lengths are unchanged. To reproduce the archived Q-v1/G-v1 build, use a separate empty directory and `--pre-or-batch-fix`; for the earlier pre-namespace prototype use `--legacy-transcripts`. These two options are mutually exclusive. Do not combine results or certificates from different profiles without labeling them. Earlier validation records remain in the separately preserved pre-revision archive and are excluded from this final source release.

The namespace patch makes the proof-family separation explicit. The batching regression checks exact algebraic identities and selector cases. The analytical security derivations are separate from these executed functional tests; see the proof-note guide below. The pre-revision identities are not an exhibited end-to-end AES forgery.

The experiment wrappers are in `experiments/`. `experiments/validate.c` is retained as a dependency of the joint test and contains the early repeated-OR bridge experiment; that early bridge is not the benchmark baseline. The current comparator in `experiments/benchmark/ordinary_benchmark.c` derives bridge inputs from the entire ordered selected set and a seed, and verifies that derivation.

## Security derivations and recorded results

The current analytical notes under `provenance/` describe the concrete Q-v2/G-v1 classical-ROM argument:

- `ring_batching_v2_proof.txt`: independent inner/outer batching, individual selector equations, and the algebraic error bounds. Its earlier audit-status paragraphs are superseded by the subsequent extraction and simulation notes.
- `commitment_vole_extraction.txt` and `extraction_fragment.tex`: compressed commitment extraction, checked-VOLE normalization, transcript chronology, and extraction after stage-5-only programming.
- `public_simulation.txt` and `simulation_fragment.tex`: the public simulator, the 34-byte check pad and three-mask distribution, shared-root punctured-stream PRG hybrids, fresh-chain bounds, and consistent joint oracle handling.
- `linked_privacy.txt`: the protected-pool identity-hiding game and reduction for adaptive overlapping selected links. The honest disclosure service refuses claims and outside-pool links involving protected reports; adversarial public computation remains available.
- `opening_bound_exact.json` and `checks/check_opening_bound.py`: exact subtree counting and the finite grinding bound. The host execution completed successfully with the recorded numerator and denominator.

These arguments state their random-oracle, AES-CTR PRG and outer tuple/PRF assumptions explicitly. They cover the randomized 64-byte-seed wrappers and atomic classical proof-service calls. They do not establish a QROM theorem or a full quantum simulation/extraction proof. The simulator is specified and analysed in the notes; this artifact does not claim that simulator code was implemented or executed. No concrete PRG advantage of 2^-256 follows from the AES key length alone.

`benchmark_summary_v2.json` and `benchmark_validation_v2.json` record the completed formal measurements: N=64 and N=1024, 30 measured repetitions and three discarded warmups per cell, with two fresh public-verification processes. This source archive includes summary metadata only. Raw samples, public reports, selections, requests, proofs and verifier logs are in the separately hashed `CLARIS_benchmark_evidence_v2_final_2026-10-02.zip`. That evidence archive contains no signing keys or executable build outputs. Its `claimant.bin` is a four-byte public claimant index.

## Licenses and release inventory

The P01 source carries the FAEST Team MIT license, retained in `LICENSE` and `licenses/P01-MIT.txt`. The local derivative experiment/build code is provided under those MIT terms. XKCP files retain their original headers, and `licenses/XKCP.txt` includes the relevant public-domain, Brian Gladman and CRYPTOGAMS notices. No upstream copyright notices were removed.

Only source, scripts, documentation, licenses and JSON validation summaries belong in this package. Put generated build products and public test fixtures outside it. `provenance/local_validation.json`, when present, records the checks actually performed and the tested host; it must not be interpreted as validation on untested platforms.

To create a deterministic archive containing only the inventoried source materials:

```sh
python3 package.py --output /tmp/CLARIS-source.zip
```
