import sys, json, re; sys.path.insert(0,'/home/claude/w'); from catA import *
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items() if not k.startswith('_')}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, float): return round(o, 5)
    return o
def img(f, p, clip):
    return image_of(getpage(f, p), pymupdf.Rect(*clip))
OUT = {}; IM = {}
def add(kind, f, p, key):
    o = {'wat': wat_chart, 'hl': hl_chart, 'dd': dd_chart, 'fx': fx_chart}[kind](f, p, key)
    o['kind'] = kind
    if kind == 'wat':
        IM[key] = o.pop('img')
    else:
        x0, y0, x1, y1 = o['_clip']; IM[key] = img(f, p, (x0, y0, x1, y1))
    if kind in ('wat', 'fx'):
        t = o['top']; o['top'] = {k: v for k, v in t.items() if not k.startswith('_')}
    OUT[key] = clean(o)
    return o
P = {'A': dict(wat=30, dd=32, todist=33, fp1=range(34, 39), acc=39, fp2=range(40, 45)),
     'B': dict(wat=68, tdph=70, hloss=71, todist=72, fp1=range(73, 78), acc=78, fp2=range(79, 84)),
     'C': dict(wat=103, rto=105, tdp=106, todist=107, fp1=range(108, 113), acc=113, fp2=range(114, 119), ldg=124),
     'D': dict(wat=142, tdph=144, hloss=145, todist=146, fp1=range(147, 152), acc=152, fp2=range(153, 158))}
for part, d in P.items():
    add('wat', F625, d['wat'], f'{part}_wat')
    for k in ('todist', 'tdph', 'rto', 'tdp', 'ldg'):
        if k in d: add('hl', F625, d[k], f'{part}_{k}')
    for k in ('dd', 'hloss'):
        if k in d: add('dd', F625, d[k], f'{part}_{k}')
    for k in ('fp1', 'fp2'):
        for p in d[k]:
            o = add('fx', F625, p, f'{part}_{k}_{p}'); OUT[f'{part}_{k}_{p}']['gw'] = o['gw']
    add('fx', F625, d['acc'], f'{part}_acc')
# FMS-74.5 Part D (runway, 103%, to 12,200 lb)
add('wat', F745, 63, 'C745_wat'); add('hl', F745, 65, 'C745_rto'); add('hl', F745, 66, 'C745_tdp'); add('hl', F745, 67, 'C745_todist')
add('fx', F745, 68, 'C745_fp1_68'); add('fx', F745, 69, 'C745_acc'); add('fx', F745, 70, 'C745_fp2_70')
json.dump(OUT, open('catA.json', 'w'), separators=(',', ':')); json.dump(IM, open('catA_img.json', 'w'))
import os; print(len(OUT), os.path.getsize('catA.json')//1024, 'KB', os.path.getsize('catA_img.json')//1024, 'KB img')
for k, o in OUT.items():
    if o['kind'] in ('wat', 'fx'):
        t = o['top']; print(f"{k:14s} {o.get('fig',''):6s} gw={o.get('gw')} fam={[int(x['v']) for x in t['fam']]} lim={list(t['lim'])} low={o.get('low',{}).get('kind') if o.get('low') else (o.get('wind') and 'wind')} ng={len(o['low']['guides']) if o.get('low') else (len(o['wind']['guides']) if o.get('wind') else '')} xres={round(t['xres'] or 0,3)} yres={round(t['yres'] or 0,1)}")
    elif o['kind'] == 'hl': print(f"{k:14s} {o['fig']:6s} PA={[int(x['v']) for x in o['pa']]} maxoat={bool(o['maxoat'])} lines={len(o['lines'])} res={round(o['xResL'],3)},{round(o['xResR'],3)}")
    else: print(f"{k:14s} {o['fig']:6s} PA={[int(x['v']) for x in o['pa']]} guides={len(o['guides'])} DA={[int(x['v']) for x in o['da']]}")
