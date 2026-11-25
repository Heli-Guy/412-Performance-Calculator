// ================= CAT-A UI (Helipad: Parts A / B / D · Runway: Part C) =================
const PROF={A:{name:'Side step — elevated heliport',hd:6000},B:{name:'Backup — surface / elevated heliport',hd:13000},
            C:{name:'Runway',hd:13000},D:{name:'Offset backup — surface / elevated heliport',hd:13000}};
const SH=(p,k)=>Object.keys(CA).filter(x=>x.startsWith(p+'_'+k+'_')).map(x=>CA[x]);
const f1=v=>fin(v)?v.toFixed(1):'—';
const DASH='– – – –';
const c10=v=>fin(v)?Math.ceil(v/10)*10:NaN;
function caChart(C,key,pathsArr,marks,cap){
  const P=[]; for(const seg of pathsArr){ if(seg.length>1)P.push({pts:seg,arrow:true}); }
  return `<div class="chart">${svgChart(C,key,P,marks||[])}<div class="cap"><span>${cap}</span><span>p.${C.page}</span></div></div>`;
}
const card=(k,v,s,cls)=>`<div class="r big ${cls||''}"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s||''}</div></div>`;

// MD-5 Fig 4-11 sheet 1 — backup obstacle clearance (distances back from the takeoff point, heights above the takeoff surface)
const BK={X:d=>498.4-1.061*d, Y:h=>542.2-2.23*h,
  lim(d){ if(d<49)return 0; if(d<=140)return 14*(d-49)/91; if(d<=385)return 14+81*(d-140)/245; return 95+4.6*Math.min(15,d-385)/15; },
  back:tdp=>(tdp-20)/0.2857};

// single-engine rates of climb used on both CAT-A tabs
function caRoc(pa,oat,gw){
  const E=window.CATA, out={};
  const se=Object.values(SE), G=Math.max(8000,Math.min(gw,11900));
  const S=E.sheets(se,G,s=>E.fx(s,pa,oat,null)); out.se2={v:S.v,S,G,over:gw>11900};
  const oei=Object.keys(RC).filter(k=>RC[k].grp==='roc_oei_off').map(k=>RC[k]);
  const G2=Math.max(7000,Math.min(gw,12200)), S2=E.sheets(oei,G2,s=>E.fx(s,pa,oat,null)); out.mcp={v:S2.v,S:S2,G:G2};
  return out;
}
const rocV=v=>fin(v)?(v<0?'−':'')+Math.abs(Math.floor(v/5)*5).toLocaleString('en-US')+' fpm':DASH;
function rocCards(R,blk){
  return card('2-min OEI ROC',blk?DASH:rocV(R.se2.v),blk?'':`V<sub>TOSS</sub> 40 KIAS · 103% N<sub>R</sub> · FMS-62.5 Fig 4A-8${R.se2.over?' · 11,900 lb sheet':''}`,blk?'':(R.se2.v>0?'ok':'bad'))+
         card('OEI MCP ROC',blk?DASH:rocV(R.mcp.v),blk?'':'V<sub>Y</sub> 70 KIAS · continuous OEI · FM-5 Fig 4-9',blk?'':(R.mcp.v>0?'ok':'bad'));
}
function rocCharts(R){
  const out=[];
  for(const [r,s] of [[R.se2.S.a,R.se2.S.sa],[R.se2.S.b,R.se2.S.sb]]) out.push(caChart(s,s.key,r.path,[[r.x,r.y,Math.round(r.v)+' fpm']],`FMS-62.5 Fig ${s.fig} · 2-min OEI at V<sub>TOSS</sub> · ${s.gw.toLocaleString()} lb`));
  for(const [r,s] of [[R.mcp.S.a,R.mcp.S.sa],[R.mcp.S.b,R.mcp.S.sb]]) out.push(caChart(s,s.key,r.path,[[r.x,r.y,Math.round(r.v)+' fpm']],`${s.src} Fig ${s.fig} · continuous OEI at V<sub>Y</sub> · ${s.gw.toLocaleString()} lb`));
  return out;
}

