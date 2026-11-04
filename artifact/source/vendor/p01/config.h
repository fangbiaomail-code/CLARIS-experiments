#ifndef CONFIG_H
#define CONFIG_H

#define ALLOW_ZERO_SBOX

#define SECURITY_PARAM 256
#define OWF_AES_CTR
#define PRG_AES_CTR
#define TREE_PRG_AES_CTR
#define LEAF_PRG_SHAKE
#define BITS_PER_WITNESS 22
#define ZERO_BITS_IN_CHALLENGE_3 6

#if 245 == -1
#define USE_IMPROVED_VECTOR_COMMITMENTS 0
#define BATCH_VECTOR_OPENING_SEEDS_TRESHOLD SECURITY_PARAM
#else
#define USE_IMPROVED_VECTOR_COMMITMENTS 1
#define BATCH_VECTOR_OPENING_SEEDS_TRESHOLD 245
#endif

// SHA3 is currently the only option.
#define RANDOM_ORACLE_SHA3

// XKCP configuration.
#define XKCP_has_KeccakP1600
#define XKCP_has_KeccakP1600times2
#define XKCP_has_KeccakP1600times4
#define XKCP_has_KeccakP1600times8

// JC: Ring sig configuration (User-defined).
#define FAEST_RING_2_POW (6) // Supported: 2 to 20.
#define FAEST_RING_HOTVECTOR_DIM (2) // Supported: 1, 2, 4. Must divde RING_2_POW.
#define FAEST_RING_SIZE (1 << FAEST_RING_2_POW)
#define FAEST_RING_HOTVECTOR_BITS ((1 << (FAEST_RING_2_POW / FAEST_RING_HOTVECTOR_DIM))-1)
#define FAEST_RING_HOTVECTOR_BYTES ((FAEST_RING_HOTVECTOR_BITS * FAEST_RING_HOTVECTOR_DIM + 7) / 8)


#endif
