import json, numpy as np, pymupdf, base64, io
from pa_ext import hough2, refine, render, SC
from catA import image_of
F='/mnt/user-data/uploads/3464f03d-412EPIFM05S04.pdf'
D=pymupdf.open(F)
CFG=[dict(key='pwr_mgt',page=7,clip=(70,330,580,660),top=338.8,bot=652.9,xl=78.2,xm=257.9,xr=550.0,
          tq=[(40,78.2),(50,123.2),(60,168.4),(70,213.3)], out=[(500,257.9),(550,303.0),(600,348.2),(650,393.0),(700,437.6),(750,482.6),(800,527.7),(850,572.2)],
          lim=825, unit='°C', name='MGT', im=(70,330,580,668)),
     dict(key='pwr_ng',page=8,clip=(35,340,545,665),top=346.0,bot=658.2,xl=41.6,xm=287.1,xr=495.5,
          tq=[(40,41.6),(50,103.1),(60,164.2),(70,225.7)], out=[(85,287.1),(90,348.1),(95,409.5),(100,471.1),(105,532.4)],
          lim=102.0, unit='%', name='Ng', im=(35,340,545,672))]
PA=[10000,8000,6000,4000,2000,0,-2000]; OAT=list(range(-50,51,10))
out={}; imgs={}
for c in CFG:
    p,clip,top,bot=c['page'],c['clip'],c['top'],c['bot']
    Ll=sorted(hough2(p,clip,top,bot,c['xl'],c['xm']+40,minfrac=0.35),key=lambda o:o['a']*bot+o['b'])[:7]
    Lr=hough2(p,clip,top,bot,c['xm']-30,c['xr'],minfrac=0.35)
    left=refine(p,clip,top,bot,c['xl'],c['xr'],Ll,7)
    right=refine(p,clip,top,bot,c['xm'],c['xr'],Lr,11)
    # short lines: fixed extrapolated slope + median offset
    for i,o in enumerate(right):
        if o['n']<300:
            s1=right[i-1]['c'][1]+2*right[i-1]['c'][0]*((top+bot)/2); s0=right[i-2]['c'][1]+2*right[i-2]['c'][0]*((top+bot)/2)
            s=2*s1-s0
            a=render(p,clip); d=a<110; ys=[];xs=[]
            for yy in np.arange(o['ymin'],bot-1,0.5):
                xc=np.polyval(o['c'],yy); r=int((yy-clip[1])*SC); c0=int((xc-2-clip[0])*SC); c1=int((xc+2-clip[0])*SC)
                idx=np.where(d[r,c0:c1])[0]
                if 0<len(idx)<12: ys.append(yy); xs.append(c0/SC+clip[0]+idx.mean()/SC)
            ys=np.array(ys);xs=np.array(xs); b=np.median(xs-s*ys)
            o['c']=[0.0,float(s),float(b)]; o['fixed']=True
    if c['key']=='pwr_mgt':
        o40=right[9]['c']; sl=o40[1]+2*o40[0]*600
        right[10]['c']=[0.0,float(sl),float(516.7-sl*640)]
    fit=lambda pts:np.polyfit([q[0] for q in pts],[q[1] for q in pts],1).tolist()
    ent=dict(key=c['key'],page=p,src='BHT-412-FM-5',fig='4-1 sheet %d'%(1 if p==7 else 2),
             top=top,bot=bot,xL=c['xl'],xR=c['xr'],xM=c['xm'],
             tq=fit(c['tq']), out=fit(c['out']), lim=c['lim'], unit=c['unit'], name=c['name'],
             pa=[dict(v=v,c=o['c']) for v,o in zip(PA,left)], oat=[dict(v=v,c=o['c']) for v,o in zip(OAT,right)],
             im=[c['im'][0],c['im'][1],c['im'][2]-c['im'][0],c['im'][3]-c['im'][1]])
    out[c['key']]=ent
    imgs[c['key']]=image_of(D[p-1],pymupdf.Rect(*c['im']),sc=2.6)
    for nm,L in (('PA',left),('OAT',right)):
        print(c['key'],nm,[round(np.polyval(o['c'],(top+bot)/2),1) for o in L], [o['n'] for o in L])
# density altitude
pg=D[8]
out['da']=dict(key='da',page=9,src='BHT-412-FM-5',fig='4-2',x=[2.849,178.2+50*2.849],y=[-14.597/1000,602.9-8*(-14.597)],
               top=135.8,bot=602.9,xL=178.2,xR=491.6,im=[130,125,450,500])
out['da']['y']=[-14.597/1000, 602.9-8*14.597]
imgs['da']=image_of(pg,pymupdf.Rect(130,125,580,625),sc=2.0)
json.dump(out,open('pwr.json','w')); json.dump(imgs,open('pwr_img.json','w'))
print({k:len(v)//1000 for k,v in imgs.items()},'KB')
