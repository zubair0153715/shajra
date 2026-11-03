"""Shajra page — interactive mind-map studio (single HTML string).

Draws the map as SVG from the server-computed layout. All editing is
client-side; maps persist in the user's own browser (localStorage).
Original design, no Xmind theme, icon or asset used.
"""

SHAJRA_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shajra — Free AI Mind Maps (no paywall, no watermark)</title>
<style>
:root{--bg:#0f172a;--panel:#1e293b;--panel2:#16213a;--line:#334155;--ink:#f1f5f9;--muted:#94a3b8;--acc:#22c55e;--acc2:#38bdf8;--warn:#f59e0b;--danger:#ef4444}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:10px;align-items:center}
header h1{margin:0;font-size:22px}header h1 span{color:var(--acc)}
header p{margin:0;color:var(--muted);font-size:13px;flex:1;min-width:220px}
.badge{font-size:12px;padding:4px 10px;border-radius:999px;background:#052e16;color:#86efac;border:1px solid #14532d}
.badge.off{background:#3f1d1d;color:#fca5a5;border-color:#7f1d1d}
#toolbar{display:flex;flex-wrap:wrap;gap:8px;padding:10px 18px;border-bottom:1px solid var(--line);background:var(--panel2)}
button,select,input[type=text]{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:14px;cursor:pointer}
button:hover{border-color:var(--acc)}button.primary{background:var(--acc);color:#052e16;border-color:var(--acc);font-weight:700}
button.danger{color:#fca5a5}button:disabled{opacity:.45;cursor:not-allowed}
#main{display:flex;min-height:calc(100vh - 210px)}
#library{width:210px;border-right:1px solid var(--line);padding:12px;overflow:auto}
#library h3{margin:4px 0 8px;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.mapitem{display:block;width:100%;text-align:left;margin:0 0 6px;padding:8px 10px;border-radius:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mapitem.active{border-color:var(--acc);background:#052e16}
#canvasWrap{flex:1;position:relative;overflow:hidden;background:radial-gradient(circle at 50% 40%,#1e293b,#0f172a)}
#canvas{width:100%;height:100%;cursor:grab}
#canvas:active{cursor:grabbing}
#hint{position:absolute;left:12px;bottom:10px;color:var(--muted);font-size:12px;background:rgba(15,23,42,.8);padding:6px 10px;border-radius:8px}
#presentBar{position:absolute;top:10px;left:50%;transform:translateX(-50%);display:none;gap:8px;background:var(--panel);border:1px solid var(--line);padding:8px 12px;border-radius:10px;align-items:center}
#panel{width:260px;border-left:1px solid var(--line);padding:14px;overflow:auto}
#panel h3{margin:0 0 4px;font-size:15px}
#panel p{color:var(--muted);font-size:13px;margin:0 0 12px}
#panel label{display:block;font-size:12px;color:var(--muted);margin:12px 0 4px}
#panel input[type=text],#panel textarea{width:100%;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px;font-size:14px}
#panel textarea{min-height:70px;resize:vertical}
.row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
#stats{font-size:12px;color:var(--muted);margin-top:14px;line-height:1.7}
#msg{margin-top:10px;font-size:13px;color:var(--warn);min-height:18px}
#modal{position:fixed;inset:0;background:rgba(2,6,23,.75);display:none;align-items:center;justify-content:center;z-index:50}
#modal .box{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px;width:min(560px,92vw)}
#modal textarea{width:100%;min-height:180px;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:10px;font-size:14px}
footer{padding:12px 18px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);line-height:1.7}
footer b{color:var(--ink)}
.node{cursor:pointer}
.node rect{stroke-width:2}
.node text{fill:#f1f5f9;font-size:13px;font-weight:600;pointer-events:none}
.node.sel rect{stroke:#fff;stroke-width:3}
.node.dim{opacity:.25}
.edge{fill:none;stroke:#64748b;stroke-width:2}
.depth0 rect{fill:#166534}.depth1 rect{fill:#155e75}.depth2 rect{fill:#1e40af}.depth3 rect{fill:#6b21a8}.depth4 rect{fill:#9f1239}.depth5 rect{fill:#713f12}
</style>
</head>
<body>
<header>
  <h1>🌳 Shajra <span>شجرہ</span></h1>
  <p>Free AI mind maps — unlimited maps, AI branches, clean exports. No account, no card, no meter, no watermark.</p>
  <span id="aiBadge" class="badge off">AI: checking…</span>
</header>
<div id="toolbar">
  <button class="primary" onclick="newMap()">＋ New map</button>
  <select id="sampleSel" onchange="loadSample(this.value);this.value=''">
    <option value="">Sample maps…</option>
    <option value="antibiotics">💊 Antibiotics (Pharm-D)</option>
    <option value="mdcat">📚 MDCAT Biology</option>
    <option value="business">💼 Start a small business</option>
  </select>
  <select id="layoutSel" onchange="setLayout(this.value)">
    <option value="right">Layout: Right tree</option>
    <option value="down">Layout: Down (org chart)</option>
    <option value="radial">Layout: Radial</option>
  </select>
  <button onclick="zoomBy(1.25)">＋ Zoom</button>
  <button onclick="zoomBy(0.8)">− Zoom</button>
  <button onclick="fitView()">Fit</button>
  <button onclick="openOutline()">⇪ Outline import</button>
  <button onclick="openAiMap()">✨ AI map from topic</button>
  <button onclick="togglePresent()">▶ Present</button>
  <button onclick="exportSVG()">↓ SVG</button>
  <button onclick="exportPNG()">↓ PNG</button>
  <button onclick="exportJSON()">↓ JSON</button>
  <button onclick="document.getElementById('fileIn').click()">↑ Load JSON</button>
  <input type="file" id="fileIn" accept=".json" style="display:none" onchange="importJSON(event)">
</div>
<div id="main">
  <div id="library"><h3>Your maps</h3><div id="mapList"></div>
    <p style="color:var(--muted);font-size:12px;line-height:1.6">Maps live in <b style="color:var(--ink)">your browser only</b> — no cloud, no account. Export JSON to keep a backup.</p>
  </div>
  <div id="canvasWrap">
    <svg id="canvas"></svg>
    <div id="presentBar"><button onclick="presentStep(-1)">‹ Prev</button><span id="presentLabel"></span><button onclick="presentStep(1)">Next ›</button><button onclick="togglePresent()">✕ Exit</button></div>
    <div id="hint">Click a node to edit • drag background to pan • scroll to zoom • double-click a node to add a child</div>
  </div>
  <div id="panel">
    <h3 id="panelTitle">No node selected</h3>
    <p>Click any node on the map to edit it, add branches, or expand it with AI.</p>
    <div id="nodeTools" style="display:none">
      <label>Label</label>
      <input type="text" id="nodeText" maxlength="200" onchange="renameNode(this.value)">
      <div class="row">
        <button onclick="addChild()">＋ Child</button>
        <button onclick="addSibling()">＋ Sibling</button>
        <button class="danger" onclick="deleteNode()">✕ Delete</button>
      </div>
      <div class="row">
        <button onclick="aiExpand()">✨ AI expand</button>
        <button onclick="toggleCollapse()">⇅ Collapse / expand</button>
      </div>
      <label>Path</label>
      <div id="nodePath" style="font-size:13px;color:var(--muted)"></div>
    </div>
    <div id="stats"></div>
    <div id="msg"></div>
  </div>
</div>
<div id="modal"><div class="box">
  <h3 id="modalTitle" style="margin-top:0">Outline import</h3>
  <p style="color:var(--muted);font-size:13px">Paste an indented outline — 2 spaces or a tab per level. First line = central topic.</p>
  <textarea id="modalText" placeholder="Antibiotics&#10;  Beta-lactams&#10;    Penicillins&#10;    Cephalosporins&#10;  Macrolides"></textarea>
  <div class="row" style="margin-top:12px">
    <button class="primary" id="modalOk" onclick="modalSubmit()">Make map</button>
    <button onclick="closeModal()">Cancel</button>
  </div>
  <div id="modalMsg" style="color:var(--warn);font-size:13px;margin-top:8px"></div>
</div></div>
<footer>
  <b>Honest limits:</b> maps are stored in your browser only (localStorage) — no cloud sync and no real-time collaboration in v1. AI branches need the server's Gemini quota; when it is exhausted the button says so and the map keeps working. Layout is automatic — no free-form drag-to-anywhere in v1. Export is SVG/PNG/JSON, not PDF. Shajra is an original build, not affiliated with Xmind.
</footer>
<script>
let uid = 1000;
const nid = () => 'n' + (uid++);
let tree = null, mode = 'right', collapsed = new Set(), selected = null;
let view = {x: 40, y: 40, k: 1}, layoutData = null;
let presenting = false, presentOrder = [], presentIdx = 0;
const $ = id => document.getElementById(id);
const LS_KEY = 'shajra-maps-v1';

function blankTree(){ return {id: nid(), text: 'New map', children: []}; }
function sampleAntibiotics(){ return {id:nid(),text:'Antibiotics',children:[
 {id:nid(),text:'Beta-lactams',children:[{id:nid(),text:'Penicillins',children:[{id:nid(),text:'Amoxicillin',children:[]},{id:nid(),text:'Flucloxacillin',children:[]}]},{id:nid(),text:'Cephalosporins',children:[{id:nid(),text:'Ceftriaxone',children:[]}]},{id:nid(),text:'Carbapenems',children:[{id:nid(),text:'Meropenem',children:[]}]}]},
 {id:nid(),text:'Macrolides',children:[{id:nid(),text:'Azithromycin',children:[]},{id:nid(),text:'Clarithromycin',children:[]}]},
 {id:nid(),text:'Fluoroquinolones',children:[{id:nid(),text:'Ciprofloxacin',children:[]},{id:nid(),text:'Levofloxacin',children:[]}]},
 {id:nid(),text:'Aminoglycosides',children:[{id:nid(),text:'Gentamicin',children:[]},{id:nid(),text:'Amikacin',children:[]}]},
 {id:nid(),text:'Tetracyclines',children:[{id:nid(),text:'Doxycycline',children:[]}]}]}; }
function sampleMdcat(){ return {id:nid(),text:'MDCAT Biology',children:[
 {id:nid(),text:'Cell Biology',children:[{id:nid(),text:'Cell organelles',children:[]},{id:nid(),text:'Cell cycle',children:[]}]},
 {id:nid(),text:'Genetics',children:[{id:nid(),text:'DNA & RNA',children:[]},{id:nid(),text:'Mendelian inheritance',children:[]}]},
 {id:nid(),text:'Human Physiology',children:[{id:nid(),text:'Circulation',children:[]},{id:nid(),text:'Respiration',children:[]},{id:nid(),text:'Excretion',children:[]}]},
 {id:nid(),text:'Plant Biology',children:[{id:nid(),text:'Photosynthesis',children:[]}]},
 {id:nid(),text:'Ecology',children:[{id:nid(),text:'Ecosystems',children:[]}]}]}; }
function sampleBusiness(){ return {id:nid(),text:'Start a small business',children:[
 {id:nid(),text:'Idea',children:[{id:nid(),text:'Problem to solve',children:[]},{id:nid(),text:'Who pays?',children:[]}]},
 {id:nid(),text:'Money',children:[{id:nid(),text:'Zero-budget start',children:[]},{id:nid(),text:'First sale',children:[]}]},
 {id:nid(),text:'Customers',children:[{id:nid(),text:'Where they are',children:[]},{id:nid(),text:'How to reach them',children:[]}]},
 {id:nid(),text:'Delivery',children:[{id:nid(),text:'What you deliver',children:[]},{id:nid(),text:'How you get paid',children:[]}]}]}; }
const SAMPLES = {antibiotics: sampleAntibiotics, mdcat: sampleMdcat, business: sampleBusiness};

function findNode(n, id){ if(!n) return null; if(n.id===id) return n; for(const c of n.children){ const f=findNode(c,id); if(f) return f; } return null; }
function findParent(n, id, p=null){ if(!n) return null; if(n.id===id) return p; for(const c of n.children){ const f=findParent(c,id,n); if(f) return f; } return null; }
function pathOf(n, id, acc=[]){ if(!n) return null; const a=[...acc,n.text]; if(n.id===id) return a; for(const c of n.children){ const f=pathOf(c,id,a); if(f) return f; } return null; }
function visibleTree(n){ if(!n) return null; const copy={id:n.id,text:n.text,children:[]}; if(!collapsed.has(n.id)) copy.children=n.children.map(visibleTree); return copy; }
function msg(t){ $('msg').textContent = t || ''; }
function saveLibrary(){ const lib = loadLibrary(); lib[tree.id] = {name: tree.text, tree, mode, updated: Date.now()}; localStorage.setItem(LS_KEY, JSON.stringify(lib)); renderLibrary(); }
function loadLibrary(){ try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}'); } catch(e){ return {}; } }
function renderLibrary(){ const lib = loadLibrary(); const el = $('mapList'); el.innerHTML=''; Object.values(lib).sort((a,b)=>b.updated-a.updated).forEach(m=>{ const b=document.createElement('button'); b.className='mapitem'+(tree && m.tree.id===tree.id?' active':''); b.textContent=m.name; b.onclick=()=>{ tree=m.tree; mode=m.mode||'right'; $('layoutSel').value=mode; collapsed=new Set(); selected=null; render(); }; el.appendChild(b); }); }

async function render(){
  if(!tree) tree = blankTree();
  const vis = visibleTree(tree);
  const fd = new FormData(); fd.append('payload', JSON.stringify({tree: vis, mode}));
  const r = await fetch('/shajra/api/layout', {method:'POST', body: fd});
  const d = await r.json();
  if(!d.ok){ msg(d.error || 'Layout failed.'); return; }
  layoutData = d;
  draw(d);
  $('stats').innerHTML = `Nodes: <b>${d.stats.nodes}</b> &nbsp; Depth: <b>${d.stats.depth}</b> &nbsp; Leaves: <b>${d.stats.leaves}</b><br>Layout: <b>${mode}</b> &nbsp; Map: <b>${tree.width||''}</b>`;
  saveLibrary();
}
function edgePath(p, c, m){
  if(m==='down') return `M ${p.x+p.w/2} ${p.y+p.h} C ${p.x+p.w/2} ${p.y+p.h+40}, ${c.x+c.w/2} ${c.y-40}, ${c.x+c.w/2} ${c.y}`;
  if(m==='radial'){ const mx=(p.x+p.w/2+c.x+c.w/2)/2, my=(p.y+p.h/2+c.y+c.h/2)/2; return `M ${p.x+p.w/2} ${p.y+p.h/2} Q ${mx} ${my}, ${c.x+c.w/2} ${c.y+c.h/2}`; }
  return `M ${p.x+p.w} ${p.y+p.h/2} C ${p.x+p.w+35} ${p.y+p.h/2}, ${c.x-35} ${c.y+c.h/2}, ${c.x} ${c.y+c.h/2}`;
}
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function wrapLabel(t){ const words=t.split(/\s+/); const lines=[]; let cur=''; for(const w of words){ if((cur+' '+w).trim().length>22 && cur){ lines.push(cur); cur=w; } else cur=(cur+' '+w).trim(); } if(cur) lines.push(cur); return lines.slice(0,2); }
function draw(d){
  const svg = $('canvas');
  const W = d.width, H = d.height;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  let html = `<g transform="translate(${view.x},${view.y}) scale(${view.k})">`;
  for(const [pid, cid] of d.edges){
    const p=d.nodes[pid], c=d.nodes[cid]; if(!p||!c) continue;
    html += `<path class="edge" d="${edgePath(p,c,mode)}"/>`;
  }
  const order = []; (function bfs(n){ order.push(n.id); n.children.forEach(bfs); })(visibleTree(tree));
  for(const id of order){
    const n=d.nodes[id]; if(!n) continue;
    const node=findNode(tree,id); if(!node) continue;
    const lines=wrapLabel(node.text);
    const dim = presenting && order[presentIdx]!==id;
    const hasKids = node.children.length>0;
    const label = lines.map((ln,i)=>`<text x="${n.x+n.w/2}" y="${n.y+17+i*15}" text-anchor="middle">${esc(ln)}</text>`).join('');
    const badge = hasKids ? `<text x="${n.x+n.w-12}" y="${n.y+15}" text-anchor="middle" style="font-size:11px">${collapsed.has(id)?'＋':'−'}</text>` : '';
    html += `<g class="node depth${Math.min(n.depth,5)}${selected===id?' sel':''}${dim?' dim':''}" data-id="${id}" onclick="selectNode('${id}',event)" ondblclick="dblNode('${id}',event)"><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="10"></rect>${label}${badge}</g>`;
  }
  html += '</g>';
  svg.innerHTML = html;
  if(presenting){ const cur=order[presentIdx]; $('presentLabel').textContent = (presentIdx+1)+' / '+order.length+' — '+(findNode(tree,cur)||{}).text; }
}
function selectNode(id, ev){ ev.stopPropagation(); selected=id; const n=findNode(tree,id); $('panelTitle').textContent=n.text; $('nodeTools').style.display='block'; $('nodeText').value=n.text; $('nodePath').textContent=(pathOf(tree,id)||[]).join(' › '); render(); }
function dblNode(id, ev){ ev.stopPropagation(); selected=id; addChild(); }
function renameNode(v){ const n=findNode(tree,selected); if(n && v.trim()){ n.text=v.trim().slice(0,200); render(); } }
function addChild(){ const n=findNode(tree,selected); if(!n) return; const c={id:nid(),text:'New branch',children:[]}; n.children.push(c); collapsed.delete(n.id); selected=c.id; render(); setTimeout(()=>{ $('nodeText').focus(); $('nodeText').select(); },50); }
function addSibling(){ const n=findNode(tree,selected); if(!n) return; const p=findParent(tree,selected); if(!p){ msg('Central topic ka sibling nahi hota — child add karein.'); return; } const c={id:nid(),text:'New branch',children:[]}; p.children.push(c); selected=c.id; render(); }
function deleteNode(){ const n=findNode(tree,selected); if(!n) return; if(n===tree){ msg('Central topic delete nahi hota — rename karein.'); return; } const p=findParent(tree,selected); p.children=p.children.filter(c=>c.id!==selected); selected=null; $('nodeTools').style.display='none'; $('panelTitle').textContent='No node selected'; render(); }
function toggleCollapse(){ if(!selected) return; const n=findNode(tree,selected); if(!n.children.length){ msg('Is node ki koi branches nahi hain.'); return; } collapsed.has(selected)?collapsed.delete(selected):collapsed.add(selected); render(); }
function setLayout(m){ mode=m; render(); }
function zoomBy(f){ view.k=Math.min(3,Math.max(.2,view.k*f)); if(layoutData) draw(layoutData); }
function fitView(){ view={x:20,y:20,k:1}; if(layoutData) draw(layoutData); }
function newMap(){ tree=blankTree(); collapsed=new Set(); selected=null; $('nodeTools').style.display='none'; $('panelTitle').textContent='No node selected'; render(); }
function loadSample(k){ if(!SAMPLES[k]) return; tree=SAMPLES[k](); collapsed=new Set(); selected=null; render(); }
function openOutline(){ $('modalTitle').textContent='Outline import'; $('modalText').value=''; $('modalText').placeholder='Antibiotics\n  Beta-lactams\n    Penicillins\n    Cephalosporins\n  Macrolides'; $('modalMsg').textContent=''; $('modal').style.display='flex'; $('modalOk').onclick=submitOutline; }
function openAiMap(){ $('modalTitle').textContent='AI map from topic'; $('modalText').value=''; $('modalText').placeholder='e.g. Photosynthesis, or MDCAT Physics, or How to start freelancing'; $('modalMsg').textContent=''; $('modal').style.display='flex'; $('modalOk').onclick=submitAiMap; }
function closeModal(){ $('modal').style.display='none'; }
function modalSubmit(){}
async function submitOutline(){
  const fd=new FormData(); fd.append('text',$('modalText').value);
  const r=await fetch('/shajra/api/outline',{method:'POST',body:fd}); const d=await r.json();
  if(!d.ok){ $('modalMsg').textContent=d.error; return; }
  tree=d.tree; collapsed=new Set(); selected=null; closeModal(); render();
}
async function submitAiMap(){
  const topic=$('modalText').value.trim(); if(!topic){ $('modalMsg').textContent='Topic likhain.'; return; }
  $('modalMsg').textContent='AI map bana raha hai…';
  const fd=new FormData(); fd.append('topic',topic); fd.append('language', detectLang(topic));
  const r=await fetch('/shajra/api/ai-map',{method:'POST',body:fd}); const d=await r.json();
  if(!d.ok){ $('modalMsg').textContent=d.error; return; }
  tree=d.tree; collapsed=new Set(); selected=null; closeModal(); render();
}
async function aiExpand(){
  const n=findNode(tree,selected); if(!n) return;
  msg('AI branches bana raha hai…');
  const fd=new FormData(); fd.append('node',n.text); fd.append('path',(pathOf(tree,selected)||[]).join(' > ')); fd.append('language', detectLang(n.text));
  const r=await fetch('/shajra/api/ai-expand',{method:'POST',body:fd}); const d=await r.json();
  if(!d.ok){ msg(d.error); return; }
  collapsed.delete(selected);
  d.children.forEach(t=>n.children.push({id:nid(),text:t,children:[]}));
  msg(d.children.length+' branches add ho gayin.'); render();
}
function detectLang(t){ if(/[\u0600-\u06FF]/.test(t)) return 'ur'; const roman=['ka','ki','ko','se','mein','hai','hain','kya','aur','bhi','karna','kaise']; const words=t.toLowerCase().split(/\s+/); let hits=words.filter(w=>roman.includes(w)).length; return (hits>=2||(words.length&&hits/words.length>=0.4))?'roman':'en'; }
function togglePresent(){
  presenting=!presenting; $('presentBar').style.display=presenting?'flex':'none';
  if(presenting){ const vis=visibleTree(tree); presentOrder=[]; (function bfs(n){ presentOrder.push(n.id); n.children.forEach(bfs); })(vis); presentIdx=0; }
  if(layoutData) draw(layoutData);
}
function presentStep(d){ presentIdx=Math.min(presentOrder.length-1,Math.max(0,presentIdx+d)); if(layoutData) draw(layoutData); }
function download(name, content, type){ const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([content],{type})); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),5000); }
function exportSVG(){ const s=new XMLSerializer().serializeToString($('canvas')); download((tree.text||'shajra').replace(/\s+/g,'-')+'.svg', s, 'image/svg+xml'); msg('SVG export ho gaya — no watermark.'); }
function exportPNG(){
  const s=new XMLSerializer().serializeToString($('canvas'));
  const img=new Image(); const url=URL.createObjectURL(new Blob([s],{type:'image/svg+xml'}));
  img.onload=()=>{ const c=document.createElement('canvas'); c.width=layoutData.width*2; c.height=layoutData.height*2; const x=c.getContext('2d'); x.fillStyle='#0f172a'; x.fillRect(0,0,c.width,c.height); x.drawImage(img,0,0,c.width,c.height); URL.revokeObjectURL(url); c.toBlob(b=>{ const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=(tree.text||'shajra').replace(/\s+/g,'-')+'.png'; a.click(); }); msg('PNG export ho gaya — no watermark.'); };
  img.onerror=()=>{ msg('PNG export fail — SVG export use karein.'); };
  img.src=url;
}
function exportJSON(){ download((tree.text||'shajra').replace(/\s+/g,'-')+'.json', JSON.stringify({tree,mode},null,2), 'application/json'); }
function importJSON(ev){ const f=ev.target.files[0]; if(!f) return; const r=new FileReader(); r.onload=()=>{ try{ const d=JSON.parse(r.result); tree=d.tree||d; mode=d.mode||'right'; $('layoutSel').value=mode; collapsed=new Set(); selected=null; render(); }catch(e){ msg('JSON file theek nahi hai.'); } }; r.readAsText(f); ev.target.value=''; }
async function aiStatus(){ try{ const r=await fetch('/shajra/api/ai-status'); const d=await r.json(); const b=$('aiBadge'); if(d.ai_available){ b.textContent='AI: available ✓'; b.classList.remove('off'); } else { b.textContent='AI: key nahi hai — map phir bhi kaam karta hai'; } }catch(e){ $('aiBadge').textContent='AI: unknown'; } }
// pan + wheel zoom
(function(){
  const wrap=$('canvasWrap'); let drag=null;
  $('canvas').addEventListener('mousedown',e=>{ drag={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y}; });
  window.addEventListener('mousemove',e=>{ if(!drag) return; view.x=drag.vx+(e.clientX-drag.x); view.y=drag.vy+(e.clientY-drag.y); if(layoutData) draw(layoutData); });
  window.addEventListener('mouseup',()=>{ drag=null; });
  wrap.addEventListener('wheel',e=>{ e.preventDefault(); zoomBy(e.deltaY<0?1.1:0.9); },{passive:false});
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&presenting) togglePresent(); });
})();
tree = sampleAntibiotics();
aiStatus(); renderLibrary(); render();
</script>
</body>
</html>
"""
