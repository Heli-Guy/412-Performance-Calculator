"""General panel extractor for FMS-62.5 style charts (any x/y axes)."""
import pymupdf, re, math
from collections import defaultdict
from ext import subpaths, merge_chain, plen, dist_pt_poly, dashes_to_line, multival, numval, linfit

def words(pg):
    return [dict(s=w[4], c=((w[0]+w[2])/2, (w[1]+w[3])/2), bb=w[:4]) for w in pg.get_text('words')]

def lines_txt(pg):
    """text lines, with multi-number lines split into one entry per word (char-level positions)"""
    T = []
    for b in pg.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            chars = [c for sp in l['spans'] for c in sp['chars']]
            s = ''.join(c['c'] for c in chars).strip()
            if not s: continue
            bb = l['bbox']
            parts = re.findall(r'-?\d+(?:\.\d+)?', s)
            if len(parts) > 1 and re.fullmatch(r'(\s*-?\d+(\.\d+)?,?)+\s*', s):
                # split into words using char boxes
                cur = []
                prev = ''
                for c in chars + [{'c': ' ', 'bbox': None}]:
                    if c['c'] == '-' and prev.isdigit() and cur:   # glued labels like '-30-20'
                        xs = [q['bbox'][0] for q in cur]+[q['bbox'][2] for q in cur]; ys = [q['bbox'][1] for q in cur]+[q['bbox'][3] for q in cur]
                        T.append(dict(s=''.join(q['c'] for q in cur).strip(','), dir=l['dir'], c=((min(xs)+max(xs))/2, (min(ys)+max(ys))/2), bb=(min(xs), min(ys), max(xs), max(ys)), base=baseline(cur, l['dir'])))
                        cur = []
                    prev = c['c']
                    if c['c'].strip() == '':
                        if cur:
                            xs = [q['bbox'][0] for q in cur]+[q['bbox'][2] for q in cur]; ys = [q['bbox'][1] for q in cur]+[q['bbox'][3] for q in cur]
                            T.append(dict(s=''.join(q['c'] for q in cur).strip(','), dir=l['dir'], c=((min(xs)+max(xs))/2, (min(ys)+max(ys))/2), bb=(min(xs), min(ys), max(xs), max(ys)), base=baseline(cur, l['dir'])))
                            cur = []
                    else: cur.append(c)
                continue
            T.append(dict(s=s, dir=l['dir'], c=((bb[0]+bb[2])/2, (bb[1]+bb[3])/2), bb=bb, base=baseline([c for c in chars if c['c'].strip()], l['dir'])))
    return T

def baseline(chars, d):
    """sample points along a text line's baseline"""
    if not chars: return []
    a = chars[0]['origin']; z = chars[-1]['origin']
    w = math.hypot(chars[-1]['bbox'][2]-chars[-1]['bbox'][0], chars[-1]['bbox'][3]-chars[-1]['bbox'][1]) * 0.6
    b = (z[0]+d[0]*w, z[1]+d[1]*w)
    return [(a[0]+(b[0]-a[0])*k/4, a[1]+(b[1]-a[1])*k/4) for k in range(5)]

def find_panels(pg, minh=30):
    """group thin vertical grid lines into panels -> list of (x0,y0,x1,y1)"""
    D = pg.get_drawings(); groups = defaultdict(list)
    for d in D:
        r = d['rect']
        if d['type'] == 's' and (d.get('width') or 0) < 0.12 and r.width < 0.6 and r.height > minh:
            groups[(round(r.y0), round(r.y1))].append(r)
    hz = [d['rect'] for d in D if d['type'] == 's' and (d.get('width') or 0) < 0.12 and d['rect'].height < 0.6 and d['rect'].width > 30]
    out = []
    for (a, b), rs in groups.items():
        if len(rs) < 3: continue
        xa, xb = min(r.x0 for r in rs), max(r.x1 for r in rs)
        hs = [h for h in hz if a-1 <= h.y0 <= b+1 and h.x1 > xa-2 and h.x0 < xb+2]
        if hs: xa = min(xa, min(h.x0 for h in hs)); xb = max(xb, max(h.x1 for h in hs))
        out.append([xa, a, xb, b])
    # merge groups with near-identical y range
    out.sort(key=lambda p: (p[1], p[0])); M = []
    for p in out:
        for q in M:
            if abs(q[1]-p[1]) < 3 and abs(q[3]-p[3]) < 3 and (p[0] <= q[2]+3 and q[0] <= p[2]+3):
                q[0] = min(q[0], p[0]); q[2] = max(q[2], p[2]); break
        else: M.append(p)
    return M

