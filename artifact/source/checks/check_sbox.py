"""Exhaustive byte algebra check, distinct from cryptographic security testing."""
from pathlib import Path
import json
def mul(a,b):
 z=0
 for _ in range(8):
  if b&1:z^=a
  a=((a<<1)^ (0x11b if a&128 else 0))&255;b>>=1
 return z
def inv(a):
 if not a:return 0
 z=1
 for _ in range(254):z=mul(z,a)
 return z
def rot(a,n):return ((a<<n)|(a>>(8-n)))&255
def sq_bits(a):
 b=[(a>>i)&1 for i in range(8)]
 rows=[(0,4,6),(4,6,7),(1,5),(4,5,6,7),(2,4,7),(5,6),(3,5),(6,7)]
 return sum((sum(b[i] for i in row)%2)<<j for j,row in enumerate(rows))
accepted=0
for x in range(256):
 assert sq_bits(x)==mul(x,x)
 for y in range(256):
  good=mul(sq_bits(x),y)==x and mul(x,sq_bits(y))==y
  assert good==(y==inv(x))
  accepted+=good
 z=inv(x);s=z^rot(z,1)^rot(z,2)^rot(z,3)^rot(z,4)^0x63
 assert (rot(s,1)^rot(s,3)^rot(s,6)^0x05)==z
assert accepted==256
result={'byte_pairs_exhaustively_checked':65536,'satisfying_pairs':accepted,'pseudoinverse_relation_exact':True,'byte_square_linear_map_exact':True,'inverse_affine_map_exact':True,'cryptographic_security_proof':False}
print(json.dumps(result))
