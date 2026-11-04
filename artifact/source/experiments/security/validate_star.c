/* v1.1: selected reports are joined directly to an anchor report.
 * Uses the existing, unchanged P01 four-tuple AES/VOLE relation.
 * No adversarially chosen linkage plaintexts, new circuit, or secret verifier.
 * This is a functional experiment; concrete QROM security remains conditional.
 */
#define main legacy_main
#include "../validate.c"
#undef main

typedef struct { uint32_t ids[NS]; uint8_t proofs[NS-1][FAEST_TAGGED_RING_SIGNATURE_BYTES]; } StarLink;
static int strict_ring(const Public*p) {
  for(size_t i=0;i<FAEST_RING_SIZE;++i) {
    if(memcmp(p->p0[0].owf_input,p->p0[i].owf_input,32)||memcmp(p->p1[0].owf_input,p->p1[i].owf_input,32))return 0;
    for(size_t j=0;j<i;++j)
      if(!memcmp(p->p0[j].owf_output,p->p0[i].owf_output,32)&&!memcmp(p->p1[j].owf_output,p->p1[i].owf_output,32))return 0;
  }
  return 1;
}
static int star_ids(const Public*p,const StarLink*l) {
  for(size_t i=0;i<NS;++i) {
    if(l->ids[i]>=NR)return 0;
    for(size_t j=0;j<i;++j) {
      if(l->ids[i]==l->ids[j])return 0;
      const Report*a=&p->reports[l->ids[i]],*b=&p->reports[l->ids[j]];
      uint8_t ai[64],bi[64];memcpy(ai,a->t0.owf_input,32);memcpy(ai+32,a->t1.owf_input,32);
      memcpy(bi,b->t0.owf_input,32);memcpy(bi+32,b->t1.owf_input,32);
      for(int x=0;x<4;++x)for(int y=0;y<4;++y)if(!memcmp(ai+16*x,bi+16*y,16))return 0;
    }
  }
  return 1;
}
static void star_ctx(const Public*p,const StarLink*l,uint8_t out[32]) {
  hash_state h;domain(&h,"EX-selected-star-v1.1");uint8_t size[4]={0,0,0,NS};hash_update(&h,size,4);
  for(size_t i=0;i<NS;++i){uint8_t id[32];reportid(p,&p->reports[l->ids[i]],id);hash_update(&h,id,32);}
  hash_final(&h,out,32);
}
static int star_verify(const Public*p,const StarLink*l) {
  if(!strict_ring(p)||!star_ids(p,l))return 0;
  for(size_t i=0;i<NS;++i)if(!rv(p,&p->reports[l->ids[i]]))return 0;
  const Report*a=&p->reports[l->ids[0]];uint8_t ctx[32];star_ctx(p,l,ctx);
  for(size_t i=1;i<NS;++i){const Report*b=&p->reports[l->ids[i]];
    if(!pair_verify(l->proofs[i-1],ctx,&a->t0,&a->t1,&b->t0,&b->t1))return 0;}
  return 1;
}
static int strict_claim(const Public*p,const Report*r,uint32_t u,const uint8_t*proof) {
  return strict_ring(p)&&cv(p,r,u,proof);
}
static void star_prove(const Public*p,StarLink*l,secret_key*sk,const uint8_t*key) {
  uint8_t ctx[32];star_ctx(p,l,ctx);const Report*a=&p->reports[l->ids[0]];
  for(size_t i=1;i<NS;++i){const Report*b=&p->reports[l->ids[i]];
    prep(sk,key,&a->t0,&a->t1,&b->t0,&b->t1);tp(l->proofs[i-1],sk,ctx,&a->t0,&a->t1,&b->t0,&b->t1);}
}
#ifndef EX_STAR_LIBRARY
int main(int argc,char**argv) {
  if(SECURITY_PARAM!=256||OWF_BLOCKS!=2)return 10;
  Public*p=aalloc(sizeof(Public));StarLink*l=aalloc(sizeof(StarLink));
  if(argc>1) {
    FILE*f=fopen("public_reports.bin","rb");size_t base=offsetof(Public,claimant);
    if(!f||fread(p,1,base,f)!=base||fgetc(f)!=EOF)return 5;fclose(f);
    check("fresh public parameters",p->magic==0x45583031&&p->n==FAEST_RING_SIZE&&p->sec==256);
    for(int i=0;i<NR;++i)check("fresh original report",strict_ring(p)&&rv(p,&p->reports[i]));
    int with_claim=!strcmp(argv[1],"verify");
    if(with_claim){f=fopen("claim.bin","rb");if(!f||fread(&p->claimant,1,4,f)!=4||fread(p->claim,1,sizeof(p->claim),f)!=sizeof(p->claim)||fgetc(f)!=EOF)return 5;fclose(f);
      check("fresh claim without key",strict_claim(p,&p->reports[0],p->claimant,p->claim));}
    f=fopen("star_link.bin","rb");if(!f||fread(l,1,sizeof(*l),f)!=sizeof(*l)||fgetc(f)!=EOF)return 5;fclose(f);
    check("fresh star link without key or identity",star_verify(p,l));
    printf("RESULT fresh=true private_keys=false claim_artifact_loaded=%s checks=%d\n",with_claim?"true":"false",tests);return 0;
  }
  p->magic=0x45583031;p->n=FAEST_RING_SIZE;p->sec=256;
  secret_key*sk=aalloc(sizeof(secret_key));uint8_t keys[2][32],ins[2][32];randomize(ins,sizeof(ins));
  for(int a=0;a<2;++a)for(int b=0;b<2;++b)ins[a][16*b]&=63;
  const uint32_t honest=FAEST_RING_SIZE/3,other=FAEST_RING_SIZE/2;
  for(uint32_t i=0;i<FAEST_RING_SIZE;++i){uint8_t key[32];randomize(key,32);sk->idx=i;
    if(!faest_unpack_secret_key_fixed_owf_inputs(sk,key,ins[0],ins[1]))return 4;
    p->p0[i]=sk->pk;p->p1[i]=sk->pk1;if(i==honest)memcpy(keys[0],key,32);if(i==other)memcpy(keys[1],key,32);}
  check("common inputs and unique ring identities",strict_ring(p));public_key_ring ring={p->p0,p->p1};
  for(int i=0;i<NR;++i){Report*r=&p->reports[i];randomize(r->msg,32);randomize(r->nonce,32);uint8_t ti[64],ctx[32],seed[64];taginputs(p,r,ti);int k=i>=5;sk->idx=k?other:honest;
    if(!faest_unpack_secret_key_fixed_owf_inputs(sk,keys[k],ins[0],ins[1])||!faest_unpack_secret_key_for_tag_alt(sk,ti,ti+32))return 4;
    r->t0=sk->tag;r->t1=sk->tag1;signctx(p,r,ctx);randomize(seed,64);
    check("real VOLE report sign",faest_tagged_ring_sign(r->proof,ctx,32,sk,&ring,&r->t0,&r->t1,seed,64));check("report verify",rv(p,r));}
  uint8_t ctx[32];claimctx(p,&p->reports[0],honest,ctx);prep(sk,keys[0],&p->p0[honest],&p->p1[honest],&p->reports[0].t0,&p->reports[0].t1);
  tp(p->claim,sk,ctx,&p->p0[honest],&p->p1[honest],&p->reports[0].t0,&p->reports[0].t1);p->claimant=honest;
  check("claim signer",strict_claim(p,&p->reports[0],honest,p->claim));check("wrong claimant rejected",!strict_claim(p,&p->reports[0],other,p->claim));
  check("claim transplant rejected",!strict_claim(p,&p->reports[1],honest,p->claim));
  uint8_t*attack=aalloc(FAEST_TAGGED_RING_SIGNATURE_BYTES);claimctx(p,&p->reports[0],other,ctx);prep(sk,keys[1],&p->p0[other],&p->p1[other],&p->reports[0].t0,&p->reports[0].t1);
  tp(attack,sk,ctx,&p->p0[other],&p->p1[other],&p->reports[0].t0,&p->reports[0].t1);check("fresh hostile claim rejected",!strict_claim(p,&p->reports[0],other,attack));
  claimctx(p,&p->reports[5],honest,ctx);prep(sk,keys[1],&p->p0[honest],&p->p1[honest],&p->reports[5].t0,&p->reports[5].t1);
  tp(attack,sk,ctx,&p->p0[honest],&p->p1[honest],&p->reports[5].t0,&p->reports[5].t1);check("fresh signer framing rejected",!strict_claim(p,&p->reports[5],honest,attack));
  l->ids[0]=0;l->ids[1]=1;l->ids[2]=2;double t=now();star_prove(p,l,sk,keys[0]);double ms=now()-t;check("star selected set",star_verify(p,l));
  StarLink*bad=aalloc(sizeof(StarLink));*bad=*l;bad->ids[2]=3;check("unselected append substitution rejected",!star_verify(p,bad));
  *bad=*l;bad->ids[2]=5;check("other signer substitution rejected",!star_verify(p,bad));
  *bad=*l;bad->ids[2]=bad->ids[0];check("duplicate report rejected",!star_verify(p,bad));
  *bad=*l;uint32_t tmp=bad->ids[0];bad->ids[0]=bad->ids[1];bad->ids[1]=tmp;check("anchor reorder rejected",!star_verify(p,bad));
  *bad=*l;bad->proofs[0][sizeof(bad->proofs[0])/2]^=1;check("proof mutation rejected",!star_verify(p,bad));
  *bad=*l;bad->ids[2]=5;star_ctx(p,bad,ctx);
  for(int i=1;i<NS;++i){const Report*a=&p->reports[0],*b=&p->reports[bad->ids[i]];prep(sk,i==2?keys[1]:keys[0],&a->t0,&a->t1,&b->t0,&b->t1);
    tp(bad->proofs[i-1],sk,ctx,&a->t0,&a->t1,&b->t0,&b->t1);}
  check("fresh mixed signer proofs rejected",!star_verify(p,bad));
  Public*q=aalloc(sizeof(Public));*q=*p;q->p0[1]=q->p0[0];q->p1[1]=q->p1[0];check("duplicate identity rejected",!strict_ring(q));
  *q=*p;((uint8_t*)q->p1[1].owf_input)[0]^=1;check("noncommon identity inputs rejected",!strict_ring(q));
  *q=*p;memcpy(&q->reports[1].t0.owf_input[0],&q->reports[0].t0.owf_input[0],16);check("shared selected input rejected",!star_ids(q,l));
  check("claim plus selected link jointly verify",strict_claim(p,&p->reports[0],honest,p->claim)&&star_verify(p,l));
  save("public_reports.bin",p,offsetof(Public,claimant));save("star_link.bin",l,sizeof(*l));FILE*f=fopen("claim.bin","wb");if(!f)return 5;
  fwrite(&p->claimant,1,4,f);fwrite(p->claim,1,sizeof(p->claim),f);fclose(f);
  f=fopen("results.json","w");if(!f)return 5;
  fprintf(f,"{\"version\":\"v1.1-star\",\"ring_size\":%d,\"checks_passed\":%d,\"selected_count\":%d,\"link_proof_count\":%d,\"link_proofs_bytes\":%u,\"star_link_ms\":%.6f,\"functional_pass\":true,\"circuit_changed\":false,\"full_concrete_security_proven\":false}\n",FAEST_RING_SIZE,tests,NS,NS-1,(NS-1)*FAEST_TAGGED_RING_SIGNATURE_BYTES,ms);fclose(f);
  memset(keys,0,sizeof(keys));memset(sk,0,sizeof(*sk));free(sk);free(p);free(q);free(l);free(bad);free(attack);return 0;
}
#endif
