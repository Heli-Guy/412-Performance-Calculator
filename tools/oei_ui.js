// ================= OEI hover (MD-5 Fig 4-3A / 4-3B, manufacturer's data) =================
function oeiHover(o,pa,oat,hw){
  const y=o.pa[0]-o.pa[1]*pa/1000, vs=o.fam.map(f=>f.v), xs=o.fam.map(f=>B.xAtY(f.pts,y));
  let st='ok'; if(pa>8000)st='hd'; if(pa<0)st='low';
  const mo=o.maxoat.length?B.xAtY(o.maxoat,y):NaN;
  const x=window.CATA.fam(oat,vs,xs,false); if(fin(mo)&&x<mo-0.5)st='oatmax';
  const G=yy=>o.gw[2]-(yy-o.gw[0])/o.gw[1]*1000, res={};
  for(const s of o.skid){ const [p,q]=[s.pts[0],s.pts[s.pts.length-1]]; const yy=p[1]+(x-p[0])*(q[1]-p[1])/(q[0]-p[0]); res[s.v]={gw:G(yy),y:yy}; }
  const hx=o.hwx[0]+o.hwx[1]*Math.max(0,Math.min(30,hw||0)), hy=B.yAtX(o.hw,hx,false), dg=hw>0&&fin(hy)?(o.dg[0]-hy)/o.dg[1]*1000:0;
  return {x,y,res,dg,hx,hy,st};
}
function oeiChart(o,r,gw){
  const P=[], M=[];
  if(fin(r.x)){ const y60=r.res[60].y, y4=r.res[4].y;
    P.push({pts:[[o.xr[0],r.y],[r.x,r.y]],arrow:true},{pts:[[r.x,r.y],[r.x,y60]],arrow:true},{pts:[[r.x,y60],[o.xr[1],y60]],arrow:true});
    P.push({pts:[[r.x,y4],[o.xr[1],y4]],arrow:true,c:'#e07b00',dash:'4 3'});
    M.push([o.xr[1],y60,`OGE ${f0(floor10(r.res[60].gw))}`,null,1],[o.xr[1],y4,`4 ft ${f0(floor10(r.res[4].gw))}`,'#e07b00',1]);
    if(r.dg>0&&fin(r.hy)){ P.push({pts:[[r.hx,o.dg[0]],[r.hx,r.hy],[o.hwx[0]+o.hwx[1]*30,r.hy]],arrow:true}); M.push([o.hwx[0]+o.hwx[1]*30,r.hy,`+${f0(Math.round(r.dg/10)*10)}`,null,1]); }
  }
  return `<div class="chart">${svgChart(o,o.key,P,M)}<div class="cap"><span>BHT-412-MD-5 Fig ${o.fig} · Single Engine Maximum Gross Weight for Hovering · ${o.power} · heater OFF (manufacturer's data)</span><span>p.${o.page}</span></div></div>`;
}
// ================= EHP kit — maximum continuous mast torque below 60 KIAS (FMS-80.5 Fig 1A-8 / 1B-8) =================
function calcMT(pa,oat,p9){
  const o=MT[p9?'mt_p9':'mt_std'], r=window.CATA.hl(o,pa,oat), q=Math.min(100,Math.max(81,r.v));
  const da=B.densityAltitude(pa,oat), hd=p9?16000:14000;
  const st=da>hd+1?'hd':r.st; const ok=st==='ok'&&fin(q);
  const card=`<div class="r ${ok?'':'bad'}"><div class="k">Max continuous Q<sub>M</sub> · below 60 KIAS</div><div class="v">${ok?q.toFixed(1)+' %':'– – – –'}</div><div class="s">${ok?`EHP kit · FMS-80.5 Fig ${o.fig}${p9?' (9 pax or less)':''} · above this the 5-min takeoff range applies (81–100% Q<sub>M</sub>)`:(st==='hd'?`above the ${f0(hd)} ft H<sub>D</sub> limit`:st==='oatmax'?'above max OAT':'outside the chart')}</div></div>`;
  const chart=`<div class="chart">${svgChart(o,o.key,[{pts:r.path[0],arrow:true}],[[r.x,r.y,ok?q.toFixed(1)+' %':'']])}<div class="cap"><span>FMS-80.5 Fig ${o.fig} · Maximum Continuous Mast Torque Limitations — Below 60 KIAS · may exceed max continuous engine limits in some conditions</span><span>p.${o.page}</span></div></div>`;
  return {card,chart,q,ok};
}
