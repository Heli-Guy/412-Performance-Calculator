// ================= LIMITATIONS — BHT-412-FM-5 Section 1 (ambient temperature & fuel) =================
const LIM={maxOat:pa=>Math.min(51.7,51.7-2*Math.max(0,pa)/1000)};
function calcLimits(ctx){
  const {pa,oat}=ctx, fuel=$('fuel').value, mo=LIM.maxOat(pa), mg=mo-oat;
  const oatOk=oat>=-40&&oat<=mo, jetA=fuel==='a', fuelOk=!jetA||oat>-30;
  const sg=v=>(v>=0?'+':'−')+Math.abs(v).toFixed(1);
  $('limTiles').innerHTML=`<div class="r sm ${oatOk?'ok':'bad'}"><div class="k">OAT limits</div><div class="v" style="white-space:nowrap">-40 … ${mo.toFixed(1)} °C</div><div class="s">FM-5 1-11 at ${f0(pa)} ft</div></div>
    <div class="r ${oatOk?'ok':'bad'}"><div class="k">OAT margin</div><div class="v">${oat<-40?sg(oat+40):sg(mg)} °C</div><div class="s">${oat<-40?'below minimum OAT':'to maximum OAT'}</div></div>
    <div class="r ${fuelOk?'ok':'bad'}"><div class="k">Fuel temp limits</div><div class="v">${jetA?'&gt; −30 °C':'None'}</div><div class="s">${jetA?'Jet A / A-1 · FM-5 1-17':'Jet B · all ambient temperatures'}</div></div>
    <div class="r ${fuelOk?'ok':'bad'}"><div class="k">Fuel temp</div><div class="v">${oat.toFixed(1)} °C</div><div class="s">= OAT</div></div>`;
  const row=(ok,name,why)=>`<div class="fuelrow ${ok?'ok':'bad'}"><span class="ic">${ok?'✓':'✕'}</span><b>${name}</b><span class="why">${why}</span></div>`;
  $('limFuels').innerHTML=`<div class="k">Valid fuels at ${oat.toFixed(1)} °C OAT · ${f0(pa)} ft</div>`+
    row(oat>-30&&oatOk,'Jet A / A-1','above −30 °C (also JP-5, JP-8, NATO F-34 / F-44)')+
    row(oatOk,'Jet B','all ambient temperatures (also JP-4, NATO F-40)')+
    (oatOk?'':`<div class="msg" style="margin-top:6px">OAT ${oat} °C is outside the operating limits (−40 °C to ${mo.toFixed(1)} °C at ${f0(pa)} ft).</div>`);
}
// Height-velocity diagram applicability (FM-5 Fig 1-4 · FMS-35.5)
function calcHV(){
  const p9=$('pax9').value==='on';
  const row=(st,name,why)=>`<div class="fuelrow ${st}"><span class="ic">${st==='ok'?'✓':'!'}</span><b>${name}</b><span class="why">${why}</span></div>`;
  $('limHV').innerHTML=`<div class="k">Height-velocity diagram (OEI) — FM-5 Fig 1-4</div>`+
    (p9?row('ok','Not a limitation','configured with 9 or fewer passenger seats — FMS-35.5 removes the H-V diagram as a limitation (still performance information, FMS-35.5 Fig 4-2A)')
       :row('warn','Limitation unless flown CAT-A','more than 9 passenger seats: the H-V diagram is a limitation unless the takeoff / landing is flown to the FMS-62.5 CAT-A profile (check the CAT-A tabs)'));
  $('limHVchart').innerHTML=`<div class="chart" style="max-width:420px;margin-top:8px"><svg viewBox="${PF.hv14.join(' ')}" xmlns="http://www.w3.org/2000/svg"><image href="${IMG.hv14}" x="${PF.hv14[0]}" y="${PF.hv14[1]}" width="${PF.hv14[2]}" height="${PF.hv14[3]}" preserveAspectRatio="none"/></svg><div class="cap"><span>BHT-412-FM-5 Fig 1-4 · Height-Velocity Diagram (OEI)</span><span>p.1-21</span></div></div>`;
}
