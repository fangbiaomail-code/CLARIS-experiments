#!/usr/bin/env python3
"""Run fresh ordinary-certificate and original-report measurements from a clean build.
No key files are created. Generated report/proof files are public test data.
"""
import argparse,hashlib,json,platform,statistics,subprocess,time
from pathlib import Path
from datetime import datetime

def summary(values):
    values=list(values); ordered=sorted(values)
    def quantile(q):
        x=(len(ordered)-1)*q; i=int(x)
        return ordered[i]+(ordered[min(i+1,len(ordered)-1)]-ordered[i])*(x-i)
    return {'n':len(values),'median':statistics.median(values),'mean':statistics.mean(values),
            'min':min(values),'max':max(values),'sample_stdev':statistics.stdev(values) if len(values)>1 else 0,
            'p25':quantile(.25),'p75':quantile(.75),'p95':quantile(.95)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--repeats',type=int,default=30);ap.add_argument('--warmups',type=int,default=3)
    ap.add_argument('--ring-sizes',nargs='+',type=int,choices=[64,1024],default=[64,1024])
    args=ap.parse_args();build=args.build.resolve();out=args.output.resolve()
    if args.repeats<1 or args.warmups<0:ap.error('invalid sample counts')
    if out.exists() and any(out.iterdir()):ap.error('use a new empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((build/'build_manifest.json').read_text())
    worker=build/'ordinary/ordinary_worker'
    started_at=datetime.now().astimezone()
    result={'schema':'claris-ordinary-benchmark-v2','date':started_at.date().isoformat(),'started_at':started_at.isoformat(),
        'host':platform.platform(),'compiler':manifest['compiler'],'flags':manifest['flags'],
        'execution_target':manifest['execution_target'],'transcript_profile':manifest['transcript_profile'],
        'repeats':args.repeats,'warmups_per_cell':args.warmups,
        'scope':{'ordinary':'in-memory witness expansion, random seed, proving/retry and verification; excludes public request construction, bridge setup, file I/O, outer worker-buffer allocation and IPC',
                 'report':'fresh message/nonce, context and tag derivation, witness expansion and report proving; verification includes registry/public-report checks',
                 'original_set':'separate in-memory validation of the selected original reports and registry',
                 'full_verify':'not measured as a single operation; no observed end-to-end latency claim',
                 'ordering':'methods measured in consecutive batches; anchor/bridge order alternates with selection size',
                 'dataset':'same public report corpus and honest registry for all certificate cells within each ring size; fresh proof randomness per sample; one bridge tuple per cell'},
        'report_rows':[],'certificate_rows':[],'fresh_public_verification':[],
        'build_manifest_sha256':hashlib.sha256((build/'build_manifest.json').read_bytes()).hexdigest()}
    try:result['cpu']=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip()
    except (OSError,subprocess.CalledProcessError):result['cpu']=platform.processor()
    for n in args.ring_sizes:
        work=out/f'n{n}';work.mkdir();driver=build/f'ring_n{n}/ordinary_benchmark'
        command=[str(driver),str(worker),str(args.repeats),str(args.warmups)]
        start=time.monotonic()
        print(f'Starting N={n}, {args.repeats} measured runs per cell',flush=True)
        with (work/'run.log').open('w') as log:
            process=subprocess.Popen(command,cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in process.stdout:
                log.write(line);log.flush()
                print(line.rstrip(),flush=True)
            if process.wait():raise RuntimeError(f'Benchmark N={n} failed; see {work}/run.log')
        with (work/'fresh_verify.log').open('w') as log:
            subprocess.run([str(driver),str(worker),'verify'],cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
        assert 'PUBLIC_RECONSTRUCTION_VERIFIED_NO_PRIVATE_KEY' in (work/'fresh_verify.log').read_text()
        result['fresh_public_verification'].append({'ring_size':n,'all_reports_and_statements_reconstructed':True,'secret_keys_loaded':False,'elapsed_workload_seconds':time.monotonic()-start})
        reports=json.loads((work/'reports.json').read_text());assert reports['all_verified']
        assert len(reports['samples'])==args.repeats
        result['report_rows'].append({'ring_size':n,'proof_bytes':reports['report_proof_bytes'],
          'canonical_payload_bytes_excluding_manifest':reports['canonical_report_payload_bytes_excluding_manifest'],
          'generate_ms':summary(x['generate_ms'] for x in reports['samples']),
          'verify_ms':summary(x['verify_ms'] for x in reports['samples']),
          'samples':reports['samples']})
        for name in ['claim_s1','anchor_s2','bridge_s2','anchor_s3','bridge_s3','anchor_s5','bridge_s5']:
            d=json.loads((work/(name+'.json')).read_text()); orig=json.loads((work/(name+'.originals.json')).read_text())
            assert d['all_verified'] and len(d['samples'])==args.repeats and len(orig['samples'])==args.repeats
            result['certificate_rows'].append({'ring_size':n,'method':orig['method'],'selected_count':orig['selected_count'],
                'proof_count':d['proof_count'],'proof_bytes':d['proof_bytes'],
                'generate_ms':summary(x['generate_ms'] for x in d['samples']),
                'verify_ms':summary(x['verify_ms'] for x in d['samples']),
                'original_set_ms':summary(orig['samples']),
                'max_rss_bytes':d['max_rss_bytes'],'samples':d['samples'],'original_set_samples_ms':orig['samples']})
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'Completed and independently verified N={n}',flush=True)
    files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='file_hashes.json'}
    (out/'file_hashes.json').write_text(json.dumps(files,indent=2)+'\n')
    print(out/'results.json',flush=True)
if __name__=='__main__':main()
