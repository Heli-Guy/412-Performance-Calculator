"""Generic vector extractor for Bell 412 hover-ceiling style charts.
Returns page-coordinate polylines + calibrations; roles assigned by rules."""
import pymupdf, re, math, json, sys
from statistics import median

NUM = re.compile(r'^-?\d{1,2}(,\d{3})?$|^-?\d{1,5}$')

def bez(p0, p1, p2, p3, n=8):
    out = []
    for i in range(1, n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0.x+3*u*u*t*p1.x+3*u*t*t*p2.x+t**3*p3.x, u**3*p0.y+3*u*u*t*p1.y+3*u*t*t*p2.y+t**3*p3.y))
    return out

def subpaths(d):
    """split a drawing into continuous point chains"""
    paths, cur, last = [], [], None
    for it in d['items']:
        if it[0] == 're':
            r = it[1]; paths.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)]); continue
        if it[0] == 'qu':
            q = it[1]; paths.append([tuple(q.ul), tuple(q.ur), tuple(q.lr), tuple(q.ll), tuple(q.ul)]); continue
        a = it[1]
        if last is None or math.hypot(a.x - last[0], a.y - last[1]) > 0.3:
            if cur: paths.append(cur)
            cur = [(a.x, a.y)]
        if it[0] == 'l':
            cur.append((it[2].x, it[2].y)); last = cur[-1]
        elif it[0] == 'c':
            cur += bez(it[1], it[2], it[3], it[4]); last = cur[-1]
    if cur: paths.append(cur)
    return paths

def plen(p):
    return sum(math.hypot(p[i+1][0]-p[i][0], p[i+1][1]-p[i][1]) for i in range(len(p)-1))

def dist_pt_poly(pt, poly):
    best = 1e9
    for i in range(len(poly)-1):
        ax, ay = poly[i]; bx, by = poly[i+1]
        dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
        t = 0 if L == 0 else max(0, min(1, ((pt[0]-ax)*dx+(pt[1]-ay)*dy)/L))
        best = min(best, math.hypot(ax+t*dx-pt[0], ay+t*dy-pt[1]))
    return best

def merge_chain(segs, tol=1.2, mindot=-0.2):
    """join polylines end to end into longest chains (only where exactly two ends meet)"""
    segs = [list(s) for s in segs if len(s) >= 2]
    ends = [e for s in segs for e in (s[0], s[-1])]
    def deg(p): return sum(1 for e in ends if math.dist(e, p) < tol)
    def dirv(a, b):
        d = math.dist(a, b); return ((b[0]-a[0])/d, (b[1]-a[1])/d) if d > 1e-6 else None
    def smooth(c, ss):
        # c ends where ss starts: direction of c's last piece vs ss's first piece
        k = len(c)-2
        while k > 0 and math.dist(c[k], c[-1]) < 1.5: k -= 1
        m = 1
        while m < len(ss)-1 and math.dist(ss[0], ss[m]) < 1.5: m += 1
        u, v = dirv(c[k], c[-1]), dirv(ss[0], ss[m])
        return u is None or v is None or (u[0]*v[0]+u[1]*v[1]) > mindot
    out = []
    while segs:
        c = segs.pop(0); grown = True
        while grown:
            grown = False
            for i, s in enumerate(segs):
                for rev_s in (False, True):
                    ss = s[::-1] if rev_s else s
                    if math.dist(c[-1], ss[0]) < tol and deg(ss[0]) == 2 and smooth(c, ss): c = c + ss[1:]; segs.pop(i); grown = True; break
                    if math.dist(c[0], ss[-1]) < tol and deg(ss[-1]) == 2 and smooth(ss, c): c = ss[:-1] + c; segs.pop(i); grown = True; break
                if grown: break
        out.append(c)
    return out

def dashes_to_line(paths):
    """filled dash shapes -> ordered centroid polyline"""
    cs = []
    for p in paths:
        if len(p) < 3: continue
        xs = [q[0] for q in p]; ys = [q[1] for q in p]
        if max(xs)-min(xs) > 25 or max(ys)-min(ys) > 25: continue
        cs.append((sum(xs)/len(xs), sum(ys)/len(ys)))
    cs.sort(key=lambda q: q[1])
    return cs

