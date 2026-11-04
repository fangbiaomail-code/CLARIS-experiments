#!/usr/bin/env python3
"""Small exact GF(2) polynomial checks; no cryptographic benchmark."""
import itertools
import json
from pathlib import Path

VARS = ('a','b','x','y','A','B','X','Y')
def monomial(**powers):
    return tuple(powers.get(v,0) for v in VARS)
def add(*polys):
    result=set()
    for p in polys: result.symmetric_difference_update(p)
    return result
def mul(left,right):
    result=set()
    for x in left:
        for y in right:
            t=tuple(a+b for a,b in zip(x,y))
            if t in result: result.remove(t)
            else: result.add(t)
    return result

def main():
    old=set(); repaired=set()
    # The last three branches have outer exponents 2,3,4 in the old code.
    for p in (2,3,4):
        f={q for q in (2,3,4) if q!=p}
        inner={monomial(a=1,x=q) for q in f}|{monomial(b=1,y=q) for q in f}
        old=add(old,mul(inner,{monomial(a=1,x=p),monomial(b=1,y=p)}))
        repaired=add(repaired,mul(inner,{monomial(A=1,X=p),monomial(B=1,Y=p)}))
    assert not old
    assert len(repaired)==24
    old_pass=0; fixed_pass=0; malformed_pass=0
    for prefix in itertools.product((0,1),repeat=7):
        last=1
        for b in prefix:last^=b
        bits=prefix+(last,)
        sigma=0
        for i,b in enumerate(bits,1):
            if b:sigma^=i
        residual=[(sigma^i) if b else 0 for i,b in enumerate(bits,1)]
        aggregate=0
        for r in residual:aggregate^=r
        old_pass+=aggregate==0
        malformed_pass+=(aggregate==0 and sum(bits)>1)
        fixed_pass+=all(r==0 for r in residual)
        assert all(r==0 for r in residual)==(sum(bits)==1)
    m32_onehot_pass=0; m32_threehot_reject=0; m32_legacy_threehot_pass=0
    # All 32 one-hot vectors and all C(32,3)=4960 three-hot vectors satisfy
    # the parity-completed last-bit representation; no sampled cases.
    for weight in (1,3):
        for positions in itertools.combinations(range(32),weight):
            sigma=0
            for position in positions:sigma^=position+1
            residual=[sigma^(position+1) for position in positions]
            aggregate=0
            for value in residual:aggregate^=value
            assert aggregate==0
            if weight==1:
                assert all(value==0 for value in residual)
                m32_onehot_pass+=1
            else:
                assert any(value!=0 for value in residual)
                m32_threehot_reject+=1
                m32_legacy_threehot_pass+=1
    result={
      'scope':'exact batching/selector algebra, not an AES signature forgery',
      'legacy_nested_batch_nonzero_residual_cancelled':not old,
      'independent_inner_outer_polynomial_monomials':len(repaired),
      'selector_dimension':8,'selector_patterns_checked':128,
      'legacy_selector_aggregate_pass':old_pass,
      'legacy_multi_hot_pass':malformed_pass,
      'repaired_per_index_pass':fixed_pass,
      'repaired_accepts_exactly_one_hot':fixed_pass==8,
      'dimension_32_one_hot_vectors_accepted':m32_onehot_pass,
      'dimension_32_three_hot_vectors_rejected':m32_threehot_reject,
      'dimension_32_legacy_three_hot_vectors_accepted':m32_legacy_threehot_pass,
      'fixed_branch_residual_exponents':{'2':[3,4],'3':[2,4],'4':[2,3]},
    }
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
