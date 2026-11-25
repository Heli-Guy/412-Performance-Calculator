// ================= Performance Class 2 — helideck (BHT-412-MD-5 Fig 4-4 / 4-5, manufacturer's data) =================
function calcPC2(ctx){
  const {pa,oat,gw,da,hw}=ctx, E=window.CATA, hwf=Math.max(0,hw)*0.5;
  const W=E.wat(PC2.pc2_wat,pa,oat,hwf,11900), g0=floor10(W.gw0), gmax=floor10(W.gw);
  const G=Math.max(8000,Math.min(11900,g0)); // drop-down uses the zero-wind weight
  const D1=E.dd(PC2.pc2_dd,pa,oat,Math.min(G,gw),Math.max(da,1000)), D2=E.dd(PC2.pc2_ddb,pa,oat,Math.min(G,gw),Math.max(da,1000));
  const over=gw>gmax, out=da>6000||pa>6000||!fin(gmax);
  const d=v=>out?'– – – –':v;
  $('pc2Cards').innerHTML=card('PC2 max T/O weight',out?'– – – –':`${f0(gmax)} Lbs`,out?'outside the chart (6,000 ft H<sub>P</sub>)':`zero wind ${f0(g0)}${gmax>g0?` · +wind ${f0(gmax-g0)}`:(hwf>0&&oat>=20?' · no headwind benefit at 20 °C and warmer':'')}`,out?'bad':(over?'bad':'ok'))+
    card('Drop-down · takeoff',d(`${f0(Math.ceil(D1.v))} ft`),out?'':`below the helideck · height loss ${f0(Math.ceil(25+D1.v))} ft (25 ft + drop down) · Fig 4-5 sheet 1`)+
    card('Drop-down · balked landing',d(`${f0(Math.ceil(D2.v))} ft`),out?'':'below the helideck · Fig 4-5 sheet 2')+
    card('Weight used',d(`${f0(Math.min(G,gw))} Lbs`),out?'':'lesser of your GW and the zero-wind PC2 weight (Bell note)');
  $('pc2Charts').innerHTML=caChart(PC2.pc2_wat,'pc2_wat',W.path,[[W.x,W.y,f0(g0)+' lb']],'BHT-412-MD-5 Fig 4-4 · Performance Class 2 WAT — vertical takeoff from helideck (offshore configuration)')+
    caChart(PC2.pc2_dd,'pc2_dd',D1.path,[[D1.x,D1.y2,f0(Math.ceil(D1.v))+' ft']],'BHT-412-MD-5 Fig 4-5 sheet 1 · PC2 drop-down height — vertical takeoff')+
    caChart(PC2.pc2_ddb,'pc2_ddb',D2.path,[[D2.x,D2.y2,f0(Math.ceil(D2.v))+' ft']],'BHT-412-MD-5 Fig 4-5 sheet 2 · PC2 drop-down height — balked landing');
}
