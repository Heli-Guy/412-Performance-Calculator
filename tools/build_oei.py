import json, pymupdf, sys; sys.path.insert(0,'/home/claude/w'); from catA import image_of
MD='/mnt/user-data/uploads/c87318f5-BHT-412-MD-5_-_4_-_Expanded_Performance.pdf'
d=pymupdf.open(MD)
def bez(p0,p1,p2,p3,n=8):
    return [((1-t)**3*p0.x+3*(1-t)**2*t*p1.x+3*(1-t)*t*t*p2.x+t**3*p3.x,(1-t)**3*p0.y+3*(1-t)**2*t*p1.y+3*(1-t)*t*t*p2.y+t**3*p3.y) for t in [i/n for i in range(1,n+1)]]
CFG={45:dict(key='oei_2m',fig='4-3A',power='2-min OEI',w=0.71,pa=(398,24.5),gw=(398,49.0,12000),hw=(333,5.0),dg=(642,48.67),x=(183,383),max=11900,im=(140,195,500,660)),
     46:dict(key='oei_30s',fig='4-3B',power='30-sec OEI',w=0.7,pa=(390.2,24.14),gw=(414.4,48.3,12000),hw=(292.8,4.937),dg=(631.7,48.2),x=(144.6,342.1),max=12200,im=(100,190,470,650))}
OUT={}; IM={}
for p,c in CFG.items():
    pg=d[p-1]; fam=[]; skid=[]; hwc=None; mx=None
    for dr in pg.get_drawings():
        w=round(dr.get('width') or 0,2); its=dr['items']
        if abs(w-c['w'])>0.05 and not (dr.get('dashes') and str(dr.get('dashes')).startswith('[ 6')): continue
        pts=[]
        for it in its:
            if it[0]=='l': pts+= [(it[1].x,it[1].y),(it[2].x,it[2].y)] if not pts else [(it[2].x,it[2].y)]
            elif it[0]=='c': pts+= ([(it[1].x,it[1].y)] if not pts else [])+bez(*it[1:5])
        r=dr['rect']
        if dr.get('dashes') and len(its)>10 and r.y1<400: mx=pts; continue
        if len(its)>2 and r.x0>c['hw'][0]-5 and r.y0>480: hwc=pts; continue
        if len(its)>=3 and r.y1<=400 and r.height>15: fam.append(pts); continue
        if len(its)<=2 and r.y1>400 and r.height>100: skid.append(pts)
    fam.sort(key=lambda P:-max(q[0] for q in P))
    skid.sort(key=lambda P:P[0][1])  # left end: highest (smallest y) first = 4 ft
    F=[]
    for v,P in zip(range(-40,51,10),fam):
        P=sorted(P,key=lambda q:q[1]); F.append(dict(v=v,pts=[[round(a,2),round(b,2)] for a,b in P]))
    S=[dict(v=v,pts=[[round(a,2),round(b,2)] for a,b in P]) for v,P in zip([4,10,20,60],skid)]
    o=dict(key=c['key'],fig=c['fig'],power=c['power'],src='BHT-412-MD-5',page=p,fam=F,skid=S,hw=sorted([[round(a,2),round(b,2)] for a,b in hwc]),maxoat=sorted([[round(a,2),round(b,2)] for a,b in (mx or [])],key=lambda q:q[1]),
           pa=c['pa'],gw=c['gw'],hwx=c['hw'],dg=c['dg'],xr=c['x'],max=c['max'],im=[c['im'][0],c['im'][1],c['im'][2]-c['im'][0],c['im'][3]-c['im'][1]],yBot=c['pa'][0])
    OUT[c['key']]=o; IM[c['key']]=image_of(pg,pymupdf.Rect(*c['im']),sc=2.2)
    print(c['key'],'fam',len(F),'skid',len(S),'hw',len(hwc or []),'max',len(mx or []))
json.dump(OUT,open('oei.json','w'),separators=(',',':')); json.dump(IM,open('oei_img.json','w'))
