import sys, json, re; sys.path.insert(0,'/home/claude/w'); from catA import *
OUT={}; IM={}
for p in range(45,50):
    o=fx_chart(F625,p,'roc_se2',matcher=assign_match); t=o['top']; key=f'roc_se2_{o["gw"]}'
    x0,y0,x1,y1=o['_clip']; IM[key]=image_of(getpage(F625,p),pymupdf.Rect(x0,y0,x1,y1))
    o['top']={k:v for k,v in t.items() if not k.startswith('_')}; o.pop('_clip'); o['key']=key; o['grp']='roc_se2'; o['src']='FMS-62.5'
    OUT[key]=o
    print(f"{key:18s} p{p} fig {o['fig']} fam={[int(x['v']) for x in t['fam']]} lim={list(t['lim'])} unl={t['unl']} xres={round(t['xres'] or -1,2)} yres={round(t['yres'] or -1,1)}")
json.dump(OUT,open('se.json','w'),separators=(',',':')); json.dump(IM,open('se_img.json','w'))
