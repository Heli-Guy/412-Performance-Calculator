// ================= LIMITATIONS — BHT-412-FM-5 Section 1 (ambient temperature & fuel) =================
const LIM={maxOat:pa=>Math.min(51.7,51.7-2*Math.max(0,pa)/1000)};
function calcLimits(ctx){
  const {pa,oat}=ctx, fuel=$('fuel').value, mo=LIM.maxOat(pa), mg=mo-oat;
  const oatOk=oat>=-40&&oat<=mo, jetA=fuel==='a', fuelOk=!jetA||oat>-30;
  const sg=v=>(v>=0?'+':'−')+Math.abs(v).toFixed(1);
  $('limTiles').innerHTML=`<div class="r ${oatOk?'ok':'bad'}"><div class="k">OAT limits</div><div class="v" style="font-size:clamp(17px,2.4vw,24px)"><span style="white-space:nowrap">−40 …</span> <span style="white-space:nowrap">${mo.toFixed(1)} °C</span></div><div class="s">FM-5 1-11 at ${f0(pa)} ft</div></div>
    <div class="r ${oatOk?'ok':'bad'}"><div class="k">OAT margin</div><div class="v">${oat<-40?sg(oat+40):sg(mg)} °C</div><div class="s">${oat<-40?'below minimum OAT':'to maximum OAT'}</div></div>
    <div class="r ${fuelOk?'ok':'bad'}"><div class="k">Fuel temp limits</div><div class="v">${jetA?'&gt; −30 °C':'None'}</div><div class="s">${jetA?'Jet A / A-1 · FM-5 1-17-A':'Jet B · all ambient temperatures'}</div></div>
    <div class="r ${fuelOk?'ok':'bad'}"><div class="k">Fuel temp</div><div class="v">${oat.toFixed(1)} °C</div><div class="s">= OAT</div></div>`;
  const row=(ok,name,why)=>`<div class="fuelrow ${ok?'ok':'bad'}"><span class="ic">${ok?'✓':'✕'}</span><b>${name}</b><span class="why">${why}</span></div>`;
  $('limFuels').innerHTML=`<div class="k">Valid fuels at ${oat.toFixed(1)} °C OAT · ${f0(pa)} ft</div>`+
    row(oat>-30&&oatOk,'Jet A / A-1','above −30 °C (also JP-5, JP-8, NATO F-34 / F-44)')+
    row(oatOk,'Jet B','all ambient temperatures (also JP-4, NATO F-40)')+
    (oatOk?'':`<div class="msg" style="margin-top:6px">OAT ${oat} °C is outside the operating limits (−40 °C to ${mo.toFixed(1)} °C at ${f0(pa)} ft).</div>`);
}
