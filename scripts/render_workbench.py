# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Render the argument workbench, version 0: one self-contained page and its review bundle.

    python3 scripts/render_workbench.py OUT_DIR

Writes OUT_DIR/index.html, OUT_DIR/MANIFEST.tsv (every input with its SHA-256 and size) and
OUT_DIR/inputs/<path> (copies of the inputs), so the folder can be sent for review as it is.
The page needs no network. Output depends only on the inputs and the git commit, never on the
clock: running it twice gives byte-identical files. Logic lives in workbench.py, chain_shape.py
and check_cards.py; this file only lays it out.
"""
from __future__ import annotations

import html
import json
import re
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_shape as cs  # noqa: E402
import check_cards as cc  # noqa: E402
import workbench as wb  # noqa: E402
from render_cards import git_head, manifest_by_derived  # noqa: E402

E = html.escape
WORD = {cs.THEREFORE: "therefore", cs.BUT: "but", cs.AND: "and", cs.AND_THEN: "and then"}
CARRY_ROWS = [
    ("Spend to electricity", ["spend_committed", "capacity_mw", "energy_twh", "share_dc_elec"]),
    ("Electricity to carbon budget", ["emissions_mt", "share_dc_emis", "cum_emissions_mt", "c_op_gt", "budget_used",
                                      "budget_used_high"]),
    ("Capacity to water", ["water_per_mw", "water_ml_day", "water_km3_yr", "share_fw_boundary"]),
]
CARRY_SLIDERS = [
    ("Spend to capacity", ["compute_share", "capex_per_mw"]),
    ("Electricity", ["utilisation", "pue", "grid_intensity", "operating_years"]),
    ("Water", ["water_vs_iea"]),
    ("Carbon budget", ["rcb_global", "s_sector", "s_op"]),
]
SURVIVE_SLIDERS = ["annual_hazard", "survival_target", "survival_years"]
ALLOC_SLOT = "planet-pb-allocation"

CSS = r"""
:root{--bg:#f7f6f2;--card:#fff;--ink:#1d1d1b;--muted:#5d5b55;--line:#dcd8cf;--accent:#2f5d8a;--sel:#fbf3dd;
--th:#2f7a4a;--but:#a0661a;--and:#6b6a64;--then:#b5462f;--gap:#b9b3a6;
--obs:#2f5d8a;--app:#a0661a;--imp:#6a4c93;--avoid:#b5462f;
--c-missing:#c9c4b8;--c-identified:#8fa7bf;--c-located:#4f86b8;--c-secondhand:#c7922e;--c-voiced:#2f7a4a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161614;--card:#21201d;--ink:#ecebe6;
--muted:#a8a59c;--line:#3a3833;--accent:#8fb6dd;--sel:#2e2a1d;--th:#6cc28c;--but:#e0a85a;--and:#a8a59c;--then:#e07a62;
--gap:#5a564d;--obs:#8fb6dd;--app:#e0a85a;--imp:#b79be0;--avoid:#e07a62;
--c-missing:#4a4740;--c-identified:#6d8299;--c-located:#5f9bd0;--c-secondhand:#d9a644;--c-voiced:#6cc28c}}
:root[data-theme="dark"]{--bg:#161614;--card:#21201d;--ink:#ecebe6;--muted:#a8a59c;--line:#3a3833;--accent:#8fb6dd;
--sel:#2e2a1d;--th:#6cc28c;--but:#e0a85a;--and:#a8a59c;--then:#e07a62;--gap:#5a564d;--obs:#8fb6dd;--app:#e0a85a;
--imp:#b79be0;--avoid:#e07a62;--c-missing:#4a4740;--c-identified:#6d8299;--c-located:#5f9bd0;--c-secondhand:#d9a644;
--c-voiced:#6cc28c}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1320px;margin:0 auto;padding:20px 16px 64px}
h1{font-size:1.45rem;margin:.1em 0 .2em;line-height:1.2}h2{font-size:1.15rem;margin:2.2em 0 .3em}
h3{font-size:.95rem;margin:1em 0 .3em}p{margin:.4em 0}.muted{color:var(--muted)}.small{font-size:.8rem}
.lede{max-width:72ch;color:var(--muted)}code,.mono{font-family:ui-monospace,Menlo,monospace;font-size:.82em}
.stamp{font-size:.78rem;color:var(--muted);overflow-wrap:anywhere}
.verdict{border-left:4px solid var(--accent);background:var(--card);padding:8px 12px;border-radius:0 8px 8px 0;margin:.8em 0;max-width:90ch}
.verdict b{font-weight:650}
.bar-top{display:flex;justify-content:space-between;gap:12px;align-items:start;flex-wrap:wrap}
button{font:inherit;color:inherit}
.tbtn{border:1px solid var(--line);background:var(--card);border-radius:6px;padding:3px 9px;cursor:pointer;font-size:.8rem}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.85rem;margin:.6em 0}nav.toc a{color:var(--accent)}
.k{font-weight:700;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;padding:1px 7px;border-radius:999px;white-space:nowrap;display:inline-block}
.k.therefore{color:#fff;background:var(--th)}.k.but{color:#fff;background:var(--but)}
.k.and{color:var(--and);border:1px solid var(--and)}.k.and-then{color:#fff;background:var(--then)}
.k.gap{color:var(--muted);border:1px dashed var(--gap)}
.tag{font-size:.66rem;text-transform:uppercase;letter-spacing:.05em;border-radius:4px;padding:0 5px;border:1px solid;white-space:nowrap}
.tag.observed{color:var(--obs);border-color:var(--obs)}.tag.applied{color:var(--app);border-color:var(--app)}
.tag.implied{color:var(--imp);border-color:var(--imp)}.tag.pending{color:var(--then);border-color:var(--then)}
.box .tag,.slider .tag{white-space:normal;overflow-wrap:anywhere;display:inline-block;max-width:100%}
.tag.ok{color:var(--th);border-color:var(--th)}.tag.fail{color:var(--then);border-color:var(--then)}
.st{display:inline-block;width:.8em;height:.8em;border-radius:2px;vertical-align:-.05em;margin-right:3px}
.st.missing{background:var(--c-missing)}.st.identified{background:var(--c-identified)}.st.located{background:var(--c-located)}
.st.secondhand{background:var(--c-secondhand)}.st.voiced{background:var(--c-voiced)}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.78rem;color:var(--muted);margin:.4em 0}
/* sphere */
.sphere-wrap{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:16px;align-items:start}
svg.sphere{width:100%;height:auto;max-height:720px;display:block}
.sphere .ln{stroke-width:1.2;fill:none;opacity:.55}.sphere .ln.identified{stroke:var(--c-identified);stroke-dasharray:3 3}
.sphere .ln.located{stroke:var(--c-located)}.sphere .ln.secondhand{stroke:var(--c-secondhand)}.sphere .ln.voiced{stroke:var(--c-voiced);stroke-width:2.4;opacity:.9}
.sphere .node{cursor:pointer}.sphere .node:focus{outline:none}.sphere .node:focus-visible .shape,.sphere .node.on .shape{stroke:var(--ink);stroke-width:3}
.sphere .th .shape{fill:var(--th);stroke:var(--th);stroke-width:1.5}.sphere .th .ring{fill:var(--card);stroke:var(--line)}
.sphere text{fill:var(--ink);font-size:15px}.sphere .sub{fill:var(--muted);font-size:12px}
.sphere .centre .shape{fill:var(--card);stroke:var(--accent);stroke-width:3}
.sphere .pt .shape{stroke:var(--card);stroke-width:1.5}
.sphere .pt.missing .shape{fill:var(--c-missing)}.sphere .pt.identified .shape{fill:var(--c-identified)}
.sphere .pt.located .shape{fill:var(--c-located)}.sphere .pt.secondhand .shape{fill:var(--c-secondhand)}.sphere .pt.voiced .shape{fill:var(--c-voiced)}
.sphere .unsup{fill:none;stroke:var(--then);stroke-width:1.6;stroke-dasharray:2 2}
.plist{list-style:none;margin:0;padding:0;font-size:.82rem;columns:2 220px;column-gap:16px}
.plist li{break-inside:avoid;margin:0 0 4px}
.plist button{background:none;border:0;padding:0;cursor:pointer;text-align:left}
.plist .why{color:var(--muted);font-size:.74rem;display:block;margin-left:1.1em}
/* IDE */
.ide{display:grid;grid-template-columns:230px minmax(0,1fr) 340px;gap:12px;align-items:start}
.pane{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;min-width:0}
#outline{max-height:min(80vh,760px);overflow:auto;font-size:.82rem;position:sticky;top:8px}
#outline details{margin:0 0 4px}#outline summary{cursor:pointer;font-weight:600}
#outline ul{list-style:none;margin:2px 0 6px;padding:0 0 0 10px}#outline li{margin:1px 0}
#outline button{background:none;border:0;padding:1px 2px;cursor:pointer;text-align:left;width:100%;border-radius:4px}
#outline button[aria-current="true"]{background:var(--sel)}
.c0{color:var(--muted)}.dot{display:inline-block;width:.55em;height:.55em;border-radius:50%;margin-right:4px;vertical-align:.05em}
.dot.p{background:var(--th)}.dot.u{border:1px dashed var(--gap)}
#inspector{position:sticky;top:8px;max-height:min(86vh,820px);overflow:auto;font-size:.85rem}
#inspector h3{margin:.1em 0 .3em;font-size:1rem}#inspector dt{color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.04em;margin-top:.7em}
#inspector dd{margin:0}#inspector ul{margin:.2em 0;padding-left:1.1em}#inspector blockquote{margin:.2em 0;padding-left:8px;border-left:2px solid var(--line);color:var(--muted)}
.lnk{background:none;border:0;padding:0;color:var(--accent);cursor:pointer;text-decoration:underline;text-underline-offset:2px}
.runpick{width:100%;margin:0 0 8px;padding:4px;font:inherit;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:6px}
.run h3{margin:.1em 0}.shape-line{font-family:ui-monospace,Menlo,monospace;font-size:.76rem;color:var(--muted);overflow-wrap:anywhere}
ol.chain{list-style:none;margin:.6em 0;padding:0}
ol.chain li.lk{margin:2px 0 2px 18px;display:flex;gap:6px;align-items:center;font-size:.75rem;color:var(--muted)}
ol.chain li.lk::before{content:"";width:2px;height:18px;background:var(--line);margin-right:6px}
.beat{display:block;width:100%;text-align:left;border:1px solid var(--line);background:var(--card);border-radius:8px;padding:6px 9px;cursor:pointer}
.beat small{display:block;color:var(--muted);font-size:.7rem}.beat .stt{display:block;font-size:.8rem;color:var(--muted);margin-top:2px}
.beat.conclusion{border:2px solid var(--accent)}.beat.ghost{border-style:dashed;border-color:var(--gap)}
.beat.dangle{border-left:4px solid var(--then)}.beat[aria-pressed="true"]{background:var(--sel)}
.fix{font-size:.82rem;margin:.3em 0 0;padding-left:1.1em}
/* tables */
table{border-collapse:collapse;width:100%;font-size:.82rem}th,td{padding:4px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:.7rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums}
.tablewrap{overflow-x:auto}
/* carry + survive */
.two{display:grid;grid-template-columns:minmax(0,340px) minmax(0,1fr);gap:16px;align-items:start}
.slider{margin:0 0 10px}.slider label{display:block;font-size:.82rem}.slider input{width:100%}
.slider .row{display:flex;justify-content:space-between;gap:6px;font-size:.76rem;color:var(--muted);flex-wrap:wrap}
.val{font-variant-numeric:tabular-nums;font-weight:650;color:var(--ink)}
fieldset{min-width:0;border:1px solid var(--line);border-radius:8px;margin:0 0 10px;padding:6px 10px}legend{font-size:.78rem;color:var(--muted);padding:0 4px}
.flow{display:flex;flex-wrap:wrap;align-items:stretch;gap:6px;margin:.3em 0 1em}
.box{border:1px solid var(--line);background:var(--card);border-radius:8px;padding:6px 9px;min-width:138px;flex:1 1 138px;max-width:220px}
.box .nm{font-size:.74rem;color:var(--muted);line-height:1.25}.box .v{font-size:1.05rem;font-weight:650;font-variant-numeric:tabular-nums}
.box .u{font-size:.74rem;color:var(--muted)}.box .f{font-family:ui-monospace,Menlo,monospace;font-size:.66rem;color:var(--muted);overflow-wrap:anywhere;margin-top:3px}
.box.applied-eff{border-style:dashed}.arrow{align-self:center;color:var(--muted)}
svg.chart{width:100%;height:auto;display:block;background:var(--card);border:1px solid var(--line);border-radius:8px}
.chart .ax{stroke:var(--line)}.chart text{fill:var(--muted);font-size:11px}
.chart .base{stroke:var(--accent);stroke-width:2.2;fill:none}.chart .prov{stroke:var(--th);stroke-width:2;fill:none}
.chart .all{stroke:var(--imp);stroke-width:2;fill:none;stroke-dasharray:6 4}.chart .avoid{stroke:var(--avoid);stroke-width:1.8;fill:none;stroke-dasharray:2 3}
.chart .tgt{fill:var(--but)}
.math{font-family:ui-monospace,Menlo,monospace;font-size:.78rem;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 10px;overflow-x:auto;white-space:pre}
.readout{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:6px;margin:.6em 0}
/* sides */
.sides{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr) minmax(0,1.2fr);gap:4px 10px;align-items:center;font-size:.8rem}
.sides .hd{font-size:.7rem;text-transform:uppercase;color:var(--muted)}
.sbar{height:14px;position:relative;background:none}.sbar span{position:absolute;top:0;height:100%;border-radius:3px}
.sbar.l span{right:0}.sbar.r span{left:0}.sbar .w{border:1px dashed var(--gap)}.sbar.l .p{background:var(--but)}.sbar.r .p{background:var(--accent)}
.sides .num{font-size:.7rem;color:var(--muted)}
footer{margin-top:3em;font-size:.8rem;color:var(--muted);border-top:1px solid var(--line);padding-top:1em}
details.index summary{cursor:pointer;font-weight:600}
.links{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:8px 24px}.linklist{margin:.2em 0;padding-left:1.1em;font-size:.85rem}.linklist li{margin:.2em 0;overflow-wrap:anywhere}.linklist a{color:var(--accent)}
@media (max-width:1100px){.ide{grid-template-columns:200px minmax(0,1fr)}#inspector{grid-column:1/-1;position:static;max-height:none}}
@media (max-width:760px){.ide,.sphere-wrap,.two{grid-template-columns:minmax(0,1fr)}#outline{position:static;max-height:260px}
.sides{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.sides .q{grid-column:1/-1;margin-top:6px}.sides .th0{display:none}.box{max-width:none}}
@media print{
:root{--bg:#fff;--card:#fff;--ink:#000;--muted:#444;--line:#bbb}
body{font-size:10.5pt;background:#fff}main{max-width:none;padding:0}
.tbtn,nav.toc,#outline,.runpick,input[type=range],.noprint{display:none!important}
.ide{display:block}.run[hidden]{display:block!important}.run{margin-bottom:10px}.beat{break-inside:avoid}
#inspector{position:static;max-height:none;border:0;padding:0}
.two,.sphere-wrap{display:block}svg.sphere{max-height:none;max-width:560px;margin:0 auto}
.box,.pane,tr,.slider{break-inside:avoid}h2{break-after:avoid}details>*{display:block}
.slider .row .rng{display:none}}
"""

JS = r"""
const D=JSON.parse(document.getElementById('data').textContent);
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
function h(tag,attrs,...kids){const e=document.createElement(tag);for(const[k,v]of Object.entries(attrs||{})){
 if(k==='on')e.addEventListener('click',v);else if(k==='cls')e.className=v;else e.setAttribute(k,v)}
 for(const k of kids.flat()){if(k==null)continue;e.append(k.nodeType?k:document.createTextNode(String(k)))}return e}
function sig(v,n){if(v===0)return'0';const a=Math.abs(v);if(a>=1000)return Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g,',');
 return String(Number(v.toPrecision(n||3)))}
function fmt(v,unit){if(v==null)return'pending';if(!isFinite(v))return'—';
 if(unit==='fraction'||unit==='probability')return sig(v*100,3)+'%';return sig(v,4)}
function unitOf(q){return(q.unit==='fraction'||q.unit==='probability')?'':q.unit}
/* ---------- inspector ---------- */
const INS=$('#inspector');
function cardBtn(id){const c=D.cards[id];return h('button',{cls:'lnk',on:()=>showCard(id)},id+(c?' · '+c.title:''))}
function ref(x){if(D.cards[x]){const c=D.cards[x];return h('li',{},cardBtn(x),' ',h('span',{cls:'tag '+(c.circle>=1?'ok':'fail')},'c'+c.circle))}
 if(D.quotes[x]){const q=D.quotes[x];return h('li',{},h('b',{},x),' ',h('span',{cls:'tag '+(q.ok?'ok':'fail')},q.ok?'quote passes':'quote fails'),
  h('blockquote',{},'“'+q.quote+'”'),q.url?h('a',{href:q.url,target:'_blank',rel:'noopener',cls:'small'},'source: '+q.path.split('/').pop()):h('span',{cls:'small muted'},q.path))}
 if(D.pending[x]){const p=D.pending[x];return h('li',{},h('b',{},x),' ',h('span',{cls:'tag pending'},'pending: '+p.kind),h('div',{cls:'small muted'},p.note))}
 return h('li',{},x+' (unknown)')}
function dl(pairs){const d=h('dl',{});for(const[k,v]of pairs){if(v==null)continue;d.append(h('dt',{},k),h('dd',{},v))}return d}
function list(xs,f){return xs.length?h('ul',{},xs.map(f)):'—'}
function setIns(...kids){INS.replaceChildren(...kids);INS.scrollTop=0}
function showCard(id){const c=D.cards[id];if(!c)return;selectRun(c.run,false);
 $$('.beat').forEach(b=>b.setAttribute('aria-pressed',b.dataset.card===id));
 const named=D.parties.filter(p=>Object.values(p.coverage).some(x=>x.cards.includes(id)));
 setIns(h('h3',{},id+' · '+c.title),h('p',{},c.statement),
  h('p',{},h('span',{cls:'tag '+(c.circle>=1?'ok':'fail')},'circle '+c.circle),' ',c.role+' · '+c.theme+' · side: '+c.side),
  dl([['Rests on',list(c.rests_on,ref)],['Used by',c.used_by.length?h('ul',{},c.used_by.map(u=>h('li',{},cardBtn(u)))):'nothing: a dead end'],
   ['Keeping it at circle 0',c.weak.length?h('ul',{},c.weak.map(ref)):'—'],
   ['Swappable for',c.alts.length?h('ul',{},c.alts.map(u=>h('li',{},cardBtn(u)))):null],
   ['Parties it names',named.length?h('ul',{},named.map(p=>h('li',{},h('button',{cls:'lnk',on:()=>showParty(p.id)},p.name)))):null]]))}
function showParty(id){const p=D.parties.find(x=>x.id===id);if(!p)return;
 $$('.sphere .node').forEach(n=>n.classList.toggle('on',n.dataset.party===id));
 const rows=D.themes.map(t=>{const c=p.coverage[t.theme];return h('tr',{},h('td',{},t.theme),h('td',{},h('span',{cls:'st '+c.state}),c.state),
  h('td',{},c.cards.map(x=>[cardBtn(x),' ']),c.note&&c.note!=='-'?h('div',{cls:'small muted'},c.note):null))});
 setIns(h('h3',{},p.name),h('p',{},h('b',{},p.kind),' · standing: '+p.standing),
  p.supported?null:h('p',{cls:'small'},h('span',{cls:'tag fail'},'barrier'),' standing '+(p.rests_on.length?'rests on unproven cards':'has no support in the deck')),
  dl([['Established by',p.rests_on.length?list(p.rests_on,ref):'nothing yet']]),
  h('table',{},h('tr',{},h('th',{},'theme'),h('th',{},'state'),h('th',{},'cards')),rows))}
function showTheme(t){const th=D.themes.find(x=>x.theme===t);if(!th)return;selectRun(th.runs[0],false);
 $$('.sphere .node').forEach(n=>n.classList.toggle('on',n.dataset.theme===t));
 const cov=D.parties.map(p=>[p,p.coverage[t]]).filter(([p,c])=>c.state!=='missing');
 const sw=D.sides.find(s=>s.theme===t);
 setIns(h('h3',{},th.question),h('p',{},th.proven+' of '+th.cards+' cards proven (circle ≥ 1)'),
  dl([['Chains',h('ul',{},th.runs.map(r=>h('li',{},h('button',{cls:'lnk',on:()=>selectRun(r,true)},r))))],
   ['Complaint / defence cards',sw.complaint.written+' / '+sw.defence.written+' written; weight '+sw.complaint.proven+' / '+sw.defence.proven+' proven'],
   ['Parties present',cov.length?h('ul',{},cov.map(([p,c])=>h('li',{},h('span',{cls:'st '+c.state}),h('button',{cls:'lnk',on:()=>showParty(p.id)},p.name),' · '+c.state))):'none'],
   ['Parties missing',String(D.parties.length-cov.length)+' of '+D.parties.length]]))}
function showCentre(){$$('.sphere .node').forEach(n=>n.classList.toggle('on',n.classList.contains('centre')));showCard(D.verdict.answer)}
function selectRun(r,focus){$$('.run').forEach(s=>s.hidden=s.dataset.run!==r);$('#runpick').value=r;
 $$('#outline [data-run]').forEach(b=>b.setAttribute('aria-current',b.dataset.run===r));
 if(focus){const s=$('.run[data-run="'+CSS.escape(r)+'"]');if(s)s.scrollIntoView({block:'nearest'})}}
$$('.beat[data-card],#outline [data-card]').forEach(b=>b.addEventListener('click',()=>showCard(b.dataset.card)));
$$('#outline [data-run]').forEach(b=>b.addEventListener('click',()=>selectRun(b.dataset.run,true)));
$('#runpick').addEventListener('change',e=>selectRun(e.target.value,false));
$$('.sphere .node').forEach(n=>{const go=()=>{if(n.dataset.party)showParty(n.dataset.party);else if(n.dataset.theme)showTheme(n.dataset.theme);else showCentre();
 document.getElementById('ide').scrollIntoView({behavior:'smooth',block:'start'})};
 n.addEventListener('click',go);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})});
$$('.plist [data-party]').forEach(b=>b.addEventListener('click',()=>{showParty(b.dataset.party);document.getElementById('ide').scrollIntoView({behavior:'smooth'})}));
$$('[data-goto]').forEach(b=>b.addEventListener('click',()=>{showCard(b.dataset.goto);document.getElementById('ide').scrollIntoView({behavior:'smooth'})}));
/* ---------- quantities ---------- */
const V={};const QBY={};D.quantities.forEach(q=>{QBY[q.id]=q;V[q.id]=q.start});
function recompute(){for(const id of D.order){const q=QBY[id];const ins=q.rests_on.map(n=>V[n]);V[id]=ins.some(x=>x==null)?null:F[id](V)}
 $$('[data-q]').forEach(e=>{e.textContent=fmt(V[e.dataset.q],QBY[e.dataset.q].unit)});drawSurvival()}
$$('input[type=range][data-in]').forEach(inp=>{inp.addEventListener('input',()=>{V[inp.dataset.in]=parseFloat(inp.value);recompute()})});
$$('input[name=alloc]').forEach(r=>r.addEventListener('change',()=>{const c=D.cards[r.value];$('#alloc-read').textContent=
 c.title+' ('+r.value+', circle '+c.circle+'). It sets no number: s_op stays yours.'}));
/* ---------- survivorship ---------- */
const CH={x0:48,x1:590,y0:20,y1:260,T:50};
function px(t){return CH.x0+(CH.x1-CH.x0)*t/CH.T}function py(s){return CH.y1-(CH.y1-CH.y0)*s}
function path(hz){let d='';for(let t=0;t<=CH.T;t+=0.5){d+=(t?'L':'M')+px(t).toFixed(1)+' '+py(Math.pow(1-hz,t)).toFixed(1)}return d}
function drawSurvival(){const hz=V.annual_hazard,lev=D.levers;
 const all=lev.reduce((a,l)=>a*(1-V[l.id]),hz),prov=lev.filter(l=>l.proven).reduce((a,l)=>a*(1-V[l.id]),hz);
 $('#c-base').setAttribute('d',path(hz));$('#c-prov').setAttribute('d',path(prov));$('#c-all').setAttribute('d',path(all));
 $('#c-avoid').setAttribute('d',path(V.hazard_avoid));
 const ty=Math.min(V.survival_years,CH.T);const tg=$('#c-tgt');tg.setAttribute('cx',px(ty));tg.setAttribute('cy',py(V.survival_target));
 $('#h-all').textContent=fmt(all,'per year');$('#h-prov').textContent=fmt(prov,'per year');
 $('#s-all').textContent=fmt(Math.pow(1-all,50),'probability');$('#s-prov').textContent=fmt(Math.pow(1-prov,50),'probability');
 $('#h-gap').textContent=V.hazard_needed>0?sig(all/V.hazard_needed,3)+'×':'—'}
/* ---------- theme + print ---------- */
$('#theme').addEventListener('click',()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
 r.dataset.theme=dark?'light':'dark'});
$('#print').addEventListener('click',()=>window.print());
let opened=[];addEventListener('beforeprint',()=>{opened=$$('details:not([open])');opened.forEach(d=>d.open=true)});
addEventListener('afterprint',()=>{opened.forEach(d=>d.open=false)});
recompute();showCentre();selectRun(D.themes[0].runs[0],false);
"""


def chips_ref(x: str, d: cc.Deck) -> str:
    return f'<button class="lnk" data-goto="{E(x)}">{E(x)}</button>' if x in d.cards else E(x)


def run_id(r: cs.Run) -> str:
    return r.theme + ("/" + r.lens if r.lens != "-" else "")


def fnum(v: float) -> str:
    return f"{v:g}"


def render(root: Path = cc.ROOT) -> tuple[str, list[tuple[str, str, int]]]:
    w = wb.check(wb.load(root))
    d = w.deck
    circ = cc.circles(d)
    rs = cs.runs(d)
    used = cs.used_by(d)
    weak = cs.weak_points(d, circ)
    seq = {r["card"]: r for r in d.sequence}
    alts = {b.card: b.alternatives for r in rs for b in r.beats}
    ver = wb.verdict(w)
    bars = wb.barriers(w)
    stats = wb.theme_stats(d)
    best = wb.best_state(w)
    sides = wb.side_weights(w)
    basis = wb.basis_of(w)
    vals = wb.evaluate(w.quantities)
    rows = wb.manifest(root)
    digest = wb.inputs_digest(rows)
    head = git_head(root)
    pend = {r["id"]: r for r in cc.read_tsv(root / cc.ARG / "pending-sources.tsv")}
    by = w.qty

    # card -> run that shows it (alternatives map to their slot default's run)
    slot_default: dict[str, str] = {}
    for r in d.sequence:
        slot_default.setdefault(r["slot"], r["card"])
    card_run: dict[str, str] = {}
    for r in rs:
        for b in r.beats:
            card_run.setdefault(b.card, run_id(r))
    for c in d.cards:
        card_run.setdefault(c, card_run.get(slot_default.get(seq.get(c, {}).get("slot", ""), c), run_id(rs[0])))
    side_of = {c: c2 for s in sides for c2 in ("complaint", "defence", "method") for c in s[c2]["cards"]}

    cov_by: dict[str, dict[str, dict[str, object]]] = {}
    for r in w.coverage:
        cov_by.setdefault(r["party"], {})[r["theme"]] = {"state": r["state"], "cards": wb.split(r["cards"]),
                                                         "note": r["note"]}
    supported = {}
    for p in w.parties:
        refs = wb.split(p["rests_on"])
        supported[p["id"]] = bool(refs) and all((x in d.cards and circ[x] >= 1) or (x in d.q_labels and x in (d.descartes_ok or ()))
                                                for x in refs)
    used_q = sorted({x for v in d.cards.values() for x in v if x in w.quotes}
                    | {x for p in w.parties for x in wb.split(p["rests_on"]) if x in w.quotes}
                    | {x for q in w.quantities for x in wb.split(q["rests_on"]) if x in w.quotes})
    levers = [{"id": q["id"], "card": wb.split(q["rests_on"])[0], "proven": circ.get(wb.split(q["rests_on"])[0], 0) >= 1}
              for q in w.quantities if q["id"].startswith("lever_")]
    order = wb.implied_order(w.quantities)
    src_urls = manifest_by_derived(root)
    data = {
        "cards": {c: {"title": seq.get(c, {}).get("title", c), "statement": d.statements[c],
                      "role": seq.get(c, {}).get("role", "?"), "theme": seq.get(c, {}).get("theme", "?"),
                      "circle": circ.get(c, 0), "rests_on": d.cards[c], "used_by": used.get(c, []),
                      "weak": weak.get(c, []), "alts": alts.get(c, []), "run": card_run[c], "side": side_of.get(c, "?")}
                  for c in d.cards},
        "quotes": {q: {"quote": w.quotes[q]["quote"], "path": w.quotes[q]["path"], "url": src_urls.get(w.quotes[q]["path"], ""),
                       "ok": d.descartes_ok is not None and q in d.descartes_ok} for q in used_q},
        "pending": {k: {"kind": v["kind"], "note": v["note"], "needed_for": v["needed_for"]} for k, v in pend.items()},
        "themes": [{"theme": t["theme"], "question": t["question"], **stats.get(t["theme"], {"cards": 0, "proven": 0}),
                    "runs": [run_id(r) for r in rs if r.theme == t["theme"]]} for t in d.themes],
        "parties": [{"id": p["id"], "name": p["name"], "kind": p["kind"], "standing": p["standing"],
                     "rests_on": wb.split(p["rests_on"]), "best": best[p["id"]], "supported": supported[p["id"]],
                     "coverage": cov_by.get(p["id"], {})} for p in w.parties],
        "quantities": [{"id": q["id"], "unit": q["unit"], "rests_on": wb.split(q["rests_on"]) if q["basis"] == "implied" else [],
                        "start": vals[q["id"]]} for q in w.quantities],
        "order": order, "levers": levers, "sides": sides,
        "verdict": {"answer": ver["answer"]},
    }

    # ---------------- header + verdict
    blockers = ver["blockers"]
    verdict = (f'<b>As written:</b> the answer ({E(ver["answer"])}) says “{E(ver["statement"])}” and is reached through '
               f'{ver["links"]} links, {ver["therefore"]} of them <i>therefore</i> and {ver["and_then"]} <i>and then</i>. '
               f'<b>As proven:</b> {ver["proven"]} of {ver["links"]} links hold ({ver["therefore_proven"]} therefore); '
               f'the answer is circle {ver["circle"]}, held back by {len(blockers)} sources.')

    # ---------------- sphere
    themes = [t["theme"] for t in d.themes]
    tpos = dict(zip(themes, wb.ring(len(themes), 215)))
    ppos = dict(zip([p["id"] for p in w.parties], wb.ring(len(w.parties), 395, phase=-90 + 180 / len(w.parties))))
    svg = ['<svg class="sphere" viewBox="-560 -470 1120 940" role="img" aria-labelledby="sph-t">'
           '<title id="sph-t">Complaint sphere: the central question, the ten themes, and the parties</title>']
    for p in w.parties:
        for t in themes:
            c = cov_by.get(p["id"], {}).get(t, {"state": "missing"})
            if c["state"] != "missing":
                (x1, y1, _), (x2, y2, _) = tpos[t], ppos[p["id"]]
                svg.append(f'<line class="ln {c["state"]}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    svg.append('<circle cx="0" cy="0" r="215" fill="none" stroke="var(--line)" stroke-dasharray="2 6"/>')
    svg.append('<g class="node centre" tabindex="0" role="button" aria-label="Central question">'
               '<circle class="shape" r="92"/>'
               '<text text-anchor="middle" y="-30" style="font-size:16px;font-weight:650">Anthropic says it is</text>'
               '<text text-anchor="middle" y="-10" style="font-size:16px;font-weight:650">a public benefit</text>'
               '<text text-anchor="middle" y="10" style="font-size:16px;font-weight:650">corporation.</text>'
               '<text text-anchor="middle" y="32" style="font-size:16px;font-weight:650">Is it?</text>'
               f'<text class="sub" text-anchor="middle" y="56">{E(ver["answer"])} · circle {ver["circle"]}</text></g>')
    for t in themes:
        x, y, a = tpos[t]
        s = stats.get(t, {"cards": 0, "proven": 0})
        frac = s["proven"] / s["cards"] if s["cards"] else 0
        r = round(18 + 3.2 * s["cards"] ** 0.5, 1)
        svg.append(f'<g class="node th" data-theme="{E(t)}" tabindex="0" role="button" '
                   f'aria-label="{E(t)}: {s["proven"]} of {s["cards"]} cards proven" transform="translate({x} {y})">'
                   f'<circle class="ring" r="{r}"/><circle class="shape" r="{round(r * frac ** 0.5, 1)}"/>'
                   f'<circle r="{r}" fill="none" stroke="var(--th)" stroke-width="1.5"/>'
                   f'<text text-anchor="middle" y="{r + 16}" style="font-weight:600">{E(t)}</text>'
                   f'<text class="sub" text-anchor="middle" y="{r + 30}">{s["proven"]}/{s["cards"]} proven</text></g>')
    for p in w.parties:
        x, y, a = ppos[p["id"]]
        ca = math.cos(math.radians(a))
        anchor = "start" if ca > 0.25 else "end" if ca < -0.25 else "middle"
        lx, ly = round(x + 16 * ca, 1), round(y + 16 * math.sin(math.radians(a)) + 5, 1)
        if anchor == "middle":
            ly = round(y + (26 if math.sin(math.radians(a)) > 0 else -16), 1)
        label = p["name"] if len(p["name"]) <= 26 else p["name"][:25].rstrip() + "…"
        shape = {"enforcer": '<rect class="shape" x="-9" y="-9" width="18" height="18" rx="2"/>',
                 "affected": '<circle class="shape" r="10"/>',
                 "both": '<path class="shape" d="M0 -12 L12 0 L0 12 L-12 0 Z"/>'}[p["kind"]]
        unsup = '' if supported[p["id"]] else '<circle class="unsup" r="15"/>'
        svg.append(f'<g class="node pt {best[p["id"]]}" data-party="{E(p["id"])}" tabindex="0" role="button" '
                   f'aria-label="{E(p["name"])}: best coverage {best[p["id"]]}" transform="translate({x} {y})">'
                   f'{unsup}{shape}</g>'
                   f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" style="font-size:13px">{E(label)}</text>')
    svg.append("</svg>")
    plist = "".join(
        f'<li><button data-party="{E(p["id"])}"><span class="st {best[p["id"]]}"></span><b>{E(p["name"])}</b></button>'
        f' <span class="small muted">{E(p["kind"])}{"" if supported[p["id"]] else " · standing unsupported"}</span>'
        f'<span class="why">{E(p["standing"])}</span></li>' for p in w.parties)
    states_n = {s: sum(1 for r in w.coverage if r["state"] == s) for s in wb.STATES}
    legend_states = " ".join(f'<span><span class="st {s}"></span>{s} ({states_n[s]})</span>' for s in wb.STATES)

    # ---------------- IDE: outline + runs
    outline = []
    for t in d.themes:
        th = t["theme"]
        trs = [r for r in rs if r.theme == th]
        s = stats.get(th, {"cards": 0, "proven": 0})
        items = []
        for r in trs:
            if len(trs) > 1:
                items.append(f'<li><button data-run="{E(run_id(r))}"><i>lens: {E(r.lens)}</i></button></li>')
            for b in r.beats:
                if len(trs) > 1 and b.card in {x.card for rr in trs[:trs.index(r)] for x in rr.beats}:
                    continue
                items.append(f'<li><button data-card="{E(b.card)}" class="{"" if b.proven else "c0"}">'
                             f'<span class="dot {"p" if b.proven else "u"}"></span>{E(b.title)}</button></li>')
        outline.append(f'<details open><summary>{E(th)} <span class="muted small">{s["proven"]}/{s["cards"]}</span></summary>'
                       f'<ul><li><button data-run="{E(run_id(trs[0]))}"><i>{E(t["question"])}</i></button></li>'
                       f'{"".join(items)}</ul></details>')
    runs_html = []
    pick = []
    for r in rs:
        rid = run_id(r)
        pick.append(f'<option value="{E(rid)}">{E(rid)}</option>')
        dangles = {r.beats[i].card for i, lk in enumerate(r.links) if lk.kind == cs.AND_THEN}
        li = []
        for i, b in enumerate(r.beats):
            if i:
                lk = r.links[i - 1]
                li.append(f'<li class="lk"><span class="k {lk.kind}">{WORD[lk.kind]}</span>'
                          + ('<span class="small">proven</span>' if lk.proven else '<span class="k gap">gap</span>') + '</li>')
            cls = ["beat", b.role] + (["ghost"] if not b.proven else []) + (["dangle"] if b.card in dangles else [])
            li.append(f'<li><button class="{" ".join(cls)}" data-card="{E(b.card)}" aria-pressed="false">'
                      f'<small>{E(b.card)} · {E(b.role)} · circle {b.circle}'
                      f'{" · " + str(len(b.alternatives)) + " alternative(s)" if b.alternatives else ""}</small>'
                      f'{E(b.title)}<span class="stt">{E(b.statement)}</span></button></li>')
        fixes = []
        for i, lk in enumerate(r.links):
            if lk.kind == cs.AND_THEN:
                fixes.append(f'<li><b>{E(r.beats[i].card)}</b> → {E(r.beats[i + 1].card)}: nothing later in this chain rests on '
                             f'{E(r.beats[i].card)}.</li>')
        n_gap = sum(not b.proven for b in r.beats)
        title = r.question + (f" — lens: {r.lens}" if r.lens != "-" else "")
        runs_html.append(
            f'<section class="run" data-run="{E(rid)}" data-theme="{E(r.theme)}" hidden><h3>{E(title)}</h3>'
            f'<div class="shape-line">proposed {E(r.shape())}<br>proven&nbsp;&nbsp; {E(r.shape(True))}</div>'
            f'<p class="small muted">{len(r.beats)} beats, {n_gap} unproven. Dashed = unproven; red edge = nothing later rests on it.</p>'
            f'<ol class="chain">{"".join(li)}</ol>'
            + (f'<h3 class="small">Breakdowns in this chain</h3><ul class="fix">{"".join(fixes)}</ul>' if fixes else "")
            + '</section>')

    # ---------------- barriers
    kinds = {k: sum(1 for b in bars if b.kind == k) for k in wb.KIND_ORDER}

    def bar_row(i: int, b: wb.Barrier) -> str:
        item = chips_ref(b.item, d) if b.item in d.cards else E(b.item)
        return (f'<tr><td class="n">{i}</td><td>{E(b.kind)}</td><td><b>{item}</b></td><td class="n">{b.links}</td>'
                f'<td class="n">{b.lifts}</td><td class="n">{b.blocks}</td><td>{E(b.detail)}</td><td>{E(b.fix)}</td></tr>')
    th_row = ('<tr><th>#</th><th>kind</th><th>item</th><th>proven links</th><th>cards lifted</th><th>depends</th>'
              '<th>where</th><th>fix</th></tr>')
    top = "".join(bar_row(i + 1, b) for i, b in enumerate(bars[:15]))
    rest = "".join(bar_row(i + 16, b) for i, b in enumerate(bars[15:]))

    # ---------------- carry-forward
    def tag(qid: str) -> str:
        b = basis[qid]
        t = b["basis"] if b["basis"] != "implied" else f'implied ← {b["effective"]}'
        cls = b["basis"]
        out = f'<span class="tag {cls}">{E(t)}</span>'
        if b["pending"]:
            n = len(b["pending"])
            out += (f' <span class="tag pending" title="{E(", ".join(b["pending"]))}">rests on {n} unproven</span>'
                    f'<div class="f">{E(", ".join(b["pending"]))}</div>')
        return out

    def box(qid: str) -> str:
        q = by[qid]
        f = q["value"] if q["basis"] == "implied" else ("from " + q["rests_on"]) if q["basis"] == "observed" else ""
        cls = "box" + (" applied-eff" if basis[qid]["effective"] == "applied" else "")
        unit = "" if q["unit"] in ("fraction", "probability") else q["unit"]
        return (f'<div class="{cls}"><div class="nm">{E(q["name"])}</div><div><span class="v" data-q="{E(qid)}">…</span> '
                f'<span class="u">{E(unit)}</span></div><div>{tag(qid)}</div><div class="f">{E(f)}</div></div>')

    def slider(qid: str) -> str:
        q = by[qid]
        lo, hi = float(q["low"]), float(q["high"])
        step = fnum((hi - lo) / 100)
        refs = wb.split(q["rests_on"])
        why = "assumption, unsourced"
        if any(x in d.pending for x in refs):
            why = "assumption until " + ", ".join(x for x in refs if x in d.pending) + " is pinned"
        elif refs:
            why = "assumption; framed by " + ", ".join(refs)
        unit = "" if q["unit"] in ("fraction", "probability") else " " + q["unit"]
        return (f'<div class="slider"><label for="in-{E(qid)}">{E(q["name"])}: <span class="val" data-q="{E(qid)}">…</span>'
                f'{E(unit)}</label><input type="range" id="in-{E(qid)}" data-in="{E(qid)}" min="{fnum(lo)}" max="{fnum(hi)}" '
                f'step="{step}" value="{fnum(wb.start_value(q))}"><div class="row"><span class="tag applied">{E(why)}</span>'
                f'<span class="rng">range {fnum(lo)} to {fnum(hi)}, starts at {"low" if q.get("start") == "low" else "midpoint"}</span></div></div>')

    sliders = "".join(f'<fieldset><legend>{E(g)}</legend>{"".join(slider(q) for q in qs)}</fieldset>' for g, qs in CARRY_SLIDERS)
    flows = "".join(f'<h3>{E(g)}</h3><div class="flow">{"<span class=arrow>→</span>".join(box(q) for q in qs)}</div>'
                    for g, qs in CARRY_ROWS)
    alloc_cards = [r["card"] for r in d.sequence if r["slot"] == ALLOC_SLOT]
    alloc = "".join(f'<label class="small" style="display:block"><input type="radio" name="alloc" value="{E(c)}"'
                    f'{" checked" if i == 0 else ""}> {E(seq[c]["title"])} <span class="tag {"ok" if circ[c] >= 1 else "fail"}">'
                    f'circle {circ[c]}</span></label>' for i, c in enumerate(alloc_cards))
    observed = [q for q in w.quantities if q["basis"] == "observed"]
    obs_rows = "".join(f'<tr><td>{E(q["name"])}</td><td class="n">{E(q["value"] if q["value"] != "-" else "pending")}</td>'
                       f'<td>{E(q["unit"])}</td><td>{E(q["rests_on"])}</td><td>{E(q["note"]) if q["note"] != "-" else ""}</td></tr>'
                       for q in observed)

    # ---------------- survivorship
    s_sliders = "".join(slider(q) for q in SURVIVE_SLIDERS)
    l_sliders = "".join(
        slider(l["id"]).replace('<span class="tag applied">',
                                f'<span class="tag {"ok" if l["proven"] else "fail"}">{"proven" if l["proven"] else "unproven"} lever '
                                f'{E(l["card"])}</span> <span class="tag applied">', 1) for l in levers)
    n_proven_levers = sum(l["proven"] for l in levers)
    grid = []
    for t in range(0, 51, 10):
        x = round(48 + (590 - 48) * t / 50, 1)
        grid.append(f'<line class="ax" x1="{x}" y1="20" x2="{x}" y2="260"/><text x="{x}" y="276" text-anchor="middle">{t}</text>')
    for s in (0, 0.25, 0.5, 0.75, 1):
        y = round(260 - 240 * s, 1)
        grid.append(f'<line class="ax" x1="48" y1="{y}" x2="590" y2="{y}"/><text x="42" y="{y + 4}" text-anchor="end">{int(s * 100)}%</text>')
    chart = (f'<svg class="chart" viewBox="0 0 600 292" role="img" aria-label="Survival curves over 50 years">{"".join(grid)}'
             '<text x="319" y="290" text-anchor="middle">years</text>'
             '<path id="c-avoid" class="avoid"/><path id="c-base" class="base"/><path id="c-prov" class="prov"/>'
             '<path id="c-all" class="all"/><circle id="c-tgt" class="tgt" r="5"/></svg>')

    # ---------------- sides
    mx = max(max(s["complaint"]["written"], s["defence"]["written"]) for s in sides) or 1
    side_rows = []
    for s in sides:
        dw, dp, cw, cp = (s["defence"]["written"], s["defence"]["proven"], s["complaint"]["written"], s["complaint"]["proven"])
        pmx = mx  # same scale as the outline; a card above circle 1 can push the fill past it (clamped)
        side_rows.append(
            f'<div class="q"><b>{E(s["theme"])}</b> <span class="muted small">{s["method"]["written"]} method</span></div>'
            f'<div><div class="sbar l"><span class="w" style="width:{100 * dw / mx:.1f}%"></span>'
            f'<span class="p" style="width:{min(100, 100 * dp / pmx):.1f}%"></span></div><div class="num" style="text-align:right">'
            f'{dw} written · weight {dp}</div></div>'
            f'<div><div class="sbar r"><span class="w" style="width:{100 * cw / mx:.1f}%"></span>'
            f'<span class="p" style="width:{min(100, 100 * cp / pmx):.1f}%"></span></div><div class="num">{cw} written · weight {cp}</div></div>')

    # ---------------- footer: missing
    applied_unsourced = [q["id"] for q in w.quantities if q["basis"] == "applied" and not q["note"].startswith("normative:")]
    missing = [
        f"{kinds['pending source']} pending sources and {kinds['failing quote']} failing quotes under the cards",
        f"{kinds['missing link']} <i>and then</i> links: beats nothing later rests on",
        f"{kinds['unsupported standing']} of {len(w.parties)} parties with standing the deck does not prove",
        f"{states_n['missing']} of {len(w.coverage)} party-theme cells missing; {states_n['voiced']} voiced, and no affected party is voiced",
        f"{len(applied_unsourced)} reader-set assumptions with no source",
    ]
    index_rows = "".join(
        f'<tr><td class="mono">{E(c)}</td><td>{E(seq.get(c, {}).get("theme", ""))}</td><td>{E(seq.get(c, {}).get("role", ""))}</td>'
        f'<td class="n">{circ.get(c, 0)}</td><td>{E(d.statements[c])}</td><td class="mono">{E(", ".join(d.cards[c]))}</td></tr>'
        for c in [r["card"] for r in d.sequence])

    js_f = "const F={" + ",".join(f'"{i}":v=>{wb.formula_js(by[i]["value"][1:])}' for i in order) + "};"
    cited: dict[str, int] = {}
    for q in data["quotes"].values():
        if q["url"]:
            cited[q["url"]] = cited.get(q["url"], 0) + 1
    manifest = {r["url"]: r["id"] for r in cc.read_tsv(root / "sources/MANIFEST.tsv")}
    src_items = "".join(f'<li><a href="{E(u)}" target="_blank" rel="noopener">{E(manifest.get(u, u))}</a> '
                        f'<span class="small muted">{n} quote{"s" if n != 1 else ""}</span></li>'
                        for u, n in sorted(cited.items(), key=lambda t: (-t[1], manifest.get(t[0], t[0]))))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Argument Workbench</title>
<meta name="description" content="The Anthropic public-benefit argument as it stands: chains, breakdowns, parties, carried-forward quantities.">
<style>{CSS}</style></head><body><main>
<div class="bar-top"><div><h1>Anthropic says it is a public benefit corporation. Is it?</h1>
<div class="stamp">Workbench v0 · commit {E(head)} · inputs sha256 {digest[:16]} · {len(d.cards)} cards · {len(w.parties)} parties · {len(w.quantities)} quantities</div></div>
<div class="noprint"><button class="tbtn" id="theme" type="button">Light / dark</button> <button class="tbtn" id="print" type="button">Print</button></div></div>
<p class="verdict">{verdict}</p>
<nav class="toc"><a href="#sphere">Complaint sphere</a><a href="#ide">Chains</a><a href="#barriers">Barriers</a>
<a href="#carry">Carry-forward</a><a href="#survive">Survivorship</a><a href="#sides">Each side</a><a href="#missing">What is missing</a><a href="#links">Links</a></nav>

<h2 id="sphere">Complaint sphere</h2>
<p class="lede">The question sits at the centre. Themes ring it; the filled part of each is the share of its cards that are proven.
Parties sit outside, coloured by how well any theme covers them. Lines join a theme to the parties it mentions. A dashed red halo means the party's standing is not proven. Click anything.</p>
<div class="legend">{legend_states} <span>■ enforcer · ● affected · ◆ both</span></div>
<div class="sphere-wrap"><div>{"".join(svg)}</div><ul class="plist">{plist}</ul></div>

<h2 id="ide">Chains</h2>
<p class="lede">Left: themes and their cards. Centre: the selected chain, each link marked <i>therefore</i>, <i>but</i>, <i>and</i> or <i>and then</i>, and whether it is proven. Right: what the selected card rests on, what uses it, and what keeps it unproven.</p>
<div class="legend"><span class="k therefore">therefore</span> rests on the last <span class="k but">but</span> objection or reply
<span class="k and">and</span> gathered for later <span class="k and-then">and then</span> nothing later uses it <span class="k gap">gap</span> not proven</div>
<div class="ide"><nav class="pane" id="outline" aria-label="Themes and cards">{"".join(outline)}</nav>
<div class="pane" id="chain"><select class="runpick" id="runpick" aria-label="Chain">{"".join(pick)}</select>{"".join(runs_html)}</div>
<aside class="pane" id="inspector" aria-live="polite"><p class="muted">Select a card, theme or party.</p></aside></div>

<h2 id="barriers">Breakdowns and barriers</h2>
<p class="lede">Everything that keeps the argument from holding, ranked by how many proven links fixing it alone would add, then by how many cards it would lift to circle 1. Most fixes unlock nothing alone: the cards above them rest on more than one gap.</p>
<div class="legend">{" · ".join(f"{E(k)}: {v}" for k, v in kinds.items())}</div>
<div class="tablewrap"><table>{th_row}{top}</table></div>
<details class="index"><summary>The other {len(bars) - 15} barriers</summary><div class="tablewrap"><table>{th_row}{rest}</table></div></details>

<h2 id="carry">Carry-forward: committed spend to the planet</h2>
<p class="lede">One number is pinned: the committed spend. Every step after it needs an assumption you set. Values below are what your settings imply, not estimates of Anthropic's footprint. Dashed boxes inherit an assumption.</p>
<div class="two"><div>{sliders}<fieldset><legend>Allocation principle (planet theme)</legend>{alloc}
<p class="small muted" id="alloc-read">Pick a principle to see its card.</p></fieldset></div>
<div>{flows}<h3>Pinned numbers</h3><div class="tablewrap"><table><tr><th>observed</th><th>value</th><th>unit</th><th>quote</th><th>note</th></tr>{obs_rows}</table></div></div></div>

<h2 id="survive">Survivorship</h2>
<p class="lede">The objective: effective control over risk, which means not facing a one in ten chance a year of the world ending. That line is drawn as the outcome to avoid. It is not an estimate, and neither is any curve here: each is a scenario you set.</p>
<div class="two"><div>{s_sliders}<fieldset><legend>Governance levers (remedy cards)</legend>
<p class="small muted">Give each lever a share of the hazard it would remove, if adopted. {n_proven_levers} of {len(levers)} levers rest on proven cards, so the proven curve moves only with those.</p>{l_sliders}</fieldset></div>
<div>{chart}<div class="legend"><span style="color:var(--accent)">━ hazard h</span><span style="color:var(--th)">━ h with proven levers</span>
<span style="color:var(--imp)">╍ h with all levers (unproven)</span><span style="color:var(--avoid)">┅ outcome to avoid: 1 in 10 a year</span><span style="color:var(--but)">● your target</span></div>
<div class="readout"><div class="box"><div class="nm">Survival over 50 years at h</div><div class="v" data-q="survival_50">…</div></div>
<div class="box"><div class="nm">Survival over 50 years at the line to avoid</div><div class="v" data-q="survival_50_avoid">…</div></div>
<div class="box"><div class="nm">Hazard that meets your target</div><div class="v"><span data-q="hazard_needed">…</span> a year</div></div>
<div class="box"><div class="nm">h with all levers credited</div><div class="v"><span id="h-all">…</span></div><div class="u">survives 50 years: <span id="s-all">…</span></div></div>
<div class="box"><div class="nm">h with proven levers only</div><div class="v"><span id="h-prov">…</span></div><div class="u">survives 50 years: <span id="s-prov">…</span></div></div>
<div class="box"><div class="nm">All-lever hazard over the hazard needed</div><div class="v" id="h-gap">…</div></div></div>
<div class="math">S(t)       = (1 − h)^t                 chance of no catastrophe in t years
h needed   = 1 − S*^(1/T)              hazard that keeps survival at S* for T years
h_levers   = h × Π (1 − r_i)           r_i: the share you credit to lever i
proven     = only levers whose remedy card is circle ≥ 1</div></div></div>

<h2 id="sides">Each side, by theme</h2>
<p class="lede">Left: cards carrying Anthropic's case (listed in <code>argument/sides.tsv</code>). Right: cards carrying the complaint. Dashed outline: cards as written, one each. Fill: weight as proven, each card counting its circle (0 to 3), so an unproven card weighs nothing. Lens and budget cards are method and sit on neither side.</p>
<div class="sides"><div class="hd th0">theme</div><div class="hd" style="text-align:right">Anthropic's case</div><div class="hd">the complaint</div>{"".join(side_rows)}</div>

<h2 id="links">Links</h2>
<div class="links"><div><h3>The paper and its code</h3><ul class="linklist">
<li><a href="{DOI_URL}" target="_blank" rel="noopener">The working paper</a> <span class="small muted">Zenodo, DOI {DOI}</span></li>
<li><a href="{REPO_URL}/tree/{head.split()[0]}/argument" target="_blank" rel="noopener">Code, cards and checks</a> <span class="small muted">GitHub; this page is built by <code>scripts/render_workbench.py</code> from <code>argument/</code></span></li>
</ul></div>
<div><h3>Sources the cards quote</h3><ul class="linklist">{src_items}</ul></div></div>

<footer id="missing"><h3>What is missing</h3><ul>{"".join(f"<li>{m}</li>" for m in missing)}</ul>
<p>A figure of $500 billion appears in no pinned quote; the page uses the S-1's $895.4 billion (Q090).</p>
<p>Regenerate: <code>python3 scripts/render_workbench.py OUT_DIR</code> (checks: <code>python3 scripts/check_workbench.py</code>).
Inputs and their SHA-256 are in <code>MANIFEST.tsv</code> beside this page; copies sit in <code>inputs/</code>. Output depends only on the inputs and commit {E(head)}.</p>
<details class="index"><summary>Card index ({len(d.cards)} cards)</summary><div class="tablewrap"><table>
<tr><th>card</th><th>theme</th><th>role</th><th>circle</th><th>claim</th><th>rests on</th></tr>{index_rows}</table></div></details></footer>
</main><script type="application/json" id="data">{json.dumps(data, sort_keys=True, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{js_f}{JS}</script></body></html>
"""
    return page, rows


ARTIFACT_TITLE = "Anthropic PBC Workbench"
REPO_URL = "https://github.com/srvo/anthropic-pbc"
DOI = "10.5281/zenodo.23928296"
DOI_URL = "https://doi.org/" + DOI


def artifact_page(page: str) -> str:
    """The same page as a claude.ai Artifact body: no document skeleton (the host adds it), no print or theme
    buttons (the host frame cannot print and sets the theme), and no local regeneration instructions."""
    head, rest = page.split("<style>", 1)
    out = f"<title>{ARTIFACT_TITLE}</title>\n<style>" + rest.replace("</head><body>", "\n", 1)
    out = re.sub(r'<div class="noprint">.*?</div></div>', "</div>", out, count=1, flags=re.S)
    out = re.sub(r"\$\('#theme'\)\.addEventListener\(.*?\}\);\n", "", out, count=1, flags=re.S)
    out = out.replace("$('#print').addEventListener('click',()=>window.print());\n", "")
    out = re.sub(r"<p>A figure of \$500 billion.*?</p>\n", "", out, count=1, flags=re.S)
    out = re.sub(r"<p>Regenerate: .*?</p>", "<p>Built only from the inputs listed, with their SHA-256, in the review "
                 "bundle's <code>MANIFEST.tsv</code>.</p>", out, count=1, flags=re.S)
    return out.replace("</body></html>\n", "")


def write_bundle(out: Path, root: Path = cc.ROOT) -> Path:
    page, rows = render(root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "artifact.html").write_text(artifact_page(page), encoding="utf-8")
    (out / "MANIFEST.tsv").write_text("path\tsha256\tbytes\n" + "".join(f"{p}\t{h}\t{n}\n" for p, h, n in rows),
                                      encoding="utf-8")
    inputs = out / "inputs"
    if inputs.exists():
        shutil.rmtree(inputs)
    for p, _, _ in rows:
        (inputs / p).parent.mkdir(parents=True, exist_ok=True)
        (inputs / p).write_bytes((root / p).read_bytes())
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: render_workbench.py OUT_DIR", file=sys.stderr)
        return 2
    print(write_bundle(Path(argv[1]).expanduser()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
