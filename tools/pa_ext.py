import pymupdf, numpy as np, json, sys
F='/mnt/user-data/uploads/3464f03d-412EPIFM05S04.pdf'
SC=6.0  # px per pt
def render(p, clip):
    pg=pymupdf.open(F)[p-1]
    pix=pg.get_pixmap(matrix=pymupdf.Matrix(SC,SC),clip=pymupdf.Rect(*clip),colorspace=pymupdf.csGRAY)
    a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width).astype(float)
    return a
def frame(a, thr=110):
    d=a<thr
    cols=d.mean(0); rows=d.mean(1)
    return cols, rows
if __name__=='__main__':
    for p,clip in [(7,(70,330,580,660)),(8,(35,340,545,665))]:
        a=render(p,clip); cols,rows=frame(a)
        vc=np.where(cols>0.6)[0]; vr=np.where(rows>0.6)[0]
        # group consecutive
        def groups(ix):
            g=[];
            for i in ix:
                if g and i-g[-1][-1]<=2: g[-1].append(i)
                else: g.append([i])
            return [(np.mean(x)/SC+clip[0] if True else 0, len(x)) for x in g]
        print('page',p,a.shape)
        print(' vertical lines (pt, width px):',[(round(x,1),w) for x,w in groups(vc)])
        print(' horizontal lines:',[(round(y/SC+clip[1]-clip[0]+clip[0],1) if False else round(np.mean([0]),1),0) for _ in []], [ (round(np.mean(x)/SC+clip[1],1),len(x)) for x in [list(gr) for gr in [ [i for i in vr] ]] ][:1])
        g=[]; 
        for i in vr:
            if g and i-g[-1][-1]<=2: g[-1].append(i)
            else: g.append([i])
        print(' horiz:',[(round(np.mean(x)/SC+clip[1],1),len(x)) for x in g])

def track(p, clip, top, bot, xsplit, thr=150):
    a=render(p,clip); H,W=a.shape
    toy=lambda y:int((y-clip[1])*SC); tox=lambda x:int((x-clip[0])*SC)
    y0,y1=toy(top)+8,toy(bot)-8
    d=a<thr
    colfrac=d[y0:y1].mean(0); gridcol=colfrac>0.35
    rowfrac=d[:, tox(clip[0]+5):].mean(1); gridrow=rowfrac>0.35
    tracks=[]
    for y in range(y1,y0,-3):
        if gridrow[max(0,y-3):y+4].any(): continue
        r=d[y].copy(); r[gridcol]=False
        # dilate gridcol neighbours
        xs=np.where(r)[0]; cents=[]
        if len(xs):
            st=xs[0]; pv=xs[0]
            for x in list(xs[1:])+[10**9]:
                if x-pv>2:
                    if pv-st<=10: cents.append((st+pv)/2)
                    st=x
                pv=x
        used=set()
        for t in tracks:
            if t['dead']: continue
            ys,xs_=t['y'],t['x']
            if len(xs_)>=4: sl=(xs_[-1]-xs_[-4])/(ys[-1]-ys[-4])
            else: sl=t.get('sl',0)
            pred=xs_[-1]+sl*(y-ys[-1])
            best=None;bd=5
            for i,c in enumerate(cents):
                if i in used: continue
                if abs(c-pred)<bd: bd=abs(c-pred);best=i
            if best is not None: used.add(best); t['y'].append(y); t['x'].append(cents[best]); t['miss']=0
            else:
                t['miss']+=1
                if t['miss']>25: t['dead']=True
        for i,c in enumerate(cents):
            if i not in used: tracks.append(dict(y=[y],x=[c],miss=0,dead=False))
    out=[]
    for t in tracks:
        if len(t['y'])<40: continue
        Y=np.array(t['y'])/SC+clip[1]; X=np.array(t['x'])/SC+clip[0]
        A=np.polyfit(Y,X,1); res=np.abs(np.polyval(A,Y)-X).max()
        span=Y.max()-Y.min()
        if span<0.2*(bot-top) or res>0.6: continue
        out.append(dict(a=A[0],b=A[1],ytop=Y.min(),ybot=Y.max(),n=len(Y),res=res))
    # dedupe near-identical
    out.sort(key=lambda o:o['a']*((top+bot)/2)+o['b'])
    D=[]
    for o in out:
        xm=o['a']*((top+bot)/2)+o['b']
        if D and abs(xm-(D[-1]['a']*((top+bot)/2)+D[-1]['b']))<1.0 and abs(o['a']-D[-1]['a'])<0.05:
            if o['n']>D[-1]['n']: D[-1]=o
            continue
        D.append(o)
    return D

