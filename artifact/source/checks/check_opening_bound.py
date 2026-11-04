#!/usr/bin/env python3
"""Exact (not sampled) opening-acceptance lower bound for the CLARIS profile.
BATCH_VEC_POS_IN_TREE follows the pinned vector_com.h mapping. Both ring sizes
use the same 22 small-VOLE vectors and the same compressed opening parameters.
Run after latency measurements, separately from their timed workload.
"""
from array import array
from fractions import Fraction
import json, math

L=61440
lengths=[4096]*8+[2048]*14
count=22
nodes=2*L-1
members=array('H',[0])*(nodes*count)
for i,n in enumerate(lengths):
    for x in range(n):
        p=L-1+(22*x+i if x<2048 else 14*2048+8*x+i)
        assert not members[p*count+i]
        members[p*count+i]=1
for p in range(L-2,-1,-1):
    for i in range(count):
        members[p*count+i]=members[(2*p+1)*count+i]+members[(2*p+2)*count+i]
assert list(members[:count])==lengths
assert all(sum(members[p*count:(p+1)*count])==1 for p in range(L-1,nodes))
den=math.prod(lengths)
assert den==2**250
marked_num=0
for p in range(nodes):
    missed=math.prod(n-members[p*count+i] for i,n in enumerate(lengths))
    marked_num+=den-missed
frontier_num=marked_num-43*den
expected=Fraction(frontier_num,den)
assert frontier_num==420943529227452672821606301575237216403132767841007174106764616203295206557736
lower=(1-expected/246)/64
assert lower>Fraction(1,1181)
# Rigorous rational upper bound ln(2)<0.693148 gives the claimed tail exponent.
assert Fraction(2**20,1181)>1280*Fraction(693148,1000000)
print(json.dumps({'method':'exact integer subtree counting; no random samples',
 'leaf_count':L,'vector_lengths':lengths,'opening_seed_threshold':245,
 'expected_frontier_numerator':str(frontier_num),'denominator':str(den),
 'expected_frontier':float(expected),'raw_acceptance_lower_bound':float(lower),
 'raw_acceptance_strictly_greater_than':'1/1181',
 'truncation_trials':2**20,'truncation_failure_strictly_below':'2^-1280',
 'passed':True},indent=2))
