// ================= CAT-A UI =================
const PROF={A:{name:'Side step — elevated heliport',fig:'Part A',hd:6000},B:{name:'Backup — surface / elevated heliport',fig:'Part B',hd:13000},
            C:{name:'Runway',fig:'Part C',hd:13000},D:{name:'Offset backup — surface / elevated heliport',fig:'Part D',hd:13000}};
const SH=(p,k)=>Object.keys(CA).filter(x=>x.startsWith(p+'_'+k+'_')).map(x=>CA[x]);
const f1=v=>fin(v)?v.toFixed(1):'—';
function caChart(C,key,pathsArr,marks,cap){
  const P=[]; for(const seg of pathsArr){ if(seg.length>1)P.push({pts:seg,arrow:true}); }
  return `<div class="chart">${svgChart(C,key,P,marks||[])}<div class="cap"><span>${cap}</span><span>p.${C.page}</span></div></div>`;
}
function calcCatA(ctx){
  const {pa,oat,gw,rw,ws,da}=ctx, E=window.CATA, p=$('caProf').value, PR=PROF[p];
  document.querySelectorAll('.caA').forEach(e=>e.style.display=p==='A'?'':'none');
  const msgs=[], rows=[], charts=[];
  // ---- wind ----
  const rel=((rw%360)+360)%360, hw=ws*Math.cos(rw*Math.PI/180), xw=Math.abs(ws*Math.sin(rw*Math.PI/180));
  let windOK=true, side=$('caSide').value;
  const within=(lo,hi)=>{const a=rel>180?rel-360:rel; return a>=lo&&a<=hi;};
  if(ws>0){
    if(p==='A'){ if(side==='R'?!within(-90,45):!within(-45,90)){windOK=false;msgs.push(`Wind ${rel}° is outside the Part A limits (pad on ${side==='R'?'right: 90° left to 45° right':'left: 45° left to 90° right'} of the nose).`);} }
    else if(!within(-90,90)){windOK=false;msgs.push('Wind must be within ±90° of the takeoff/landing direction.');}
    if(xw>10.05){windOK=false;msgs.push(`Crosswind ${xw.toFixed(1)} kt exceeds the 10 kt limit.`);}
  }
  const credit=ws>0&&within(-45,45)&&hw>0; const hwf=credit?0.5*hw:0;
  if(ws>0&&!credit&&windOK)msgs.push('No headwind credit: wind is not within ±45° of the takeoff direction.');
  // ---- WAT / max GW ----
  const use745=p==='C'&&gw>11900;
  const W=E.wat(CA[p+'_wat'],pa,oat,hwf,11900);
  let maxGW=W.gw, gwCap=11900;
  if(p==='C'){ const W2=E.wat(CA.C745_wat,pa,oat,0,12200); ctx.W2=W2; maxGW=Math.max(W.gw,W2.gw); gwCap=12200; }
  const hdLim=PR.hd, hdOut=da>hdLim+1;
  if(hdOut)msgs.push(`Density altitude ${f0(da)} ft is above the ${f0(hdLim)} ft H<sub>D</sub> limit for this profile.`);
  // drop-down limit (Part A)
  let ddMaxGW=null;
  if(p==='A'){
    const allow=parseFloat($('caDrop').value);
    if(fin(allow)&&allow<90){ let lo=8000,hi=11900; const ddv=g=>E.dd(CA.A_dd,pa,oat,g,da).v;
      if(ddv(lo)>allow) ddMaxGW=NaN; else { for(let k=0;k<30;k++){const m=(lo+hi)/2; if(ddv(m)<=allow)lo=m; else hi=m;} ddMaxGW=lo; }
      msgs.push('Allowable drop-down below 90 ft: maximum weight from the Drop Down Height chart (Fig 4A-3).'); }
  }
  let limGW=Math.min(maxGW, ddMaxGW??Infinity);
  const gwOK=gw<=floor10(limGW)&&!hdOut;
  rows.push(['Maximum gross weight',`${f0(floor10(limGW))} lb`,`zero wind ${f0(floor10(W.gw0))} lb${hwf>0?` · factored headwind ${hwf.toFixed(1)} kt${W.windLimited?' (OAT limit line)':''} → ${f0(floor10(W.gw))} lb`:''}${p==='C'?` · FMS-74.5 Part D (103%, to 12,200 lb): ${f0(floor10(ctx.W2.gw))} lb`:''}${ddMaxGW!=null?` · drop-down limit ${fin(ddMaxGW)?f0(floor10(ddMaxGW)):'below chart'} lb`:''}`, gwOK?'ok':'bad']);
  charts.push(caChart(CA[p+'_wat'],p+'_wat',W.path,[[W.x,W.y,f0(floor10(W.gw0))+' lb']],`FMS-62.5 Fig ${CA[p+'_wat'].fig} · WAT`));
  if(p==='C')charts.push(caChart(CA.C745_wat,'C745_wat',ctx.W2.path,[[ctx.W2.x,ctx.W2.y,f0(floor10(ctx.W2.gw0))+' lb']],`FMS-74.5 Fig ${CA.C745_wat.fig} · WAT (to 12,200 lb)`));
  const G=Math.max(8000,Math.min(gw,use745?12200:11900));
  // ---- Segment 1 ----
  let seg1=NaN, climbH=165;
  if(p==='A'){
    const T=E.hl(CA.A_todist,pa,oat), DD=E.dd(CA.A_dd,pa,oat,G,da);
    seg1=Math.max(T.v,500); const h=parseFloat($('caSurf').value);
    climbH=200+DD.v;
    rows.push(['Drop-down height',`${f1(DD.v)} ft`,`height loss ${f1(35+DD.v)} ft (35 ft + drop down) · at ${f0(G)} lb`,'']);
    if(fin(h))rows.push(['Obstacle clearance',`${f1(h-DD.v)} ft`,`takeoff surface ${f0(h)} ft − drop down · minimum 15 ft`,h-DD.v>=15?'ok':'bad']);
    rows.push(['Segment 1 — TDP to V<sub>TOSS</sub>',`${f0(seg1)} ft`,`OEI takeoff distance (Fig 4A-4, minimum 500 ft)${T.st!=='ok'?' · outside chart':''}`,T.st==='ok'?'':'bad']);
    charts.push(caChart(CA.A_dd,'A_dd',DD.path,[[DD.x,DD.y2,f1(DD.v)+' ft']],'FMS-62.5 Fig 4A-3 · Drop down height'));
    charts.push(caChart(CA.A_todist,'A_todist',T.path,[[T.x,T.y,f0(T.v)+' ft']],'FMS-62.5 Fig 4A-4 · OEI takeoff distance'));
  } else if(p==='B'||p==='D'){
    const TH=E.hl(CA[p+'_tdph'],pa,oat), HL=E.dd(CA[p+'_hloss'],pa,oat,G,da), T=E.hl(CA[p+'_todist'],pa,oat);
    seg1=T.v;
    rows.push(['Height of TDP / LDP',`${f0(TH.v)} ft`,`Fig ${CA[p+'_tdph'].fig}`,TH.st==='ok'?'':'bad']);
    rows.push(['Height loss from TDP',`${f0(HL.v)} ft`,`Fig ${CA[p+'_hloss'].fig} · at ${f0(G)} lb · WAT chart assures 15 ft ground clearance`,'']);
    rows.push(['Segment 1 — TDP to V<sub>TOSS</sub> & 35 ft',`${f0(seg1)} ft`,`OEI takeoff distance (Fig ${CA[p+'_todist'].fig})`,T.st==='ok'?'':'bad']);
    charts.push(caChart(CA[p+'_tdph'],p+'_tdph',TH.path,[[TH.x,TH.y,f0(TH.v)+' ft']],`FMS-62.5 Fig ${CA[p+'_tdph'].fig} · TDP/LDP height`));
    charts.push(caChart(CA[p+'_hloss'],p+'_hloss',HL.path,[[HL.x,HL.y2,f0(HL.v)+' ft']],`FMS-62.5 Fig ${CA[p+'_hloss'].fig} · Height loss`));
    charts.push(caChart(CA[p+'_todist'],p+'_todist',T.path,[[T.x,T.y,f0(T.v)+' ft']],`FMS-62.5 Fig ${CA[p+'_todist'].fig} · OEI takeoff distance`));
  } else {
    const k=use745?'C745':'C', R=E.hl(CA[k+'_rto'],pa,oat), TD=E.hl(CA[k+'_tdp'],pa,oat), T=E.hl(CA[k+'_todist'],pa,oat), L=E.hl(CA.C_ldg,pa,oat);
    seg1=T.v; const src=use745?'FMS-74.5':'FMS-62.5';
    rows.push(['Rejected takeoff distance',`${f0(R.v)} ft`,`${src} Fig ${CA[k+'_rto'].fig} · minimum runway 625 ft`,R.st==='ok'?'':'bad']);
    rows.push(['Takeoff decision point',`${f1(TD.v)} s`,`${src} Fig ${CA[k+'_tdp'].fig} · seconds from start of takeoff`,TD.st==='ok'?'':'bad']);
    rows.push(['Segment 1 — 10 ft hover to V<sub>TOSS</sub> & 35 ft',`${f0(seg1)} ft`,`${src} Fig ${CA[k+'_todist'].fig}`,T.st==='ok'?'':'bad']);
    rows.push(['OEI landing distance (50 ft obstacle)',`${f0(L.v)} ft`,'FMS-62.5 Fig 4C-10 · 40 KIAS, zero wind',L.st==='ok'?'':'bad']);
    for(const [kk,r,t] of [[k+'_rto',R,'Rejected takeoff distance'],[k+'_tdp',TD,'TDP (seconds)'],[k+'_todist',T,'OEI takeoff distance'],['C_ldg',L,'OEI landing distance']])
      charts.push(caChart(CA[kk],kk,r.path,[[r.x,r.y,(kk.endsWith('tdp')?f1(r.v)+' s':f0(r.v)+' ft')]],`${kk.startsWith('C745')?'FMS-74.5':'FMS-62.5'} Fig ${CA[kk].fig} · ${t}`));
  }
  // ---- Segment 2 & 3 ----
  const fp1=SH(p,'fp1').concat(p==='C'&&use745?SH('C745','fp1'):[]), fp2=SH(p,'fp2').concat(p==='C'&&use745?SH('C745','fp2'):[]);
  const s2=E.sheets(fp1,G,s=>E.fx(s,pa,oat,hwf)), s3=E.sheets(fp2,G,s=>E.fx(s,pa,oat,hwf));
  const accC=use745?CA.C745_acc:CA[p+'_acc'], AC=E.fx(accC,pa,oat,G);
  let acc=AC.v; const accOver=!(acc<=2800); if(accOver)acc=3900;
  const g2=s2.v/100, g3=s3.v/100, d2=climbH/g2, d3=800/g3;
  rows.push([`Segment 2 — climb gradient at V<sub>TOSS</sub>`,`${f1(s2.v)} %`,`at ${f0(G)} lb (sheets ${s2.sa.gw.toLocaleString()} / ${s2.sb.gw.toLocaleString()} lb) · ${hwf>0?`factored headwind ${hwf.toFixed(1)} kt`:'zero wind'}`,g2>0?'':'bad']);
  rows.push(['  climb distance',`${f0(d2)} ft`,`${f0(climbH)} ft ÷ ${f1(s2.v)} %${p==='A'?' (200 ft + drop down)':' (35 → 200 ft)'}`,'']);
  rows.push(['  level acceleration V<sub>TOSS</sub> → V<sub>Y</sub>',`${f0(acc)} ft`,accOver?'beyond the 2,800 ft chart boundary — 3,900 ft used':`Fig ${accC.fig} · zero wind`,'']);
  rows.push([`Segment 3 — climb gradient at V<sub>Y</sub>`,`${f1(s3.v)} %`,`200 → 1000 ft · ${hwf>0?`factored headwind ${hwf.toFixed(1)} kt`:'zero wind'}`,g3>0?'':'bad']);
  rows.push(['  climb distance',`${f0(d3)} ft`,`800 ft ÷ ${f1(s3.v)} %`,'']);
  const total=seg1+d2+acc+d3;
  rows.push(['<b>Total takeoff distance to 1000 ft</b>',`<b>${f0(total)} ft</b>`,'Segment 1 + 2 + level acceleration + 3','tot']);
  if(p==='B'||p==='D')rows.push(['Landing distance (50 ft obstacle)','200 ft','all allowable gross weights','']);
  const fpc=(r,s,title)=>caChart(s,s.key,r.path,[[r.x,r.y,f1(r.v0)+' %']],`${s.key.startsWith('C745')?'FMS-74.5':'FMS-62.5'} Fig ${s.fig} · ${title} · ${s.gw.toLocaleString()} lb → ${f1(r.v)} %`);
  charts.push(fpc(s2.a,s2.sa,'V<sub>TOSS</sub> to 200 ft'),fpc(s2.b,s2.sb,'V<sub>TOSS</sub> to 200 ft'));
  charts.push(caChart(accC,use745?'C745_acc':p+'_acc',AC.path,[[AC.x,AC.y,'']],`Fig ${accC.fig} · Level acceleration → ${f0(AC.v)} ft`));
  charts.push(fpc(s3.a,s3.sa,'200 to 1000 ft'),fpc(s3.b,s3.sb,'200 to 1000 ft'));
  msgs.push('Gradients are interpolated linearly between the gross-weight sheets, as in the FMS-62.5 examples. Power assurance must meet the FM-5 chart before CAT-A operations.');
  $('caRes').innerHTML='<table class="ca">'+rows.map(([a,b,c,s])=>`<tr class="${s}"><td class="l">${a}</td><td class="v">${b}</td><td class="n">${c}</td></tr>`).join('')+'</table>';
  $('caMsgs').innerHTML=msgs.map(m=>`<div class="msg">${m}</div>`).join('');
  $('caCharts').innerHTML=charts.join('');
}