if __name__=='__main__' and len(sys.argv)>1:
    for p,clip,top,bot,xs in [(7,(70,330,580,660),338.8,652.9,213.3),(8,(35,340,545,665),346.0,658.2,225.7)]:
        L=track(p,clip,top,bot,xs); ym=(top+bot)/2
        print('page',p,len(L))
        for o in L: print('  xmid %.1f slope %.4f y %.0f-%.0f n %d res %.2f %s'%(o['a']*ym+o['b'],o['a'],o['ytop'],o['ybot'],o['n'],o['res'],'L' if o['a']*ym+o['b']<xs else 'R'))

def hough(p, clip, top, bot, xl, xr, thr=150, smin=-0.75, smax=-0.15, ds=0.0015):
    a=render(p,clip); H,W=a.shape
    toy=lambda y:(y-clip[1])*SC; tox=lambda x:(x-clip[0])*SC
    y0,y1=int(toy(top))+6,int(toy(bot))-6
    d=(a<thr)
    colfrac=d[y0:y1].mean(0); d[:,colfrac>0.3]=False
    # widen grid column mask by 1px
    gc=np.where(colfrac>0.3)[0]
    for c in gc:
        d[:,max(0,c-1):c+2]=False
    rowfrac=d[:,int(tox(xl)):int(tox(xr))].mean(1)
    for r in np.where(rowfrac>0.3)[0]: d[max(0,r-1):r+2,:]=False
    D=d[y0:y1].astype(np.int32); R=D.shape[0]; ys=np.arange(R)
    slopes=np.arange(smin,smax,ds); acc=np.zeros((len(slopes),W),np.int32); cnt=np.zeros((len(slopes),W),np.int32)
    XL,XR=int(tox(xl))+3,int(tox(xr))-3
    for i,s in enumerate(slopes):
        # line through (x0 at row 0) : x = x0 + s*row  ; s in px/px
        sh=np.round(s*ys).astype(int)
        A=np.zeros(W,np.int32); C=np.zeros(W,np.int32)
        for r in range(R):
            k=sh[r]
            # x0 = x - k for all x in row
            row=D[r]
            if k>=0: A[:W-k]+=row[k:]
            else: A[-k:]+=row[:W+k]
            # coverage: rows where x0+k inside [XL,XR]
            lo=max(XL-k,0); hi=min(XR-k,W)
            if hi>lo: C[lo:hi]+=1
        acc[i]=A; cnt[i]=C
    frac=np.where(cnt>0.15*R, acc/np.maximum(cnt,1), 0)
    # non-max suppression
    lines=[]
    F=frac.copy()
    while True:
        i,x=np.unravel_index(np.argmax(F),F.shape)
        if F[i,x]<0.55: break
        s=slopes[i]
        lines.append(dict(s=s,x0=x,frac=float(F[i,x]),cov=int(cnt[i,x])))
        F[max(0,i-40):i+41, max(0,x-10):x+11]=0
    out=[]
    for L in lines:
        # convert to page coords: x(y) = a*y + b
        a_=L['s']; x0=L['x0']/SC+clip[0]; ytop=(y0)/SC+clip[1]
        out.append(dict(a=a_, b=x0-a_*ytop, frac=L['frac'], cov=L['cov']/SC))
    return out

if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='h':
    import time
    for p,clip,top,bot,xs,xl,xr in [(7,(70,330,580,660),338.8,652.9,213.3,78.2,572.2),(8,(35,340,545,665),346.0,658.2,225.7,41.6,532.4)]:
        t=time.time(); L=hough(p,clip,top,bot,xl,xr); ym=(top+bot)/2
        L.sort(key=lambda o:o['a']*ym+o['b'])
        print('page',p,len(L),'%.1fs'%(time.time()-t))
        for o in L: print('  xmid %.1f  slope %.4f  frac %.2f  cov %.0f'%(o['a']*ym+o['b'],o['a'],o['frac'],o['cov']))