def texts(pg):
    T = []
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            s = ''.join(sp['text'] for sp in l['spans']).strip()
            if s:
                bb = l['bbox']; T.append(dict(s=s, dir=l['dir'], c=((bb[0]+bb[2])/2, (bb[1]+bb[3])/2), bb=bb))
    return T

def numval(s):
    s = s.replace(',', '').replace('−', '-').replace('–', '-')
    if s.upper() in ('SEA LEVEL', 'SL'): return 0
    try: return float(s)
    except: return None

def multival(s):
    s = s.replace('−', '-').replace('–', '-').replace(' ', '')
    if s.upper() in ('SEALEVEL', 'SL'): return [0]
    parts = re.split(r',(?=-)|,(?=\d{1,2}$)', s) if re.fullmatch(r'-?\d{1,2}(,-?\d{1,2})+', s) else [s]
    out = []
    for p in parts:
        v = numval(p)
        if v is None: return []
        out.append(v)
    return out

def linfit(pairs):
    n = len(pairs); mx = sum(p[0] for p in pairs)/n; my = sum(p[1] for p in pairs)/n
    sxx = sum((p[0]-mx)**2 for p in pairs); sxy = sum((p[0]-mx)*(p[1]-my) for p in pairs)
    a = sxy/sxx; return (a, my-a*mx)  # value = a*pos + b

