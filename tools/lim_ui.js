// ================= LIMITATIONS — BHT-412-FM-5 Section 1 (+ supplements) =================
const LIM=(function(){
  // Fig 1-6 VNE placard: indicated VNE (KIAS) by PA (x1000 ft) and OAT (°C); null = outside envelope
  const PAS=[0,2,4,6,8,10,12,14,16,18,20], OATS=[51.7,40,20,0,-10,-20,-30,-40];
  const T=[
    [137,null,null,null,null,null,null,null,null,null,null],
    [140,134,128,122,null,null,null,null,null,null,null],
    [140,139,133,127,121,115,109,103,97,null,null],
    [140,140,140,133,127,121,115,109,103,96,91],
    [140,140,140,140,131,124,118,112,106,100,94],
    [140,140,140,138,133,127,121,115,108,102,96],
    [140,139,134,129,124,120,115,110,106,101,97],
    [134,129,124,120,116,111,107,102,98,94,90]];
  // VNE at one PA column for any OAT: linear between rows, extrapolated from the two
  // nearest colder rows where the warmer cell is blank on the placard
  function col(j,oat){
    const pts=OATS.map((t,i)=>[t,T[i][j]]).filter(p=>p[1]!=null).sort((a,b)=>a[0]-b[0]);
    if(oat<=pts[0][0])return {v:pts[0][1],ex:false};
    for(let i=0;i<pts.length-1;i++)if(oat<=pts[i+1][0]){const[a,va]=pts[i],[b,vb]=pts[i+1];return {v:va+(vb-va)*(oat-a)/(b-a),ex:false};}
    const n=pts.length,[a,va]=pts[n-2],[b,vb]=pts[n-1];
    return {v:vb+(vb-va)/(b-a)*(oat-b),ex:true};
  }
  function vne(pa,oat){
    const k=Math.max(0,Math.min(20,pa/1000)); let j=Math.min(9,Math.floor(k/2)); const f=(k-PAS[j])/2;
    const a=col(j,oat),b=col(j+1,oat);
    return {v:Math.min(140,a.v+(b.v-a.v)*f),ex:(f<1&&a.ex)||(f>0&&b.ex)};
  }
  const maxOat=pa=>Math.min(51.7,51.7-2*Math.max(0,pa)/1000);
  // Fig 1-3: max sideward flight / crosswind at a hover vs density altitude
  const sideLim=da=>da<=2000?45:da>=8000?35:45-10*(da-2000)/6000;
  return {vne,maxOat,sideLim,T,PAS,OATS};
})();

