// ================= CAT-A ENGINE (FMS-62.5 / FMS-74.5 Part D) =================
(function(root){
'use strict';
const fin=Number.isFinite;
function xAtY(pts,y){
  for(let i=1;i<pts.length;i++){const p=pts[i-1],q=pts[i];
    if(y>=Math.min(p[1],q[1])-1e-9&&y<=Math.max(p[1],q[1])+1e-9){ if(q[1]===p[1])return Math.max(p[0],q[0]); return p[0]+(y-p[1])*(q[0]-p[0])/(q[1]-p[1]);}}
  let last=pts[0],first=pts[0]; for(const p of pts){if(p[1]>last[1])last=p; if(p[1]<first[1])first=p;}
  if(y>last[1])return last[0]; if(y<first[1]&&y>first[1]-3)return first[0]; return NaN;
}
function yAtX(pts,x,extend){
  for(let i=1;i<pts.length;i++){const p=pts[i-1],q=pts[i];
    if(x>=Math.min(p[0],q[0])-1e-9&&x<=Math.max(p[0],q[0])+1e-9&&q[0]!==p[0])return p[1]+(x-p[0])*(q[1]-p[1])/(q[0]-p[0]);}
  if(!extend)return NaN;
  const s=pts.slice().sort((a,b)=>a[0]-b[0]); const lo=x<s[0][0];
  const a=lo?s[0]:s[s.length-1]; let k=lo?1:s.length-2; while(k>0&&k<s.length-1&&Math.abs(s[k][0]-a[0])<6)k+=lo?1:-1;
  const b=s[k]; if(b[0]===a[0])return NaN; return a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0]);
}
function fam(t,vs,xs,extrap){
  const P=vs.map((v,i)=>[v,xs[i]]).filter(q=>fin(q[1])).sort((a,b)=>a[0]-b[0]);
  if(!P.length)return NaN; if(P.length===1)return P[0][1];
  if(!extrap){ if(t<=P[0][0])return P[0][1]; if(t>=P[P.length-1][0])return P[P.length-1][1]; }
  let i=0; while(i<P.length-2&&t>P[i+1][0])i++;
  const a=P[i],b=P[i+1]; return a[1]+(t-a[0])*(b[1]-a[1])/(b[0]-a[0]);
}
// follow a family of guide curves from (x0,y0) to height y1, keeping the fractional position between neighbours
function followY(guides,x0,y0,y1,mode){
  const gs=guides.map(g=>[xAtY(g,y0),g]).filter(q=>fin(q[0])).sort((a,b)=>a[0]-b[0]);
  if(gs.length<2)return x0;
  let i=gs.findIndex((q,k)=>k<gs.length-1&&x0>=q[0]&&x0<=gs[k+1][0]); if(i<0)i=x0<gs[0][0]?0:gs.length-2;
  const a=gs[i],b=gs[i+1],f=(x0-a[0])/(b[0]-a[0]);
  let xa=xAtY(a[1],y1),xb=xAtY(b[1],y1); if(!fin(xb))xb=xa+(b[0]-a[0]); if(!fin(xa))return NaN;
  if(mode==='parallel')return x0+(xa-a[0]);   // slide parallel to the guide line just below the entry point (matches Bell's WAT examples)
  return xa+f*(xb-xa);
}
function followX(guides,x0,y0,x1){
  const gs=guides.map(g=>[yAtX(g,x0,false),g]).filter(q=>fin(q[0])).sort((a,b)=>a[0]-b[0]);
  if(gs.length<2)return y0;
  let i=gs.findIndex((q,k)=>k<gs.length-1&&y0>=q[0]&&y0<=gs[k+1][0]); if(i<0)i=y0<gs[0][0]?0:gs.length-2;
  const a=gs[i],b=gs[i+1],f=(y0-a[0])/(b[0]-a[0]);
  const ya=yAtX(a[1],x1,true),yb=yAtX(b[1],x1,true); return ya+f*(yb-ya);
}
const lin=(c,p)=>c[0]*p+c[1], inv=(c,v)=>(v-c[1])/c[0];
// PA on the y axis, OAT family -> x  (WAT, flight path, acceleration)
function famTop(t,pa,oat){
  const y=inv(t.y,pa); const xs=t.fam.map(f=>xAtY(f.pts,y)); const x=fam(oat,t.fam.map(f=>f.v),xs,false);
  return {y,x,v:lin(t.x,x)};
}
function wat(o,pa,oat,hwf,gwMax){
  const t=o.top, r=famTop(t,pa,oat); r.gw0=r.v; r.gw=r.gw0; r.path=[[[r.x,t.panel[3]],[r.x,r.y]],[[t.panel[0],r.y],[r.x,r.y]]];
  if(o.wind&&hwf>0&&fin(r.x)){
    const w=o.wind, y0=w.panel[1], yh=inv(w.y,hwf);
    const L=w.lims.map(l=>[l.v??0,l.y]); const ylim=L.length?fam(oat,L.map(a=>a[0]),L.map(a=>a[1]),false):Infinity;
    const y1=Math.min(yh,ylim), xw=inv(w.x,r.gw0), x1=Math.min(followY(w.guides,xw,y0,y1,'parallel'),w.xmax??Infinity);
    r.gw=lin(w.x,x1); r.windLimited=ylim<yh; r.hwUsed=lin(w.y,y1);
    const P=[]; for(let k=0;k<=12;k++){const yy=y0+(y1-y0)*k/12; P.push([Math.min(followY(w.guides,xw,y0,yy,'parallel'),w.xmax??Infinity),yy]);}
    r.path.push([[r.x,t.panel[3]],[r.x,y0]].concat(P),[[x1,y1],[x1,w.panel[3]]]);
  }
  r.gw=Math.min(r.gw,gwMax); return r;
}
// hover-style: OAT x -> PA family y -> result line x
function hl(o,pa,oat){
  const x0=inv(o.xOat,oat), y=fam(pa,o.pa.map(f=>f.v),o.pa.map(f=>yAtX(f.pts,x0,true)),true);
  const xs=o.lines.map(l=>xAtY(l,y)).filter(fin); const x=xs.length?Math.max(...xs):NaN;
  let st='ok'; if(o.maxoat){const xm=xAtY(o.maxoat,Math.max(o.L[1],Math.min(o.L[3],y))); if(fin(xm)&&x0>xm+0.8)st='oatmax';}
  if(y<o.L[1]-0.5)st='hd';
  return {x0,y,x,v:lin(o.xR,x),st,path:[[[x0,o.L[3]],[x0,y],[x,y],[x,o.R[3]]]]};
}
// drop down / height loss
function dd(o,pa,oat,gw,da){
  const x0=inv(o.xOat,oat), y=fam(pa,o.pa.map(f=>f.v),o.pa.map(f=>yAtX(f.pts,x0,true)),true);
  const xl=o.M[0], xg=inv(o.xGw,gw); let y2=Math.min(followX(o.guides,xl,y,xg),o.M[3]);
  const xs=o.da.map(f=>xAtY(f.pts,y2)); const x=fam(Math.max(da,o.da[0].v),o.da.map(f=>f.v),xs,false);
  const P=[]; for(let k=0;k<=12;k++){const xx=xl+(xg-xl)*k/12; P.push([xx,Math.min(followX(o.guides,xl,y,xx),o.M[3])]);}
  return {v:lin(o.xR,x),x,y,y2,path:[[[x0,o.L[3]],[x0,y],[xl,y]],P,[[xg,y2],[x,y2],[x,o.R[3]]]]};
}
// flight path / acceleration: top family + lower panel guides (headwind or gross weight)
function fx(o,pa,oat,low){
  const t=o.top, r=famTop(t,pa,oat); r.v0=r.v; const L=o.low;
  r.path=[[[t.panel[0],r.y],[r.x,r.y],[r.x,t.panel[3]]]];
  if(L&&low!=null&&fin(r.x)){
    const y0=L.panel[1], y1=Math.min(inv(L.y,low),L.panel[3]); const x1=followY(L.guides,r.x,y0,y1);
    r.v=lin(t.x,x1);
    const P=[]; for(let k=0;k<=12;k++){const yy=y0+(y1-y0)*k/12; P.push([followY(L.guides,r.x,y0,yy),yy]);}
    r.path.push([[r.x,t.panel[3]]].concat(P),[[x1,y1],[x1,L.panel[3]]]);
  }
  return r;
}
// gross-weight interpolation across sheets {gw:..}
function sheets(list,gw,f){
  const s=list.slice().sort((a,b)=>a.gw-b.gw); let i=0; while(i<s.length-2&&gw>s[i+1].gw)i++;
  const a=s[i],b=s[i+1]; const ra=f(a),rb=f(b); const t=(gw-a.gw)/(b.gw-a.gw);
  return {v:ra.v+(rb.v-ra.v)*t, a:ra, b:rb, sa:a, sb:b};
}
root.CATA={xAtY,yAtX,fam,followY,followX,wat,hl,dd,fx,sheets,lin,inv};
})(typeof window!=='undefined'?window:globalThis);
