import sys, re, math, json, io, base64
sys.path.insert(0, '/home/claude/w')
from ext2 import *
import ext2
from PIL import Image

U = '/mnt/user-data/uploads/'
F625 = U+'d0de70ba-412FMS6205.pdf'; F745 = U+'252bae3c-412FMS7405.pdf'

def R(p): return [round(p[0], 2), round(p[1], 2)]
def thin(pts):
    pts = list(pts); out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) > 0.25: out.append(p)
    if out[-1] != pts[-1]: out.append(pts[-1])
    return [R(p) for p in out]
def topdown(c): return c if c[0][1] <= c[-1][1] else c[::-1]

_DOCS = {}
def getpage(f, p):
    if f not in _DOCS:
        d = pymupdf.open(f)
        for pg in d:
            if pg.rotation: pg.remove_rotation()
        _DOCS[f] = d
    return _DOCS[f][p-1]

def first_num(s):
    m = re.search(r'-?\d+(\.\d+)?', s.replace('−', '-'))
    return float(m.group(0)) if m else None

def image_of(pg, clip, sc=2.0):
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(sc, sc), clip=clip, colorspace=pymupdf.csGRAY)
    im = Image.open(io.BytesIO(pix.tobytes('png'))).quantize(8)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

def bridge(curves, labs, gap=16):
    """join curve pieces broken around a label (label centre near the gap midpoint)"""
    curves = [list(c) for c in curves]
    changed = True
    while changed:
        changed = False
        for i in range(len(curves)):
            for j in range(len(curves)):
                if i == j: continue
                a, b = curves[i], curves[j]
                for A in (a, a[::-1]):
                    for Bc in (b, b[::-1]):
                        e, s0 = A[-1], Bc[0]
                        dd = math.dist(e, s0)
                        if 1.0 < dd < gap:
                            mid = ((e[0]+s0[0])/2, (e[1]+s0[1])/2)
                            if any(math.dist(t['c'], mid) < 5 for t in labs):
                                curves[i] = A + Bc; curves.pop(j); changed = True; break
                    if changed: break
                if changed: break
            if changed: break
    return curves

def ldist(t, c):
    """label-to-curve distance: from the text baseline when known (Bell labels sit on their line)"""
    if t.get('base'): return min(dist_pt_poly(p, c) for p in t['base'])
    return dist_pt_poly(t['c'], c)

def order_match(curves, labs, famfilter=None, maxd=14, skip_pen=14):
    """order-preserving label->curve matching (labels and curves both ordered across the family)"""
    if not curves or not labs: return {}
    # stage 1: labels lying on a curve (leader tips, bridged gaps) claim it outright
    fam = {}; used_c = set(); rest = []
    for t in labs:
        ds = sorted((ldist(t, c), i) for i, c in enumerate(curves))
        if ds and ((t.get('tip') and ds[0][0] < 0.8) or (ds[0][0] < 1.6 and (len(ds) == 1 or ds[1][0] > 2.0))) and ds[0][1] not in used_c:
            used_c.add(ds[0][1])
            for v in multival(t['s']):
                if not famfilter or famfilter(v): fam.setdefault(v, curves[ds[0][1]])
        else: rest.append(t)
    if not rest: return fam
    curves = [c for i, c in enumerate(curves) if i not in used_c]; labs = rest
    if not curves: return fam
    # mean direction of curves -> normal
    sx = sy = 0
    for c in curves:
        dx, dy = c[-1][0]-c[0][0], c[-1][1]-c[0][1]
        if dx < 0: dx, dy = -dx, -dy
        L = math.hypot(dx, dy) or 1; sx += dx/L; sy += dy/L
    L = math.hypot(sx, sy) or 1; nx, ny = -sy/L, sx/L
    def proj_c(c):
        # projection of curve onto normal, measured where curve is nearest the label cloud centre
        cx = sum(t['c'][0] for t in labs)/len(labs); cy = sum(t['c'][1] for t in labs)/len(labs)
        p = min(c, key=lambda q: math.dist(q, (cx, cy)))
        return p[0]*nx+p[1]*ny
    C = sorted(curves, key=proj_c); Ls = sorted(labs, key=lambda t: t['c'][0]*nx+t['c'][1]*ny)
    n, m = len(Ls), len(C)
    D = [[ldist(Ls[i], C[j]) for j in range(m)] for i in range(n)]
    INF = 1e9
    # dp[i][j]: best cost matching first i labels using first j curves
    dp = [[INF]*(m+1) for _ in range(n+1)]; bk = [[None]*(m+1) for _ in range(n+1)]
    for j in range(m+1): dp[0][j] = 0
    for i in range(1, n+1):
        for j in range(0, m+1):
            best = dp[i-1][j] + skip_pen; arg = ('skipL',)
            if j > 0 and dp[i][j-1] < best: best = dp[i][j-1]; arg = ('skipC',)
            if j > 0 and D[i-1][j-1] < maxd and dp[i-1][j-1] + D[i-1][j-1] < best: best = dp[i-1][j-1]+D[i-1][j-1]; arg = ('m',)
            dp[i][j] = best; bk[i][j] = arg
    i, j = n, m
    while i > 0:
        a = bk[i][j]
        if a[0] == 'm':
            for v in multival(Ls[i-1]['s']):
                if not famfilter or famfilter(v): fam.setdefault(v, C[j-1])
            i -= 1; j -= 1
        elif a[0] == 'skipC': j -= 1
        else: i -= 1
    return fam

