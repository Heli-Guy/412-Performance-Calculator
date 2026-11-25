// ================= STAY UP WEIGHT (OEI at cruise) =================
function zeroRoc(list,pa,oat){
  const E=window.CATA, s=list.slice().sort((a,b)=>a.gw-b.gw);
  const pts=s.map(sh=>({sh,r:E.fx(sh,pa,oat,null)})).filter(q=>fin(q.r.v));
  if(!pts.length) return {st:'out'};
  const top=pts[pts.length-1], bot=pts[0];
  if(top.r.v>=0) return {st:'max',gw:top.sh.gw,roc:top.r.v,a:top,b:top};
  if(bot.r.v<0) return {st:'below',gw:bot.sh.gw,roc:bot.r.v,a:bot,b:bot};
  for(let i=0;i<pts.length-1;i++){const a=pts[i],b=pts[i+1]; if(a.r.v>=0&&b.r.v<0){const t=a.r.v/(a.r.v-b.r.v); return {st:'ok',gw:a.sh.gw+t*(b.sh.gw-a.sh.gw),a,b};}}
  return {st:'out'};
}
function calcStay(ctx){
  const {elev,alt,oat,gw}=ctx, E=window.CATA;
  const cAlt=parseFloat($('calt').value), cOatIn=parseFloat($('coat').value);
  const cruise=fin(cAlt)?cAlt:elev, auto=!fin(cOatIn), cOat=auto?Math.round((oat-2*(cruise-elev)/1000)*10)/10:cOatIn;
  $('coat').placeholder=`${fin(cOat)?cOat:''} (auto)`;
  const cpa=cruise+(29.92-alt)*1000, cda=B.densityAltitude(cpa,cOat), isa=15-2*cpa/1000;
  const LIST={mcp:Object.keys(RC).filter(k=>RC[k].grp==='roc_oei_off').map(k=>RC[k]), se2:Object.values(SE)};
  const MAXS={mcp:12200,se2:11900};
  const res={}, msgs=[];
  for(const k of ['mcp','se2']){
    const z=zeroRoc(LIST[k],cpa,cOat), G=Math.max(k==='mcp'?7000:8000,Math.min(gw,MAXS[k])), S=E.sheets(LIST[k],G,s=>E.fx(s,cpa,cOat,null));
    res[k]={z,S,G};
  }
  const lbs=v=>`${f0(Math.floor(v/10)*10)} Lbs`;
  const zTxt=z=>z.st==='ok'?lbs(z.gw):z.st==='max'?lbs(z.gw):z.st==='below'?`< ${f0(z.gw)} Lbs`:'– – – –';
  const zSub=(z,k)=>z.st==='ok'?`zero ROC · ${k==='mcp'?'FM-5 Fig 4-9':'FMS-62.5 Fig 4A-8'}${gw>z.gw?' · <b>your GW will descend</b>':` · +${f0(z.gw-gw)} Lbs margin`}`:
    z.st==='max'?`max GW — still climbing at ${f0(Math.floor(z.roc/5)*5)} fpm`:z.st==='below'?'descending even at the lightest chart weight':'outside the charts at this altitude / OAT';
  const cls=z=>z.st==='ok'?(gw<=z.gw?'ok':'bad'):z.st==='max'?'ok':'bad';
  const head=`Cruise PA ${f0(cpa)} ft · OAT ${cOat} °C${auto?` (estimated: ${oat} °C at ${f0(elev)} ft − 2 °C / 1,000 ft)`:''} · ISA ${isa<=cOat?'+':'−'}${Math.abs(cOat-isa).toFixed(1)} · DA ${f0(cda)} ft`;
  let h=`<p class="legend" style="margin:0 0 8px">${head}</p><div class="rlab">STAY-UP</div><div class="res" id="stayW">`+
    card('Max continuous OEI',zTxt(res.mcp.z),zSub(res.mcp.z,'mcp'),cls(res.mcp.z))+
    card('2-min OEI · V<sub>TOSS</sub>',zTxt(res.se2.z),zSub(res.se2.z,'se2'),cls(res.se2.z))+'</div>'+
    `<div class="rlab" style="margin-top:12px">OEI ROC AT YOUR WEIGHT (${f0(gw)} LBS)</div><div class="res">`+
    card('Max continuous OEI',rocV(res.mcp.S.v),`V<sub>Y</sub> 70 KIAS · FM-5 Fig 4-9${gw>12200?' · 12,200 lb sheet':''}`,res.mcp.S.v>0?'ok':'bad')+
    card('2-min OEI',rocV(res.se2.S.v),`V<sub>TOSS</sub> 40 KIAS · 103% N<sub>R</sub> · FMS-62.5 Fig 4A-8${gw>11900?' · 11,900 lb sheet':''}`,res.se2.S.v>0?'ok':'bad')+'</div>';
  msgs.push('Stay-up weight is the gross weight that gives zero rate of climb on one engine at the cruise pressure altitude and OAT, interpolated between the gross-weight sheets. Use it, with the OEI MCP rate of climb, to confirm you can hold MOCA on one engine at night or IFR. If cruise OAT is left blank it is estimated from the surface OAT at the standard lapse rate (2 °C / 1,000 ft); real temperatures aloft can differ (inversions), so enter the forecast or actual OAT when known.');
  if(cpa>20000)msgs.push('Cruise pressure altitude above the 20,000 ft maximum operating altitude.');
  h+=`<div class="msgs">${msgs.map(m=>`<div class="msg">${m}</div>`).join('')}</div>`;
  // charts: the two sheets bracketing the stay-up weight, with the zero-ROC weight marked
  const chartsFor=(k,title)=>{ const z=res[k].z; if(!z.a) return '';
    const pair=z.a===z.b?[z.a]:[z.a,z.b];
    return `<h3 class="sub">${title}</h3><div class="pair">`+pair.map(q=>{const r=q.r,s=q.sh; return `<div class="chart">${svgChart(s,s.key,[{pts:r.path[0],arrow:true,c:'#14883e'}],[[r.x,r.y,Math.round(r.v)+' fpm',null]])}<div class="cap"><span>${s.src} Fig ${s.fig} · ${s.gw.toLocaleString()} lb sheet at cruise</span><span>p.${s.page}</span></div></div>`;}).join('')+'</div>'; };
  h+=chartsFor('mcp','OEI · Max continuous OEI power — FM-5 Fig 4-9 at cruise')+chartsFor('se2','OEI · 2-min OEI power — FMS-62.5 Fig 4A-8 (V<sub>TOSS</sub> 40 KIAS) at cruise');
  $('stayBody').innerHTML=h;
}
