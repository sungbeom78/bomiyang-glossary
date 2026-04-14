import re

content = open('e:/project/glossary/web/index.html', encoding='utf-8').read()

# 1. Add timezone select to topbar
tz_html = '<select id="tz-sel" onchange="updateAllTimestamps()" style="background:var(--s2);border:1px solid var(--ln);border-radius:var(--r);padding:2px 6px;color:var(--tx3);font-family:var(--mono);font-size:10px"><option value="KST">KST</option><option value="UTC">UTC</option></select>'
content = content.replace('<div id="tb-stats"></div>', tz_html + '<div id="tb-stats"></div>')

# 2. Add scripts
scripts = '''
function fmtDT(iso){
  if(!iso) return '';
  const d = new Date(iso);
  if(isNaN(d.getTime())) return iso;
  const tz = document.getElementById('tz-sel')?.value || 'KST';
  if(tz === 'UTC') return d.toISOString().replace('T',' ').substring(0,19) + 'Z';
  const kst = new Date(d.getTime() + 9*3600000);
  return kst.toISOString().replace('T',' ').substring(0,19) + '+09:00';
}
function updateAllTimestamps(){
  document.querySelectorAll('.dt-val').forEach(el => {
    const raw = el.dataset.dt;
    if(raw) el.textContent = fmtDT(raw);
  });
}
'''
content = content.replace('let WORDS=[],COMPOUNDS=[],BANNED=[],DRAFTS=[];', scripts + 'let WORDS=[],COMPOUNDS=[],BANNED=[],DRAFTS=[];')

# 3. Add to Word forms & save
wf_status_html = '<div class="fg"><div class="fl">status</div><select class="fsel" id="wf-status"><option value="active">active</option><option value="deprecated">deprecated</option></select></div>'
content = content.replace('<div class="fg"><div class="fl">domain <span class="req">*</span></div>', wf_status_html + '<div class="fg"><div class="fl">domain <span class="req">*</span></div>')

content = content.replace('document.getElementById(\'wf-domain\').value=w?.domain||\'general\';', 'document.getElementById(\'wf-domain\').value=w?.domain||\'general\';document.getElementById(\'wf-status\').value=w?.status||\'active\';')
content = content.replace('let body={id,domain:dom,status:"active",canonical_pos:pos,lang:{en,ko}};', 'let body={id,domain:dom,status:document.getElementById(\'wf-status\').value,canonical_pos:pos,lang:{en,ko}};')

# 4. Add to Compound forms & save
cf_status_html = '<div class="fg"><div class="fl">status</div><select class="fsel" id="cf-status"><option value="active">active</option><option value="deprecated">deprecated</option></select></div>'
content = content.replace('<div class="fg"><div class="fl">domain <span class="req">*</span></div>', cf_status_html + '<div class="fg"><div class="fl">domain <span class="req">*</span></div>')

content = content.replace('document.getElementById(\'cf-domain\').value=c?.domain||\'system\';', 'document.getElementById(\'cf-domain\').value=c?.domain||\'system\';document.getElementById(\'cf-status\').value=c?.status||\'active\';')
content = content.replace('let body={id,words,domain:dom,status:"active",lang:{en,ko},abbr:{long,short},reason};', 'let body={id,words,domain:dom,status:document.getElementById(\'cf-status\').value,lang:{en,ko},abbr:{long,short},reason};')

# 5. Add to Banned forms & save
bf_status_html = '<div class="fg"><div class="fl">status</div><select class="fsel" id="bf-status"><option value="active">active</option><option value="deprecated">deprecated</option></select></div>'
content = content.replace('<div class="fg"><div class="fl">사유 <span class="req">*</span></div>', bf_status_html + '<div class="fg"><div class="fl">사유 <span class="req">*</span></div>')

content = content.replace('document.getElementById(\'bf-reason\').value=b?.reason||\'\';', 'document.getElementById(\'bf-reason\').value=b?.reason||\'\';document.getElementById(\'bf-status\').value=b?.status||\'active\';')
content = content.replace('const body={expression:expr,context,correct,reason};', 'const body={expression:expr,context,correct,reason,status:document.getElementById(\'bf-status\').value};')

# 6. Add status badge to table ID column + metadata info to xrow
# Words
old_c_id = '<td class="c-id">${x(w.id)}</td>'
new_c_id = '<td class="c-id">${w.status==="deprecated"?`<span style="color:var(--re);margin-right:4px">[DEP]</span>`:""}${x(w.id)}</td>'
content = content.replace(old_c_id, new_c_id)

old_xi_w1 = '<div class="xv" style="font-family:var(--mono);color:var(--tx3)">${x(w.id)}</div></div>'
new_xi_w1 = old_xi_w1 + '<div class="xf"><label>status</label><div class="xv">${x(w.status||`active`)}</div></div><div class="xf"><label>created_at</label><div class="xv dt-val" data-dt="${x(w.created_at||``)}" style="font-family:var(--mono);font-size:9px">${fmtDT(w.created_at)}</div></div><div class="xf"><label>updated_at</label><div class="xv dt-val" data-dt="${x(w.updated_at||``)}" style="font-family:var(--mono);font-size:9px">${fmtDT(w.updated_at)}</div></div>'
content = content.replace(old_xi_w1, new_xi_w1)

# Compounds
old_c_id_comp = '<td class="c-id">${x(c.id)}</td>'
new_c_id_comp = '<td class="c-id">${c.status==="deprecated"?`<span style="color:var(--re);margin-right:4px">[DEP]</span>`:""}${x(c.id)}</td>'
content = content.replace(old_c_id_comp, new_c_id_comp)

old_xi_c1 = '<div class="xv" style="font-family:var(--mono);color:var(--tx3)">${x(c.id)}</div></div>'
new_xi_c1 = old_xi_c1 + '<div class="xf"><label>status</label><div class="xv">${x(c.status||`active`)}</div></div><div class="xf"><label>created_at</label><div class="xv dt-val" data-dt="${x(c.created_at||``)}" style="font-family:var(--mono);font-size:9px">${fmtDT(c.created_at)}</div></div><div class="xf"><label>updated_at</label><div class="xv dt-val" data-dt="${x(c.updated_at||``)}" style="font-family:var(--mono);font-size:9px">${fmtDT(c.updated_at)}</div></div>'
content = content.replace(old_xi_c1, new_xi_c1)

# Banned
old_b_td = '<td><code class="c-expr">${x(b.expression)}</code></td>'
new_b_td = '<td>${b.status==="deprecated"?`<span style="color:var(--re);margin-right:4px;font-size:9px">[DEP]</span>`:""}<code class="c-expr">${x(b.expression)}</code></td>'
content = content.replace(old_b_td, new_b_td)

with open('e:/project/glossary/web/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated index.html')