def hough2(p, clip, top, bot, xl, xr, thr=90, smin=-0.7, smax=-0.15, ds=0.002, minfrac=0.45):
    a=render(p,clip); H,W=a.shape
    toy=lambda y:(y-clip[1])*SC; tox=lambda x:(x-clip[0])*SC
    y0,y1=int(toy(top))+6,int(toy(bot))-6
    d=(a<thr)
    colfrac=d[y0:y1].mean(0)
    for c in np.where(colfrac>0.3)[0]: d[:,max(0,c-2):c+3]=False
    rowfrac=d[:,int(tox(xl)):int(tox(xr))].mean(1)
    for r in np.where(rowfrac>0.3)[0]: d[max(0,r-2):r+3,:]=False
    D=d[y0:y1]; R=D.shape[0]; ys=np.arange(R)
    XL,XR=int(tox(xl))+4,int(tox(xr))-4
    slopes=np.arange(smin,smax,ds); res=[]
    pts_y,pts_x=np.nonzero(D)
    keep=(pts_x>=XL)&(pts_x<=XR); pts_y,pts_x=pts_y[keep],pts_x[keep]
    acc=np.zeros((len(slopes),W),np.int32); cov=np.zeros((len(slopes),W),np.int32)
    xs0=np.arange(W)
    for i,s in enumerate(slopes):
        x0=np.round(pts_x-s*pts_y).astype(int); ok=(x0>=0)&(x0<W)
        acc[i]=np.bincount(x0[ok],minlength=W)[:W]
        # coverage rows: x0+s*r in [XL,XR]
        # r range: (XL-x0)/s .. (XR-x0)/s  (s<0)
        ra=(XR-xs0)/s; rb=(XL-xs0)/s
        lo=np.clip(np.minimum(ra,rb),0,R); hi=np.clip(np.maximum(ra,rb),0,R)
        cov[i]=(hi-lo).astype(int)
    frac=np.where(cov>0.12*R, acc/np.maximum(cov,1), 0)
    F=frac.copy(); out=[]
    while True:
        i,x=np.unravel_index(np.argmax(F),F.shape)
        if F[i,x]<minfrac: break
        out.append((slopes[i],x,F[i,x],cov[i,x]))
        # suppress all lines that are close to this one anywhere along y
        for j,s in enumerate(slopes):
            xa=x+slopes[i]*np.array([0,R/2,R]); 
            lo=int(min(xa-s*np.array([0,R/2,R]))-60); hi=int(max(xa-s*np.array([0,R/2,R]))+60)
            F[j,max(0,lo):max(0,hi)]=0
    L=[]
    for s,x,f,c in out:
        # refine: least squares on pixels within 6px
        dist=np.abs(pts_x-(x+s*pts_y)); m=dist<6
        A=np.polyfit(pts_y[m],pts_x[m],1)
        ytop=y0/SC+clip[1]
        a_=A[0]; b_=A[1]/SC+clip[0]-a_*ytop
        L.append(dict(a=a_,b=b_,frac=float(f),cov=c/SC))
    return L

def refine(p, clip, top, bot, xl, xr, lines, n_expect, thr=110, band=2.0):
    a=render(p,clip)
    toy=lambda y:(y-clip[1])*SC; tox=lambda x:(x-clip[0])*SC
    y0,y1=int(toy(top))+6,int(toy(bot))-6
    d=(a<thr)
    colfrac=d[y0:y1].mean(0)
    for c in np.where(colfrac>0.3)[0]: d[:,max(0,c-3):c+4]=False
    rowfrac=d[:,int(tox(xl)):int(tox(xr))].mean(1)
    for r in np.where(rowfrac>0.3)[0]: d[max(0,r-3):r+4,:]=False
    L=sorted(lines,key=lambda o:o['a']*bot+o['b'])
    # extrapolate missing at high end
    while len(L)<n_expect:
        o1,o2=L[-2],L[-1]
        L.append(dict(a=2*o2['a']-o1['a'], b=None, xb=2*(o2['a']*bot+o2['b'])-(o1['a']*bot+o1['b'])))
        L[-1]['b']=L[-1]['xb']-L[-1]['a']*bot
    out=[]
    for o in L:
        A=np.array([0.0,o['a'],o['b']])
        for it in range(3):
            Y=[];X=[]
            for r in range(y0,y1,2):
                yy=r/SC+clip[1]; xc=np.polyval(A,yy)
                if xc<xl+1 or xc>xr-1: continue
                c0=int(tox(xc-band)); c1=int(tox(xc+band))
                seg=d[r,max(0,c0):max(0,c1)]
                idx=np.where(seg)[0]
                if len(idx)==0 or len(idx)>14: continue
                # contiguous run nearest center
                Y.append(yy); X.append((max(0,c0)+idx.mean())/SC+clip[0])
            Y=np.array(Y);X=np.array(X)
            if len(Y)<20: break
            deg=2 if (Y.max()-Y.min())>120 else 1
            B=np.polyfit(Y,X,deg); B=np.concatenate([np.zeros(3-len(B)),B])
            res=X-np.polyval(B,Y); keep=np.abs(res)<max(0.6,2.5*res.std())
            B=np.polyfit(Y[keep],X[keep],deg); A=np.concatenate([np.zeros(3-len(B)),B])
            band=1.5
        out.append(dict(c=A.tolist(),n=int(len(Y)),ymin=float(Y.min()) if len(Y) else 0,ymax=float(Y.max()) if len(Y) else 0,rms=float(np.sqrt(np.mean((X-np.polyval(A,Y))**2))) if len(Y) else 9))
    return out
