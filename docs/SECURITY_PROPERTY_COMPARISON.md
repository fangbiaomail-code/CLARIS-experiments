# Security-property and construction comparison

This table is a literature-level comparison for Chapter VII. It is not a cryptographic proof and does not substitute for checking each paper's formal games. "Not stated" means the cited source does not establish the property in the scope used here; it must not be read as a proof that the property is impossible.

| Construction | PQ basis | Anonymous ring signing | Claim / later attribution | Link / association | Accountability / opening | What is actually comparable |
|---|---|---|---|---|---|---|
| Park–Sealfon, *It Wasn't Me!* (2019) | Not a PQ construction claim | Ring-signature setting | Studies repudiability and (un)claimability; the CLARIS manuscript's generic-claimability row uses a commitment tied to the ring signature and named key | Not the main feature | Claimability/repudiability semantics | Disclosure mechanism and what a later claim proves; no matched runtime data |
| Fiore et al., RS-UCL (2022) | Depends on the selected base ring signature; not a PQ claim of the cited construction | Yes | Not the primary feature | User-controlled linking; linking evidence can be produced at signing time or after signatures are output | No central group manager required by RS-UCL | Closest functional comparison for signer-authorized post-hoc association; different UCL/UCAL security profile and link secret |
| Chiang et al., VOLEitH threshold ring signatures (CCS 2025) | AES one-wayness + VOLE-in-the-Head; paper presents post-quantum constructions | Yes, threshold ring signatures | No CLARIS-style named-key Claim interface is established in the cited construction comparison | Key-binding deterministic tags provide linkability | Threshold aggregation and anonymous-ledger applications | Closest implementation/proof-system baseline; its tag-link rule is not the same as CLARIS's selected-report endpoint proofs |
| DualRing-PRF / DualRingL-PRF (ACISP 2024) | Symmetric Legendre and power-residue PRFs; paper presents post-quantum variants | Yes | Not the stated feature | Linkable ring-signature variant; linkability is used to detect repeated signing under the scheme's constraints | Non-slanderability is discussed in the construction | Useful PQ symmetric-primitive comparison; not the same selected, post-hoc report-association interface |
| SPRING (2026) | Module-lattice based | Yes | Not the concrete extension emphasized in the paper | Relation proofs are discussed as possible extensions, but the demonstrated extension is accountability | Concrete accountable ring signature with designated opener | Useful lattice-based ring-signature and accountability comparison; no matched implementation benchmark here |
| TalosLogic libtalos_voleith (design documentation) | VOLEitH / symmetric primitives | Yes | Claimable-commitment module documented | Linkable-nullifier module documented | Designated-opener module documented | Engineering reference only; documentation is not treated as an independent formal security theorem or matched benchmark |
| **CLARIS** | AES-256 + VOLEitH; **conditional** QPT claim under the joint proof and tuple assumptions in the manuscript | Yes; anonymity is claimed for challenge reports left undisclosed | Signer-authorized Claim names the registered key for one report | Signer-authorized selected-set association; an s-report anchor link uses s−1 ordinary proofs | Voluntary public claim; no designated opener | Claim proof size pG; anchor selected-set proof size (s−1)pG; proof relation and source assumptions differ from the schemes above |

## Security scope that must remain visible

1. CLARIS's anonymity game protects an uncorrupted challenge report only while that report is neither claimed nor linked. A link certificate containing no identity field is not, by itself, a proof of anonymity for linked records.
2. CLARIS's claim and link operations are signer-authorized. A public claim identifies the registered key; an identity-free link establishes a common registered owner under the stated key-binding assumptions.
3. CLARIS's main theorem is conditional. The manuscript explicitly leaves the concrete joint zero-knowledge simulator/extractor transfer, the compatible quantum oracle experiment, real-AES tuple preimage resistance, and candidate-key pseudorandomness as obligations/assumptions.
4. Linkability is not one uniform feature across these papers: deterministic nullifiers for repeated-use detection, user-controlled link proofs, designated opening, and CLARIS's selected post-hoc same-owner association have different semantics and security games.

## Performance-comparison status

- The pinned Chiang et al. implementation is the only external executable baseline currently integrated into this workspace.
- The 128-bit baseline observations are one sample per ring size and are descriptive only.
- The 256-bit baseline is complete (one sample per N); the full CLARIS N x s matrix was measured on 2026-11-04 on one build and one host (see `EXPERIMENT_STATUS.md`).
- No speed ranking against DualRing-PRF, SPRING, Park–Sealfon, Fiore et al., or TalosLogic is reported. Their concrete runtimes are not matched in hardware, security level, implementation, and operation scope.

## References

- Park and Sealfon, *It Wasn't Me! Repudiability and (Un)claimability of Ring Signatures*, CRYPTO 2019: https://www.iacr.org/archive/crypto2019/116940474/116940474.pdf
- Fiore et al., *Ring Signatures with User-Controlled Linkability*, ESORICS 2022: https://eprint.iacr.org/2022/1743
- Chiang et al., *Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head*, CCS 2025: https://eprint.iacr.org/2025/113
- Zhang et al., *DualRing-PRF: Post-Quantum (Linkable) Ring Signatures from Legendre and Power Residue PRFs*, ACISP 2024: https://eprint.iacr.org/2024/985
- Zhang, Luo, and Huang, *SPRING: Sign-then-prove ring signatures from lattices with compactness, extensibility, and efficiency*, Computer Standards & Interfaces 96 (2026): https://doi.org/10.1016/j.csi.2025.104084
- TalosLogic, libtalos_voleith design documentation: https://github.com/TalosLogic/libtalos_voleith/blob/master/docs/DESIGN.md
