import sys,json,types; sys.path.insert(0,'/home/claude/w')
import catA, ext2
from catA import *
MD='/mnt/user-data/uploads/c87318f5-BHT-412-MD-5_-_4_-_Expanded_Performance.pdf'
BC=types.SimpleNamespace(); exec(open('/home/claude/w/build_catA.py').read().split('\nP = {')[0],BC.__dict__)
class Proxy:
    def __init__(s,pg): s._pg=pg; s._d=None
    def __getattr__(s,k): return getattr(s._pg,k)
    def get_drawings(s,*a,**k):
        if s._d is None:
            D=s._pg.get_drawings()
            for d in D:
                w=d.get('width') or 0
                if 0.1<w<0.2: d['width']=0.05
                elif 1.0<w<1.2: d['width']=0.71
                elif 0.3<w<0.4: d['width']=0.71
            s._d=D
        return s._d
og=catA.getpage
catA.getpage=lambda f,p:(Proxy(og(f,p)) if f==MD and p in (49,50) else og(f,p))
# axis calibration (text on these pages is outlined): value = a*x + b
CAL={49:{'L':(602.0,1.588,60,10),'M':(617.9,15.88,8.0,0.25),'R':(903.7,15.88,0,10)},
     50:{'L':(580.8,1.544,60,10),'M':(596.2,15.44,8.0,0.25),'R':(874.1,15.44,0,10)}}
cur={'p':None}
ocal=catA.calib
def calib(W,panel,side,*a,**k):
    p=cur['p']
    if p in CAL:
        x0=panel[0]
        key='L' if abs(x0-min(v[0] for v in [(443.2,),(426.4,)]))<60 and x0<CAL[p]['M'][0]-50 else ('M' if abs(x0-CAL[p]['M'][0])<2 else 'R')
        if key=='L': X,ppu,v,_=CAL[p]['L']; a_=1/ppu; return ((a_, v-X*a_, 0.0),None)
        X,ppg,v,step=CAL[p][key]; a_=step/ppg; return ((a_, v-X*a_, 0.0),None)
    return ocal(W,panel,side,*a,**k)
catA.calib=calib
BC.dd_chart=catA.dd_chart; BC.getpage=catA.getpage
BC.OUT.clear(); BC.IM.clear()
for kind,p,k in [('wat',47,'pc2_wat'),('dd',49,'pc2_dd'),('dd',50,'pc2_ddb')]:
    cur['p']=p
    o=BC.add(kind,MD,p,k); BC.OUT[k]['src']='BHT-412-MD-5'; O=BC.OUT[k]
    if kind=='wat': print(k,'fam',[f['v'] for f in O['top']['fam']],'wind',[l.get('v') for l in O['wind']['lims']])
    else: print(k,'xOat',O['xOat'],'xGw',O['xGw'],'xR',O['xR'],'pa',[f['v'] for f in O['pa']],'da',[f['v'] for f in O['da']],'guides',len(O['guides']),'M',O['M'])
json.dump(BC.OUT,open('pc2.json','w'),separators=(',',':')); json.dump(BC.IM,open('pc2_img.json','w'))
# outlined labels: assign the PA (left) and DA (right) families by position
for p,k in [(49,'pc2_dd'),(50,'pc2_ddb')]:
    cur['p']=p; pg=catA.getpage(MD,p); Ps=catA.split_panels(pg,sorted(ext2.find_panels(pg),key=lambda q:q[0])); L,M,R=Ps
    s,_,_=ext2.panel_items(pg,L); pa=sorted([c for c in s if catA.plen(c)>20],key=lambda c:min(q[1] for q in c))
    s,_,_=ext2.panel_items(pg,R); da=sorted([c for c in s if catA.plen(c)>100 and abs(c[0][0]-R[0])<2],key=lambda c:-c[0][1])
    O=BC.OUT[k]
    O['pa']=[dict(v=v,pts=[[round(a,2),round(b,2)] for a,b in sorted(c)]) for v,c in zip([0,2000,4000,6000],pa)]
    O['da']=[dict(v=v,pts=[[round(a,2),round(b,2)] for a,b in sorted(c)]) for v,c in zip([1000,2000,3000,4000,5000,6000],da)]
    print(k,'pa',len(O['pa']),'da',len(O['da']))
json.dump(BC.OUT,open('pc2.json','w'),separators=(',',':'))

# fixes: guide starts sit a hair right of the panel edge; "20 AND WARMER" wind limit (no headwind credit) is the panel top
O=json.load(open('pc2.json'))
for k in ('pc2_dd','pc2_ddb'): O[k]['M'][0]=round(max(g[0][0] for g in O[k]['guides'])+0.02,2)
w=O['pc2_wat']['wind']
if not any(l.get('v')==20 for l in w['lims']): w['lims'].insert(0,{'y':w['panel'][1],'lab':'20 AND WARMER','v':20.0})
json.dump(O,open('pc2.json','w'),separators=(',',':'))