def hover(fname, pno, debug=False):
    doc = pymupdf.open(fname); pg = doc[pno-1]; T = texts(pg); D = pg.get_drawings()
    # --- axes: find bottom axis titles
    oatT = [t for t in T if t['s'].startswith('OAT') and t['dir'][0] > .99]
    gwT = [t for t in T if 'LB x 1000' in t['s']]
    gwT = max(gwT, key=lambda t: t['c'][1]); oatB = max(oatT, key=lambda t: t['c'][1])
    yLab = gwT['c'][1] - 11.4
    W = [dict(s=w[4], c=((w[0]+w[2])/2, (w[1]+w[3])/2), bb=w[:4], dir=(1, 0)) for w in pg.get_text('words')]
    nums = [t for t in W if abs(t['c'][1]-yLab) < 3 and numval(t['s']) is not None]
    gwN = [(t['c'][0], numval(t['s'])*1000) for t in nums if t['c'][0] > gwT['bb'][0]-30]
    oN = [(t['c'][0], numval(t['s'])) for t in nums if t['c'][0] < gwT['bb'][0]-30]
    # dedupe GW: labels 8..12 increasing
    gwN.sort(); oN.sort()
    ag, bg = linfit(gwN); ao, bo = linfit(oN)
    # grid extents
    vg = [d for d in D if d['type'] == 's' and (d.get('width') or 0) < .1 and d['rect'].width < .5 and d['rect'].height > 100]
    yTop = median([d['rect'].y0 for d in vg]); yBot = median([d['rect'].y1 for d in vg])
    xL = min(d['rect'].x0 for d in vg); xR = max(d['rect'].x1 for d in vg)
    thick = [d for d in D if d['type'] == 's' and (d.get('width') or 0) > 1.2]
    # split between panels: right-panel bottom thick line start
    xs = [d['rect'].x0 for d in thick if abs(d['rect'].y0-yBot) < 1 and d['rect'].height < 1 and d['rect'].x1 > gwN[-1][0]-5]
    xSplit = min(xs) if xs else gwN[0][0]
    xR = max(xR, max((d['rect'].x1 for d in thick if abs(d['rect'].y0-yBot) < 1 and d['rect'].height < 1), default=xR))
    xL = min(xL, min((d['rect'].x0 for d in thick if abs(d['rect'].y0-yBot) < 1 and d['rect'].height < 1), default=xL))
    inside = lambda r: r.x0 > xL-2.5 and r.x1 < xR+2.5 and r.y0 > yTop-1.5 and r.y1 < yBot+1.5
    solids, dashed, grays = [], [], []
    for d in D:
        r = d['rect']
        if not inside(r): continue
        w = d.get('width') or 0
        if d['type'] == 'f' and d.get('fill') and 0.5 < d['fill'][0] < 0.95 and abs(d['fill'][0]-d['fill'][2]) < .05:
            for p in subpaths(d): grays.append(p)
            continue
        sp = subpaths(d)
        isdash = (d['type'] in ('fs', 'f') and d.get('fill') and d['fill'][0] < .1) or (d.get('dashes') and d['dashes'] not in ('[] 0', '[] 0.0'))
        if d['type'] == 's' and 0.3 < w < 1.0 and not isdash:
            ch = merge_chain(sp)
            if len(ch) > 6 and max(plen(c) for c in ch) < 15:
                dashed.append(dashes_to_line([c+[c[0]] for c in ch]) if False else sorted([((c[0][0]+c[-1][0])/2, (c[0][1]+c[-1][1])/2) for c in ch], key=lambda q: q[1]))
            else:
                solids += [c for c in ch if plen(c) > 2]
        elif isdash:
            if d['type'] == 's':
                dashed.append(sorted([p for c in sp for p in c], key=lambda q: q[1]))
            else:
                dl = dashes_to_line(sp)
                if len(dl) > 3: dashed.append(dl)
                else:
                    pts = sorted([p for c in sp for p in c], key=lambda q: q[1])
                    if pts and (max(q[1] for q in pts)-min(q[1] for q in pts) > 6): dashed.append(pts[::max(1,len(pts)//25)])
    labels = [t for t in T if inside(pymupdf.Rect(t['bb'])) or (t['bb'][1] > yTop-12 and t['bb'][3] < yBot+2 and t['bb'][0] > xL-5 and t['bb'][2] < xR+40)]
    def near_label(p, pad=5, anyl=False):
        best, bd = None, 1e9
        for t in labels:
            b = t['bb']
            if b[0]-pad < p[0] < b[2]+pad and b[1]-pad < p[1] < b[3]+pad and t['dir'][0] > .99 and (anyl or multival(t['s'])):
                dd = math.hypot(max(b[0]-p[0], 0, p[0]-b[2]), max(b[1]-p[1], 0, p[1]-b[3]))
                if dd < bd: bd, best = dd, t
        return best
    leaders, rest = [], []
    for c in solids:
        lab = near_label(c[0]) or near_label(c[-1]) or near_label(c[0], 4, True) or near_label(c[-1], 4, True) or near_label(c[0], 9) or near_label(c[-1], 9)
        if len(c) <= 4 and lab is not None and plen(c) < 90: leaders.append((c, lab))
        else: rest.append(c)
    # right-panel dashed pieces that are not the MAX OAT line are parts of OAT lines (e.g. IGE MCP 30 C)
    mo = [t['c'] for t in labels if 'MAX' in t['s'].upper() and 'OAT' in t['s'].upper() and t['c'][0] > xSplit]
    keep = []
    for d in dashed:
        ends = [e for c in rest for e in (c[0], c[-1])]
        conn = len(d) > 1 and any(math.dist(e, d[0]) < 4.5 or math.dist(e, d[-1]) < 4.5 for e in ends)
        if conn and sum(q[0] for q in d)/len(d) >= xSplit and mo and min(dist_pt_poly(c, d) for c in mo) > 12:
            d = list(d)
            for idx in (0, -1):
                near = min(ends, key=lambda e: math.dist(e, d[idx]), default=None)
                if near and math.dist(near, d[idx]) < 4.5: d[idx] = near
            rest.append(d)
        else: keep.append(d)
    dashed[:] = keep
    solids = merge_chain(rest, 1.0)
    # drop grid-coincident & frame pieces
    def is_axisline(c):
        xs_ = [p[0] for p in c]; ys_ = [p[1] for p in c]
        return (max(ys_)-min(ys_) < .3 and (abs(ys_[0]-yBot) < 1 or abs(ys_[0]-yTop) < 1))
    solids = [c for c in solids if not is_axisline(c)]
    curves = [c for c in solids if plen(c) > 12]
    def nearest(pt, cands, maxd):
        best = None; bd = maxd
        for i, c in enumerate(cands):
            dd = dist_pt_poly(pt, c)
            if dd < bd: bd, best = dd, i
        return best, bd
    left = [c for c in curves if sum(p[0] for p in c)/len(c) < xSplit]
    right = [c for c in curves if sum(p[0] for p in c)/len(c) >= xSplit]
    res = dict(file=fname.split('/')[-1], page=pno, xOat=[ao, bo], xGw=[ag, bg], yTop=yTop, yBot=yBot, xL=xL, xR=xR, xSplit=xSplit,
               pa=[], oat=[], other=[], dashed=dashed, gray=grays, leftUn=[], rightUn=[])
    used = set()
    for t in labels:
        vs = multival(t['s']); c = t['c']
        if c[0] < xSplit and vs and abs(t['dir'][1]) > .2:
            i, dd = nearest(c, left, 14)
            if i is not None:
                for v in vs: res['pa'].append(dict(v=v, pts=left[i], dd=round(dd, 1)))
                used.add(('L', i))
    lead_by_label = {}
    for c, lab in leaders: lead_by_label.setdefault(id(lab), []).append(c)
    for t in labels:
        vs = multival(t['s']); c = t['c']
        if c[0] >= xSplit - 5 and vs and t['bb'][1] > yTop - 2 and not (abs(t['dir'][1]) < .2 and abs(c[1]-yLab) < 4):
            i = None
            if id(t) in lead_by_label:
                for L in lead_by_label[id(t)]:
                    far = max((L[0], L[-1]), key=lambda p: math.dist(p, c))
                    i, dd = nearest(far, right, 5)
                    if i is not None: break
            if i is None: i, dd = nearest(c, right, 14 if abs(t['dir'][1]) > .2 else 8)
            if i is not None:
                for v in vs: res['oat'].append(dict(v=v, pts=right[i], dd=round(dd, 1)))
                used.add(('R', i))
    def tail_from(c, p):
        """portion of curve c (oriented top->bottom) below the projection of p"""
        c = c if c[0][1] <= c[-1][1] else c[::-1]
        best, bi, bt = 1e9, 0, 0
        for a in range(len(c)-1):
            ax, ay = c[a]; bx, by = c[a+1]; dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
            t = 0 if L2 == 0 else max(0, min(1, ((p[0]-ax)*dx+(p[1]-ay)*dy)/L2))
            dd = math.hypot(ax+t*dx-p[0], ay+t*dy-p[1])
            if dd < best: best, bi, bt = dd, a, t
        q = (c[bi][0]+bt*(c[bi+1][0]-c[bi][0]), c[bi][1]+bt*(c[bi+1][1]-c[bi][1]))
        return best, [q] + c[bi+1:]
    def extend(pts):
        pts = list(pts)
        for _ in range(5):
            grown = False
            for c in right + left:
                if c is pts or len(c) < 2: continue
                dd, tail = tail_from(c, pts[-1])
                if dd < 1.0 and len(tail) > 1 and tail[-1][1] > pts[-1][1] + 2 and plen(tail) > 2:
                    pts = pts + tail[1:]; grown = True; break
            if not grown: break
        return pts
    for f in res['oat'] + res['pa'] + res['other']:
        f['pts'] = sorted(f['pts'], key=lambda q: q[1]) if False else (f['pts'] if f['pts'][0][1] <= f['pts'][-1][1] else f['pts'][::-1])
        f['pts'] = extend(f['pts'])
    for t in labels:
        u = t['s'].upper()
        if ('TAKEOFF' in u or 'GROSS WEIGHT' in u or 'LIMIT' in u) and 'FT' not in u and 'KG' not in u and 'LB' not in u and t['c'][0] > xSplit:
            i = None
            for L, lab in leaders:
                if lab is t:
                    far = max((L[0], L[-1]), key=lambda p: math.dist(p, t['c']))
                    cand = [j for j, c in enumerate(right) if ('R', j) not in used and dist_pt_poly(far, c) < 6]
                    if cand: i = min(cand, key=lambda j: dist_pt_poly(far, right[j])); break
                    i, dd = nearest(far, right, 6)
                    if i is not None: break
            if i is None and 'TAKEOFF' in u: i, dd = nearest(t['c'], right, 25)
            if i is not None:
                res['other'].append(dict(name='maxgw' if 'GROSS' in u else 'tol', pts=right[i])); used.add(('R', i))
    for f in res['other']:
        f['pts'] = extend(f['pts'] if f['pts'][0][1] <= f['pts'][-1][1] else f['pts'][::-1])
    want = []
    for t in labels:
        vs = multival(t['s']); c = t['c']
        if vs and c[0] >= xSplit-5 and t['bb'][1] > yTop-2 and not (abs(t['dir'][1]) < .2 and abs(c[1]-yLab) < 4): want += vs
    res['missing'] = sorted(set(want) - set(f['v'] for f in res['oat']))
    if res['missing']:
        # second pass: unclaimed solid pieces starting within 9pt of a missing label
        claimed = set(id(L) for L, lab in leaders)
        for t in labels:
            vs = multival(t['s'])
            if not vs or not set(vs) & set(res['missing']) or t['c'][0] < xSplit: continue
            b = t['bb']
            for c in [L for L, lab in leaders] + rest:
                for e, o in ((c[0], c[-1]), (c[-1], c[0])):
                    if b[0]-9 < e[0] < b[2]+2 and b[1]-3 < e[1] < b[3]+3 and math.dist(e, o) > 10:
                        i, dd = nearest(o, right, 3)
                        if i is None:  # bent leader: walk to the vertex farthest from label
                            far = max(c, key=lambda p: math.dist(p, t['c'])); i, dd = nearest(far, right, 3)
                        if i is not None:
                            for v in vs: res['oat'].append(dict(v=v, pts=extend(right[i] if right[i][0][1] <= right[i][-1][1] else right[i][::-1]), dd=dd))
                            res['missing'] = sorted(set(res['missing']) - set(vs)); break
                if not (set(vs) & set(res['missing'])): break
    res['leftUn'] = [c for i, c in enumerate(left) if ('L', i) not in used]
    res['rightUn'] = [c for i, c in enumerate(right) if ('R', i) not in used]
    res['hd'] = [t['s'] for t in T if 'HD LIMIT' in t['s'].replace('H D', 'HD').upper() or 'H D LIMIT' in t['s'].upper()]
    res['title'] = ' | '.join(t['s'] for t in T if 110 < t['c'][1] < yTop-20 and t['dir'][0] > .99 and not NUM.match(t['s']))
    return res

def overlay(res, out, scale=2.2):
    doc = pymupdf.open('/mnt/user-data/uploads/' + res['file']); pg = doc[res['page']-1]
    sh = pg.new_shape()
    def poly(pts, col, w=1.2):
        if len(pts) < 2: return
        sh.draw_polyline([pymupdf.Point(*p) for p in pts]); sh.finish(color=col, width=w, closePath=False)
    for f in res['pa']: poly(f['pts'], (1, 0, 0))
    for f in res['oat']: poly(f['pts'], (0, 0, 1))
    for f in res['other']: poly(f['pts'], (0, .6, 0))
    for c in res['dashed']: poly(c, (1, .5, 0), 1.6)
    for c in res['leftUn'] + res['rightUn']: poly(c, (1, 0, 1), 2)
    for g in res['gray']: poly(g, (0, .7, .7), .8)
    cols = [(0,0,1),(0,.6,0),(.8,0,.8),(0,.6,.7),(.6,.3,0),(1,0,0),(.3,.3,.3),(0,0,.5),(.5,0,.5),(0,.4,0)]
    for n, f in enumerate(sorted(res['oat'], key=lambda f: f['v'])):
        poly(f['pts'], cols[n % len(cols)], 1.4)
        P = f['pts']; Ltot = plen(P); acc = 0; tgt = Ltot*(0.25+0.12*(n % 5))
        p = P[-1]
        for a in range(len(P)-1):
            seg = math.dist(P[a], P[a+1])
            if acc+seg >= tgt: t = (tgt-acc)/seg if seg else 0; p = (P[a][0]+t*(P[a+1][0]-P[a][0]), P[a][1]+t*(P[a+1][1]-P[a][1])); break
            acc += seg
        sh.draw_circle(pymupdf.Point(*p), 1.2); sh.finish(color=cols[n % len(cols)], fill=cols[n % len(cols)])
        sh.insert_text(pymupdf.Point(p[0]-22, p[1]+2), '%g' % f['v'], fontsize=6.5, color=cols[n % len(cols)])
    for f in res['pa']:
        p = f['pts'][len(f['pts'])//2]
        sh.insert_text(pymupdf.Point(p[0]+2, p[1]+7), '%g' % f['v'], fontsize=6, color=(0, .5, 0))
    for f in res['other']: poly(f['pts'], (0, .8, 0), 2.2)
    sh.commit()
    clip = pymupdf.Rect(res['xL']-30, res['yTop']-40, res['xR']+40, res['yBot']+30)
    pg.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip).save(out)