def calib(W, panel, side, numfilter=None):
    """axis calibration from numeric words beside a panel. side: 'left','bottom','right','top'"""
    x0, y0, x1, y1 = panel; pts = []
    for w in W:
        v = numval(w['s'])
        if v is None or (numfilter and not numfilter(v)): continue
        cx, cy = w['c']
        if side == 'left' and x0-48 < w['bb'][2] < x0-1 and y0-4 < cy < y1+4: pts.append((cy, v))
        if side == 'right' and x1+1 < w['bb'][0] < x1+40 and y0-4 < cy < y1+4: pts.append((cy, v))
        if side == 'bottom' and y1+1 < w['bb'][1] < y1+24 and x0-7 < cx < x1+7: pts.append((cx, v))
        if side == 'top' and y0-16 < w['bb'][3] < y0-1 and x0-12 < cx < x1+12: pts.append((cx, v))
    # de-duplicate positions and drop outliers (labels belonging to a neighbouring panel)
    pts = sorted(set((round(p, 1), v) for p, v in pts))
    if len(pts) < 2: return None, pts
    while True:
        a, b = linfit(pts)
        errs = [abs(a*p+b-v) for p, v in pts]
        rng = (max(v for p, v in pts)-min(v for p, v in pts)) or 1
        k = max(range(len(pts)), key=lambda i: errs[i])
        if errs[k] > 0.01*rng and len(pts) > 3: pts.pop(k); continue
        break
    return [a, b, max(errs)], pts   # value = a*pos + b

def split_sharp(c, mindot=-0.3):
    """split a polyline where it doubles back (e.g. a leader drawn in the same stroke)"""
    out = [[c[0]]]
    for i in range(1, len(c)):
        cur = out[-1]
        if len(cur) >= 2:
            k = len(cur)-2
            while k > 0 and math.dist(cur[k], cur[-1]) < 1.5: k -= 1
            a, b, p = cur[k], cur[-1], c[i]
            u = (b[0]-a[0], b[1]-a[1]); v = (p[0]-b[0], p[1]-b[1]); nu, nv = math.hypot(*u), math.hypot(*v)
            if nu > 1 and nv > 0.5 and (u[0]*v[0]+u[1]*v[1])/(nu*nv) < mindot:
                out.append([b]); 
        out[-1].append(c[i])
    return [q for q in out if len(q) >= 2]

