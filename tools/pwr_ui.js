// ================= POWER ASSURANCE + DENSITY ALTITUDE =================
const PWR=(function(){
  const fin=Number.isFinite;
  const pv=(c,y)=>(c[0]*y+c[1])*y+c[2];
  // y where a (near straight) line reaches x — Newton from the linear guess
  function yOnLine(c,x){ let y=(x-c[2])/c[1]; for(let i=0;i<6;i++){const f=pv(c,y)-x, d=2*c[0]*y+c[1]; y-=f/d;} return y; }
  function interp(arr,v){ // arr sorted by v ascending: [{v,val}]
    let i=0; while(i<arr.length-2&&v>arr[i+1].v)i++;
    const a=arr[i],b=arr[i+1]; return a.val+(b.val-a.val)*(v-a.v)/(b.v-a.v);
  }
  // chart: torque -> up to PA -> right to OAT -> down to max allowable value
  function check(C,pa,oat,tq){
    const notes=[]; let PAc=pa, OATc=oat;
    if(pa>10000){PAc=10000;notes.push('Pressure altitude above 10,000 ft — chart edge (10,000 ft) used.');}
    if(pa<-2000){PAc=-2000;notes.push('Pressure altitude below −2,000 ft — chart edge used.');}
    if(oat>50){OATc=50;notes.push('OAT above 50 °C — chart edge used.');}
    if(oat<-50){OATc=-50;notes.push('OAT below −50 °C — chart edge used.');}
    const xT=C.tq[0]*tq+C.tq[1];
    const ys=C.pa.map(l=>({v:l.v,val:yOnLine(l.c,xT)})).sort((a,b)=>a.v-b.v);
    const y=interp(ys,PAc);
    const xs=C.oat.map(l=>({v:l.v,val:pv(l.c,y)})).sort((a,b)=>a.v-b.v);
    const x=interp(xs,OATc);
    let v=(x-C.out[1])/C.out[0], status='ok';
    if(y>C.bot+1||y<C.top-1){status='off';notes.push(`Torque ${tq}% is outside the chart at this altitude — reading extrapolated.`);}
    const capped=v>C.lim; if(capped)v=C.lim;
    return {xT,y,x:Math.min(x,C.out[0]*C.lim+C.out[1]),v,status,notes,capped};
  }
  // ISA density altitude (matches FM-5 Fig 4-2 within ~10 ft)
  function sigma(pa,oat){const T0=288.15,L=0.0019812,g=5.25588;return Math.pow(1-L*pa/T0,g)*T0/(oat+273.15);}
  return {check,sigma};
})();