// profile figure with this takeoff's values written on it
function profFig(p,V,blk){
  const im=PF['prof_'+p], [x,y,w,h]=im;
  const T=(tx,ty,t,o={})=>`<text x="${tx}" y="${ty}" font-size="${o.fs||9}" font-weight="700" fill="${o.c||(blk?'#5b6b7b':'#d0021b')}" text-anchor="${o.a||'start'}" stroke="#fff" stroke-width="2.6" paint-order="stroke" font-family="Helvetica,Arial">${t}</text>`;
  const D=v=>blk?'– – –':v;
  let s=`<svg viewBox="${x} ${y} ${w} ${h+46}" xmlns="http://www.w3.org/2000/svg"><rect x="${x}" y="${y}" width="${w}" height="${h+46}" fill="#fff"/><image href="${IMG['prof_'+p]}" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="none"/>`;
  if(p==='A'){
    s+=T(60,402,D(`${V.tdp} ft`))+T(200,492,D(V.surf),{a:'middle'})+T(298,458,D(`${V.dd} ft`))+T(272,512,D(V.clr),{a:'middle'})+T(470,262,D(`${V.c200} ft`))+T(215,555,D(`${V.seg1} ft`),{a:'middle'});
  } else if(p==='B'||p==='D'){
    s+=T(62,338,D(`TDP ${V.tdp} ft`),{fs:10})+T(372,474,D(`${V.clr} clearance`),{a:'middle'})+T(500,452,D('35 ft'))+T(497,322,D('200 ft'),{a:'end'});
  } else {
    s+=T(300,452,D(`TDP ${V.tdpS} s`),{a:'end'})+T(318,545,D(`rejected T/O ${V.rto} ft`),{a:'middle',fs:10})+T(70,450,D(`OEI landing ${V.ldg} ft`),{fs:10});
  }
  // distance strip
  const segs=V.strip.filter(q=>fin(q[1])&&q[1]>0), tot=segs.reduce((a,q)=>a+q[1],0), y0=y+h+14;
  if(segs.length&&!blk){ let cx=x+20; const W=w-40;
    for(const [lab,d] of segs){ const sw=W/segs.length, x2=cx+sw;
      s+=`<line x1="${cx}" y1="${y0}" x2="${x2}" y2="${y0}" stroke="#1f2d3d" stroke-width="1"/><line x1="${cx}" y1="${y0-5}" x2="${cx}" y2="${y0+5}" stroke="#1f2d3d"/><line x1="${x2}" y1="${y0-5}" x2="${x2}" y2="${y0+5}" stroke="#1f2d3d"/>`;
      s+=T((cx+x2)/2,y0-4,lab,{a:'middle',fs:8,c:'#5b6b7b'})+T((cx+x2)/2,y0+13,d.toLocaleString('en-US')+' ft',{a:'middle',fs:9});
      cx=x2; }
    s+=T(x+w/2,y0+28,`total to 1,000 ft above the takeoff surface: ${tot.toLocaleString('en-US')} ft`,{a:'middle',fs:9,c:'#1f2d3d'});
  }
  return s+'</svg>';
}

