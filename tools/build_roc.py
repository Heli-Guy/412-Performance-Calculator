import sys, json, re; sys.path.insert(0,'/home/claude/w'); from catA import *
FM=U+'3464f03d-412EPIFM05S04.pdf'; WH=U+'453da255-412FMS0105.pdf'
L=[]
for i,p in enumerate(range(25,37)): L.append((FM,p,'roc_top_'+('off' if i<6 else 'on')))
for i,p in enumerate(range(37,49)): L.append((FM,p,'roc_mcp_'+('off' if i<6 else 'on')))
for p in range(49,55): L.append((FM,p,'roc_oei_off'))
for p in range(21,27): L.append((WH,p,'roc_top_win'))
for p in range(27,33): L.append((WH,p,'roc_mcp_win'))
for p,k in [(35,'roc_top_off'),(36,'roc_top_on'),(37,'roc_mcp_off'),(38,'roc_mcp_on'),(39,'roc_oei_off'),(50,'roc_top_win'),(51,'roc_mcp_win')]: L.append((F745,p,k))
SRC={FM:'BHT-412-FM-5',WH:'FMS-1.5',F745:'FMS-74.5'}
OUT={}; IM={}
for f,p,grp in L:
    o=fx_chart(f,p,grp,matcher=assign_match); t=o['top']; key=f'{grp}_{o["gw"]}'
    x0,y0,x1,y1=o['_clip']; IM[key]=image_of(getpage(f,p),pymupdf.Rect(x0,y0,x1,y1))
    o['top']={k:v for k,v in t.items() if not k.startswith('_')}; o.pop('_clip'); o['key']=key; o['grp']=grp; o['src']=SRC[f]
    txt=getpage(f,p).get_text(); m=re.search(r'DECREASE (\d+) FT/MIN',txt); o['doors']=int(m.group(1)) if m else None
    OUT[key]=o
    print(f"{key:20s} {o['src']:12s} p{p:<3} fig {o['fig']:5s} fam={[int(x['v']) for x in t['fam']]} lim={list(t['lim'])} unl={t['unl']} xres={round(t['xres'] or -1,2)} yres={round(t['yres'] or -1,1)} doors={o['doors']}")
json.dump(OUT,open('roc.json','w'),separators=(',',':')); json.dump(IM,open('roc_img.json','w'))
import os; print(len(OUT), os.path.getsize('roc.json')//1024,'KB', os.path.getsize('roc_img.json')//1024,'KB img')