function calcPWR(ctx){
  const {pa,oat,da}=ctx, fin=Number.isFinite;
  const E=[1,2].map(n=>({n,tq:val('pq'+n),mgt:val('pm'+n),ng:val('pn'+n)}));
  const msgs=[], COL=['#14883e','#0a6ad1'], R={mgt:[],ng:[]}, cards=[];
  const fm=(v,d,u)=>fin(v)?(v>=0?'+':'−')+Math.abs(v).toFixed(d)+u:'—';
  const card=(k,v,s,cls)=>`<div class="r ${cls}"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`;
  let anyBad=false;
  for(const e of E){
    const c=COL[e.n-1];
    if(!fin(e.tq)){cards.push(`<div class="paceng" style="border-color:${c}"><div class="rlab" style="color:${c}">ENGINE ${e.n} — enter test torque</div></div>`);continue;}
    const rm=PWR.check(PW.pwr_mgt,pa,oat,e.tq), rn=PWR.check(PW.pwr_ng,pa,oat,e.tq);
    R.mgt.push([e,rm]); R.ng.push([e,rn]);
    for(const m of [...rm.notes,...rn.notes]) if(!msgs.some(x=>x[1]===m)) msgs.push(['',m]);
    if(e.tq>66.2)msgs.push(['bad',`Engine ${e.n}: torque above the 66.2% check limit.`]);
    if(fin(e.mgt)&&e.mgt>825)msgs.push(['bad',`Engine ${e.n}: MGT above the 825 °C check limit.`]);
    if(fin(e.ng)&&e.ng>102)msgs.push(['bad',`Engine ${e.n}: NG above the 102.0% check limit.`]);
    if((rm.capped||rn.capped)&&!msgs.some(x=>x[1].startsWith('A reading')))msgs.push(['','A reading reached the chart “Do Not Exceed” edge (825 °C / 102% NG) — that value is used as the limit.']);
    const mm=fin(e.mgt)?rm.v-e.mgt:NaN, nm=fin(e.ng)?rn.v-e.ng:NaN, both=fin(mm)&&fin(nm), ok=both&&mm>=0&&nm>=0;
    if((fin(mm)&&mm<0)||(fin(nm)&&nm<0))anyBad=true;
    cards.push(`<div class="paceng" style="border-color:${c}"><div class="rlab" style="color:${c}">ENGINE ${e.n} — ${both?(ok?'PASS':'BELOW MIN SPEC'):'—'}</div><div class="grid3" style="grid-template-columns:1fr 1fr">`+
      card('MGT margin',fm(mm,0,' °C'),'max allowable '+rm.v.toFixed(0)+' °C',fin(mm)?(mm>=0?'ok':'bad'):'')+
      card('NG margin',fm(nm,1,' %'),'max allowable '+rn.v.toFixed(1)+' %',fin(nm)?(nm>=0?'ok':'bad'):'')+'</div></div>');
  }
  $('pwrRes').innerHTML=cards.join('');
  if(anyBad)msgs.push(['bad','Margin below zero: engine below minimum specification — published performance may not be achievable. Determine the cause as soon as practical.']);
  $('pwrMsgs').innerHTML=msgs.map(m=>`<div class="msg ${m[0]}">${m[1]}</div>`).join('');
  let ch='';
  for(const k of ['mgt','ng']){
    const C=PW['pwr_'+k], P=[], M=[];
    for(const [e,r] of R[k]){
      const c=COL[e.n-1], yc=Math.max(C.top,Math.min(C.bot,r.y));
      P.push({pts:[[r.xT,C.bot],[r.xT,yc]],arrow:true,c},{pts:[[r.xT,yc],[r.x,yc]],arrow:true,c},{pts:[[r.x,yc],[r.x,C.bot]],arrow:true,c});
      M.push([r.x,yc,(k==='mgt'?r.v.toFixed(0)+' °C':r.v.toFixed(1)+'%'),c,e.n===2?1:0]);
    }
    ch+=`<div class="chart">${svgChart(C,C.key,P,M)}<div class="cap"><span>${C.src} Fig ${C.fig} · Power assurance (${C.name}) — ground / hover, PT6T-9</span><span>p.${C.page}</span></div></div>`;
  }
  $('pwrCharts').innerHTML=ch;

  // ---------- density altitude ----------
  const D=PW.da, s=PWR.sigma(pa,oat), inv=1/Math.sqrt(s), kc=val('kcas');
  const X=t=>D.x[0]*t+D.x[1], Y=h=>D.y[0]*h+D.y[1];
  const x=X(Math.max(-50,Math.min(60,oat))), y=Y(Math.max(-8000,Math.min(24000,da)));
  const off=oat<-50||oat>60||da<-8000||da>24000;
  $('daRes').innerHTML=`<div class="r"><div class="k">Density altitude</div><div class="v">${Math.round(da).toLocaleString('en-US')}</div><div class="s">ft</div></div>
    <div class="r"><div class="k">Density ratio <span style="text-transform:none">σ</span></div><div class="v">${s.toFixed(4)}</div><div class="s">ρ / ρ₀</div></div>
    <div class="r"><div class="k" style="text-transform:none">1/√σ</div><div class="v">${inv.toFixed(3)}</div><div class="s">TAS = CAS × 1/√σ</div></div>
    <div class="r"><div class="k">True airspeed</div><div class="v">${fin(kc)?(kc*inv).toFixed(1):'—'}</div><div class="s">KTAS at ${fin(kc)?kc:'—'} KCAS</div></div>`;
  const P=[{pts:[[x,D.bot],[x,y]],arrow:true},{pts:[[x,y],[D.xL,y]],arrow:true},{pts:[[x,y],[D.xR,y]],arrow:true}];
  $('daChart').innerHTML=`<div class="chart">${svgChart(D,'da',P,[[x,y,Math.round(da).toLocaleString('en-US')+' ft'],[D.xR,y,inv.toFixed(3),null,1]])}<div class="cap"><span>${D.src} Fig ${D.fig} · Density altitude${off?' · outside chart range (value computed)':''}</span><span>p.${D.page}</span></div></div>`;
}
