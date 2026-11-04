# CLARIS benchmark-matrix extension

This working-copy note describes the planned matrix extension to execute N={16,64,256,1024} and s={2,3,5,10,20}. It is not a substitute for the actual source diff or raw run artifacts.

Planned harness changes:
1. Permit ring sizes 16 and 256 in build, smoke, and benchmark entry points.
2. Increase the benchmark fixture report pool to 22 so up to 20 distinct reports can be selected.
3. Allow ordinary workers to prove and verify batches up to 20.
4. Add Anchor and Bridge output cells for s=10 and s=20.

The cryptographic relations and vendored implementation are intended to remain unchanged. The benchmark scope remains in-memory proof generation/verification and original-report validation; it does not produce a single end-to-end full-verification timer or portable network serialization.

Important status: the matrix-extension source tree and complete raw per-sample outputs are not currently included in this GitHub upload. Do not treat this note as evidence that the full N-by-s matrix has completed.
