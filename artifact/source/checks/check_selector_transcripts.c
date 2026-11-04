/* Isolated low-level selector regression, not a registry-level forgery.
 * Every ring entry is intentionally the same public tuple, making every
 * AES branch true. Only selector well-formedness distinguishes the cases.
 * Build against a Q backend. argv[1]=legacy expects the old three-hot pass.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "faest.h"
#include "faest_details.h"
#include "owf_proof.h"
#include "randomness.h"

static void* allocate(size_t n) {
    void* p=aligned_alloc(32,(n+31)&~(size_t)31);
    if(!p)exit(10);
    memset(p,0,(n+31)&~(size_t)31);
    return p;
}
static void setbit(uint8_t* w,size_t bit) { w[bit/8]|=(uint8_t)(1u<<(bit%8)); }
int main(int argc,char**argv) {
    if(FAEST_RING_HOTVECTOR_DIM!=2||OWF_BLOCKS!=2||SECURITY_PARAM!=256)return 11;
    int legacy=argc>1&&!strcmp(argv[1],"legacy");
    secret_key* sk=allocate(sizeof(*sk));
    public_key* p0=allocate(FAEST_RING_SIZE*sizeof(*p0));
    public_key* p1=allocate(FAEST_RING_SIZE*sizeof(*p1));
    uint8_t key[32],inputs[128],seed[64],context[32];
    if(rand_bytes(key,sizeof(key))||rand_bytes(inputs,sizeof(inputs))||
       rand_bytes(seed,sizeof(seed))||rand_bytes(context,sizeof(context)))return 12;
    sk->idx=0;
    if(!faest_unpack_secret_key_fixed_owf_inputs(sk,key,inputs,inputs+32)||
       !faest_unpack_secret_key_for_tag_alt(sk,inputs+64,inputs+96))return 13;
    for(size_t i=0;i<FAEST_RING_SIZE;++i){p0[i]=sk->pk;p1[i]=sk->pk1;}
    public_key_ring ring={p0,p1};
    public_key tag0=sk->tag,tag1=sk->tag1;
    uint8_t* proof=allocate(FAEST_TAGGED_RING_SIGNATURE_BYTES);
    uint8_t* w=(uint8_t*)sk->tagged_ring_witness;
    size_t offset=TAGGED_RING_WITNESS_BITS-8*FAEST_RING_HOTVECTOR_BYTES;
    int accepted[4]={0};
    for(int which=0;which<4;++which){
        memset(w+offset/8,0,FAEST_RING_HOTVECTOR_BYTES);
        for(size_t dim=0;dim<2;++dim){
            size_t start=offset+dim*FAEST_RING_HOTVECTOR_BITS;
            setbit(w,start);
            if(which&(1<<dim)){setbit(w,start+1);setbit(w,start+2);}
        }
        seed[0]^=(uint8_t)(which+1);
        if(!faest_tagged_ring_sign(proof,context,sizeof(context),sk,&ring,&tag0,&tag1,seed,sizeof(seed)))return 14;
        accepted[which]=faest_tagged_ring_verify(proof,context,sizeof(context),&ring,&tag0,&tag1);
        if(accepted[which]!=(which==0||legacy))return 20+which;
    }
    printf("{\"ring_size\":%d,\"low_level_duplicate_ring\":true,\"end_to_end_forgery_test\":false,\"legacy\":%s,\"honest_accept\":%s,\"three_hot_first_accept\":%s,\"three_hot_second_accept\":%s,\"three_hot_both_accept\":%s,\"checks_passed\":4}\n",FAEST_RING_SIZE,legacy?"true":"false",accepted[0]?"true":"false",accepted[1]?"true":"false",accepted[2]?"true":"false",accepted[3]?"true":"false");
    memset(key,0,sizeof(key));memset(sk,0,sizeof(*sk));free(sk);free(p0);free(p1);free(proof);
    return 0;
}