HEAVY = []
def panel_items(pg, panel, pad=2.5, texts=None):
    x0, y0, x1, y1 = panel
    inside = lambda r: r.x0 > x0-pad and r.x1 < x1+pad and r.y0 > y0-pad and r.y1 < y1+pad
    solids, dashed, grays = [], [], []
    HEAVY.clear()
    for d in pg.get_drawings():
        r = d['rect']
        if not inside(r): continue
        w = d.get('width') or 0
        if d['type'] == 'f' and d.get('fill') and 0.5 < d['fill'][0] < 0.95: grays += subpaths(d); continue
        sp = subpaths(d)
        if texts and d['type'] == 's' and len(d['items']) <= 3 and all(it[0] == 'l' for it in d['items']):
            ends = [(d['items'][0][1].x, d['items'][0][1].y), (d['items'][-1][2].x, d['items'][-1][2].y)]
            if any(t['bb'][0]-7 < e[0] < t['bb'][2]+7 and t['bb'][1]-5 < e[1] < t['bb'][3]+5 and abs(t['dir'][1]) < 0.15 for e in ends for t in texts):
                continue   # leader line from a horizontal label
        isdash = (d['type'] in ('fs', 'f') and d.get('fill') and d['fill'][0] < .1) or (d.get('dashes') and d['dashes'] not in ('[] 0', '[] 0.0'))
        if d['type'] == 's' and 0.3 < w < 1.0 and not isdash:
            ch = merge_chain(sp, 1.2, 0.75)
            if len(ch) > 6 and max(plen(c) for c in ch) < 15:
                dashed.append(sorted([((c[0][0]+c[-1][0])/2, (c[0][1]+c[-1][1])/2) for c in ch], key=lambda q: q[1]))
            else: solids += [c for c in ch if plen(c) > 1.5]
        elif d['type'] == 's' and w >= 1.0 and not isdash:
            HEAVY.extend([c for c in sp if plen(c) > 1.5])        # heavy lines: limit lines / example arrows (kept apart)
        elif isdash:
            if d['type'] == 's': dashed.append(sorted([p for c in sp for p in c], key=lambda q: q[1]))
            else:
                # split filled dash shapes into separate dashed curves by proximity chaining
                cs = []
                for p in sp:
                    if len(p) < 3: continue
                    xs = [q[0] for q in p]; ys = [q[1] for q in p]
                    if max(xs)-min(xs) > 25 or max(ys)-min(ys) > 25: continue
                    cs.append((sum(xs)/len(xs), sum(ys)/len(ys)))
                if cs: dashed += chain_points(cs)
    # drop frame-coincident horizontal/vertical pieces
    def frame(c):
        xs = [p[0] for p in c]; ys = [p[1] for p in c]
        horiz = max(ys)-min(ys) < .3 and (abs(ys[0]-y0) < 1 or abs(ys[0]-y1) < 1)
        vert = max(xs)-min(xs) < .3 and (abs(xs[0]-x0) < 1 or abs(xs[0]-x1) < 1)
        return horiz or vert
    solids = [c for c in merge_chain(solids, 1.0, 0.75) if not frame(c)]
    solids = [q for c in solids for q in split_sharp(c)]
    return solids, dashed, grays

def chain_points(cs, gap=16):
    """order dash centroids into separate polylines (nearest neighbour, direction-consistent)"""
    cs = list(cs); out = []
    def ok(cur, p, end):
        if len(cur) < 2: return True
        a, b = (cur[1], cur[0]) if end == 0 else (cur[-2], cur[-1])
        u = (b[0]-a[0], b[1]-a[1]); v = (p[0]-b[0], p[1]-b[1])
        nu, nv = math.hypot(*u), math.hypot(*v)
        return nu == 0 or nv == 0 or (u[0]*v[0]+u[1]*v[1])/(nu*nv) > 0.6
    while cs:
        cur = [cs.pop(0)]
        grown = True
        while grown and cs:
            grown = False
            for end in (0, -1):
                cand = sorted(range(len(cs)), key=lambda k: math.dist(cs[k], cur[end]))
                for j in cand[:3]:
                    if math.dist(cs[j], cur[end]) < gap and ok(cur, cs[j], end):
                        p = cs.pop(j)
                        if end == 0: cur.insert(0, p)
                        else: cur.append(p)
                        grown = True; break
                if grown: break
        if len(cur) >= 3: out.append(cur)
    return out

def labels_in(T, panel, pad=10):
    x0, y0, x1, y1 = panel
    return [t for t in T if x0-pad < t['c'][0] < x1+pad and y0-pad < t['c'][1] < y1+pad]

def assign(curves, labs, leaders=None, maxd=14):
    """label -> nearest curve. returns dict value->curve"""
    out = {}
    for t in labs:
        vs = multival(t['s'])
        if not vs: continue
        best, bd = None, maxd
        for i, c in enumerate(curves):
            d = dist_pt_poly(t['c'], c)
            if d < bd: bd, best = d, i
        if best is not None:
            for v in vs: out.setdefault(v, (curves[best], bd))
    return out