function calcLimits(ctx){
  const {pa,oat,da,gw,rw,ws,cfg,heat}=ctx, fin=Number.isFinite;
  const fuel=$('limFuel').value, rows=[], add=(st,txt,why)=>rows.push(`<div class="fuelrow ${st}"><span class="ic">${st==='ok'?'✓':st==='warn'?'!':'✕'}</span><span>${txt}</span><span class="why">${why}</span></div>`);
  const mo=LIM.maxOat(pa), daLim=cfg==='p9'?16000:14000;
  add(pa<=20000?'ok':'bad',`Pressure altitude <b>${f0(pa)} ft</b>`,'Max operating PA 20,000 ft (FM-5 1-8)');
  add(oat<=mo?'ok':'bad',`OAT <b>${oat} °C</b> ${oat<=mo?'≤':'>'} max <b>${mo.toFixed(1)} °C</b>`,'51.7 °C at sea level, −2 °C / 1,000 ft PA (FM-5 1-11)');
  add(oat>=-40?'ok':'bad',`OAT ${oat>=-40?'at or above':'below'} minimum <b>−40 °C</b>`,'All altitudes (FM-5 1-11)');
  add(da<=daLim?'ok':'bad',`Density altitude <b>${f0(da)} ft</b> ${da<=daLim?'≤':'>'} <b>${f0(daLim)} ft</b>`,`Takeoff, landing &amp; IGE manoeuvres (${cfg==='p9'?'FMS-35.5, 9 pax or less':'FM-5 1-8'})`);
  if(fuel==='a') add(oat>-30?'ok':'bad',`Jet A / A-1 / JP-5 / JP-8: OAT ${oat>-30?'above':'not above'} <b>−30 °C</b>`,'Jet B / JP-4 usable at all temperatures (FM-5 1-17-A)');
  else add('ok','Jet B / JP-4 / NATO F-40: all ambient temperatures','FM-5 1-17-A');
  if(heat!=='off') add(oat<=21?'ok':'bad',`${heat==='win'?'Winterization heater':'Heater'} ON at <b>${oat} °C</b> — ${oat<=21?'permitted (max 21 °C OAT)':'<b>not permitted</b> above 21 °C OAT'}`,heat==='win'?'FMS-1.5 1A-21':'Placard, FM-5 Fig 1-6');
  else add('ok','Heater OFF',oat<=21?'Heater may be used up to 21 °C OAT':'Do not operate heater above 21 °C OAT');
  add(oat>=-25?'ok':'warn',`Cold-soaked battery start (53 Ah): ${oat>=-25?'permitted':'<b>not permitted</b>'} at ${oat} °C`,'Minimum −25 °C for the 53 Ah battery fitted to all CCG 412s (FM-5 1-12-A)');
  const gmax=12200, gok=gw>=6400&&gw<=gmax;
  add(gok?(gw>11900?'warn':'ok'):'bad',`Gross weight <b>${f0(gw)} lb</b>`,gw>11900&&gw<=gmax?'Above 11,900 lb: FMS-74.5 (12,200 lb) limitations and charts apply':'Min 6,400 lb · max 11,900 lb (12,200 lb with FMS-74.5) · WAT chart below');

  // hover wind (Fig 1-3)
  const r=((rw%360)+360)%360, xw=Math.abs(ws*Math.sin(r*Math.PI/180)), tail=r>=150&&r<=210, sl=LIM.sideLim(Math.max(da,-2000));
  if(tail) add(ws<=35?'ok':'bad',`Wind from ${r}° is a downwind hover: <b>${f0(ws)} kt</b> ${ws<=35?'≤':'>'} 35 kt`,'Relative wind 150°–210°, IGE or OGE, all Hd (Fig 1-3 note 1)');
  else add(xw<=sl+1e-9?'ok':'bad',`Crosswind at a hover <b>${xw.toFixed(0)} kt</b> ${xw<=sl+1e-9?'≤':'>'} <b>${sl.toFixed(0)} kt</b> at ${f0(da)} ft Hd`,'45 kt to 2,000 ft Hd, 35 kt above 8,000 ft Hd; rearward / tailwind 35 kt (Fig 1-3)');
  if(!tail&&((r>=30&&r<=95)||(r>=180&&r<=270))&&ws>0) add('warn',`Relative wind ${r}° is in an OGE critical azimuth`,r<=95?'30°–95°: pedal margin may be limited (Fig 1-3 note 2)':'180°–270°: aft cyclic may be limited with AFCS hardover (note 3)');
  $('limChecks').innerHTML=rows.join('');

  // VNE
  const V=LIM.vne(pa,oat), base=Math.floor(V.v);
  const ext=cfg==='ext'?Math.max(0,80-(da>10000?2.5*(da-10000)/1000:0)):null;
  const head=ext!=null?Math.min(base,Math.floor(ext)):base;
  $('limVne').innerHTML=`<div class="r ${oat>mo?'bad':''}"><div class="k">V<sub>NE</sub> (placard)</div><div class="v">${oat>mo?'—':base}</div><div class="s">KIAS at ${f0(pa)} ft · ${oat} °C${V.ex&&oat<=mo?' · extrapolated':''}</div></div>
    ${ext!=null?`<div class="r warn"><div class="k">V<sub>NE</sub> external load</div><div class="v">${Math.floor(ext)}</div><div class="s">KIAS · FMS-9.5 (80 to 10,000 ft Hd, −2.5 kt/1,000 ft)</div></div>`:''}
    <div class="r"><div class="k">Above 81% mast torque</div><div class="v">${Math.min(105,head)}</div><div class="s">KIAS</div></div>
    <div class="r"><div class="k">Autorotation</div><div class="v">${Math.min(pa>10000?80:105,head)}</div><div class="s">KIAS · 105 to 10,000 ft PA, 80 above</div></div>
    <div class="r"><div class="k">One autopilot</div><div class="v">${Math.min(115,head)}</div><div class="s">KIAS</div></div>`;
  // placard table with current cell bracket highlighted
  const k=Math.max(0,Math.min(20,pa/1000)), j=Math.min(9,Math.floor(k/2));
  const oi0=LIM.OATS.findIndex((t,i)=>i<LIM.OATS.length-1&&oat<=t&&oat>=LIM.OATS[i+1]), oi=oi0<0?(oat>51.7?0:LIM.OATS.length-2):oi0;
  let tb='<table class="ar vne"><tr><th>OAT °C</th>'+LIM.PAS.map(p=>`<th>${p}</th>`).join('')+'</tr>';
  LIM.T.forEach((row,i)=>{tb+=`<tr><th>${LIM.OATS[i]}</th>`+row.map((v,c)=>`<td class="${(c===j||c===j+1)&&(i===oi||i===oi+1)?'hl':''}">${v??'—'}</td>`).join('')+'</tr>';});
  $('limVneT').innerHTML=tb+'</table>';

  // envelope chart: OAT (x) vs PA (y)
  const W=560,H=360,L=46,R=12,Tp=12,B=34, x=t=>L+(t+50)/(60+50)*(W-L-R), y=p=>Tp+(22000-p)/(24000)*(H-Tp-B);
  let s=`<svg viewBox="0 0 ${W} ${H}" class="env" role="img" aria-label="Operating envelope">`;
  for(let t=-50;t<=60;t+=10)s+=`<line x1="${x(t)}" x2="${x(t)}" y1="${Tp}" y2="${H-B}" class="g"/><text x="${x(t)}" y="${H-B+14}" class="ax" text-anchor="middle">${t}</text>`;
  for(let p=-2000;p<=22000;p+=2000)s+=`<line x1="${L}" x2="${W-R}" y1="${y(p)}" y2="${y(p)}" class="g"/>${p%4000===0?`<text x="${L-5}" y="${y(p)+4}" class="ax" text-anchor="end">${p/1000}</text>`:''}`;
  s+=`<text x="${(L+W-R)/2}" y="${H-4}" class="ax" text-anchor="middle">OAT °C</text><text x="12" y="${(Tp+H-B)/2}" class="ax" text-anchor="middle" transform="rotate(-90 12 ${(Tp+H-B)/2})">PA ×1000 ft</text>`;
  // permitted envelope
  const env=[[-40,-2000],[51.7,-2000],[51.7,0],[11.7,20000],[-40,20000]];
  s+=`<polygon points="${env.map(([t,p])=>x(t)+','+y(p)).join(' ')}" class="envp"/>`;
  // DA limit curve: OAT where DA = daLim, for PA
  const daAt=(p,t)=>B412.densityAltitude(p,t), tAt=(p,lim)=>{let lo=-60,hi=70;for(let i=0;i<40;i++){const m=(lo+hi)/2;if(daAt(p,m)<lim)lo=m;else hi=m;}return lo;};
  const dpts=[];for(let p=-2000;p<=20000;p+=500){const t=tAt(p,daLim);if(t>=-40&&t<=LIM.maxOat(p))dpts.push(x(t)+','+y(p));}
  if(dpts.length>1)s+=`<polyline points="${dpts.join(' ')}" class="dal"/><text x="${dpts[0].split(',')[0]-4}" y="${+dpts[0].split(',')[1]-6}" class="lb dal" text-anchor="end">${daLim/1000}k ft Hd (TO/LDG/IGE)</text>`;
  s+=`<line x1="${x(-30)}" x2="${x(-30)}" y1="${y(20000)}" y2="${y(-2000)}" class="fl"/><text x="${x(-30)+4}" y="${y(19000)}" class="lb">Jet A min −30</text>`;
  s+=`<line x1="${x(21)}" x2="${x(21)}" y1="${y(20000)}" y2="${y(-2000)}" class="ht"/><text x="${x(21)+4}" y="${y(17500)}" class="lb">heater max 21</text>`;
  s+=`<line x1="${x(-25)}" x2="${x(-25)}" y1="${y(20000)}" y2="${y(-2000)}" class="bt"/><text x="${x(-25)+4}" y="${y(16000)}" class="lb">battery start −25</text>`;
  s+=`<text x="${x(30)}" y="${y(9200)}" class="lb" transform="rotate(-38 ${x(30)} ${y(9200)})">max OAT</text>`;
  const cx=x(Math.max(-50,Math.min(60,oat))), cy=y(Math.max(-2000,Math.min(22000,pa)));
  s+=`<circle cx="${cx}" cy="${cy}" r="6" class="pt"/></svg>`;
  $('limEnv').innerHTML=s;
}
