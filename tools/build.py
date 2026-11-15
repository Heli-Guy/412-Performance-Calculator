import sys,json,base64,io,math; sys.path.insert(0,'.'); from ext import *; from hovlist import L
from PIL import Image
U='/mnt/user-data/uploads/'
SRC={'3464f03d-412EPIFM05S04.pdf':'BHT-412-FM-5','67962796-412EPIFMS3505.pdf':'FMS-35.5','bd6642ab-412EPIFMS0905.pdf':'FMS-9.5',
     '252bae3c-412FMS7405.pdf':'FMS-74.5','703cd4c8-412FMS8005.pdf':'FMS-80.5','453da255-412FMS0105.pdf':'FMS-1.5','8cbc5859-412EPIFM05S01.pdf':'BHT-412-FM-5'}
def R(p): return [round(p[0],2),round(p[1],2)]
def thin(pts):
    out=[pts[0]]
    for p in pts[1:]:
        if math.dist(p,out[-1])>0.25: out.append(p)
    if out[-1]!=pts[-1]: out.append(pts[-1])
    return [R(p) for p in out]
def xat(pts,y):
    for i in range(len(pts)-1):
        (x0,y0),(x1,y1)=pts[i],pts[i+1]
        if min(y0,y1)<=y<=max(y0,y1) and y1!=y0: return x0+(y-y0)*(x1-x0)/(y1-y0)
def yat(pts,x):
    for i in range(len(pts)-1):
        (x0,y0),(x1,y1)=pts[i],pts[i+1]
        if min(x0,x1)<=x<=max(x0,x1) and x1!=x0: return y0+(x-x0)*(y1-y0)/(x1-x0)
charts={}; imgs={}
todo=L+[('8cbc5859-412EPIFM05S01.pdf',19,'wat_fm'),('252bae3c-412FMS7405.pdf',13,'wat_gw'),('67962796-412EPIFMS3505.pdf',10,'wat_p9')]
for f,p,k in todo:
    r=hover(U+f,p); pg=pymupdf.open(U+f)[p-1]; txt=pg.get_text()
    fig=re.search(r'Figure ([0-9A-Z-]+)\.\s+([^\n]*)',txt)
    pa={}
    for x in r['pa']: pa.setdefault(x['v'],x['pts'])
    oat={}
    for x in r['oat']: oat.setdefault(x['v'],x['pts'])
    dl=[d for d in r['dashed'] if len(d)>1 and sum(q[0] for q in d)/len(d)<r['xSplit']]
    dr=[d for d in r['dashed'] if len(d)>1 and sum(q[0] for q in d)/len(d)>=r['xSplit']]
    C=dict(src=SRC[f],page=p,fig=fig.group(1) if fig else '',title=(fig.group(2).strip() if fig else ''),
        xOat=[round(r['xOat'][0],7),round(r['xOat'][1],5)],xGw=[round(r['xGw'][0],5),round(r['xGw'][1],3)],
        yTop=round(r['yTop'],2),yBot=round(r['yBot'],2),xL=round(r['xL'],2),xR=round(r['xR'],2),xSplit=round(r['xSplit'],2),
        pa=[dict(v=v,pts=thin(pts)) for v,pts in sorted(pa.items())],
        oat=[dict(v=v,pts=thin(pts)) for v,pts in sorted(oat.items())],
        paMax=thin(sorted([q for d in dl for q in d],key=lambda q:q[1])) if dl else None, oatMax=thin(sorted([q for d in dr for q in d],key=lambda q:q[1])) if dr else None,
        tol=next((thin(o['pts']) for o in r['other'] if o['name']=='tol'),None),
        maxgw=next((thin(o['pts']) for o in r['other'] if o['name']=='maxgw'),None),
        areaB=[thin(g) for g in r['gray'] if len(g)>3],
        hdLim=int(re.search(r'(\d+),?(\d+) FT H',txt.replace('\n',' ')).group(0).replace(',','').split()[0]) if re.search(r'(\d+),?(\d+) FT H',txt.replace('\n',' ')) else None,
        hdr=[l for l in txt.split('\n') if re.search(r'POWER|RPM|SKID|HEATER|°C$|PASSENGER|EXTERNAL|EHP',l) and len(l)<60][:8],
        oatRange=[float(a) for a in re.search(r'(-?\d+) TO (-?\d+) ?°C',txt).groups()] if re.search(r'(-?\d+) TO (-?\d+) ?°C',txt) else None,
        notes=[' '.join(m.split()) for m in re.findall(r'(?:FOR POINTS ABOVE|NOTE: THIS DATA)[^\n]*(?:\n[A-Z0-9][^\n]*){0,3}',txt)])
    # Hd calibration from PA lines at ISA temp
    pts=[]
    for x in C['pa']:
        isa=15-1.98*x['v']/1000; X=(isa-C['xOat'][1])/C['xOat'][0]; y=yat(x['pts'],X)
        if y is not None: pts.append((x['v'],y))
    if len(pts)>=3:
        a,b=linfit([(y,v) for v,y in pts]); C['hdY']=[round(a,4),round(b,2)]  # Hd = a*y+b
    # image crop
    clip=pymupdf.Rect(r['xL']-40,r['yTop']-48,r['xR']+42,r['yBot']+34); C['im']=[round(clip.x0,2),round(clip.y0,2),round(clip.width,2),round(clip.height,2)]
    pix=pg.get_pixmap(matrix=pymupdf.Matrix(2.6,2.6),clip=clip,colorspace=pymupdf.csGRAY)
    im=Image.open(io.BytesIO(pix.tobytes('png'))).quantize(16)
    b=io.BytesIO(); im.save(b,'PNG',optimize=True); imgs[k]='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
    charts[k]=C
json.dump(charts,open('charts412.json','w'),separators=(',',':'))
json.dump(imgs,open('imgs412.json','w'))
import os; print(len(charts), os.path.getsize('charts412.json')//1024,'KB data', os.path.getsize('imgs412.json')//1024,'KB imgs')
for k in ['fm_std_100_oge_top_off_pos','wat_gw','gw_ext_103_ige_top_on']: c=charts[k]; print(k,c['fig'],c['hdLim'],c.get('hdY'),c['hdr'],c['notes'])