def _xat(pts, y):
    for i in range(1, len(pts)):
        p, q = pts[i-1], pts[i]
        if min(p[1], q[1]) <= y <= max(p[1], q[1]) and q[1] != p[1]: return p[0]+(y-p[1])*(q[0]-p[0])/(q[1]-p[1])
    return None

def assign_match(curves, labs, famfilter=None, maxd=6.0):
    """optimal one-to-one label->curve assignment on baseline / leader-tip distance (for families whose lines cross)"""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    if not curves or not labs: return {}
    C = np.array([[ldist(t, c) for c in curves] for t in labs])
    C2 = np.where(C < maxd, C, 1e6)
    r, c = linear_sum_assignment(C2)
    fam = {}
    for i, j in zip(r, c):
        if C2[i, j] >= 1e6: continue
        for v in multival(labs[i]['s']):
            if not famfilter or famfilter(v): fam.setdefault(v, curves[j])
    return fam

def rank_match(curves, labs, famfilter=None, maxd=14, skip_pen=14):
    """order-preserving match using horizontal distance at each label's own height;
    labels ordered by their fractional rank among the curves at that height"""
    if not curves or not labs: return {}
    ys = sorted(y for c in curves for _, y in c); yref = ys[len(ys)//2]
    def cx(c):
        x = _xat(c, yref)
        return x if x is not None else sum(p[0] for p in c)/len(c)
    C = sorted(curves, key=cx)
    def frank(t):
        lx, ly = t['c']; xs = sorted((x, j) for j, c in enumerate(C) for x in [_xat(c, ly)] if x is not None)
        if not xs: return 0
        k = sum(1 for x, j in xs if x < lx); return k
    Ls = sorted(labs, key=frank)
    n, m = len(Ls), len(C)
    def cost(t, c):
        x = _xat(c, t['c'][1])
        return abs(t['c'][0]-x) if x is not None else dist_pt_poly(t['c'], c)+5
    D = [[cost(Ls[i], C[j]) for j in range(m)] for i in range(n)]
    INF = 1e9; dp = [[INF]*(m+1) for _ in range(n+1)]; bk = [[None]*(m+1) for _ in range(n+1)]
    for j in range(m+1): dp[0][j] = 0
    for i in range(1, n+1):
        for j in range(0, m+1):
            best = dp[i-1][j]+skip_pen; arg = 'L'
            if j > 0 and dp[i][j-1] < best: best = dp[i][j-1]; arg = 'C'
            if j > 0 and D[i-1][j-1] < maxd and dp[i-1][j-1]+D[i-1][j-1] < best: best = dp[i-1][j-1]+D[i-1][j-1]; arg = 'm'
            dp[i][j] = best; bk[i][j] = arg
    fam = {}; i, j = n, m
    while i > 0:
        a = bk[i][j]
        if a == 'm':
            for v in multival(Ls[i-1]['s']):
                if not famfilter or famfilter(v): fam.setdefault(v, C[j-1])
            i -= 1; j -= 1
        elif a == 'C': j -= 1
        else: i -= 1
    return fam

def fam_panel(pg, P, T, W, xside='bottom', yside='left', famfilter=None, matcher=None):
    """panel with a labelled family of curves + dashed limits. returns dict"""
    cx, _ = calib(W, P, xside); cy, _ = calib(W, P, yside)
    solids, dashed, grays = panel_items(pg, P, texts=[t for t in T if multival(t['s']) or 'AND' in t['s'].upper()])
    labs = labels_in(T, P, 12)
    hv = solids + list(ext2.HEAVY)
    vert = [c for c in hv if max(p[0] for p in c)-min(p[0] for p in c) < 0.6 and plen(c) > 40]
    horiz = [c for c in hv if max(p[1] for p in c)-min(p[1] for p in c) < 0.6 and plen(c) > 40]
    curves = [c for c in solids if c not in vert and c not in horiz and plen(c) > 15]
    for t in labs:
        if re.search(r'AND (COLDER|BELOW|ABOVE|WARMER)', t['s'].upper()) and first_num(t['s']) is not None: t['s'] = '%g' % first_num(t['s'])
    rot = [t for t in labs if abs(t['dir'][1]) > 0.15 and multival(t['s'])]
    # horizontal labels joined to their curve by a short leader: use the leader tip as the label position
    hz = [t for t in labs if abs(t['dir'][1]) <= 0.15 and multival(t['s']) and P[0] < t['c'][0] < P[2]+16 and P[1] < t['c'][1] < P[3]]
    for t in hz:
        b = t['bb']; best = None
        for d in pg.get_drawings():
            if d['type'] != 's' or len(d['items']) > 3 or any(it[0] != 'l' for it in d['items']): continue
            pts = [d['items'][0][1]] + [it[2] for it in d['items']]
            for e, o_ in ((pts[0], pts[-1]), (pts[-1], pts[0])):
                if b[0]-7 < e.x < b[2]+7 and b[1]-5 < e.y < b[3]+5 and 4 < math.dist((e.x, e.y), (o_.x, o_.y)) < 70:
                    best = (o_.x, o_.y)
        have = set(v for r_ in rot if not r_.get('tip') for v in multival(r_['s']))
        if best and not (set(multival(t['s'])) <= have):
            rot.append(dict(s=t['s'], dir=t['dir'], c=best, bb=(best[0]-1, best[1]-1, best[0]+1, best[1]+1), tip=True))
    curves = bridge(curves, rot)
    fam = (matcher or order_match)(curves, rot, famfilter)
    lim = {}
    for d in dashed:
        best = None; bd = 30
        for t in labs:
            u = t['s'].upper()
            if 'MAX OAT' in u or 'HD' in u.replace(' ', '') or 'H D' in u:
                dd = dist_pt_poly(t['c'], d)
                if dd < bd: bd, best = dd, t
        if best is not None:
            u = best['s'].upper()
            key = 'maxoat' if 'OAT' in u else 'hd'
            if key not in lim or len(d) > len(lim[key]['pts']):
                lim[key] = dict(pts=thin(topdown(d)), v=first_num(u.replace(',', '')) if key == 'hd' else None)
    unl = [c for c in curves if all(c is not f for f in fam.values())]
    return dict(panel=[round(v, 2) for v in P], x=cx[:2] if cx else None, y=cy[:2] if cy else None, xres=cx[2] if cx else None, yres=cy[2] if cy else None,
                fam=[dict(v=v, pts=thin(topdown(c))) for v, c in sorted(fam.items())],
                lim=lim, vert=[round(c[0][0], 2) for c in vert], horiz=[round(c[0][1], 2) for c in horiz],
                unl=len(unl), dashed_n=len(dashed), _unl=unl, _dashed=dashed)

def wind_panel(pg, P, T, W, Wall_lines):
    cx, _ = calib(W, P, 'bottom'); cy, _ = calib(W, P, 'left')
    solids, dashed, grays = panel_items(pg, P)
    guides = [list(topdown(d)) for d in dashed if len(d) >= 3]
    vx = [c[0][0] for c in solids if max(p[0] for p in c)-min(p[0] for p in c) < 0.6 and plen(c) > 40]
    xmax = min(vx) if vx else P[2]
    G = []
    for g in guides:
        a, b = g[0], g[1]
        if b[1] != a[1] and g[0][1] > P[1]:
            t = (P[1]-a[1])/(b[1]-a[1]); g = [(a[0]+t*(b[0]-a[0]), P[1])] + g
        c, d = g[-2], g[-1]
        if 0 < xmax-d[0] < 10 and d[0] != c[0]:
            t = (xmax-c[0])/(d[0]-c[0]); g = g + [(xmax, c[1]+t*(d[1]-c[1]))]
        G.append(thin(g))
    guides = G
    # temperature limit lines: long horizontal lines crossing the panel, labelled at right
    lims = []
    for d in pg.get_drawings():
        r = d['rect']
        if d['type'] == 's' and r.height < 0.6 and r.width > 150 and P[1]+2 < r.y0 < P[3]-2 and (d.get('width') or 0) > 0.3:
            y = r.y0
            labs = [t for t in T if t['c'][0] > P[2]+2 and abs(t['c'][1]-y) < 6]
            lab = min(labs, key=lambda t: abs(t['c'][1]-y)) if labs else None
            lims.append(dict(y=round(y, 2), lab=lab['s'] if lab else None, v=first_num(lab['s']) if lab else None))
    lims.sort(key=lambda l: l['y'])
    return dict(panel=[round(v, 2) for v in P], x=cx[:2], y=cy[:2], xmax=round(xmax,2), guides=sorted(guides, key=lambda g: g[0][0]), lims=lims)

def wat_chart(f, p, key):
    pg = getpage(f, p); T = lines_txt(pg); W = words(pg)
    Ps = sorted(find_panels(pg), key=lambda q: q[1])
    top = fam_panel(pg, Ps[0], T, W)
    out = dict(key=key, file=f.split('/')[-1], page=p, top=top)
    if len(Ps) > 1:
        out['wind'] = wind_panel(pg, Ps[1], T, W, None)
    x0 = min(q[0] for q in Ps)-48; x1 = max(q[2] for q in Ps)+50; y0 = Ps[0][1]-45; y1 = Ps[-1][3]+32
    out['im'] = [round(x0, 2), round(y0, 2), round(x1-x0, 2), round(y1-y0, 2)]
    out['img'] = image_of(pg, pymupdf.Rect(x0, y0, x1, y1))
    txt = pg.get_text(); fig = re.search(r'Figure ([0-9A-Z-]+)\.\s+([^\n]*)', txt)
    out['fig'] = fig.group(1) if fig else ''; out['title'] = fig.group(2).strip() if fig else ''
    return out

if __name__ == '__main__' and len(sys.argv) == 1:
    for f, p, k in [(F625, 30, 'catA_wat_A'), (F625, 68, 'catA_wat_B'), (F625, 103, 'catA_wat_C'), (F625, 142, 'catA_wat_D'), (F745, 63, 'catA_wat_C745')]:
        o = wat_chart(f, p, k); t = o['top']
        print(k, o['fig'], 'x', t['x'], t['xres'], 'y', t['y'], t['yres'], 'fam', [x['v'] for x in t['fam']], 'lim', {a: b['v'] for a, b in t['lim'].items()}, 'vert', t['vert'], 'unl', t['unl'], 'dashed', t['dashed_n'])
        if 'wind' in o: w = o['wind']; print('    wind x', w['x'], 'y', w['y'], 'guides', len(w['guides']), 'lims', [(l['y'], l['lab']) for l in w['lims']])

def split_panels(pg, Ps):
    """split panels at heavy vertical divider lines"""
    D = pg.get_drawings(); out = []
    for P in Ps:
        xs = []
        for d in D:
            r = d['rect']
            if d['type'] == 's' and (d.get('width') or 0) > 1.0 and r.width < 1 and r.height > 0.7*(P[3]-P[1]) and P[0]+5 < r.x0 < P[2]-5 and r.y0 < P[1]+0.3*(P[3]-P[1]):
                xs.append(r.x0)
        xs = sorted(set(round(x, 1) for x in xs)); edges = [P[0]] + xs + [P[2]]
        for a, b in zip(edges, edges[1:]):
            if b-a > 20: out.append([a, P[1], b, P[3]])
    return out

def is_axis_arrow(c):
    xs = [p[0] for p in c]; ys = [p[1] for p in c]
    return len(c) <= 3 and (max(xs)-min(xs) < 0.5 or max(ys)-min(ys) < 0.5)

def left_family(pg, P, T, labdir=None):
    solids, dashed, grays = panel_items(pg, P)
    labs = labels_in(T, P, 10)
    rot = [t for t in labs if abs(t['dir'][1]) > 0.15 and (multival(t['s']) or 'SEA' in t['s'].upper())]
    if labdir: rot = [t for t in rot if t['dir'][1]*labdir > 0]
    for t in rot:
        if 'SEA' in t['s'].upper(): t['s'] = '0'
    curves = [c for c in solids + merge_chain(list(ext2.HEAVY), 1.0, 0.75) if plen(c) > 15 and not is_axis_arrow(c)]
    curves = bridge(curves, rot)
    # max OAT line first: curve (solid or dashed) nearest the MAX OAT text, whose direction differs from the PA lines
    mo = [t for t in labs if 'MAX' in t['s'].upper() or ('LIMIT' in t['s'].upper() and 'OAT' not in t['s'].upper() and abs(t['dir'][1]) > .5)]
    cand = curves + [list(d) for d in dashed]
    maxoat = None
    if mo:
        def score(c): return min(dist_pt_poly(t['c'], c) for t in mo)
        best = min(cand, key=score)
        if score(best) < 25:
            maxoat = best
            curves = [c for c in curves if c is not best]
    fam = order_match(curves, rot)
    return fam, (thin(topdown(maxoat)) if maxoat else None), curves
def right_line(pg, P):
    solids, dashed, grays = panel_items(pg, P)
    cs = [c for c in solids + list(ext2.HEAVY) if plen(c) > 12 and not is_axis_arrow(c)]
    cs = merge_chain(cs, 2.0)
    cs = [c for c in cs if plen(c) > 30]
    return [thin(topdown(c)) for c in cs]

def hl_chart(f, p, key):
    pg = getpage(f, p); T = lines_txt(pg); W = words(pg)
    Ps = split_panels(pg, sorted(find_panels(pg), key=lambda q: q[0]))
    Ps.sort(key=lambda q: q[0])
    L, Rp = Ps[0], Ps[-1]
    cxL, _ = calib(W, L, 'bottom'); cxR, _ = calib(W, Rp, 'bottom')
    fam, maxoat, other = left_family(pg, L, T)
    lines = right_line(pg, Rp)
    txt = pg.get_text(); fig = re.search(r'Figure ([0-9A-Z-]+)\.\s+([^\n]*)', txt)
    hd = re.search(r'(\d+),?(\d{3}) ?FT\.? ?H', txt.replace('\n', ' '))
    x0 = L[0]-45; x1 = Rp[2]+40; y0 = L[1]-28; y1 = L[3]+30
    return dict(key=key, file=f.split('/')[-1], page=p, fig=fig.group(1) if fig else '', title=fig.group(2).strip() if fig else '',
                L=[round(v, 2) for v in L], R=[round(v, 2) for v in Rp], xOat=cxL[:2], xR=cxR[:2], xResL=cxL[2], xResR=cxR[2],
                pa=[dict(v=v, pts=thin(topdown(c))) for v, c in sorted(fam.items())], maxoat=maxoat, lines=lines,
                hdLim=int(hd.group(1)+hd.group(2)) if hd else None,
                im=[round(x0, 2), round(y0, 2), round(x1-x0, 2), round(y1-y0, 2)], _clip=(x0, y0, x1, y1))

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'hl':
    for p in map(int, sys.argv[2:]):
        o = hl_chart(F625, p, 'x')
        print(p, o['fig'], 'xOat', [round(v, 5) for v in o['xOat']], o['xResL'], 'xR', [round(v, 4) for v in o['xR']], round(o['xResR'], 3), 'PA', [x['v'] for x in o['pa']], 'maxoat', bool(o['maxoat']), 'lines', [(len(l), round(plen(l))) for l in o['lines']], 'hd', o['hdLim'])


def guides_of(pg, P):
    solids, dashed, grays = panel_items(pg, P)
    solids = solids + merge_chain(list(ext2.HEAVY), 1.0, 0.75)
    vert = [c for c in solids if max(p[0] for p in c)-min(p[0] for p in c) < 0.6]
    gs = [c for c in solids if c not in vert and plen(c) > 30 and not is_axis_arrow(c)] + [list(d) for d in dashed if len(d) >= 3]
    # left-to-right orientation
    gs = [c if c[0][0] <= c[-1][0] else c[::-1] for c in gs]
    G = []
    for g in gs:   # dashed guides start a few points inside the panel: extend to the left edge
        g = list(g)
        if 0.4 < g[0][0]-P[0] < 8 and g[1][0] != g[0][0]:
            a, b = g[0], g[1]; t_ = (P[0]-a[0])/(b[0]-a[0]); g = [(P[0], a[1]+t_*(b[1]-a[1]))] + g
        G.append(g)
    gs = G
    xmax = min((c[0][0] for c in vert if plen(c) > 40), default=None)
    gs = sorted(gs, key=lambda g: g[0][1])
    # keep guides that start on the panel's left edge at the regular spacing (drops drawn example arrows)
    st = [g for g in gs if abs(g[0][0]-P[0]) < 0.4]
    if len(st) >= 4:
        sp = sorted(b[0][1]-a[0][1] for a, b in zip(st, st[1:]))[len(st)//2]
        y0 = st[0][0][1]
        gs = [g for g in st if abs(((g[0][1]-y0)/sp) - round((g[0][1]-y0)/sp)) < 0.15]
    return [thin(g) for g in gs], xmax

def dd_chart(f, p, key):
    pg = getpage(f, p); T = lines_txt(pg); W = words(pg)
    Ps = sorted(split_panels(pg, sorted(find_panels(pg), key=lambda q: q[0])), key=lambda q: q[0])
    L, M, Rp = Ps[0], Ps[1], Ps[-1]
    cxL, _ = calib(W, L, 'bottom'); cxM, _ = calib(W, M, 'bottom'); cxR, _ = calib(W, Rp, 'bottom')
    fam, maxoat, _ = left_family(pg, L, T, labdir=+1)
    guides, gwmax = guides_of(pg, M)
    # right panel: DA family
    solids, dashed, grays = panel_items(pg, Rp)
    labs = [t for t in labels_in(T, Rp, 10) if abs(t['dir'][1]) > 0.15 and (multival(t['s']) or 'AND BELOW' in t['s'].upper())]
    for t in labs:
        if 'AND BELOW' in t['s'].upper(): t['s'] = str(int(first_num(t['s'])))
    cur = [c for c in solids + list(ext2.HEAVY) if plen(c) > 15 and not is_axis_arrow(c)]
    cur = bridge(cur, labs)
    da = order_match(cur, labs)
    txt = pg.get_text(); fig = re.search(r'Figure ([0-9A-Z-]+)\.\s+([^\n]*)', txt)
    x0 = L[0]-40; x1 = Rp[2]+30; y0 = L[1]-20; y1 = L[3]+34
    return dict(key=key, file=f.split('/')[-1], page=p, fig=fig.group(1) if fig else '', title=fig.group(2).strip() if fig else '',
                L=[round(v, 2) for v in L], M=[round(v, 2) for v in M], R=[round(v, 2) for v in Rp],
                xOat=cxL[:2], xGw=[cxM[0]*1000, cxM[1]*1000], xR=cxR[:2], res=[cxL[2], cxM[2], cxR[2]],
                pa=[dict(v=v, pts=thin(topdown(c))) for v, c in sorted(fam.items())], maxoat=maxoat,
                guides=guides, gwmax=gwmax, da=[dict(v=v, pts=thin(topdown(c))) for v, c in sorted(da.items())],
                im=[round(x0, 2), round(y0, 2), round(x1-x0, 2), round(y1-y0, 2)], _clip=(x0, y0, x1, y1))

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'dd':
    for p in map(int, sys.argv[2:]):
        o = dd_chart(F625, p, 'x')
        print(p, o['fig'], 'res', o['res'], 'PA', [x['v'] for x in o['pa']], 'maxoat', bool(o['maxoat']), 'guides', len(o['guides']), 'gwmax', o['gwmax'], 'DA', [x['v'] for x in o['da']])

def fx_chart(f, p, key, matcher=None):
    pg = getpage(f, p); T = lines_txt(pg); W = words(pg)
    Ps = sorted(find_panels(pg), key=lambda q: q[1])
    top = Ps[0]; low = Ps[1] if len(Ps) > 1 else None
    t = fam_panel(pg, top, T, W, matcher=matcher)
    if low is not None:   # top panel shares the lower panel's x scale (labels are under the lower panel)
        cx, _ = calib(W, [top[0], low[1], top[2], low[3]], 'bottom'); t['x'] = cx[:2]; t['xres'] = cx[2]
    out = dict(key=key, file=f.split('/')[-1], page=p, top=t)
    if low is not None:
        labsL = ' '.join(x['s'].upper() for x in T if low[0]-60 < x['c'][0] < low[0] and low[1] < x['c'][1] < low[3])
        cy, _ = calib(W, low, 'left'); cx, _ = calib(W, low, 'bottom')
        solids, dashed, grays = panel_items(pg, low)
        gs = [c for c in solids if plen(c) > 25 and not is_axis_arrow(c) and max(p_[1] for p_ in c)-min(p_[1] for p_ in c) > 3] + [list(d) for d in dashed if len(d) >= 3]
        gs = [thin(topdown(g)) for g in gs]
        kind = 'wind' if 'WIND' in labsL else ('gw' if 'WEIGHT' in labsL else '?')
        out['low'] = dict(kind=kind, panel=[round(v, 2) for v in low], y=cy[:2] if cy else None, x=cx[:2] if cx else None, guides=sorted(gs, key=lambda g: g[0][0]))
    txt = pg.get_text(); fig = re.search(r'Figure ([0-9A-Z-]+)\.\s+([^\n]*)', txt)
    g = re.search(r'GROSS WEIGHT (\d[\d,]*) LB', txt)
    out['gw'] = int(g.group(1).replace(',', '')) if g else None
    out['fig'] = fig.group(1) if fig else ''
    x0 = min(q[0] for q in Ps)-48; x1 = max(q[2] for q in Ps)+52; y0 = Ps[0][1]-30; y1 = Ps[-1][3]+30
    out['im'] = [round(x0, 2), round(y0, 2), round(x1-x0, 2), round(y1-y0, 2)]; out['_clip'] = (x0, y0, x1, y1)
    return out

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'fx':
    for p in map(int, sys.argv[2:]):
        o = fx_chart(F625, p, 'x'); t = o['top']
        print(p, o['fig'], o['gw'], 'x', t['x'] and [round(v, 5) for v in t['x']], round(t['xres'] or 0, 3), 'y', t['y'] and [round(v, 3) for v in t['y']], round(t['yres'] or 0, 2), 'fam', [x['v'] for x in t['fam']], 'lim', {a: b['v'] for a, b in t['lim'].items()}, 'unl', t['unl'],
              'low', o.get('low') and (o['low']['kind'], len(o['low']['guides']), o['low']['y'] and [round(v, 4) for v in o['low']['y']]))
