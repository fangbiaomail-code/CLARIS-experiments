/* Chapter VII primitive microbenchmarks: 50 measured samples per row after 3 warm-ups.
 * Harness-only file; the cryptographic backend is the unmodified vendor code.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "config.h"
#include "randomness.h"
#include "aes.h"
#include "hash.h"
#include "small_vole.h"

#define SAMPLES 50
#define WARMUPS 3

static double ms_now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000.0+t.tv_nsec/1e6;}
static void *a32(size_t n){void*p=aligned_alloc(32,(n+31)&~(size_t)31);if(!p)exit(2);memset(p,0,n);return p;}
static volatile uint8_t sink;

static double aes_keygen_one(size_t reps){
    block_secpar key=block_secpar_set_all_8(0x42);rijndael_round_keys rk;
    double t=ms_now();
    for(size_t i=0;i<reps;i++){rijndael_keygen(&rk,key);sink^=((uint8_t*)&rk)[i%sizeof(rk)];}
    return (ms_now()-t)*1000.0/reps;
}
static double aes_ctr_one(size_t reps){
    block_secpar key=block_secpar_set_all_8(0x42);block256 in=block256_set_all_8(0x11),out;rijndael_round_keys rk;
    rijndael_keygen(&rk,key);
    double t=ms_now();
    for(size_t i=0;i<reps;i++){rijndael_fixed_key_ctr(&rk,&in,1,1,(uint32_t)i,&out);sink^=((uint8_t*)&out)[0];}
    return (ms_now()-t)*1000.0/reps;
}
static double hash_one(size_t reps){
    uint8_t msg[64],out[32];memset(msg,0x5a,sizeof(msg));
    double t=ms_now();
    for(size_t i=0;i<reps;i++){hash_state h;hash_init(&h);hash_update(&h,msg,sizeof(msg));hash_final(&h,out,sizeof(out));sink^=out[0];}
    return (ms_now()-t)*1000.0/reps;
}
static double rand_one(size_t reps){
    uint8_t out[64];
    double t=ms_now();
    for(size_t i=0;i<reps;i++){if(rand_bytes(out,sizeof(out)))exit(3);sink^=out[i%sizeof(out)];}
    return (ms_now()-t)*1000.0/reps;
}
static double vole_one(size_t reps,int receiver){
    size_t nk=(size_t)1<<VOLE_MAX_K;block_secpar*keys=a32(nk*sizeof(*keys));vole_block*u=a32(VOLE_COL_BLOCKS*sizeof(*u));
    vole_block*v=a32(nk*VOLE_COL_BLOCKS*sizeof(*v));vole_block*c=a32(VOLE_COL_BLOCKS*sizeof(*c));uint8_t*delta=a32(VOLE_MAX_K);
    for(size_t i=0;i<nk;i++)keys[i]=block_secpar_set_all_8((uint8_t)i);
    for(size_t i=0;i<VOLE_MAX_K;i++)delta[i]=0xff;
    block128 iv=block128_set_all_8(0x22);
    double t=ms_now();
    for(size_t i=0;i<reps;i++){if(receiver)vole_receiver(VOLE_MAX_K,keys,iv,NULL,c,v,delta,VOLE_COL_BLOCKS);else vole_sender(VOLE_MAX_K,keys,iv,NULL,u,v,c,VOLE_COL_BLOCKS);sink^=((uint8_t*)v)[i%sizeof(*v)];}
    double x=(ms_now()-t)*1000.0/reps;
    free(keys);free(u);free(v);free(c);free(delta);return x;
}
static double vole_sender_one(size_t n){return vole_one(n,0);}
static double vole_receiver_one(size_t n){return vole_one(n,1);}

static void row(const char*name,const char*scope,double(*f)(size_t),size_t reps,int last,int volectx){
    double a[SAMPLES];
    for(int i=0;i<WARMUPS;i++)f(reps);
    for(int i=0;i<SAMPLES;i++)a[i]=f(reps);
    printf("{\"operation\":\"%s\",\"scope\":\"%s\",\"unit\":\"us\",\"repetitions\":%d,\"warmups\":%d,\"inner_repetitions\":%zu",
           name,scope,SAMPLES,WARMUPS,reps);
    if(volectx)printf(",\"vole_max_k\":%d,\"vole_col_blocks\":%d",VOLE_MAX_K,VOLE_COL_BLOCKS);
    printf(",\"samples\":[");
    for(int i=0;i<SAMPLES;i++)printf("%s%.9f",i?",":"",a[i]);
    printf("]}%s",last?"":",\n");
}
int main(void){
    printf("{\"schema\":\"claris-basic-operations-v2\",\"security_parameter\":%d,\"ring_independent\":true,\"rows\":[\n",SECURITY_PARAM);
    row("AES-256 key schedule","one 256-bit key schedule",aes_keygen_one,1000,0,0);
    row("AES-256 CTR block","one 128-bit block, fixed key",aes_ctr_one,1000,0,0);
    row("SHAKE256 hash","64-byte input, 32-byte output",hash_one,1000,0,0);
    row("rand_bytes 64","64 random bytes from the platform RNG",rand_one,1000,0,0);
    row("VOLE sender","vendor small-VOLE sender, one protocol call",vole_sender_one,5,0,1);
    row("VOLE receiver","vendor small-VOLE receiver, one protocol call",vole_receiver_one,5,1,1);
    printf("]}\n");return 0;
}