function caCompute(p,ctx){
  const {pa,oat,gw,rw,ws,da,heat,acOn}=ctx, E=window.CATA, PR=PROF[p];
  const msgs=[], charts=[], V={};
  // ---- wind ----
  const rel=((rw%360)+360)%360, hw=ws*Math.cos(rw*Math.PI/180), xw=Math.abs(ws*Math.sin(rw*Math.PI/180));
  let windOK=true; const side=$('caSide').value;
  const within=(lo,hi)=>{const a=rel>180?rel-360:rel; return a>=lo&&a<=hi;};
  if(ws>0){
    if(p==='A'){ if(side==='R'?!within(-90,45):!within(-45,90)){windOK=false;msgs.push(['bad',`Wind ${rel}° is outside the Part A limits (pad on ${side==='R'?'right: 90° left to 45° right':'left: 45° left to 90° right'} of the takeoff direction).`]);} }
    else if(!within(-90,90)){windOK=false;msgs.push(['bad','Wind must be within ±90° of the takeoff / landing direction.']);}
    if(xw>10.05){windOK=false;msgs.push(['bad',`Crosswind ${xw.toFixed(1)} kt exceeds the 10 kt CAT-A limit.`]);}
  }
  const credit=ws>0&&within(-45,45)&&hw>0; const hwf=credit?0.5*hw:0;
  if(ws>0&&!credit&&windOK)msgs.push(['','No headwind credit: wind is not within ±45° of the takeoff direction.']);
  const cfgBlk=heat!=='off'||acOn;
  if(cfgBlk)msgs.unshift(['bad','Heater and/or air conditioner ON: CAT-A not valid. FMS-62.5 requires cabin heat OFF and air conditioner OFF for CAT-A takeoff and landing, and all CAT-A charts are for heater OFF.']);
  // ---- WAT / max GW ----
  const use745=p==='C'&&gw>11900;
  const W=E.wat(CA[p+'_wat'],pa,oat,hwf,11900);
  let maxGW=W.gw, W2=null;
  if(p==='C'){ W2=E.wat(CA.C745_wat,pa,oat,0,12200); maxGW=Math.max(W.gw,W2.gw); }
  const hdOut=da>PR.hd+1;
  if(hdOut)msgs.push(['bad',`Density altitude ${f0(da)} ft is above the ${f0(PR.hd)} ft H<sub>D</sub> limit for this profile.`]);
  let ddMaxGW=null;
  if(p==='A'){
    const allow=parseFloat($('caDrop').value);
    if(fin(allow)&&allow<90){ let lo=8000,hi=11900; const ddv=g=>E.dd(CA.A_dd,pa,oat,g,da).v;
      if(ddv(lo)>allow) ddMaxGW=NaN; else { for(let k=0;k<30;k++){const m=(lo+hi)/2; if(ddv(m)<=allow)lo=m; else hi=m;} ddMaxGW=lo; }
      msgs.push(['','Allowable drop-down below 90 ft: maximum weight limited by the Drop Down Height chart (Fig 4A-3).']); }
  }
  const limGW=floor10(Math.min(maxGW, ddMaxGW??Infinity));
  const over=!(gw<=limGW), blkW=!windOK||hdOut, blk=blkW||over||cfgBlk;
  if(over&&!blkW)msgs.unshift(['bad',`Gross weight ${f0(gw)} Lbs exceeds the CAT-A ${p==='C'?'runway':'helipad'} maximum takeoff weight (${f0(limGW)} Lbs): CAT-A data not valid.`]);
  V.maxGW=limGW; V.wat0=floor10(W.gw0); V.wind=floor10(W.gw)-floor10(W.gw0); V.ddLim=ddMaxGW;
  charts.push(caChart(CA[p+'_wat'],p+'_wat',W.path,[[W.x,W.y,f0(floor10(W.gw0))+' lb']],`FMS-62.5 Fig ${CA[p+'_wat'].fig} · WAT`));
  if(W2)charts.push(caChart(CA.C745_wat,'C745_wat',W2.path,[[W2.x,W2.y,f0(floor10(W2.gw0))+' lb']],`FMS-74.5 Fig ${CA.C745_wat.fig} · WAT (to 12,200 lb)`));
  const G=Math.max(8000,Math.min(gw,use745?12200:11900));
  // ---- segment 1 ----
  let climbH=165;
  if(p==='A'){
    const T=E.hl(CA.A_todist,pa,oat), DD=E.dd(CA.A_dd,pa,oat,G,da), h=parseFloat($('caSurf').value);
    V.seg1=c10(Math.max(T.v,500)); V.dd=Math.ceil(DD.v); V.tdp=35; climbH=200+DD.v; V.c200=Math.round(200);
    V.surf=fin(h)?`${f0(h)} ft`:'heliport height'; V.clrV=fin(h)?h-DD.v:NaN; V.clr=fin(h)?`${f0(Math.floor(h-DD.v))} ft clearance`:'15 ft minimum';
    if(fin(h)&&h-DD.v<15&&!blk)msgs.push(['bad',`Obstacle clearance ${f0(Math.floor(h-DD.v))} ft is less than the 15 ft minimum (takeoff surface ${f0(h)} ft − drop down ${f0(Math.ceil(DD.v))} ft).`]);
    V.st1=T.st;
    charts.push(caChart(CA.A_dd,'A_dd',DD.path,[[DD.x,DD.y2,f1(DD.v)+' ft']],'FMS-62.5 Fig 4A-3 · Drop down height'));
    charts.push(caChart(CA.A_todist,'A_todist',T.path,[[T.x,T.y,f0(T.v)+' ft']],'FMS-62.5 Fig 4A-4 · OEI takeoff distance'));
  } else if(p==='B'||p==='D'){
    const TH=E.hl(CA[p+'_tdph'],pa,oat), HL=E.dd(CA[p+'_hloss'],pa,oat,G,da), T=E.hl(CA[p+'_todist'],pa,oat);
    const ob=Math.max(0,parseFloat($('caFly').value)||0);
    const need=HL.v+15+ob; V.tdpChart=Math.ceil(TH.v); V.tdp=Math.ceil(Math.max(TH.v,need)); V.hl=Math.ceil(HL.v); V.ob=ob;
    V.raised=need>TH.v+0.5; V.clrV=V.tdp-HL.v; V.clr=`${f0(Math.floor(V.clrV))} ft`;
    V.seg1=c10(T.v); V.st1=T.st; V.thSt=TH.st;
    charts.push(caChart(CA[p+'_tdph'],p+'_tdph',TH.path,[[TH.x,TH.y,f0(TH.v)+' ft']],`FMS-62.5 Fig ${CA[p+'_tdph'].fig} · TDP/LDP height`));
    charts.push(caChart(CA[p+'_hloss'],p+'_hloss',HL.path,[[HL.x,HL.y2,f0(HL.v)+' ft']],`FMS-62.5 Fig ${CA[p+'_hloss'].fig} · Height loss`));
    charts.push(caChart(CA[p+'_todist'],p+'_todist',T.path,[[T.x,T.y,f0(T.v)+' ft']],`FMS-62.5 Fig ${CA[p+'_todist'].fig} · OEI takeoff distance`));
    // backup obstacle (MD-5 Fig 4-11)
    const bh=parseFloat($('caBkh').value), bd=parseFloat($('caBkd').value);
    V.bk={on:fin(bh)&&fin(bd),h:bh,d:bd};
    if(V.bk.on){ const b=V.bk; b.dT=BK.back(V.tdp); b.behind=bd>b.dT; b.allow=BK.lim(bd); b.inside=!b.behind&&bh>b.allow+0.05; b.beyond=V.tdp>130;
      if(b.beyond&&!blk)msgs.push(['',`TDP ${f0(V.tdp)} ft is above the 130 ft maximum shown on MD-5 Fig 4-11 — backup obstacle assessed with the chart's line extended.`]);
      if(b.inside&&!blk)msgs.unshift(['bad',`Backup obstacle ${f0(bh)} ft at ${f0(bd)} ft is taller than the ${f0(Math.floor(b.allow))} ft allowed there (MD-5 Fig 4-11: TDP ${f0(V.tdp)} ft backs up to about ${f0(b.dT)} ft) — CAT-A backup profile not valid.`]); }
  } else {
    const k=use745?'C745':'C', R=E.hl(CA[k+'_rto'],pa,oat), TD=E.hl(CA[k+'_tdp'],pa,oat), T=E.hl(CA[k+'_todist'],pa,oat), L=E.hl(CA.C_ldg,pa,oat);
    const src=use745?'FMS-74.5':'FMS-62.5';
    V.seg1=c10(T.v); V.rto=c10(Math.max(R.v,625)); V.tdpS=f1(TD.v); V.ldg=c10(L.v); V.st1=T.st; V.src=src; V.k=k;
    V.rtoSt=R.st; V.ldgSt=L.st;
    for(const [kk,r,t] of [[k+'_rto',R,'Rejected takeoff distance'],[k+'_tdp',TD,'TDP (seconds)'],[k+'_todist',T,'OEI takeoff distance'],['C_ldg',L,'OEI landing distance']])
      charts.push(caChart(CA[kk],kk,r.path,[[r.x,r.y,(kk.endsWith('tdp')?f1(r.v)+' s':f0(r.v)+' ft')]],`${kk.startsWith('C745')?'FMS-74.5':'FMS-62.5'} Fig ${CA[kk].fig} · ${t}`));
  }
  if(V.st1&&V.st1!=='ok'&&!blk)msgs.push(['bad','OEI takeoff distance: conditions fall outside the chart.']);
  // ---- segments 2 & 3 ----
  const fp1=SH(p,'fp1').concat(p==='C'&&use745?SH('C745','fp1'):[]), fp2=SH(p,'fp2').concat(p==='C'&&use745?SH('C745','fp2'):[]);
  const s2=E.sheets(fp1,G,s=>E.fx(s,pa,oat,hwf)), s3=E.sheets(fp2,G,s=>E.fx(s,pa,oat,hwf));
  const accC=use745?CA.C745_acc:CA[p+'_acc'], AC=E.fx(accC,pa,oat,G);
  let acc=AC.v; V.accOver=!(acc<=2800); if(V.accOver)acc=3900;
  V.g2=s2.v; V.g3=s3.v; V.d2=c10(climbH/(s2.v/100)); V.acc=c10(acc); V.d3=c10(800/(s3.v/100)); V.climbH=Math.round(climbH);
  if(!(s2.v>0)||!(s3.v>0))msgs.push(['bad','Climb gradient zero or negative — CAT-A climb not achievable.']);
  V.total=V.seg1+V.d2+V.acc+V.d3;
  V.strip=[[p==='C'?'hover → V_TOSS / 35 ft':'TDP → V_TOSS',V.seg1],[`climb to 200 ft · ${f1(s2.v)} %`,V.d2],['accelerate to V_Y',V.acc],[`200 → 1,000 ft · ${f1(s3.v)} %`,V.d3]].map(q=>[q[0].replace('V_TOSS','VTOSS').replace('V_Y','VY'),q[1]]);
  const fpc=(r,s,title)=>caChart(s,s.key,r.path,[[r.x,r.y,f1(r.v0)+' %']],`${s.key.startsWith('C745')?'FMS-74.5':'FMS-62.5'} Fig ${s.fig} · ${title} · ${s.gw.toLocaleString()} lb → ${f1(r.v)} %`);
  charts.push(fpc(s2.a,s2.sa,'V<sub>TOSS</sub> to 200 ft'),fpc(s2.b,s2.sb,'V<sub>TOSS</sub> to 200 ft'));
  charts.push(caChart(accC,use745?'C745_acc':p+'_acc',AC.path,[[AC.x,AC.y,'']],`Fig ${accC.fig} · Level acceleration → ${f0(AC.v)} ft`));
  charts.push(fpc(s3.a,s3.sa,'200 to 1000 ft'),fpc(s3.b,s3.sb,'200 to 1000 ft'));
  V.hwf=hwf; V.G=G; V.s2=s2; V.s3=s3; V.accC=accC;
  return {V,msgs,charts,blk,blkW,over,cfgBlk};
}

