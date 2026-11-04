/* Experimental ordinary eight-block AES/VOLE pair relation. No OR branch.
 * Request = 128 input bytes | 128 expected output bytes | 32 context bytes.
 * Prover additionally reads a temporary 32-byte witness key, never logs it.
 * Including faest.c permits fresh false-relation tests with the full expected
 * statement in the transcript. All other crypto objects are ordinary P01.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "randomness.h"
#include "faest.c"
static void exact_read(const char*p,void*b,size_t n){FILE*f=fopen(p,"rb");if(!f||fread(b,1,n,f)!=n||fgetc(f)!=EOF)exit(20);fclose(f);}
static void exact_save(const char*p,const void*b,size_t n){FILE*f=fopen(p,"wb");if(!f||fwrite(b,1,n,f)!=n)exit(21);fclose(f);}
int main(int argc,char**argv){
 if(SECURITY_PARAM!=256||OWF_BLOCKS!=8||FAEST_PUBLIC_KEY_BYTES!=256)return 22;
 if(argc==2&&!strcmp(argv[1],"info")){printf("{\"blocks\":8,\"public_key_bytes\":256,\"proof_bytes\":%u,\"witness_bits\":%u,\"constraints\":%u,\"ring_or_used\":false}\n",FAEST_SIGNATURE_BYTES,WITNESS_BITS,OWF_NUM_CONSTRAINTS);return 0;}
 if(argc<4)return 23;
 uint8_t req[288];exact_read(argv[2],req,sizeof(req));
 uint8_t*proof=aligned_alloc(32,(FAEST_SIGNATURE_BYTES+31)&~(size_t)31);if(!proof)return 24;
 if(!strcmp(argv[1],"verify")){exact_read(argv[3],proof,FAEST_SIGNATURE_BYTES);int ok=faest_verify(proof,req+256,32,req);printf("PAIR_VERIFY %s\n",ok?"PASS":"REJECT");free(proof);return ok?0:2;}
 if(argc!=5||strcmp(argv[1],"prove"))return 25;
 uint8_t key[32],skpacked[FAEST_SECRET_KEY_BYTES],seed[64];exact_read(argv[4],key,32);memcpy(skpacked,req,128);memcpy(skpacked+128,key,32);
 secret_key*sk=aligned_alloc(32,(sizeof(secret_key)+31)&~(size_t)31);if(!sk)return 26;memset(sk,0,sizeof(*sk));
 if(!faest_unpack_secret_key(sk,skpacked,false))return 27;
 /* Retain the actual-key witness, but bind every expected output even when
  * it is false. A hostile proof must fail the relation, not a stale prehash. */
 memcpy(sk->pk.owf_output,req+128,128);
 if(rand_bytes(seed,64))return 28;
 uint64_t attempt=0;while(!faest_sign_attempt(proof,req+256,32,sk,req,seed,64,attempt++)){if(attempt>100000)return 29;}
 exact_save(argv[3],proof,FAEST_SIGNATURE_BYTES);memset(key,0,sizeof(key));memset(skpacked,0,sizeof(skpacked));memset(sk,0,sizeof(*sk));free(sk);free(proof);return 0;
}
