/* Original P01 ring reports + experimental ordinary eight-block Claim/Link.
 * Public verifier reconstructs every statement from original reports.
 * Temporary witness files are mode 0600 and removed immediately after proving.
 */
#define EX_STAR_LIBRARY
#include "../validate_star.c"
#include <unistd.h>
#include <sys/wait.h>
#include <sys/stat.h>
static const char*cli;
static void request(uint8_t out[288],const public_key*a,const public_key*b,const public_key*c,const public_key*d,const uint8_t ctx[32]) {
 const public_key*q[4]={a,b,c,d};for(int i=0;i<4;++i){memcpy(out+32*i,q[i]->owf_input,32);memcpy(out+128+32*i,q[i]->owf_output,32);}memcpy(out+256,ctx,32);
}
static int command(const char*mode,const char*r,const char*p,const char*k) {
 pid_t id=fork();if(id<0)exit(30);if(!id){if(k)execl(cli,cli,mode,r,p,k,(char*)NULL);else execl(cli,cli,mode,r,p,(char*)NULL);_exit(31);}int status;if(waitpid(id,&status,0)!=id)exit(32);return WIFEXITED(status)?WEXITSTATUS(status):33;
}
static void produce(const char*name,const uint8_t req[288],const uint8_t key[32]) {
 char r[100],p[100],tmp[]="pair-key-XXXXXX";snprintf(r,sizeof(r),"%s.request",name);snprintf(p,sizeof(p),"%s.proof",name);save(r,req,288);
 int fd=mkstemp(tmp);if(fd<0)exit(34);if(fchmod(fd,0600)||write(fd,key,32)!=32){close(fd);unlink(tmp);exit(35);}close(fd);
 int status=command("prove",r,p,tmp);unlink(tmp);if(status)exit(36);
}
static int verify_request(const char*name,const uint8_t req[288]) {
 char p[100];snprintf(p,sizeof(p),"%s.proof",name);save("verifier.request",req,288);int status=command("verify","verifier.request",p,NULL);if(status!=0&&status!=2)exit(37);return status==0;
}
static void ordinary_claim_ctx(const Public*p,const Report*r,uint32_t u,uint8_t out[32]) {
 hash_state h;domain(&h,"EX-claim-ordinary8-v0");uint8_t id[32];reportid(p,r,id);hash_update(&h,id,32);keyhash(&h,&p->p0[u]);keyhash(&h,&p->p1[u]);hash_final(&h,out,32);
}
static void ordinary_link_ctx(const Public*p,const StarLink*l,uint8_t out[32]) {
 hash_state h;domain(&h,"EX-selected-star-ordinary8-v0");uint8_t n[4]={0,0,0,NS};hash_update(&h,n,4);for(int i=0;i<NS;++i){uint8_t id[32];reportid(p,&p->reports[l->ids[i]],id);hash_update(&h,id,32);}hash_final(&h,out,32);
}
static void claim_request(const Public*p,int report,uint32_t u,uint8_t req[288]) {
 uint8_t ctx[32];ordinary_claim_ctx(p,&p->reports[report],u,ctx);request(req,&p->p0[u],&p->p1[u],&p->reports[report].t0,&p->reports[report].t1,ctx);
}
static void edge_request(const Public*p,const StarLink*l,int edge,uint8_t req[288]) {
 uint8_t ctx[32];ordinary_link_ctx(p,l,ctx);const Report*a=&p->reports[l->ids[0]],*b=&p->reports[l->ids[edge]];request(req,&a->t0,&a->t1,&b->t0,&b->t1,ctx);
}
static int claim_verify(const Public*p,int report,uint32_t u,const char*name) {
 if(u>=FAEST_RING_SIZE||!strict_ring(p)||!rv(p,&p->reports[report]))return 0;uint8_t req[288];claim_request(p,report,u,req);return verify_request(name,req);
}
static int link_verify(const Public*p,const StarLink*l,const char*prefix) {
 if(!strict_ring(p)||!star_ids(p,l))return 0;for(int i=0;i<NS;++i)if(!rv(p,&p->reports[l->ids[i]]))return 0;
 for(int i=1;i<NS;++i){uint8_t req[288];char name[100];snprintf(name,sizeof(name),"%s%d",prefix,i);edge_request(p,l,i,req);if(!verify_request(name,req))return 0;}return 1;
}
static void load(const char*path,void*b,size_t n) {FILE*f=fopen(path,"rb");if(!f||fread(b,1,n,f)!=n||fgetc(f)!=EOF)exit(38);fclose(f);}
int main(int argc,char**argv) {
 if(argc<2||OWF_BLOCKS!=2||SECURITY_PARAM!=256)return 39;cli=argv[1];Public*p=aalloc(sizeof(Public));StarLink*l=aalloc(sizeof(StarLink));
 const uint32_t honest=FAEST_RING_SIZE/3,other=FAEST_RING_SIZE/2;
 if(argc>2){load("public_reports.bin",p,offsetof(Public,claimant));load("selected_ids.bin",l->ids,sizeof(l->ids));
  check("fresh public parameters",p->magic==0x45583031&&p->n==FAEST_RING_SIZE&&p->sec==256);
  for(int i=0;i<NR;++i)check("fresh original ring report",strict_ring(p)&&rv(p,&p->reports[i]));
  int with_claim=!strcmp(argv[2],"verify");if(with_claim){uint32_t u;load("claimant.bin",&u,4);check("fresh ordinary claim without key",claim_verify(p,0,u,"claim"));}
  check("fresh ordinary selected link without key or identity",link_verify(p,l,"edge"));FILE*f=fopen(with_claim?"fresh.json":"fresh_link.json","w");if(!f)return 40;
  fprintf(f,"{\"checks_passed\":%d,\"private_keys_loaded\":false,\"claim_identity_loaded\":%s,\"joint_pass\":true}\n",tests,with_claim?"true":"false");fclose(f);free(l);free(p);return 0;
 }
 p->magic=0x45583031;p->n=FAEST_RING_SIZE;p->sec=256;secret_key*sk=aalloc(sizeof(secret_key));uint8_t keys[2][32],ins[2][32];randomize(ins,sizeof(ins));for(int a=0;a<2;++a)for(int b=0;b<2;++b)ins[a][16*b]&=63;
 for(uint32_t u=0;u<FAEST_RING_SIZE;++u){uint8_t key[32];randomize(key,32);sk->idx=u;if(!faest_unpack_secret_key_fixed_owf_inputs(sk,key,ins[0],ins[1]))return 41;p->p0[u]=sk->pk;p->p1[u]=sk->pk1;if(u==honest)memcpy(keys[0],key,32);if(u==other)memcpy(keys[1],key,32);memset(key,0,32);}
 check("honest registry inputs and distinct identities",strict_ring(p));public_key_ring ring={p->p0,p->p1};
 for(int i=0;i<NR;++i){Report*r=&p->reports[i];randomize(r->msg,32);randomize(r->nonce,32);uint8_t ti[64],ctx[32],seed[64];taginputs(p,r,ti);int k=i>=5;sk->idx=k?other:honest;
  if(!faest_unpack_secret_key_fixed_owf_inputs(sk,keys[k],ins[0],ins[1])||!faest_unpack_secret_key_for_tag_alt(sk,ti,ti+32))return 42;r->t0=sk->tag;r->t1=sk->tag1;signctx(p,r,ctx);randomize(seed,64);
  check("original real ring report sign",faest_tagged_ring_sign(r->proof,ctx,32,sk,&ring,&r->t0,&r->t1,seed,64));check("original ring report verifies",rv(p,r));}
 uint8_t req[288];claim_request(p,0,honest,req);produce("claim",req,keys[0]);check("ordinary Claim valid",claim_verify(p,0,honest,"claim"));
 check("wrong identity transplant rejected",!claim_verify(p,0,other,"claim"));check("other report transplant rejected",!claim_verify(p,1,honest,"claim"));
 claim_request(p,0,other,req);produce("hostile_claim",req,keys[1]);check("fresh wrong-owner claim rejected",!claim_verify(p,0,other,"hostile_claim"));
 claim_request(p,5,honest,req);produce("hostile_frame",req,keys[1]);check("fresh signer framing rejected",!claim_verify(p,5,honest,"hostile_frame"));
 l->ids[0]=0;l->ids[1]=1;l->ids[2]=2;for(int i=1;i<NS;++i){char name[50];snprintf(name,sizeof(name),"edge%d",i);edge_request(p,l,i,req);produce(name,req,keys[0]);}
 check("ordinary selected link valid",link_verify(p,l,"edge"));check("Claim and Link jointly valid",claim_verify(p,0,honest,"claim")&&link_verify(p,l,"edge"));
 StarLink*bad=aalloc(sizeof(StarLink));*bad=*l;bad->ids[2]=3;check("unselected same-owner report transplant rejected",!link_verify(p,bad,"edge"));*bad=*l;bad->ids[2]=5;check("other owner transplant rejected",!link_verify(p,bad,"edge"));*bad=*l;bad->ids[1]=bad->ids[0];check("duplicate report rejected",!link_verify(p,bad,"edge"));*bad=*l;bad->ids[1]=2;bad->ids[2]=1;check("selected order transplant rejected",!link_verify(p,bad,"edge"));
 *bad=*l;bad->ids[2]=5;for(int i=1;i<NS;++i){char name[50];snprintf(name,sizeof(name),"hostile_edge%d",i);edge_request(p,bad,i,req);produce(name,req,keys[i==2]);}check("fresh mixed-owner linked set rejected",!link_verify(p,bad,"hostile_edge"));
 save("public_reports.bin",p,offsetof(Public,claimant));save("selected_ids.bin",l->ids,sizeof(l->ids));save("claimant.bin",&honest,4);
 FILE*f=fopen("results.json","w");if(!f)return 43;fprintf(f,"{\"ring_size\":%d,\"selected_count\":%d,\"checks_passed\":%d,\"functional_pass\":true,\"ordinary_pair_proof_bytes\":49208,\"link_core_proof_bytes\":98416,\"ring_report_circuit_changed\":false,\"pair_uses_ring_OR\":false,\"quantum_security_certified\":false}\n",FAEST_RING_SIZE,NS,tests);fclose(f);
 memset(keys,0,sizeof(keys));memset(sk,0,sizeof(*sk));free(sk);free(p);free(l);free(bad);return 0;
}