function calcCatA(ctx){
  const R=caRoc(ctx.pa,ctx.oat,ctx.gw);
  // ---------- Helipad (Part A / B / D) ----------
  let p=$('caProf').value; if(p==='C'){p='A';$('caProf').value='A';}
  document.querySelectorAll('.caA').forEach(e=>e.style.display=p==='A'?'':'none');
  document.querySelectorAll('.caB').forEach(e=>e.style.display=p==='A'?'none':'');
  {
    const r0=caCompute(p,ctx), {V,msgs,charts,blkW,over,cfgBlk}=r0, blk=r0.blk||!!(V.bk&&V.bk.on&&V.bk.inside), d=v=>blk?DASH:v;
    const mx=blkW||cfgBlk?DASH:`${f0(V.maxGW)} Lbs`, mxs=blkW||cfgBlk?'':(V.ddLim!=null?'drop-down limited (Fig 4A-3)':`WAT ${f0(V.wat0)}${V.wind>0?` · +wind ${f0(V.wind)}`:''}`);
    let h=card('Max T/O weight',mx,mxs,blkW||cfgBlk?'':(over?'bad':'ok'))+
      card('GW margin',blkW||cfgBlk?DASH:`${over?'−':'+'}${f0(Math.abs(V.maxGW-ctx.gw))} Lbs`,blkW||cfgBlk?'':(over?'over WAT limit':'within WAT'),blkW||cfgBlk?'':(over?'bad':'ok'))+
      card('TDP / LDP',d(`${f0(V.tdp)} ft`),blk?'':(p==='A'?'above the takeoff surface (fixed)':(V.raised?`raised for ${V.ob?f0(V.ob)+' ft flyaway obstacle + ':''}15 ft clearance (chart ${f0(V.tdpChart)} ft)`:`Fig ${p==='B'?'4B-3':'4D-3'} · 15 ft clearance`)));
    if(p==='A') h+=card('Obstacle clearance',d(fin(V.clrV)?`${f0(Math.floor(V.clrV))} ft`:DASH),blk?'':(fin(V.clrV)?`surface − ${f0(V.dd)} ft drop down · min 15 ft`:'enter takeoff surface height'),blk||!fin(V.clrV)?'':(V.clrV>=15?'ok':'bad'));
    else { const b=V.bk; h+=b&&b.on?card('Backup obstacle',r0.blk?DASH:(b.inside?'Not clear':'Clear'),r0.blk?'no TDP — cannot be assessed':`${f0(b.h)} ft at ${f0(b.d)} ft · `+(b.behind?`behind the TDP point (${f0(b.dT)} ft back)`:`max ${f0(Math.floor(b.allow))} ft there`)+' · MD-5 Fig 4-11',r0.blk?'':(b.inside?'bad':'ok'))
                                  :card('Backup obstacle','—','enter height and distance behind the takeoff point',''); }
    h+=card(p==='A'?'Drop-down height':'Height loss',d(`${f0(p==='A'?V.dd:V.hl)} ft`),blk?'':(p==='A'?`35 ft + drop down = ${f0(35+V.dd)} ft height loss · Fig 4A-3`:`from TDP · Fig ${p==='B'?'4B-4':'4D-4'} · zero-wind weight`));
    h+=card('OEI takeoff',d(`${f0(V.seg1)} ft`),blk?'':`TDP → V<sub>TOSS</sub> 40 KIAS${p==='A'?' · min 500 ft':' · 35 ft'}`);
    h+=card('Stage 1 climb',d(`${f0(V.d2)} ft`),blk?'':`${p==='A'?'V<sub>TOSS</sub> → 200 ft above surface':'35 → 200 ft'} · ${f1(V.g2)} % gradient`);
    h+=card('Level acceleration',d(`${f0(V.acc)} ft`),blk?'':(V.accOver?'beyond 2,800 ft chart edge — 3,900 ft used':'V<sub>TOSS</sub> → V<sub>Y</sub> 70 KIAS · zero wind'));
    h+=card('Stage 2 climb',d(`${f0(V.d3)} ft`),blk?'':`200 → 1,000 ft · ${f1(V.g3)} % gradient · V<sub>Y</sub>`);
    h+=card('Total distance',d(`${f0(V.total)} ft`),blk?'':'TDP to 1,000 ft above the takeoff surface');
    h+='<div class="rowdiv"></div>'+rocCards(R,blk);
    $('heli').innerHTML=h;
    msgs.push(['','Climb gradients are interpolated between the gross-weight sheets, as in the FMS-62.5 examples. Power assurance must meet the FM-5 chart before CAT-A operations.']);
    $('heliMsgs').innerHTML=msgs.map(m=>`<div class="msg ${m[0]}">${m[1]}</div>`).join('');
    $('heliProf').innerHTML=`<div class="chart">${profFig(p,{tdp:f0(V.tdp),surf:V.surf,dd:f0(V.dd),clr:V.clr,c200:200,seg1:f0(V.seg1),strip:V.strip},blk)}<div class="cap"><span>FMS-62.5 Fig ${p==='A'?'3A-1':p==='B'?'3B-1':'3D-1'} · Emergency Landing/Takeoff Profile — ${PROF[p].name}, with this takeoff's values</span><span>${blk?'no valid CAT-A solution':'distances not to scale'}</span></div></div>`;
    let ch=charts.slice();
    if(p!=='A'){ // backup obstacle chart
      const b=V.bk, P=[], M=[], C={im:PF.bk411,page:61};
      if(fin(V.tdp)&&!blk){ const dT=Math.min(400,BK.back(V.tdp)); P.push({pts:[[BK.X(0),BK.Y(20)],[BK.X(dT),BK.Y(20+0.2857*dT)]],c:'#0a6ad1',w:1.6,dash:'5 3'}); M.push([BK.X(dT),BK.Y(20+0.2857*dT),`TDP ${f0(V.tdp)} ft · ${f0(BK.back(V.tdp))} ft back`,'#0a6ad1']); }
      if(b&&b.on){ const dd=Math.min(400,b.d), col=b.inside?'#d0021b':'#14883e'; P.push({pts:[[BK.X(dd),BK.Y(0)],[BK.X(dd),BK.Y(Math.min(b.h,140))]],c:col,w:4}); M.push([BK.X(dd),BK.Y(Math.min(b.h,140)),`obstacle ${f0(b.h)} ft @ ${f0(b.d)} ft`,col]); }
      ch.unshift(`<div class="chart">${svgChart(C,'bk411',P,M)}<div class="cap"><span>BHT-412-MD-5 Fig 4-11 · Backup Obstacle Clearance Chart (manufacturer's data)</span><span>${b&&b.on?(b.inside?'obstacle not clear':(b.behind?'clear · behind TDP point':`clear · max ${f0(Math.floor(b.allow))} ft at ${f0(b.d)} ft`)):'enter backup obstacle height and distance'}</span></div></div>`);
    }
    $('heliCharts').innerHTML=ch.concat(rocCharts(R)).join('');
  }
  // ---------- Runway (Part C) ----------
  {
    const {V,msgs,charts,blk,blkW,over,cfgBlk}=caCompute('C',ctx), d=v=>blk?DASH:v;
    let h=card('Max T/O weight',blkW||cfgBlk?DASH:`${f0(V.maxGW)} Lbs`,blkW||cfgBlk?'':(V.maxGW>11900?'FMS-74.5 Part D (12,200 lb)':`WAT ${f0(V.wat0)}${V.wind>0?` · +wind ${f0(V.wind)}`:''}`),blkW||cfgBlk?'':(over?'bad':'ok'))+
      card('GW margin',blkW||cfgBlk?DASH:`${over?'−':'+'}${f0(Math.abs(V.maxGW-ctx.gw))} Lbs`,blkW||cfgBlk?'':(over?'over WAT limit':'within WAT'),blkW||cfgBlk?'':(over?'bad':'ok'))+
      card('Rejected T/O dist',d(`${f0(V.rto)} ft`),blk?'':`runway length required · ${V.src} Fig ${CA[V.k+'_rto'].fig} · min 625 ft`)+
      card('OEI landing dist',d(`${f0(V.ldg)} ft`),blk?'':'from 50 ft · 40 KIAS · Fig 4C-10 · zero wind')+
      card('TDP',d(`${V.tdpS} s`),blk?'':`seconds from start of takeoff · ${V.src} Fig ${CA[V.k+'_tdp'].fig}`)+
      card('OEI takeoff',d(`${f0(V.seg1)} ft`),blk?'':`10 ft hover → V<sub>TOSS</sub> 40 KIAS & 35 ft · Fig ${CA[V.k+'_todist'].fig}`)+
      card('Stage 1 climb',d(`${f0(V.d2)} ft`),blk?'':`35 → 200 ft · ${f1(V.g2)} % gradient`)+
      card('Level acceleration',d(`${f0(V.acc)} ft`),blk?'':(V.accOver?'beyond 2,800 ft chart edge — 3,900 ft used':'V<sub>TOSS</sub> → V<sub>Y</sub> 70 KIAS'))+
      card('Stage 2 climb',d(`${f0(V.d3)} ft`),blk?'':`200 → 1,000 ft · ${f1(V.g3)} % gradient`)+
      card('Total distance',d(`${f0(V.total)} ft`),blk?'':'start of takeoff to 1,000 ft');
    h+='<div class="rowdiv"></div>'+rocCards(R,blk);
    $('rwy').innerHTML=h;
    msgs.push(['','Climb gradients are interpolated between the gross-weight sheets, as in the FMS-62.5 examples. Above 11,900 lb the FMS-74.5 Part D charts are used.']);
    $('rwyMsgs').innerHTML=msgs.map(m=>`<div class="msg ${m[0]}">${m[1]}</div>`).join('');
    $('rwyProf').innerHTML=`<div class="chart">${profFig('C',{tdpS:V.tdpS,rto:f0(V.rto),ldg:f0(V.ldg),strip:V.strip},blk)}<div class="cap"><span>FMS-62.5 Fig 3C-1 · Emergency Landing/Takeoff Profile — Runway, with this takeoff's values</span><span>${blk?'no valid CAT-A solution':'distances not to scale'}</span></div></div>`;
    $('rwyCharts').innerHTML=charts.concat(rocCharts(R)).join('');
  }
}
