/* In-memory ordinary-proof timing worker. Witness arrives only on stdin.
 * Public requests: u32 count followed by count*(128 inputs|128 outputs|32 ctx).
 * Files contain public statements, proofs, or timing records, never keys.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/resource.h>
#include "randomness.h"
#include "faest.c"
static double millis(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000.0+t.tv_nsec/1e6;}
static void*alloc32(size_t n){void*p=aligned_alloc(32,(n+31)&~(size_t)31);if(!p)exit(40);memset(p,0,n);return p;}
static void wipe(void*p,size_t n){volatile unsigned char*q=p;while(n--)*q++=0;}
static void readn(FILE*f,void*p,size_t n){if(!f||fread(p,1,n,f)!=n)exit(41);}
static void save_proofs(const char*name,const uint8_t*p,size_t n){FILE*f=fopen(name,"wb");if(!f||fwrite(p,1,n,f)!=n||fclose(f))exit(42);}
static int verify_batch(const uint8_t*requests,const uint8_t*proofs,uint32_t n){for(uint32_t i=0;i<n;++i)if(!faest_verify(proofs+i*FAEST_SIGNATURE_BYTES,requests+i*288+256,32,requests+i*288))return 0;return 1;}
static void prove_batch(const uint8_t*requests,uint8_t*proofs,uint32_t n,const uint8_t key[32],secret_key*sk,uint64_t*attempts){
 for(uint32_t i=0;i<n;++i){const uint8_t*r=requests+i*288;uint8_t packed[FAEST_SECRET_KEY_BYTES],seed[64];memcpy(packed,r,128);memcpy(packed+128,key,32);
  if(!faest_unpack_secret_key(sk,packed,false))exit(43);
  /* No expected-output overwrite here: this benchmark requires true statements. */
  if(memcmp(sk->pk.owf_output,r+128,128))exit(44);
  if(rand_bytes(seed,sizeof(seed)))exit(45);uint64_t a=0;
  while(!faest_sign_attempt(proofs+i*FAEST_SIGNATURE_BYTES,r+256,32,sk,r,seed,sizeof(seed),a++)){if(a>100000)exit(46);}*attempts+=a;wipe(seed,sizeof(seed));wipe(packed,sizeof(packed));
 }
}
int main(int argc,char**argv){
 if(argc<4||OWF_BLOCKS!=8||SECURITY_PARAM!=256||FAEST_PUBLIC_KEY_BYTES!=256)return 47;
 FILE*f=fopen(argv[2],"rb");uint32_t n;readn(f,&n,4);if(n<1||n>31)return 48;uint8_t*requests=alloc32(288*n);readn(f,requests,288*n);if(fgetc(f)!=EOF)return 49;fclose(f);
 uint8_t*proofs=alloc32(n*FAEST_SIGNATURE_BYTES);
 if(!strcmp(argv[1],"verify")){f=fopen(argv[3],"rb");readn(f,proofs,n*FAEST_SIGNATURE_BYTES);if(fgetc(f)!=EOF)return 50;fclose(f);int ok=verify_batch(requests,proofs,n);free(requests);free(proofs);puts(ok?"PUBLIC_BATCH_PASS":"PUBLIC_BATCH_REJECT");return ok?0:2;}
 if(argc!=7||strcmp(argv[1],"bench"))return 51;int reps=atoi(argv[5]),warm=atoi(argv[6]);if(reps<1||reps>10000||warm<0||warm>100)return 52;
 uint8_t key[32];readn(stdin,key,32);if(fgetc(stdin)!=EOF)return 53;secret_key*sk=alloc32(sizeof(*sk));f=fopen(argv[4],"w");if(!f)return 54;
 fprintf(f,"{\"proof_count\":%u,\"proof_bytes\":%u,\"repeats\":%d,\"warmups\":%d,\"timing_scope\":\"in-memory AES witness expansion, random seed, prove/retry and verify; excludes IPC, file I/O and request preparation\",\"samples\":[",n,n*FAEST_SIGNATURE_BYTES,reps,warm);
 for(int j=-warm;j<reps;++j){uint64_t attempts=0;double t=millis();prove_batch(requests,proofs,n,key,sk,&attempts);double gen=millis()-t;t=millis();int ok=verify_batch(requests,proofs,n);double ver=millis()-t;if(!ok)return 55;
  if(j>=0)fprintf(f,"%s{\"iteration\":%d,\"generate_ms\":%.6f,\"verify_ms\":%.6f,\"sign_attempts\":%llu}",j?",":"",j,gen,ver,(unsigned long long)attempts);
 }
 struct rusage usage;getrusage(RUSAGE_SELF,&usage);
 #ifdef __APPLE__
 size_t rss=(size_t)usage.ru_maxrss;
 #else
 size_t rss=(size_t)usage.ru_maxrss*1024;
 #endif
 fprintf(f,"],\"max_rss_bytes\":%zu,\"all_verified\":true}\n",rss);fclose(f);save_proofs(argv[3],proofs,n*FAEST_SIGNATURE_BYTES);wipe(key,sizeof(key));wipe(sk,sizeof(*sk));free(sk);free(requests);free(proofs);return 0;
}
