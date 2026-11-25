import sys,json; sys.path.insert(0,'/home/claude/w'); from catA import *
F805='/mnt/user-data/uploads/703cd4c8-412FMS8005.pdf'
OUT={};IM={}
for p,k in [(11,'mt_std'),(26,'mt_p9')]:
    o=hl_chart(F805,p,k); x0,y0,x1,y1=o.pop('_clip'); IM[k]=image_of(getpage(F805,p),pymupdf.Rect(x0,y0,x1,y1)); o['src']='FMS-80.5'
    OUT[k]=o; print(k,o['fig'],'xOat',[round(v,4) for v in o['xOat']],o['xResL'],'xR',[round(v,4) for v in o['xR']],round(o['xResR'],3),'PA',[x['v'] for x in o['pa']],'maxoat',bool(o['maxoat']),'lines',len(o['lines']),'hd',o['hdLim'])
json.dump(OUT,open('mt.json','w'),separators=(',',':')); json.dump(IM,open('mt_img.json','w'))
