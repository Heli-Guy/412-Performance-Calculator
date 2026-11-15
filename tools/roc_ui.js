// ================= RATE OF CLIMB UI =================
function calcROC(ctx){
  const {pa,oat,gw,heat}=ctx, E=window.CATA;
  const doors=$('rocDoors').value==='open';
  const G=Math.max(7000,Math.min(gw,12200));
  const rows=[], charts=[], msgs=[];
  const LBL={top:'Twin engine — takeoff power',mcp:'Twin engine — max continuous power',oei:'Single engine — max continuous OEI power'};
  for(const pw of ['top','mcp','oei']){
    let h=heat; if(pw==='oei'&&h!=='off'){ h='off'; msgs.push('OEI rate of climb is published for heater OFF only — heater-off chart shown.'); }
    const list=Object.keys(RC).filter(k=>RC[k].grp===`roc_${pw}_${h}`).map(k=>RC[k]);
    if(list.length<2){ rows.push([LBL[pw],'—','no chart for this configuration','']); continue; }
    const S=E.sheets(list,G,s=>E.fx(s,pa,oat,null));
    let v=S.v; if(doors)v-=S.sa.doors||275;
    const src=s=>`${s.src} Fig ${s.fig}`;
    rows.push([LBL[pw],`${fin(v)?Math.round(v).toLocaleString('en-US'):'—'} ft/min`,
      `at ${f0(G)} lb (sheets ${S.sa.gw.toLocaleString()} / ${S.sb.gw.toLocaleString()} lb) · ${h==='off'?'heater off':h==='on'?'heater on':'winterization heater on'}${doors?` · doors open: −${S.sa.doors||275} ft/min, climb at 60 KIAS`:' · 70 KIAS'}`, fin(v)&&v>0?'':'bad']);
    for(const [r,s] of [[S.a,S.sa],[S.b,S.sb]]){
      const P=[{pts:r.path[0],arrow:true}];
      charts.push(`<div class="chart">${svgChart(s,s.key,P,[[r.x,r.y,Math.round(r.v)+' ft/min']])}<div class="cap"><span>${src(s)} · ${LBL[pw]} · ${s.gw.toLocaleString()} lb</span><span>p.${s.page}</span></div></div>`);
    }
  }
  if(gw>11900)msgs.push('Above 11,900 lb the 12,200 lb sheets come from FMS-74.5.');
  if(gw<7000)msgs.push('Gross weight below 7,000 lb — 7,000 lb sheet used.');
  $('rocRes').innerHTML='<table class="ca">'+rows.map(([a,b,c,s])=>`<tr class="${s}"><td class="l">${a}</td><td class="v">${b}</td><td class="n">${c}</td></tr>`).join('')+'</table>';
  $('rocMsgs').innerHTML=[...new Set(msgs)].map(m=>`<div class="msg">${m}</div>`).join('');
  $('rocCharts').innerHTML=charts.join('');
}
