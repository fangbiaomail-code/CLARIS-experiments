/* Report costs and ordinary certificate workloads using real ring reports.
 * This driver reconstructs each public statement and starts a separate ordinary
 * worker whose timer excludes process/file overhead. Keys travel only by pipe.
 */
#define EX_STAR_LIBRARY
#include "validate_star.c"
#include <unistd.h>
#include <sys/wait.h>
#include <sys/resource.h>
typedef struct{uint32_t count,ids[NR];uint8_t seed[32];public_key tau,tau1;} Selection;
static size_t peak_rss(void){struct rusage u;getrusage(RUSAGE_SELF,&u);
#ifdef __APPLE__
return (size_t)u.ru_maxrss;
#else
return (size_t)u.ru_maxrss*1024;
#endif
}
static const char*worker;
static void wipe(void*p,size_t n){volatile unsigned char*q=p;while(n--)*q++=0;}
static void exact_load(const char*name,void*p,size_t n){FILE*f=fopen(name,"rb");if(!f||fread(p,1,n,f)!=n||fgetc(f)!=EOF)exit(60);fclose(f);}
static void sizehash2(hash_state*h,uint32_t s){uint8_t b[4]={s>>24,s>>16,s>>8,s};hash_update(h,b,4);}
static void selectedhash(hash_state*h,const Public*p,const Selection*l){sizehash2(h,l->count);for(uint32_t i=0;i<l->count;++i){uint8_t id[32];reportid(p,&p->reports[l->ids[i]],id);hash_update(h,id,32);}}
static int selected_ok(const Public*p,const Selection*l){if(l->count<2||l->count>NR)return 0;for(uint32_t i=0;i<l->count;++i){if(l->ids[i]>=NR)return 0;for(uint32_t j=0;j<i;++j){if(l->ids[i]==l->ids[j])return 0;uint8_t x[64],y[64];memcpy(x,p->reports[l->ids[i]].t0.owf_input,32);memcpy(x+32,p->reports[l->ids[i]].t1.owf_input,32);memcpy(y,p->reports[l->ids[j]].t0.owf_input,32);memcpy(y+32,p->reports[l->ids[j]].t1.owf_input,32);for(int a=0;a<4;++a)for(int b=0;b<4;++b)if(!memcmp(x+16*a,y+16*b,16))return 0;}}return 1;}
static void bridge_inputs2(const Public*p,const Selection*l,uint8_t out[64]){hash_state h;domain(&h,"CLARIS-benchmark-ordinary-bridge-inputs-v2");selectedhash(&h,p,l);hash_update(&h,l->seed,32);hash_final(&h,out,64);for(int i=0;i<4;++i)out[16*i]=(out[16*i]&63)|128;}
static int bridge_ok2(const Public*p,const Selection*l){uint8_t in[64];bridge_inputs2(p,l,in);if(memcmp(in,l->tau.owf_input,32)||memcmp(in+32,l->tau1.owf_input,32))return 0;for(int i=0;i<4;++i)for(int j=0;j<i;++j)if(!memcmp(in+16*i,in+16*j,16))return 0;return 1;}
static void tuple_request(uint8_t out[288],const public_key*a,const public_key*b,const public_key*c,const public_key*d,const uint8_t ctx[32]){const public_key*pk[4]={a,b,c,d};for(int i=0;i<4;++i){memcpy(out+32*i,pk[i]->owf_input,32);memcpy(out+128+32*i,pk[i]->owf_output,32);}memcpy(out+256,ctx,32);}
static uint32_t make_requests(const Public*p,const Selection*l,int method,uint32_t owner,uint8_t out[NR*288]){uint8_t ctx[32];hash_state h;
 if(method==0){if(owner>=FAEST_RING_SIZE)return 0;uint8_t id[32];reportid(p,&p->reports[0],id);domain(&h,"EX-claim-ordinary8-v0");hash_update(&h,id,32);keyhash(&h,&p->p0[owner]);keyhash(&h,&p->p1[owner]);hash_final(&h,ctx,32);tuple_request(out,&p->p0[owner],&p->p1[owner],&p->reports[0].t0,&p->reports[0].t1,ctx);return 1;}
 if(!selected_ok(p,l)||(method==2&&!bridge_ok2(p,l)))return 0;
 domain(&h,method==2?"CLARIS-benchmark-ordinary-bridge-proof-v2":"EX-selected-star-ordinary8-v0");selectedhash(&h,p,l);if(method==2){hash_update(&h,l->seed,32);keyhash(&h,&l->tau);keyhash(&h,&l->tau1);}hash_final(&h,ctx,32);
 uint32_t offset=0;for(uint32_t i=method==2?0:1;i<l->count;++i){const Report*r=&p->reports[l->ids[i]],*a=&p->reports[l->ids[0]];if(method==2)tuple_request(out+288*offset,&r->t0,&r->t1,&l->tau,&l->tau1,ctx);else tuple_request(out+288*offset,&a->t0,&a->t1,&r->t0,&r->t1,ctx);++offset;}return offset;
}
static void request_file(const char*name,const uint8_t*req,uint32_t n){FILE*f=fopen(name,"wb");if(!f||fwrite(&n,1,4,f)!=4||fwrite(req,288,n,f)!=n)exit(61);fclose(f);}
static void call_worker(const char*mode,const char*req,const char*proof,const char*result,int reps,int warm,const uint8_t*key){int fd[2]={-1,-1};if(key&&pipe(fd))exit(62);pid_t pid=fork();if(pid<0)exit(63);if(!pid){if(key){close(fd[1]);if(dup2(fd[0],STDIN_FILENO)<0)_exit(64);close(fd[0]);}char a[20],b[20];snprintf(a,sizeof(a),"%d",reps);snprintf(b,sizeof(b),"%d",warm);if(key)execl(worker,worker,mode,req,proof,result,a,b,(char*)NULL);else execl(worker,worker,mode,req,proof,(char*)NULL);_exit(65);}if(key){close(fd[0]);if(write(fd[1],key,32)!=32)exit(66);close(fd[1]);}int st;if(waitpid(pid,&st,0)!=pid||!WIFEXITED(st)||WEXITSTATUS(st))exit(67);}
static void report_sign(Public*p,int i,secret_key*sk,const uint8_t key[32],uint32_t owner,const uint8_t ins[2][32]){Report*r=&p->reports[i];randomize(r->msg,32);randomize(r->nonce,32);uint8_t in[64],ctx[32],seed[64];taginputs(p,r,in);sk->idx=owner;if(!faest_unpack_secret_key_fixed_owf_inputs(sk,key,ins[0],ins[1])||!faest_unpack_secret_key_for_tag_alt(sk,in,in+32))exit(68);r->t0=sk->tag;r->t1=sk->tag1;signctx(p,r,ctx);randomize(seed,64);public_key_ring ring={p->p0,p->p1};if(!faest_tagged_ring_sign(r->proof,ctx,32,sk,&ring,&r->t0,&r->t1,seed,64))exit(69);}
static double originals(const Public*p,const Selection*l,int method){double t=now();if(!strict_ring(p))exit(70);if(method==0){if(!rv(p,&p->reports[0]))exit(71);}else{if(!selected_ok(p,l))exit(72);for(uint32_t i=0;i<l->count;++i)if(!rv(p,&p->reports[l->ids[i]]))exit(73);}return now()-t;}
static const char*method_name(int method){return method==0?"claim":method==1?"anchor":"bridge";}
int main(int argc,char**argv){if(argc<3||OWF_BLOCKS!=2||SECURITY_PARAM!=256)return 74;worker=argv[1];int verify=!strcmp(argv[2],"verify");int reps=verify?0:atoi(argv[2]),warm=argc>3?atoi(argv[3]):3;if(!verify&&(reps<1||reps>10000||warm<0))return 75;
 Public*p=aalloc(sizeof(*p));secret_key*sk=aalloc(sizeof(*sk));uint8_t key[32],ins[2][32];uint32_t owner=FAEST_RING_SIZE/3;
 if(verify){exact_load("public_reports.bin",p,offsetof(Public,claimant));exact_load("claimant.bin",&owner,4);if(p->magic!=0x45583031||p->n!=FAEST_RING_SIZE||p->sec!=256||owner>=FAEST_RING_SIZE||!strict_ring(p))return 76;for(int i=0;i<NR;++i)if(!rv(p,&p->reports[i]))return 86;}
 else{p->magic=0x45583031;p->n=FAEST_RING_SIZE;p->sec=256;randomize(ins,sizeof(ins));for(int i=0;i<2;++i)for(int j=0;j<2;++j)ins[i][16*j]&=63;
  for(uint32_t u=0;u<FAEST_RING_SIZE;++u){uint8_t k[32];randomize(k,32);sk->idx=u;if(!faest_unpack_secret_key_fixed_owf_inputs(sk,k,ins[0],ins[1]))return 77;p->p0[u]=sk->pk;p->p1[u]=sk->pk1;if(u==owner)memcpy(key,k,32);wipe(k,32);}if(!strict_ring(p))return 78;
  FILE*f=fopen("reports.json","w");if(!f)return 79;fprintf(f,"{\"ring_size\":%d,\"report_proof_bytes\":%u,\"canonical_report_payload_bytes_excluding_manifest\":%u,\"repeats\":%d,\"warmups\":%d,\"samples\":[",FAEST_RING_SIZE,FAEST_TAGGED_RING_SIGNATURE_BYTES,192+FAEST_TAGGED_RING_SIGNATURE_BYTES,reps,warm);
  for(int i=-warm;i<reps;++i){int idx=i<0?0:i%5;double t=now();report_sign(p,idx,sk,key,owner,ins);double sign=now()-t;t=now();int ok=strict_ring(p)&&rv(p,&p->reports[idx]);double ver=now()-t;if(!ok)return 80;if(i>=0)fprintf(f,"%s{\"iteration\":%d,\"generate_ms\":%.6f,\"verify_ms\":%.6f}",i?",":"",i,sign,ver);}
  /* A one-sample smoke run still needs a complete five-report fixture. */
  for(int i=reps<5?reps:5;i<NR;++i)report_sign(p,i,sk,key,owner,ins);
  fprintf(f,"],\"all_verified\":true,\"max_rss_bytes\":%zu}\n",peak_rss());fclose(f);save("public_reports.bin",p,offsetof(Public,claimant));save("claimant.bin",&owner,4);puts("REPORT_TIMINGS_COMPLETE");fflush(stdout);
 }
 uint32_t sizes[6]={1,2,3,5,10,20};for(int z=0;z<6;++z){for(int order=0;order<(z?2:1);++order){int method=z?(1+((order+z)%2)):0;Selection l={0};l.count=sizes[z];for(uint32_t i=0;i<l.count;++i)l.ids[i]=i;char base[64],rf[80],pf[80],jf[80],sf[80],of[80];snprintf(base,sizeof(base),"%s_s%u",method_name(method),l.count);snprintf(rf,sizeof(rf),"%s.requests",base);snprintf(pf,sizeof(pf),"%s.proofs",base);snprintf(jf,sizeof(jf),"%s.json",base);snprintf(sf,sizeof(sf),"%s.selection",base);snprintf(of,sizeof(of),"%s.originals.json",base);
  if(verify)exact_load(sf,&l,sizeof(l));else if(method==2){uint8_t in[64];do{randomize(l.seed,32);bridge_inputs2(p,&l,in);if(!faest_unpack_secret_key_fixed_owf_inputs(sk,key,in,in+32))return 81;l.tau=sk->pk;l.tau1=sk->pk1;}while(!bridge_ok2(p,&l));}
  uint8_t req[NR*288];uint32_t count=make_requests(p,&l,method,owner,req);if(!count)return 82;
  if(verify){uint8_t stored[NR*288];FILE*f=fopen(rf,"rb");uint32_t k;if(!f||fread(&k,1,4,f)!=4||k!=count||fread(stored,288,count,f)!=count||fgetc(f)!=EOF)return 83;fclose(f);if(memcmp(req,stored,288*count))return 84;originals(p,&l,method);call_worker("verify",rf,pf,NULL,0,0,NULL);}
  else{request_file(rf,req,count);save(sf,&l,sizeof(l));FILE*f=fopen(of,"w");if(!f)return 85;fprintf(f,"{\"ring_size\":%d,\"selected_count\":%u,\"method\":\"%s\",\"samples\":[",FAEST_RING_SIZE,l.count,method_name(method));for(int i=-warm;i<reps;++i){double ms=originals(p,&l,method);if(i>=0)fprintf(f,"%s%.6f",i?",":"",ms);}fprintf(f,"]}\n");fclose(f);call_worker("bench",rf,pf,jf,reps,warm,key);printf("CERTIFICATE_TIMINGS_COMPLETE N=%d %s\n",FAEST_RING_SIZE,base);fflush(stdout);}
 }}
 wipe(key,sizeof(key));wipe(sk,sizeof(*sk));free(sk);free(p);if(verify)puts("PUBLIC_RECONSTRUCTION_VERIFIED_NO_PRIVATE_KEY");return 0;
}
