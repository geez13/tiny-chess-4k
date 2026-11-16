# tiny-chess-4k (MIT). 120-square board, alpha-beta+quiescence, null move, TT, fixed node budget.
import json,os,urllib.request as U
from collections import namedtuple
E=os.environ['MAKEFUN_ENV_URL']
def post(r,b):return json.load(U.urlopen(U.Request(E+r,json.dumps(b).encode(),{'content-type':'application/json'})))
N,S,W,O=-10,10,-1,1
A1,H1,A8,H8=91,98,21,28
D={'P':(N,N+N,N+W,N+O),'N':(N+N+O,N+N+W,S+S+O,S+S+W,N+O+O,N+W+W,S+O+O,S+W+W),'B':(N+O,N+W,S+O,S+W),'R':(N,S,O,W)}
D['Q']=D['K']=D['B']+D['R']
def pv(k,x):
 r=9-x//10;c=x%10-1;z=7-abs(2*c-7)+7-abs(2*r-7)
 return{'P':100+2*r*r+(r>1)*(3-abs(2*c-7))*4,'N':300+4*z,'B':320+2*z,'R':500+15*(r==6),'Q':900+z,'K':60000-8*r*r+(r==0)*(c in(1,2,6))*15}[k]
T={k:[pv(k,x)if 20<x<99 and 0<x%10<9 else 0 for x in range(120)]for k in'PNBRQK'}
ML,MU=50000,70000
P=namedtuple('P','b s wc bc ep kp')
I=P(' '*20+' rnbqkbnr\n pppppppp\n'+' ........\n'*4+' PPPPPPPP\n RNBQKBNR\n'+' '*20,0,(1,1),(1,1),0,0)
def rot(p,z=0):return P(p.b[::-1].swapcase(),-p.s,p.bc,p.wc,0 if z or not p.ep else 119-p.ep,0 if z or not p.kp else 119-p.kp)
def gen(p):
 b=p.b
 for i,q in enumerate(b):
  if not q.isupper():continue
  for d in D[q]:
   j=i+d
   while 1:
    t=b[j]
    if t.isspace()or t.isupper():break
    if q=='P':
     if d in(N,N+N)and t!='.':break
     if d==N+N and(i<A1+N or b[i+N]!='.'):break
     if d in(N+W,N+O)and t=='.'and j not in(p.ep,p.kp,p.kp-1,p.kp+1):break
     if A8<=j<=H8:yield i,j,'Q';yield i,j,'N';break
    yield i,j,''
    if q in'PNK'or t.islower():break
    if i==A1 and b[j+O]=='K'and p.wc[0]:yield j+O,j+W,''
    if i==H1 and b[j+W]=='K'and p.wc[1]:yield j+W,j+O,''
    j+=d
def val(p,m):
 i,j,r=m;q=p.b[i];t=p.b[j];s=T[q][j]-T[q][i]
 if t.islower():s+=T[t.upper()][119-j]
 if abs(j-p.kp)<2:s+=T['K'][119-j]
 if q=='K'and abs(i-j)==2:s+=T['R'][(i+j)//2]-T['R'][A1 if j<i else H1]
 if q=='P':
  if r:s+=T[r][j]-T['P'][j]
  if j==p.ep:s+=T['P'][119-j-S]
 return s
def mv(p,m,v=None):
 i,j,r=m;b=list(p.b);q=b[i];s=p.s+(val(p,m)if v is None else v);wc,bc,ep,kp=p.wc,p.bc,0,0
 b[j]=q;b[i]='.'
 if i==A1:wc=(0,wc[1])
 if i==H1:wc=(wc[0],0)
 if j==A8:bc=(bc[0],0)
 if j==H8:bc=(0,bc[1])
 if q=='K':
  wc=(0,0)
  if abs(j-i)==2:kp=(i+j)//2;b[A1 if j<i else H1]='.';b[kp]='R'
 if q=='P':
  if r:b[j]=r
  if j-i==2*N:ep=i+N
  if j==p.ep:b[j+S]='.'
 return rot(P(''.join(b),s,wc,bc,ep,kp))
def chk(p):q=rot(p,1);return any(q.b[j]=='k'for i,j,r in gen(q))
def srch(p,d,a,b,h):
 global n;n+=1
 if n>4*NB:raise OverflowError
 if p.s<=-ML:return h-MU
 if h and p in H:return 0
 q=d<=0;e=V.get((p,max(d,0)))
 if e and(e[1]==0 or e[1]>0 and e[0]>=b or e[1]<0 and e[0]<=a):return e[0]
 a0=a;best=p.s if q else-MU
 if best>=b:return best
 if d>2 and p.s>=b:
  s=-srch(rot(p,1),d-3,-b,1-b,h+1)
  if s>=b:return s
 k=K.get(p)
 for v,m in sorted(((val(p,m),m)for m in gen(p)if not q or p.b[m[1]]!='.'or m[2]),key=lambda x:(x[1]!=k,-x[0])):
  s=-srch(mv(p,m,v),d-1,-b,-max(a,best),h+1)
  if s>best:best=s;K[p]=m
  if best>=b:break
 if not q and best<-ML and not chk(p):best=0
 V[p,max(d,0)]=best,(best>=b)-(best<=a0);return best
def sq(u,f):x=10*(10-int(u[1]))+'abcdefgh'.index(u[0])+1;return 119-x if f else x
def u2m(u,f):return sq(u[:2],f),sq(u[2:4],f),u[4:].upper()
def pick(g):
 global n,H,K,V
 p=I;H=set();f=0
 for u in g['moves']:p=mv(p,u2m(u,f));f^=1;H.add(p)
 H.discard(p);K={};V={};n=0
 ms=[u2m(u,f)for u in g['legal_moves']];bm=ms[0];d=1
 try:
  while n<NB and d<30:
   best=-MU
   for m in sorted(ms,key=lambda m:(m!=bm,-val(p,m))):
    s=-srch(mv(p,m),d-1,-MU,-best,1)
    if s>best:best=s;c=m
   bm=c;d+=1
 except(OverflowError,RecursionError):pass
 return ''.join('abcdefgh'[x%10-1]+str(10-x//10)for x in(bm[:2]if not f else(119-bm[0],119-bm[1])))+bm[2].lower()
NB=40000
if __name__=='__main__':
 while 1:
  g=post('/game',{})
  if g['status']=='done':break
  while g['status']=='your_move':
   try:m=pick(g)
   except Exception:m=g['legal_moves'][0]
   g=post('/move',{'game':g['game'],'move':m})
