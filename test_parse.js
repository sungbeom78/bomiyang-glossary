
const IS_PUBLIC = true;

// --- I18N SYSTEM ---
const I18N_DICT = {
  ko: {
    tab_words: "단어", tab_compounds: "복합어", tab_banned: "금지표현", tab_drafts: "보류(Drafts)",
    btn_checkid: "⊙ check-id", btn_log: "📋 log", btn_batch: "⚙ batch", btn_settings: "⚙ 설정", btn_git: "⎇ commit & push",
    btn_add_word: "+ 단어 추가",
    search_placeholder: "검색 — id, 영문, 한글, 약어…",
    all_domain: "전체 domain", all_pos: "전체 품사",
    th_id: "ID", th_en: "ENGLISH", th_ko: "한글", th_abbr: "ABBR", th_pos: "POS", th_domain: "DOMAIN", th_desc: "설명",
    stats_format: "단어 {words} · 복합어 {compounds} · 금지 {banned} · 보류 {drafts}",
    msg_saving: "저장 중...", msg_saved: "저장 성공", msg_error: "오류 발생",
    setting_title: "환경 설정",
    btn_close: "닫기",
    modal_settings: "⚙ 환경설정",
    modal_checkid: "⊙ check-id / suggest",
    modal_log: "📋 서버 로그",
    modal_git: "⎇ commit & push",
    modal_run: "실행",
    modal_batch: "⚙ 배치 병합",
    tab_scan: "1. 스캔",
    tab_result: "2. 결과 파일",
    tab_merge: "3. 병합",
    msg_drafts_cleared: "전체 스캔 결과가 없으므로, 보류(drafts) 리스트 {n}건을 전부 삭제했습니다.",
    msg_drafts_same: "발견된 후보와 현재 보류 건수가 동일합니다. '보류 목록 처리하기'를 진행하세요.",
    msg_drafts_diff: "새로운 항목이 발견되었습니다. 상단의 배치(Batch) 창에서 검증 작업을 수행하세요.",
    btn_scan_drafts: "▷ 스캔 (결과가 없을 경우 삭제)"
  },
  en: {
    tab_words: "Words", tab_compounds: "Compounds", tab_banned: "Banned", tab_drafts: "Drafts",
    btn_checkid: "⊙ check-id", btn_log: "📋 log", btn_batch: "⚙ batch", btn_settings: "⚙ Settings", btn_git: "⎇ commit & push",
    btn_add_word: "+ Add Word",
    search_placeholder: "Search — id, en, ko, abbr…",
    all_domain: "All domains", all_pos: "All POS",
    th_id: "ID", th_en: "ENGLISH", th_ko: "KOREAN", th_abbr: "ABBR", th_pos: "POS", th_domain: "DOMAIN", th_desc: "DESC",
    stats_format: "Words {words} · Compounds {compounds} · Banned {banned} · Drafts {drafts}",
    msg_saving: "Saving...", msg_saved: "Saved", msg_error: "Error",
    setting_title: "Settings",
    btn_close: "Close",
    modal_settings: "⚙ Settings",
    modal_checkid: "⊙ check-id / suggest",
    modal_log: "📋 Server Logs",
    modal_git: "⎇ commit & push",
    modal_run: "Run",
    modal_batch: "⚙ Batch Merge",
    tab_scan: "1. Scan",
    tab_result: "2. Results",
    tab_merge: "3. Merge",
    msg_drafts_cleared: "Since there are no scan results, all {n} draft items have been deleted.",
    msg_drafts_same: "Scan count matches drafts. Please proceed with 'Batch Editor'.",
    msg_drafts_diff: "New candidates found. Please run the Batch Analyzer.",
    btn_scan_drafts: "▷ Scan (Auto-clear if 0)"
  },
  ja: {
    msg_drafts_cleared: "全スキャン結果がないため、保留リストの{n}件をすべて削除しました。",
    msg_drafts_same: "候補数と保留リストの件数が同じです。バッチ処理を進めてください。",
    msg_drafts_diff: "新しい候補が見つかりました。バッチスキャンをやり直してください。",
    btn_scan_drafts: "▷ スキャン (結果0件で削除)"
  },
  zh_hans: {
    msg_drafts_cleared: "由于没有扫描结果，已删除全部 {n} 个候选列表项。",
    msg_drafts_same: "扫描结果与保留列表数量相同。请继续进行批量处理。",
    msg_drafts_diff: "发现新候选。请重新运行批量扫描作业。",
    btn_scan_drafts: "▷ 扫描 (如果为0则删除)"
  }
};

function t(key, args = {}) {
  const lang = window.LANG || 'en'; // default english if not ko
  let dict = I18N_DICT[lang];
  // fallback to en if language dictionary doesn't exist (e.g. ja, zh_hans)
  if (!dict) dict = I18N_DICT['en'];
  
  let str = dict[key] || I18N_DICT['en'][key] || key;
  for (const k in args) {
    str = str.replace(`{${k}}`, args[k]);
  }
  return str;
}

function updateI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (el.tagName === 'INPUT' && el.type === 'text') {
      if (el.placeholder) el.placeholder = t(key);
    } else {
      // Keep any span badges like <span class="badge"> inside
      let badge = el.querySelector('.badge');
      if (badge) {
        // Only replace text nodes to preserve child HTML
        for (let node of el.childNodes) {
          if (node.nodeType === 3 && node.nodeValue.trim()) {
            node.nodeValue = t(key);
            break;
          }
        }
      } else {
        el.textContent = t(key);
      }
    }
  });
  
  // Custom non-declarative elements
  if(window.renderWords) renderWords();
}
// -------------------



function initMultiInput(containerId, initialValues, datalistId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    
    container.style.display = 'flex';
    container.style.flexWrap = 'wrap';
    container.style.gap = '4px';
    container.style.alignItems = 'center';
    container.style.cursor = 'text';
    
    let values = Array.isArray(initialValues) ? [...initialValues] : (initialValues ? String(initialValues).split(',').map(s=>s.trim()).filter(Boolean) : []);
    
    function render() {
        container.innerHTML = '';
        values.forEach((val, idx) => {
            const tag = document.createElement('div');
            tag.style.cssText = 'background:var(--ac);color:#000;border-radius:2px;padding:1px 5px;font-size:10px;display:flex;align-items:center;gap:4px;';
            tag.innerHTML = `<span style="font-family:var(--mono);font-weight:600">${escapeHtml(val)}</span>`;
            
            const btn = document.createElement('span');
            btn.textContent = '×';
            btn.style.cssText = 'cursor:pointer;font-weight:bold;color:rgba(0,0,0,0.5);margin-left:2px;';
            btn.onmouseenter = () => btn.style.color = '#000';
            btn.onmouseleave = () => btn.style.color = 'rgba(0,0,0,0.5)';
            btn.onclick = (e) => {
                e.stopPropagation();
                values.splice(idx, 1);
                updateValue();
                render();
            };
            tag.appendChild(btn);
            container.appendChild(tag);
        });
        
        const input = document.createElement('input');
        input.type = 'text';
        if(datalistId) input.setAttribute('list', datalistId);
        input.style.cssText = 'border:none;outline:none;background:transparent;color:var(--tx);flex:1;min-width:70px;padding:0;font-size:10px;font-family:inherit;';
        
        input.onkeydown = (e) => {
            if(e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                const v = input.value.trim().replace(/,/g, '');
                if(v && !values.includes(v)) {
                    values.push(v);
                    updateValue();
                    render();
                    setTimeout(() => { const i = container.querySelector('input'); if(i) i.focus(); }, 0);
                }
            } else if(e.key === 'Backspace' && input.value === '' && values.length > 0) {
                values.pop();
                updateValue();
                render();
                setTimeout(() => { const i = container.querySelector('input'); if(i) i.focus(); }, 0);
            }
        };
        input.onblur = () => {
            const v = input.value.trim().replace(/,/g, '');
            if(v && !values.includes(v)) {
                values.push(v);
                updateValue();
                render();
            }
        };
        container.appendChild(input);
        container.onclick = () => input.focus();
    }
    
    function updateValue() {
        container.dataset.value = JSON.stringify(values);
    }
    
    updateValue();
    render();
}

function getMultiInputValue(containerId) {
    const container = document.getElementById(containerId);
    if (!container || !container.dataset.value) return [];
    try { return JSON.parse(container.dataset.value); } catch(e) { return []; }
}

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
let WORDS=[],COMPOUNDS=[],BANNED=[],DRAFTS=[];
let wFlt=[],cFlt=[],bFlt=[],dFlt=[];
let wSort={col:'id',dir:1},cSort={col:'id',dir:1};
let wExpId=null,cExpId=null;
let editWordId=null,editCompoundId=null,editBannedExpr=null;
let _batchSelFile=null,_batchTerms=[],_allLogLines=[];
const STEPS=['validate + generate','git add','git commit','git push'];
const DC={trading:'d-trading',market:'d-market',system:'d-system',infra:'d-infra',ui:'d-ui',general:'d-general',proper:'d-proper'};

// variants array 헬퍼 (Plan v2.5.1 §3)
function getVariantShort(variants) {
  if (Array.isArray(variants)) {
    const v = variants.find(v => v && v.type === 'abbreviation' && v.short);
    return v ? v.short : '';
  }
  // 하위호환: object 형식
  const abbr = variants?.abbreviation;
  if (Array.isArray(abbr)) return abbr[0] || '';
  return abbr || '';
}
function getVariantLong(variants) {
  if (Array.isArray(variants)) {
    const v = variants.find(v => v && v.type === 'abbreviation' && v.long);
    return v ? v.long : '';
  }
  return '';
}
// compound의 abbreviation short/long 추출 (variants array 또는 구 bbr 하위호환)
function cAbbrShort(c) { return getVariantShort(c.variants) || c.abbreviation?.short || ''; }
function cAbbrLong(c)  { return getVariantLong(c.variants)  || c.abbreviation?.long  || ''; }

// words ETag cache for reload optimization
let _wordsETag = '';
async function boot(){
  // 언어/시간대 초기화
  const savedLang = localStorage.getItem('glossary_lang') || 'ko';
  const savedTz   = localStorage.getItem('glossary_tz')   || 'KST';
  window.LANG = savedLang;
  updateI18n(); // 초기 다국어 적용
  const langSel = document.getElementById('lang-sel');
  if (langSel) langSel.value = savedLang;
  const tzSel = document.getElementById('tz-sel');
  if (tzSel) tzSel.value = savedTz;
  try{
    // words를 먼저 로드하여 첫 번째 페인트를 앞당김
    const wd = await fetch('/api/words').then(r => {
      _wordsETag = r.headers.get('ETag') || '';
      return r.json();
    });
    WORDS = wd.words || [];
    wFlt = [...WORDS];
    renderWords();
    updateStats();
    // 나머지는 병렬로 처리
    const [cd, bd, dd] = await Promise.all([
      fetch('/api/compounds').then(r => r.json()),
      fetch('/api/banned').then(r => r.json()),
      fetch('/api/drafts').then(r => r.json())
    ]);
    COMPOUNDS = cd.compounds || []; BANNED = bd.banned || []; DRAFTS = dd.drafts || [];
    cFlt = [...COMPOUNDS]; bFlt = [...BANNED]; dFlt = [...DRAFTS];
    renderCompounds(); renderBanned(); renderDrafts(); updateStats(); loadBranch();
  } catch(e) { toast('서버 연결 실패', 'ter'); }
}

function updateStats(){
  document.getElementById('tb-stats').textContent=`단어 ${WORDS.length} · 복합어 ${COMPOUNDS.length} · 금지 ${BANNED.length} · 보류 ${DRAFTS.length}`;
  document.getElementById('badge-words').textContent=WORDS.length;
  document.getElementById('badge-compounds').textContent=COMPOUNDS.length;
  document.getElementById('badge-banned').textContent=BANNED.length;
  document.getElementById('badge-drafts').textContent=DRAFTS.length;
}

function renderDrafts(){
  const b=document.getElementById('d-body');
  if(!b) return;
  b.innerHTML='';
  document.getElementById('d-cnt').textContent=`총 ${dFlt.length}개`;
  dFlt.forEach((d,i)=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td class="id-cell">${escapeHtml(d.id||'')}</td>
      <td>${escapeHtml(d.lang?.ko||d.ko||'')}</td>
      <td><pre style="margin:0;font-size:9px;white-space:pre-wrap;color:var(--tx3)">${escapeHtml(JSON.stringify(d, null, 2))}</pre></td>
      <td></td>
    `;
    b.appendChild(tr);
  });
}

function dFilter(){
  const sq=document.getElementById('d-search').value.toLowerCase();
  dFlt=DRAFTS.filter(d=>(d.id||'').toLowerCase().includes(sq)||(d.lang?.ko||d.ko||'').includes(sq));
  renderDrafts();
}

async function loadDrafts(){
  try{
    const dd=await fetch('/api/drafts').then(r=>r.json());
    DRAFTS=dd.drafts||[];
    dFilter();
    updateStats();
  }catch(e){toast('Drafts 로드 실패','ter');}
}

async function loadBranch(){
  try{const d=await(await fetch('/api/git/status')).json();
    document.getElementById('br-nm').textContent=d.branch||'—';
    document.getElementById('tb-branch').classList.toggle('dirty',d.has_changes);
    document.getElementById('git-btn').textContent=d.has_changes?`⎇ commit & push (${d.changed.length})`:'⎇ commit & push';
  }catch(e){}
}

function switchTab(tab){
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===tab));
  document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${tab}`));
  const a=document.getElementById('tab-actions');
  if(tab==='words'||tab==='compounds')
    a.innerHTML=IS_PUBLIC ? '' : `<button class="btn btn-gh" onclick="runGenerate()">▷ generate</button><button class="btn btn-gh" onclick="runValidate()">▷ validate</button>`;
  else a.innerHTML='';
  
  if (tab === 'drafts') loadDrafts();
}
switchTab('words');

// ── WORDS ──
function wFilter(){
  const q=document.getElementById('w-search').value.toLowerCase().trim();
  const dm=document.getElementById('w-domain').value,ps=document.getElementById('w-pos').value;
  wFlt=WORDS.filter(w=>{if(dm&&(!Array.isArray(w.domain)?w.domain!==dm:!w.domain.includes(dm)))return false;if(ps&&w.canonical_pos!==ps)return false;
    if(!q)return true;return[w.id,w.lang?.en,w.lang?.ko,w.abbreviation?.short,w.abbreviation?.long,getVariantShort(w.variants),w.description_i18n?.ko].some(v=>v&&v.toLowerCase().includes(q));});
  wFlt.sort((a,b)=>{const av=(a[wSort.col]||'').toLowerCase(),bv=(b[wSort.col]||'').toLowerCase();return av<bv?-wSort.dir:av>bv?wSort.dir:0;});
  renderWords();
}

function renderWords(){
  const tb = document.getElementById('w-body');
  const frag = document.createDocumentFragment();
  const n = wFlt.length;
  const lang = window.LANG || 'ko';
  for (let i = 0; i < n; i++) {
    const w = wFlt[i];
    const isExp = w.id === wExpId;
    const tr = document.createElement('tr');
    if (isExp) tr.classList.add('sel');
    tr.dataset.id = w.id;
    const en   = w.lang && w.lang.en   ? w.lang.en   : '';
    const ko   = w.lang && w.lang.ko   ? w.lang.ko   : '';
    const displayLang = (w.lang && w.lang[lang]) ? w.lang[lang] : (en || ko);
    const desc = (w.description_i18n && w.description_i18n[lang])
                 ? w.description_i18n[lang]
                 : (w.description_i18n && w.description_i18n.ko ? w.description_i18n.ko : '');
    const abbr = getVariantShort(w.variants);
    const depBadge = w.status === 'deprecated'
      ? '<span style="color:var(--re);margin-right:4px">[DEP]</span>' : '';
    const abbrHtml = abbr ? '<span class="c-abbr">' + x(abbr) + '</span>' : '—';
    tr.innerHTML = (
      '<td class="c-id">' + depBadge + x(w.id) + '</td>' +
      '<td class="c-en">' + x(en) + '</td>' +
      '<td class="c-ko">' + x(lang === 'ko' ? ko : displayLang) + '</td>' +
      '<td>' + abbrHtml + '</td>' +
      '<td><span class="c-pos">' + x(w.canonical_pos) + '</span></td>' +
      '<td><span class="c-domain ' + (DC[Array.isArray(w.domain)?w.domain[0]:w.domain] || 'd-general') + '">' + x(Array.isArray(w.domain)?w.domain[0]:w.domain) + '</span></td>' +
      '<td class="c-desc" title="' + x(desc) + '">' + x(desc) + '</td>' +
      '<td style="text-align:center">' + (IS_PUBLIC ? '' : '<button class="del-btn" data-del-word="' + x(w.id) + '" data-del-ko="' + x(ko) + '">&#x1F5D1;</button>') + '</td>'
    );
    frag.appendChild(tr);
    if (isExp) {
      const xr = document.createElement('tr');
      xr.className = 'xrow';
      const nots = (w.not || []).map(function(n){ return '<span class="not-chip">' + x(n) + '</span>'; }).join(' ');
      const wid = x(w.id);
      const varHtml = (w.variants || []).filter(function(v){ return v && v.type !== 'abbreviation'; })
        .map(function(v){
          return '<span class="c-word-chip">' + x(v.type) + ':<b style="color:var(--tx)">' + x(v.value || v.short || '') + '</b></span>';
        }).join(' ');
      const synHtml = (w.synonyms || []).map(function(s){ return '<span class="c-word-chip">' + x(s) + '</span>'; }).join(' ');
      const antHtml = (w.antonyms || []).map(function(s){ return '<span class="not-chip">' + x(s) + '</span>'; }).join(' ');
      const urlHtml = (w.source_urls || []).map(function(u){
        return '<a href="' + x(u) + '" target="_blank" style="color:var(--ac);font-family:var(--mono);font-size:9px;word-break:break-all">' + x(u) + '</a>';
      }).join('<br>');
      const jaVal  = w.lang && w.lang.ja      ? w.lang.ja      : '—';
      const zhVal  = w.lang && w.lang.zh_hans ? w.lang.zh_hans : '—';
      const descKo = w.description_i18n && w.description_i18n.ko ? w.description_i18n.ko : '';
      const descEn = w.description_i18n && w.description_i18n.en ? w.description_i18n.en : '';
      let xi = (
        '<td colspan="8"><div class="xi">' +
        '<div class="xf"><label>id</label><div class="xv" style="font-family:var(--mono);color:var(--tx3)">' + wid + '</div></div>' +
        '<div class="xf"><label>status</label><div class="xv">' + x(w.status || 'active') + '</div></div>' +
        '<div class="xf"><label>created_at</label><div class="xv dt-val" data-dt="' + x(w.created_at || '') + '" style="font-family:var(--mono);font-size:9px">' + fmtDT(w.created_at) + '</div></div>' +
        '<div class="xf"><label>updated_at</label><div class="xv dt-val" data-dt="' + x(w.updated_at || '') + '" style="font-family:var(--mono);font-size:9px">' + fmtDT(w.updated_at) + '</div></div>' +
        '<div class="xf"><label>pos</label><div class="xv"><span class="c-pos">' + x(w.canonical_pos) + '</span></div></div>' +
        '<div class="xf"><label>domain</label><div class="xv"><span class="c-domain ' + (DC[Array.isArray(w.domain)?w.domain[0]:w.domain] || '') + '">' + x(Array.isArray(w.domain)?w.domain[0]:w.domain) + '</span></div></div>' +
        '<div class="xf"><label>lang.ja</label><div class="xv">' + x(jaVal) + '</div></div>' +
        '<div class="xf"><label>lang.zh_hans</label><div class="xv">' + x(zhVal) + '</div></div>' +
        '<div class="xf full"><label>description (ko)</label><div class="xv">' + x(descKo) + '</div></div>'
      );
      if (descEn) xi += '<div class="xf full"><label>description (en)</label><div class="xv" style="color:var(--tx3)">' + x(descEn) + '</div></div>';
      if (w.from) xi += '<div class="xf"><label>from</label><div class="xv" style="font-family:var(--mono);color:var(--ye)">' + x(w.from) + '</div></div>';
      if (varHtml) xi += '<div class="xf full"><label>variants</label><div class="xv">' + varHtml + '</div></div>';
      if (synHtml) xi += '<div class="xf full"><label>synonyms</label><div class="xv">' + synHtml + '</div></div>';
      if (antHtml) xi += '<div class="xf full"><label>antonyms</label><div class="xv">' + antHtml + '</div></div>';
      if (urlHtml) xi += '<div class="xf full"><label>source_urls</label><div class="xv">' + urlHtml + '</div></div>';
      if (w.not && w.not.length) xi += '<div class="xf full"><label>NOT</label><div class="xv">' + nots + '</div></div>';
      if (!IS_PUBLIC) xi += '<div class="xf full"><span class="edit-link" data-edit-word="' + wid + '">&#x270F; &#xC218;&#xC815;</span></div>';
      xi += '</div></td>';
      xr.innerHTML = xi;
      frag.appendChild(xr);
    }
  }
  tb.innerHTML = '';
  tb.appendChild(frag);
  const cntEl = document.getElementById('w-cnt');
  cntEl.textContent = wFlt.length === WORDS.length
    ? wFlt.length + '개'
    : wFlt.length + '/' + WORDS.length + '개';
}
function toggleWExp(id){ wExpId = (wExpId === id) ? null : id; renderWords(); }
document.getElementById('w-body').addEventListener('click', e => {
  const delBtn = e.target.closest('[data-del-word]');
  if (delBtn) {
    e.stopPropagation();
    const wid = delBtn.dataset.delWord;
    const ko  = delBtn.dataset.delKo;
    confirmDel(() => doDeleteWord(wid), ko);
    return;
  }
  const editLink = e.target.closest('[data-edit-word]');
  if (editLink) {
    openWordForm(WORDS.find(w => w.id === editLink.dataset.editWord));
    return;
  }
  const tr = e.target.closest('tr[data-id]');
  if (tr) toggleWExp(tr.dataset.id);
});
document.getElementById('w-body').addEventListener('dblclick', e => {
  const tr = e.target.closest('tr[data-id]');
  if (tr) { e.preventDefault(); openWordForm(WORDS.find(w => w.id === tr.dataset.id)); }
});
document.querySelectorAll('#w-tbl th.srt').forEach(th=>{th.addEventListener('click',()=>{const col=th.dataset.col;wSort.dir=(wSort.col===col)?-wSort.dir:1;wSort.col=col;document.querySelectorAll('#w-tbl th').forEach(h=>h.classList.remove('sa','sd'));th.classList.add(wSort.dir===1?'sa':'sd');wFilter();});});

// ── COMPOUNDS ──
function cFilter(){
  const q=document.getElementById('c-search').value.toLowerCase().trim();
  const dm=document.getElementById('c-domain').value;
  cFlt=COMPOUNDS.filter(c=>{if(dm&&(!Array.isArray(c.domain)?c.domain!==dm:!c.domain.includes(dm)))return false;if(!q)return true;
    return[c.id,c.lang?.ko,c.lang?.en,cAbbrLong(c),cAbbrShort(c),(c.words||[]).join(' '),c.description_i18n?.ko].some(v=>v&&v.toLowerCase().includes(q));});
  cFlt.sort((a,b)=>{const av=(a[cSort.col]||'').toLowerCase(),bv=(b[cSort.col]||'').toLowerCase();return av<bv?-cSort.dir:av>bv?cSort.dir:0;});
  renderCompounds();
}
function renderCompounds(){
  const tb=document.getElementById('c-body');tb.innerHTML='';
  cFlt.forEach(c=>{const isExp=c.id===cExpId;const tr=document.createElement('tr');if(isExp)tr.classList.add('sel');tr.dataset.id=c.id;
    const wchips=(c.words||[]).map(w=>`<span class="c-word-chip">${x(w)}</span>`).join('');
    const ko=x(c.lang?.ko||''), en=x(c.lang?.en||''), desc=x(c.description_i18n?.ko||'');
    tr.innerHTML=`<td class="c-id">${c.status==="deprecated"?`<span style="color:var(--re);margin-right:4px">[DEP]</span>`:""}${x(c.id)}</td><td><div class="c-words">${wchips}</div></td><td class="c-ko">${ko}</td><td class="c-en" style="font-family:var(--mono);font-size:11px">${x(cAbbrLong(c))}</td><td><span class="c-abbr">${x(cAbbrShort(c))}</span></td><td><span class="c-domain ${DC[c.domain]||'d-general'}">${x(c.domain)}</span></td><td class="c-desc" title="${desc}">${desc}</td><td style="text-align:center">${IS_PUBLIC ? '' : `<button class="del-btn" onclick="event.stopPropagation();confirmDel(()=>doDeleteCompound('${x(c.id)}'),'${ko}')">🗑</button>`}</td>`;
    tr.addEventListener('click',()=>toggleCExp(c.id));tr.addEventListener('dblclick',e=>{e.preventDefault();openCompoundForm(c);});tb.appendChild(tr);
    if(isExp){const xr=document.createElement('tr');xr.className='xrow';const nots=(c.not||[]).map(n=>`<span class="not-chip">${x(n)}</span>`).join(' ');
      xr.innerHTML=`<td colspan="8"><div class="xi"><div class="xf"><label>id</label><div class="xv" style="font-family:var(--mono);color:var(--tx3)">${x(c.id)}</div></div><div class="xf"><label>status</label><div class="xv">${x(c.status||`active`)}</div></div><div class="xf"><label>created_at</label><div class="xv dt-val" data-dt="${x(c.created_at||``)}" style="font-family:var(--mono);font-size:9px">${fmtDT(c.created_at)}</div></div><div class="xf"><label>updated_at</label><div class="xv dt-val" data-dt="${x(c.updated_at||``)}" style="font-family:var(--mono);font-size:9px">${fmtDT(c.updated_at)}</div></div><div class="xf"><label>abbr_long</label><div class="xv" style="font-family:var(--mono);color:var(--gr)">${x(cAbbrLong(c))}</div></div><div class="xf"><label>abbr_short</label><div class="xv"><span class="c-abbr">${x(cAbbrShort(c))}</span></div></div><div class="xf full"><label>등록 사유</label><div class="xv">${x(c.reason||'')}</div></div><div class="xf full"><label>description</label><div class="xv">${desc}</div></div>${c.not?.length?`<div class="xf full"><label>NOT</label><div class="xv">${nots}</div></div>`:''}${IS_PUBLIC ? '' : `<div class="xf full"><span class="edit-link" onclick="openCompoundForm(COMPOUNDS.find(c=>c.id==='${x(c.id)}'))">✏ 수정</span></div>`}</div></td>`;
      tb.appendChild(xr);}
  });
  document.getElementById('c-cnt').textContent=cFlt.length===COMPOUNDS.length?`${COMPOUNDS.length}개`:`${cFlt.length}/${COMPOUNDS.length}개`;
}
function toggleCExp(id){cExpId=(cExpId===id)?null:id;renderCompounds();}
document.querySelectorAll('#c-tbl th.srt').forEach(th=>{th.addEventListener('click',()=>{const col=th.dataset.col;cSort.dir=(cSort.col===col)?-cSort.dir:1;cSort.col=col;document.querySelectorAll('#c-tbl th').forEach(h=>h.classList.remove('sa','sd'));th.classList.add(cSort.dir===1?'sa':'sd');cFilter();});});

// ── BANNED ──
function bFilter(){const q=document.getElementById('b-search').value.toLowerCase().trim();bFlt=BANNED.filter(b=>{if(!q)return true;const cv=typeof b.correct==='object'?(b.correct?.value||''):String(b.correct||'');const reason=b.reason_i18n?.[window.LANG]||b.reason_i18n?.ko||b.reason||'';return[b.expression,b.context,cv,reason].some(v=>v&&v.toLowerCase().includes(q));});renderBanned();}
function renderBanned(){const tb=document.getElementById('b-body');if(!tb)return;tb.innerHTML='';bFlt.forEach(b=>{const tr=document.createElement('tr');const cv=typeof b.correct==='object'?(b.correct?.value||''):String(b.correct||'');const reason=b.reason_i18n?.[window.LANG]||b.reason_i18n?.ko||b.reason||'';const ctx=b.context||'';tr.innerHTML=`<td>${b.status==="deprecated"?`<span style="color:var(--re);margin-right:4px;font-size:9px">[DEP]</span>`:""}<code class="c-expr">${x(b.expression)}</code></td><td class="c-desc">${x(ctx)}</td><td><code class="c-correct">${x(cv)}</code></td><td class="c-desc">${x(reason)}</td><td style="text-align:center">${IS_PUBLIC ? '' : `<button class="del-btn" onclick="event.stopPropagation();confirmDel(()=>doDeleteBanned('${x(b.expression)}'),'${x(b.expression)}')">🗑</button>`}</td>`;if(!IS_PUBLIC){tr.addEventListener('dblclick',e=>{e.preventDefault();openBannedForm(b);});}tb.appendChild(tr);});document.getElementById('b-cnt').textContent=`${bFlt.length}개`;}

// ── WORD FORM ──
// variants 배열 → textarea 포맷 변환 (abbreviation type 제외)
function variantsToText(variants) {
  if (!Array.isArray(variants)) return '';
  return variants
    .filter(v => v && v.type !== 'abbreviation')
    .map(v => `${v.type}:${v.value || v.short || ''}`)
    .join('\n');
}
// textarea 텍스트 → variants 배열 변환
function textToVariants(text, abbr) {
  const result = [];
  if (abbr) result.push({type: 'abbreviation', short: abbr});
  if (text.trim()) {
    text.split('\n').forEach(line => {
      const p = line.trim();
      if (!p) return;
      const colon = p.indexOf(':');
      if (colon > 0) {
        result.push({type: p.slice(0, colon).trim(), value: p.slice(colon+1).trim()});
      }
    });
  }
  return result;
}
function openWordForm(w) {
  editWordId = w ? w.id : null;
  document.getElementById('word-title').textContent = w ? '단어 수정' : '단어 추가';
  document.getElementById('wf-id').value        = w?.id || '';
  document.getElementById('wf-id').disabled     = !!w;
  document.getElementById('wf-pos').value       = w?.canonical_pos || 'noun';
  document.getElementById('wf-status').value    = w?.status || 'active';
  initMultiInput('wf-domain', w?.domain || ['general'], 'domain-list');
  // 다국어
  document.getElementById('wf-en').value        = w?.lang?.en || '';
  document.getElementById('wf-ko').value        = w?.lang?.ko || '';
  document.getElementById('wf-ja').value        = w?.lang?.ja || '';
  document.getElementById('wf-zh').value        = w?.lang?.zh_hans || '';
  // 설명
  document.getElementById('wf-desc').value      = w?.description_i18n?.ko || '';
  document.getElementById('wf-desc-en').value   = w?.description_i18n?.en || '';
  // 형태소
  document.getElementById('wf-abbr').value      = getVariantShort(w?.variants) || '';
  document.getElementById('wf-from').value      = w?.from || '';
  document.getElementById('wf-variants').value  = variantsToText(w?.variants);
  document.getElementById('wf-synonyms').value  = (w?.synonyms || []).join(', ');
  document.getElementById('wf-antonyms').value  = (w?.antonyms || []).join(', ');
  document.getElementById('wf-urls').value      = (w?.source_urls || []).join('\n');
  document.getElementById('wf-not').value       = (w?.not || []).join(', ');
  document.getElementById('wf-del-btn').style.display = w ? '' : 'none';
  openOv('word-ov');
}
async function saveWord() {
  const id     = document.getElementById('wf-id').value.trim();
  const en     = document.getElementById('wf-en').value.trim();
  const ko     = document.getElementById('wf-ko').value.trim();
  const ja     = document.getElementById('wf-ja').value.trim();
  const zh     = document.getElementById('wf-zh').value.trim();
  const abbr   = document.getElementById('wf-abbr').value.trim() || null;
  const pos    = document.getElementById('wf-pos').value;
  const dom    = getMultiInputValue('wf-domain');
  const desc   = document.getElementById('wf-desc').value.trim();
  const descEn = document.getElementById('wf-desc-en').value.trim();
  const fromV  = document.getElementById('wf-from').value.trim();
  const varTxt = document.getElementById('wf-variants').value;
  const synTxt = document.getElementById('wf-synonyms').value.trim();
  const antTxt = document.getElementById('wf-antonyms').value.trim();
  const urlTxt = document.getElementById('wf-urls').value.trim();
  const notV   = document.getElementById('wf-not').value.trim();
  if (!id || !en || !ko || !desc) { toast('필수 항목 누락 (id, english, 한글, 설명)', 'ter'); return; }
  const langObj = {en, ko};
  if (ja) langObj.ja = ja;
  if (zh) langObj.zh_hans = zh;
  const descObj = {ko: desc};
  if (descEn) descObj.en = descEn;
  const variants = textToVariants(varTxt, abbr);
  let body = {
    id, domain: dom,
    status: document.getElementById('wf-status').value,
    canonical_pos: pos,
    lang: langObj,
    description_i18n: descObj,
  };
  if (variants.length) body.variants = variants;
  else if (abbr) body.variants = [{type:'abbreviation', short: abbr}];
  if (fromV) body.from = fromV;
  if (synTxt) body.synonyms = synTxt.split(',').map(s => s.trim()).filter(Boolean);
  if (antTxt) body.antonyms = antTxt.split(',').map(s => s.trim()).filter(Boolean);
  if (urlTxt) body.source_urls = urlTxt.split('\n').map(s => s.trim()).filter(Boolean);
  if (notV)   body.not = notV.split(',').map(s => s.trim()).filter(Boolean);
  const isAdd = !editWordId;
  const res = await fetch(isAdd ? '/api/words' : `/api/words/${editWordId}`,
    {method: isAdd ? 'POST' : 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const d = await res.json();
  if (!res.ok) { toast(d.error || '저장 실패', 'ter'); return; }
  toast(isAdd ? '추가 완료' : '수정 완료', 'tok');
  closeOv('word-ov');
  await reloadWords();
}
async function doDeleteWord(id){const res=await fetch(`/api/words/${id}`,{method:'DELETE'});if(!res.ok){toast('삭제 실패','ter');return;}toast('삭제 완료','tok');closeOv('del-ov');closeOv('word-ov');await reloadWords();}
function delWord(){confirmDel(()=>doDeleteWord(editWordId),editWordId);}
async function reloadWords(){
  const headers = _wordsETag ? {'If-None-Match': _wordsETag} : {};
  const resp = await fetch('/api/words', {headers});
  if (resp.status === 304) { wFlt = [...WORDS]; wFilter(); updateStats(); return; }
  _wordsETag = resp.headers.get('ETag') || '';
  const d = await resp.json();
  WORDS = d.words || []; wFlt = [...WORDS]; wFilter(); updateStats();
}

// ── COMPOUND FORM ──
function openCompoundForm(c){editCompoundId=c?c.id:null;document.getElementById('compound-title').textContent=c?'복합어 수정':'복합어 추가';document.getElementById('cf-id').value=c?.id||'';document.getElementById('cf-id').disabled=!!c;document.getElementById('cf-words').value=(c?.words||[]).join(', ');document.getElementById('cf-ko').value=c?.lang?.ko||'';document.getElementById('cf-en').value=c?.lang?.en||'';document.getElementById('cf-long').value=cAbbrLong(c)||'';document.getElementById('cf-short').value=cAbbrShort(c)||'';initMultiInput('cf-domain', c?.domain || ['system'], 'domain-list');document.getElementById('cf-status').value=c?.status||'active';document.getElementById('cf-reason').value=c?.reason||'의미 비합산';document.getElementById('cf-desc').value=c?.description_i18n?.ko||'';document.getElementById('cf-not').value=(c?.not||[]).join(', ');document.getElementById('cf-del-btn').style.display=c?'':'none';openOv('compound-ov');}
async function saveCompound(){const id=document.getElementById('cf-id').value.trim(),words=document.getElementById('cf-words').value.split(',').map(s=>s.trim()).filter(Boolean),ko=document.getElementById('cf-ko').value.trim(),en=document.getElementById('cf-en').value.trim(),long=document.getElementById('cf-long').value.trim(),short=document.getElementById('cf-short').value.trim(),dom=getMultiInputValue('cf-domain'),reason=document.getElementById('cf-reason').value,desc=document.getElementById('cf-desc').value.trim(),notV=document.getElementById('cf-not').value.trim();if(!id||!words.length||!ko||!en||!long||!short||!desc){toast('필수 항목 누락','ter');return;}const abbrVariant={type:'abbreviation',short};if(long)abbrVariant.long=long;let body={id,words,domain:dom,status:document.getElementById('cf-status').value,lang:{en,ko},variants:[abbrVariant],reason};if(desc)body.description_i18n={ko:desc};if(notV)body.not=notV.split(',').map(s=>s.trim()).filter(Boolean);const isAdd=!editCompoundId;const res=await fetch(isAdd?'/api/compounds':`/api/compounds/${editCompoundId||id}`,{method:isAdd?'POST':'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await res.json();if(!res.ok){toast(d.error||'저장 실패','ter');return;}toast(isAdd?'추가 완료':'수정 완료','tok');closeOv('compound-ov');await reloadCompounds();}
async function doDeleteCompound(id){const res=await fetch(`/api/compounds/${id}`,{method:'DELETE'});if(!res.ok){toast('삭제 실패','ter');return;}toast('삭제 완료','tok');closeOv('del-ov');closeOv('compound-ov');await reloadCompounds();}
function delCompound(){confirmDel(()=>doDeleteCompound(editCompoundId),editCompoundId);}
async function reloadCompounds(){const d=await(await fetch('/api/compounds')).json();COMPOUNDS=d.compounds||[];cFlt=[...COMPOUNDS];cFilter();updateStats();}

// ── BANNED FORM ──
function openBannedForm(b){editBannedExpr=b?b.expression:null;document.getElementById('banned-title').textContent=b?'금지표현 수정':'금지표현 추가';document.getElementById('bf-expr').value=b?.expression||'';document.getElementById('bf-expr').disabled=!!b;document.getElementById('bf-ctx').value=b?.context||'';const cv=typeof b?.correct==='object'?(b?.correct?.value||''):String(b?.correct||'');document.getElementById('bf-correct').value=cv;const reason=b?.reason_i18n?.ko||b?.reason||'';document.getElementById('bf-reason').value=reason;document.getElementById('bf-status').value=b?.status||'active';document.getElementById('bf-del-btn').style.display=b?'':'none';openOv('banned-ov');}
async function saveBanned(){const expr=document.getElementById('bf-expr').value.trim(),context=document.getElementById('bf-ctx').value.trim(),correct_val=document.getElementById('bf-correct').value.trim(),reason=document.getElementById('bf-reason').value.trim();if(!expr||!correct_val||!reason){toast('필수 항목 누락','ter');return;}const body={expression:expr,context,correct:{type:'id',value:correct_val},reason_i18n:{ko:reason,en:reason},status:document.getElementById('bf-status').value};const isAdd=!editBannedExpr;const encoded=encodeURIComponent(editBannedExpr||'');const res=await fetch(isAdd?'/api/banned':`/api/banned/${encoded}`,{method:isAdd?'POST':'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await res.json();if(!res.ok){toast(d.error||'저장 실패','ter');return;}toast(isAdd?'추가 완료':'수정 완료','tok');closeOv('banned-ov');await reloadBanned();}
async function doDeleteBanned(expr){const res=await fetch(`/api/banned/${encodeURIComponent(expr)}`,{method:'DELETE'});if(!res.ok){toast('삭제 실패','ter');return;}toast('삭제 완료','tok');closeOv('del-ov');closeOv('banned-ov');await reloadBanned();}
function delBanned(){confirmDel(()=>doDeleteBanned(editBannedExpr),editBannedExpr);}
async function reloadBanned(){const d=await(await fetch('/api/banned')).json();BANNED=d.banned||[];bFlt=[...BANNED];bFilter();updateStats();}

// ── GENERATE / VALIDATE ──
async function runGenerate(){document.getElementById('run-title').textContent='▷ generate';document.getElementById('run-out').textContent='실행 중…';openOv('run-ov');const res=await fetch('/api/generate',{method:'POST'});const d=await res.json();document.getElementById('run-out').innerHTML=colorize(d.output||'(출력 없음)');document.getElementById('run-title').textContent=(d.ok?'✅ ':'❌ ')+'generate';toast(d.ok?'생성 완료':'실패',d.ok?'tok':'ter');}
async function runValidate(){document.getElementById('run-title').textContent='▷ validate';document.getElementById('run-out').textContent='실행 중…';openOv('run-ov');const res=await fetch('/api/validate',{method:'POST'});const d=await res.json();document.getElementById('run-out').innerHTML=colorize(d.output||'(출력 없음)');document.getElementById('run-title').textContent=(d.ok?'✅ ':'❌ ')+'validate';}
function colorize(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/(\[OK\][^\n]*)/g,'<span style="color:var(--gr)">$1</span>').replace(/(\[FATAL\][^\n]*)/g,'<span style="color:var(--re)">$1</span>').replace(/(\[WARN\][^\n]*)/g,'<span style="color:var(--ye)">$1</span>').replace(/(✅[^\n]*)/g,'<span style="color:var(--gr)">$1</span>').replace(/(❌[^\n]*)/g,'<span style="color:var(--re)">$1</span>');}

// ── CHECK-ID ──
function openCheckId(){openOv('checkid-ov');setTimeout(()=>document.getElementById('ci-input').focus(),100);}
async function runCheckId(){const id=document.getElementById('ci-input').value.trim();if(!id)return;document.getElementById('ci-result').textContent='조회 중…';const res=await fetch('/api/check-id',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const d=await res.json();document.getElementById('ci-result').textContent=d.output||'(결과 없음)';}
async function runSuggest(){const id=document.getElementById('ci-input').value.trim();if(!id)return;document.getElementById('ci-result').textContent='제안 생성 중…';const res=await fetch('/api/suggest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const d=await res.json();document.getElementById('ci-result').textContent=d.output||'(결과 없음)';}

// ── GIT ──
async function openGit(){openOv('git-ov');document.getElementById('git-body').innerHTML='<div style="padding:14px;font-family:var(--mono);font-size:10px;color:var(--tx3)">로딩 중…</div>';document.getElementById('git-ft').innerHTML=`<button class="btn btn-gh" onclick="closeOv('git-ov')" data-i18n="btn_close">닫기</button><button class="btn btn-gr" id="cbtn" onclick="doCommit()">commit + push</button>`;const[sr,lr]=await Promise.all([fetch('/api/git/status'),fetch('/api/git/log?limit=5')]);const st=await sr.json(),lg=await lr.json();const fHtml=st.changed.length?st.changed.map(f=>`<div class="gfile"><span class="gflag ${f.flag}">${f.flag}</span><span class="gpath">${x(f.path)}</span></div>`).join(''):'<div class="gempty">변경 없음</div>';const lHtml=lg.entries.length?lg.entries.map(e=>`<div class="glog"><span class="gh">${x(e.hash)}</span><span class="gs">${x(e.subject)}</span><span class="gw">${x(e.when)}</span></div>`).join(''):'<div class="gempty">이력 없음</div>';const tmpls=['feat: 단어 추가','feat: 복합어 추가','fix: 약어 수정','fix: 설명 수정','chore: generate'];document.getElementById('git-body').innerHTML=`<div class="gsec">변경 파일 (${st.changed.length})</div>${fHtml}<div class="gsec" style="margin-top:8px">커밋 메시지</div><div style="padding:10px"><textarea id="cmsg" placeholder="feat: 단어 추가 (kill, switch)"></textarea><div class="tmpls">${tmpls.map(t=>`<button class="tmpl" onclick="document.getElementById('cmsg').value='${t}'">${t}</button>`).join('')}</div></div><div class="gsec" style="margin-top:6px">최근 커밋</div>${lHtml}`;document.getElementById('cbtn').disabled=!st.has_changes;}

async function doCommit(){const msg=document.getElementById('cmsg')?.value.trim();if(!msg){toast('커밋 메시지 필요','ter');return;}document.getElementById('cbtn').disabled=true;document.getElementById('git-body').innerHTML=`<div style="padding:4px 0">${STEPS.map((_,i)=>`<div class="srow" id="st${i}"><span class="sic spen">○</span><span class="snm">${STEPS[i]}</span></div>`).join('')}</div><div class="cerr" id="cerr" style="display:none"></div>`;document.getElementById('git-ft').innerHTML='<button class="btn btn-gh" onclick="closeOv(\'git-ov\')">닫기</button>';markSt(0,'run');const res=await fetch('/api/git/commit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});const d=await res.json();(d.steps||[]).forEach((s,i)=>markSt(i,s.ok?'ok':'fail'));if(!d.ok){const e=document.getElementById('cerr');e.style.display='block';e.textContent=d.error||'오류';toast('실패','ter');}else{toast('commit & push 완료','tok');loadBranch();}}
function markSt(i,state){const el=document.getElementById('st'+i);if(!el)return;const ic=el.querySelector('.sic');ic.className=`sic ${state==='ok'?'sok':state==='fail'?'sfail':'spen'}`;ic.innerHTML=state==='ok'?'✓':state==='fail'?'✗':state==='run'?'<span class="spin">◌</span>':'○';if(state==='ok'&&i<STEPS.length-1)markSt(i+1,'run');}

// ── LOG ──
async function openLogModal(){openOv('log-ov');await loadLogs();}
async function loadLogs(){const res=await fetch('/api/logs?lines=300');const d=await res.json();_allLogLines=d.lines||[];document.getElementById('log-total').textContent=`총 ${d.total}줄 (최근 ${_allLogLines.length}줄)`;filterLogs();}
function filterLogs(){const q=(document.getElementById('log-filter')?.value||'').toLowerCase(),lv=document.getElementById('log-level-sel')?.value||'',tail=document.getElementById('log-tail')?.checked;let lines=_allLogLines;if(lv)lines=lines.filter(l=>l.includes(`| ${lv}`));if(q)lines=lines.filter(l=>l.toLowerCase().includes(q));const el=document.getElementById('log-content');if(!lines.length){el.textContent='없음';return;}el.innerHTML=lines.map(l=>{const e=l.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');if(e.includes('| ERROR'))return`<span style="color:var(--re)">${e}</span>`;if(e.includes('| WARNING'))return`<span style="color:var(--ye)">${e}</span>`;if(e.includes('[OK]'))return`<span style="color:var(--gr)">${e}</span>`;return`<span style="color:var(--tx3)">${e}</span>`;}).join('\n');if(tail)el.scrollTop=el.scrollHeight;}
async function clearLogs(){if(!confirm('로그 초기화?'))return;await fetch('/api/logs/clear',{method:'POST'});_allLogLines=[];document.getElementById('log-content').textContent='초기화됨';toast('로그 초기화','tok');}

// ── BATCH ──
const BATCH_MODELS={claude:[{v:'claude-sonnet-4-20250514',l:'Claude Sonnet 4'},{v:'claude-haiku-4-5-20251001',l:'Claude Haiku 4.5'}],openai:[{v:'gpt-4o',l:'GPT-4o'},{v:'gpt-4o-mini',l:'GPT-4o mini'}],google:[{v:'gemini-2.0-flash',l:'Gemini 2.0 Flash (RPD무제한)'},{v:'gemini-2.5-flash-lite',l:'Gemini 2.5 Flash Lite'},{v:'gemini-2.5-flash',l:'Gemini 2.5 Flash'},{v:'gemini-1.5-pro',l:'Gemini 1.5 Pro'}]};
function openBatchModal(){openOv('batch-ov');switchBtab('scan');}
function switchBtab(tab){document.querySelectorAll('.btab-btn').forEach(b=>b.classList.toggle('active',b.dataset.btab===tab));document.querySelectorAll('.btab-pane').forEach(p=>p.classList.toggle('active',p.id===`btab-${tab}`));if(tab==='result')loadBatchFiles();}
function onBatchApiChange(){const t=document.getElementById('batch-api-type').value,s=document.getElementById('batch-model');s.innerHTML='<option value="">-- .env --</option>';if(t&&BATCH_MODELS[t])BATCH_MODELS[t].forEach(m=>{const o=document.createElement('option');o.value=m.v;o.textContent=m.l;s.appendChild(o);});}
async function __coreScanLogic(){const res=await fetch('/api/batch/scan',{method:'POST'});const d=await res.json();if(!d.ok)throw new Error(d.error||'실패');return{count:d.count,cands:d.candidates,clearedN:0};}
async function doScan(){const btn=document.getElementById('scan-btn'),pre=document.getElementById('scan-preview'),sts=document.getElementById('scan-status');btn.disabled=true;btn.textContent='스캔 중…';sts.textContent='';pre.style.display='none';try{const d=await __coreScanLogic();sts.textContent=`후보 ${d.count}개`;const lines=(d.cands||[]).slice(0,40).map(c=>`${c.name.padEnd(32)} ${(c.sources||[])[0]||''}`);if(d.count>40)lines.push(`... 외 ${d.count-40}개`);pre.textContent=lines.join('\\n');pre.style.display='block';if(d.clearedN>0)toast(t('msg_drafts_cleared',{n:d.clearedN}),'tok',5000);}catch(e){sts.textContent='오류: '+e.message;}finally{btn.disabled=false;btn.textContent='▷ 스캔';}}
async function doDraftsScan(){const btn=document.getElementById('btn-drafts-scan');btn.disabled=true;btn.textContent='스캔 중...';try{const d=await __coreScanLogic();if(d.count===0){toast('스캔 결과 0건','tok');}else{const sr=await fetch('/api/drafts/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items:d.cands||[]})});const srd=await sr.json();if(srd.ok){await loadDrafts();toast(`${srd.added}건 저장 (총 ${srd.total}건)`,'tok');}else{toast('저장 실패: '+(srd.error||''),'ter');}}}catch(e){toast('오류 발생: '+e.message,'tin');}finally{btn.disabled=false;btn.textContent=t('btn_scan_drafts');updateI18n();}}
async function doBatchDryRun(){_runBatch(true);}
async function doBatchRun(){if(!confirm('API를 호출해 분석을 실행합니다.'))return;_runBatch(false);}
async function _runBatch(dryRun){const outEl=document.getElementById('batch-output'),runBtn=document.getElementById('run-btn'),dryBtn=document.getElementById('dry-btn');const apiType=document.getElementById('batch-api-type')?.value||'',model=document.getElementById('batch-model')?.value||'';const regMode=document.getElementById('batch-reg-mode')?.value||'normal';outEl.style.display='block';outEl.innerHTML='';const progDiv=document.createElement('div');progDiv.style.marginBottom='15px';progDiv.style.color='var(--gr)';const logDiv=document.createElement('div');outEl.appendChild(progDiv);outEl.appendChild(logDiv);runBtn.disabled=dryBtn.disabled=true;const payload={dry_run:dryRun,register_mode:regMode};if(apiType)payload.api_type=apiType;if(model)payload.model=model;try{const res=await fetch('/api/batch/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const reader=res.body.getReader();const decoder=new TextDecoder('utf-8');let buffer='',tasks={};function renderTasks(){progDiv.innerHTML=Object.values(tasks).sort((a,b)=>a.idx-b.idx).map(t=>{let pct=t.total?Math.round((t.cur/t.total)*100):0;let ar=t.status==='완료'?'>>>>>>>':(t.status==='대기 중'?'>':'>>');return`<div>${t.idx}. ${t.name.padEnd(20,'\u00a0')} ${ar} ${String(t.cur).padStart(4,'\u00a0')}/${t.total} ${t.status} (${pct}%)</div>`;}).join('');}while(true){const{done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let lines=buffer.split('\n');buffer=lines.pop();for(let i=0;i<lines.length;i++){const line=lines[i];if(line.startsWith('PROG|')){let p=line.split('|');if(p.length>=6){tasks[parseInt(p[1])]={idx:parseInt(p[1]),name:p[2],cur:parseInt(p[3]),total:parseInt(p[4]),status:p[5]};renderTasks();}}else{logDiv.appendChild(document.createTextNode(line+'\n'));outEl.scrollTop=outEl.scrollHeight;}}}if(buffer.trim())logDiv.appendChild(document.createTextNode(buffer+'\n'));if(!dryRun&&logDiv.textContent.includes('[완료]'))toast('분석 완료','tok');}catch(e){logDiv.appendChild(document.createTextNode('\\n연결 오류: '+e));}runBtn.disabled=dryBtn.disabled=false;}
async function loadBatchFiles(){const wrap=document.getElementById('batch-file-list');wrap.innerHTML='<div style="padding:10px;font-family:var(--mono);font-size:10px;color:var(--tx3)">로딩 중…</div>';const d=await(await fetch('/api/batch/files')).json();if(!d.files.length){wrap.innerHTML='<div style="padding:14px;text-align:center;font-family:var(--mono);font-size:11px;color:var(--tx3)">없음</div>';return;}wrap.innerHTML=d.files.map(f=>`<div class="batch-file-row${_batchSelFile===f.name?' sel':''}" onclick="selectBatchFile('${f.name}')"><span style="font-family:var(--mono);font-size:11px;color:var(--ac);flex:1">${f.name}</span><span style="font-family:var(--mono);font-size:10px;color:var(--tx3)">${f.count}개</span><button class="btn btn-ac" style="padding:3px 9px;font-size:9px" onclick="event.stopPropagation();selectBatchFile('${f.name}');switchBtab('merge')">병합 →</button></div>`).join('');}
function onAiDraftApiChange(){
  const t=document.getElementById('ai-draft-api')?.value;
  const s=document.getElementById('ai-draft-model');
  if(!s) return;
  s.innerHTML='<option value="">-- .env --</option>';
  if(t && BATCH_MODELS[t]) BATCH_MODELS[t].forEach(m=>{ const o=document.createElement('option'); o.value=m.v; o.textContent=m.l; s.appendChild(o); });
}

async function selectBatchFile(fname, draftData = null){
  _batchSelFile=fname;
  document.getElementById('merge-fname').textContent=fname;
  const container=document.getElementById('merge-preview');
  container.innerHTML='<div style="padding:8px;font-family:var(--mono);font-size:10px;color:var(--tx3)">화면 렌더링 준비 중…</div>';
  document.getElementById('merge-actions').style.display='none';
  document.getElementById('ai-draft-prog').style.display='none';
  
  if (draftData) {
    _batchTerms = draftData;
  } else {
    container.innerHTML='<div style="padding:8px;font-family:var(--mono);font-size:10px;color:var(--tx3)">서버에서 파일 읽는 중…</div>';
    const d=await(await fetch(`/api/batch/preview?file=${encodeURIComponent(fname)}`)).json();
    if(!d.ok||!(d.items && d.items.length)){
      container.innerHTML='<div style="padding:8px;font-family:var(--mono);font-size:10px;color:var(--tx3)">없음</div>';
      return;
    }
    _batchTerms=d.items;
  }
  const total = _batchTerms.length;
  let current = 0;
  const chunkSize = 40; 
  
  container.innerHTML = `<div id="render-prog" style="padding:10px;font-family:var(--mono);font-size:11px;color:var(--ac);font-weight:bold;">화면 생성 중... 0/${total} (0%)</div>`;
  const progEl = document.getElementById('render-prog');
  const wrap = document.createElement('div');
  container.appendChild(wrap);

  function renderChunk() {
    let end = Math.min(current + chunkSize, total);
    let chunkHtml = '';
    
    for(let i=current; i<end; i++){
      const t = _batchTerms[i];
      let isRec = (t.recommended || t.recommended === undefined) ? 'checked' : '';
      
      let enr = t.enriched || {};
      let posInfo = enr.canonical_pos ? `<span class="c-pos">${escapeHtml(enr.canonical_pos)}</span>` : '';
      let descKo = enr.description_i18n && enr.description_i18n.ko ? escapeHtml(enr.description_i18n.ko) : '';
      let descEn = enr.description_i18n && enr.description_i18n.en ? escapeHtml(enr.description_i18n.en) : '';
      let miniDesc = descKo || descEn || '';

      // 상세 패널 — 모든 enriched + lang + sources 정보 표시
      let detailsHtml = '';
      {
        let lines = [];

        // 1. 다국어 이름 (lang)
        let langObj = t.lang || {};
        let langParts = [];
        if(langObj.ko)      langParts.push(`KO: ${escapeHtml(langObj.ko)}`);
        if(langObj.ja)      langParts.push(`JA: ${escapeHtml(langObj.ja)}`);
        if(langObj.zh_hans) langParts.push(`ZH: ${escapeHtml(langObj.zh_hans)}`);
        if(langParts.length) lines.push(`<span style="color:var(--ac)">언어:</span> ${langParts.join(' &nbsp;|&nbsp; ')}`);

        // 2. 설명
        if(descKo) lines.push(`<span style="color:var(--ye)">KO 설명:</span> ${descKo}`);
        if(descEn) lines.push(`<span style="color:var(--tx)">EN 설명:</span> ${descEn}`);

        // 3. 어원 (from)
        if(enr.from) lines.push(`<span style="color:var(--pu)">from:</span> ${escapeHtml(String(enr.from))}`);

        // 4. variants
        if(enr.variants && enr.variants.length > 0) {
          let varParts = enr.variants.map(v => {
            let val = v.value || v.short || '';
            return `<span style="color:var(--gr);font-family:var(--mono)">${escapeHtml(val)}</span><span style="color:var(--tx3);font-size:9px">(${escapeHtml(v.type||'')})</span>`;
          }).join(' &nbsp; ');
          lines.push(`<span style="color:var(--ac)">variants:</span> ${varParts}`);
        }

        // 5. 출처 URL
        if(enr.source_urls && enr.source_urls.length > 0) {
          let urlLinks = enr.source_urls.map(u =>
            `<a href="${escapeHtml(u)}" target="_blank" style="color:var(--ac);text-decoration:none">${escapeHtml(u)}</a>`
          ).join('<br>');
          lines.push(`<span style="color:var(--ac)">URL:</span> ${urlLinks}`);
        }

        // 6. AI 판정 이유
        if(t.reason) lines.push(`<span style="color:var(--tx3)">판정:</span> ${escapeHtml(t.reason)}`);
        
        // AI 초안 간단 설명 엘리먼트 (기본은 감춤)
        lines.push(`<div id="ai-short-desc-${i}" style="color:var(--tx2);display:none;margin-top:2px;margin-bottom:2px;"></div>`);

        // 7. 발견 위치 (sources)
        if(t.sources && t.sources.length > 0) {
          let uniqueSrc = [...new Set(t.sources)];
          let srcHtml = uniqueSrc.map(s => `<span style="font-family:var(--mono);color:var(--tx3)">${escapeHtml(s)}</span>`).join('<br>');
          lines.push(`<span style="color:var(--tx3)">발견 위치 (${t.count}회):</span><br>${srcHtml}`);
        }

        // 8. 편집 섹션 (관련 단어 / 참고 URL)
        const editSection = `
          <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--ln)">
            <div style="color:var(--ac);font-weight:600;margin-bottom:6px;font-size:10px">✏ 등록 전 수정</div>
            <div style="display:flex;flex-direction:column;gap:5px">
              <div style="display:flex;align-items:center;gap:6px">
                <label style="min-width:70px;color:var(--tx3)">관련 단어/<br>합성어:</label>
                <input id="edit-rel-${i}" type="text" placeholder="단어(예: annotation) 또는 합성어(예: automatic data exchange)" value="${escapeHtml((t.user_edit&&t.user_edit.related_input)||enr.from||'')}"
                  style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:3px 7px;font-size:10px;font-family:var(--mono)">
              </div>
              <div style="display:flex;align-items:center;gap:6px">
                <label style="min-width:70px;color:var(--tx3)">참고 URL:</label>
                <input id="edit-url-${i}" type="text" placeholder="https://... (생략 가능)" value="${escapeHtml((t.user_edit&&t.user_edit.ref_url)||'')}"
                  style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:3px 7px;font-size:10px;font-family:var(--mono)">
              </div>
              <div style="display:flex;align-items:center;gap:6px">
                <label style="min-width:70px;color:var(--tx3)">도메인:</label>
                <div id="edit-domain-${i}" data-dom="${escapeHtml(JSON.stringify((t.user_edit&&t.user_edit.domain)||(enr.domain||[])))}"
                  style="flex:1;background:var(--s1);border:1px solid var(--ln);border-radius:3px;color:var(--tx);font-size:10px;font-family:var(--mono);min-height:24px;cursor:text"></div>
              </div>
              <!-- 명칭 섹션 -->
              <div style="border-top:1px solid var(--ln);margin-top:6px;padding-top:6px">
                <div style="color:var(--pu);font-size:9px;margin-bottom:4px">🌐 명칭 (선택)</div>
                <div style="display:grid;grid-template-columns:2fr 2fr;gap:4px">
                  <div style="display:flex;align-items:center;gap:4px">
                    <label style="min-width:24px;color:var(--tx3);font-size:9px">EN:</label>
                    <input id="edit-name-en-${i}" type="text" placeholder="English name" value="${escapeHtml((t.user_edit&&t.user_edit.lang_custom&&t.user_edit.lang_custom.en)||enr.lang&&enr.lang.en||t.word||'')}"
                      style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:2px 6px;font-size:9px;font-family:var(--mono)">
                  </div>
                  <div style="display:flex;align-items:center;gap:4px">
                    <label style="min-width:24px;color:var(--tx3);font-size:9px">KO:</label>
                    <input id="edit-name-ko-${i}" type="text" placeholder="한글 명칭" value="${escapeHtml((t.user_edit&&t.user_edit.lang_custom&&t.user_edit.lang_custom.ko)||enr.lang&&enr.lang.ko||enr.description_i18n&&enr.description_i18n.ko||'')}"
                      style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:2px 6px;font-size:9px;font-family:var(--mono)">
                  </div>
                  <div style="display:flex;align-items:center;gap:4px">
                    <label style="min-width:24px;color:var(--tx3);font-size:9px">JA:</label>
                    <input id="edit-name-ja-${i}" type="text" placeholder="日本語名" value="${escapeHtml((t.user_edit&&t.user_edit.lang_custom&&t.user_edit.lang_custom.ja)||enr.lang&&enr.lang.ja||'')}"
                      style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:2px 6px;font-size:9px;font-family:var(--mono)">
                  </div>
                  <div style="display:flex;align-items:center;gap:4px">
                    <label style="min-width:24px;color:var(--tx3);font-size:9px">ZH:</label>
                    <input id="edit-name-zh-${i}" type="text" placeholder="中文名称" value="${escapeHtml((t.user_edit&&t.user_edit.lang_custom&&t.user_edit.lang_custom.zh_hans)||enr.lang&&enr.lang.zh_hans||'')}"
                      style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:2px 6px;font-size:9px;font-family:var(--mono)">
                  </div>
                </div>
              </div>
              <!-- 설명 섹션 -->
              <div style="border-top:1px solid var(--ln);margin-top:6px;padding-top:6px">
                <div style="color:var(--pu);font-size:9px;margin-bottom:4px">📝 설명 (선택 — 한글만 입력 시 영문으로 복사, 반대도 동일)</div>
                <div style="display:flex;flex-direction:column;gap:4px">
                  <div style="display:flex;align-items:flex-start;gap:4px">
                    <label style="min-width:24px;color:var(--tx3);font-size:9px;padding-top:3px">KO:</label>
                    <textarea id="edit-desc-ko-${i}" rows="2" placeholder="한글 설명 (선택)" style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:3px 6px;font-size:9px;resize:vertical;font-family:var(--mono)">${escapeHtml((t.user_edit&&t.user_edit.desc_custom&&t.user_edit.desc_custom.ko)||enr.description_i18n&&enr.description_i18n.ko||'')}</textarea>
                  </div>
                  <div style="display:flex;align-items:flex-start;gap:4px">
                    <label style="min-width:24px;color:var(--tx3);font-size:9px;padding-top:3px">EN:</label>
                    <textarea id="edit-desc-en-${i}" rows="2" placeholder="English description (optional)" style="flex:1;background:var(--bg);border:1px solid var(--ln);border-radius:3px;color:var(--tx);padding:3px 6px;font-size:9px;resize:vertical;font-family:var(--mono)">${escapeHtml((t.user_edit&&t.user_edit.desc_custom&&t.user_edit.desc_custom.en)||enr.description_i18n&&enr.description_i18n.en||'')}</textarea>
                  </div>
                </div>
              </div>
              <div style="display:flex;justify-content:flex-end;margin-top:6px">
                <button id="btn-apply-${i}" class="btn" style="margin-right:6px;padding:3px 10px;font-size:9px;background:var(--ac);color:#000;border:none;border-radius:3px;cursor:pointer"
                  onclick="applyUserEdit(${i})">적용</button>
                <button class="btn btn-gh" style="padding:3px 10px;font-size:9px"
                  onclick="closeDetailsScroll(${i})">상세 닫기</button>
              </div>
            </div>
          </div>`;

        if(lines.length > 0) {
          detailsHtml = `<div style="margin-top:8px;margin-left:24px;font-size:10px;color:var(--tx2);padding:8px 12px;background:var(--s1);border:1px solid var(--ln);border-radius:4px;display:none;line-height:1.9;" id="det${i}">${lines.join('<br>')}${editSection}</div>`;
        } else {
          detailsHtml = `<div style="margin-top:8px;margin-left:24px;font-size:10px;color:var(--tx2);padding:8px 12px;background:var(--s1);border:1px solid var(--ln);border-radius:4px;display:none;line-height:1.9;" id="det${i}">${editSection}</div>`;
        }
      }

      chunkHtml += `<div class="merge-item" style="padding-bottom:10px;border-bottom:1px solid var(--ln);margin-bottom:8px;flex-direction:column;align-items:stretch">
         <div style="display:flex;align-items:center;width:100%">
           <input type="checkbox" id="mc${i}" ${isRec}>
           <div style="flex:1;margin-left:8px;display:flex;align-items:center;min-width:0;">
             <span style="font-weight:600;min-width:110px;display:inline-block">${escapeHtml(t.word)}</span>
             ${posInfo}
             <span style="font-family:var(--mono);font-size:10px;color:var(--tx3);margin-left:12px;white-space:nowrap;">발견: ${t.count}회</span>
             <span id="ai-status-${i}" style="margin-left:8px;font-family:var(--mono);font-size:9px;padding:1px 7px;border-radius:10px;background:rgba(255,255,255,0.07);color:var(--tx3);white-space:nowrap;border:1px solid rgba(255,255,255,0.1)">AI 입력 보류</span>
             <span style="margin-left:8px;font-size:11px;color:var(--ye);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;">${miniDesc}</span>
             ${detailsHtml ? `<button class="btn btn-gh" style="margin-left:8px;padding:3px 7px;font-size:9px;flex-shrink:0" onclick="const e=document.getElementById('det${i}'); const open2=e.style.display==='none';e.style.display=open2?'block':'none';if(open2){const c=document.getElementById('merge-preview');if(c)setTimeout(()=>{const top=e.getBoundingClientRect().top-c.getBoundingClientRect().top;c.scrollBy({top:top-20,behavior:'smooth'})},50)}">상세▼</button>` : ''}
           </div>
         </div>
         ${detailsHtml}
      </div>`;

    }
    
    wrap.insertAdjacentHTML('beforeend', chunkHtml);
    for(let i=current; i<end; i++) {
        const el = document.getElementById(`edit-domain-${i}`);
        if(el && el.dataset.dom) {
            let arr = [];
            const dec = (html) => { const x = document.createElement('textarea'); x.innerHTML = html; return x.value; };
            try { arr = JSON.parse(dec(el.dataset.dom)); } catch(e){}
            initMultiInput(`edit-domain-${i}`, arr, 'domain-list');
        }
    }
    current = end;
    
    if(current < total) {
       let pct = Math.round((current/total)*100);
       progEl.textContent = `화면 생성 중... ${current}/${total} (${pct}%)`;
       requestAnimationFrame(renderChunk);
    } else {
       progEl.style.display = 'none';
       document.getElementById('merge-actions').style.display='flex';
       document.getElementById('merge-status').textContent=`총 ${_batchTerms.length}개`;
       // 마스터 체크박스가 ON이면 모든 mc{i} 체크박스도 ON
       const aiChk2 = document.getElementById('ai-draft-chk');
       if (aiChk2 && aiChk2.checked) {
         for (let j = 0; j < _batchTerms.length; j++) {
           const cb = document.getElementById('mc' + j); if (cb) cb.checked = true;
         }
       }
    }
  }
  
  requestAnimationFrame(renderChunk);
}

// ai-draft-chk 마스터 체크박스: 모든 mc{i} 일괄 선택/해제
document.addEventListener('DOMContentLoaded', () => {
  const chk = document.getElementById('ai-draft-chk');
  if (chk) {
    chk.addEventListener('change', () => {
      for (let j = 0; j < _batchTerms.length; j++) {
        const cb = document.getElementById('mc' + j); if (cb) cb.checked = chk.checked;
      }
    });
  }
});

// ── AI 초안 입력 (체크된 항목만) ──
async function runAiDraftForChecked() {
  if (!_batchTerms.length) { toast('먼저 파일을 로드하세요', 'ter'); return; }
  // 체크된 mc{i} 인덱스 수집
  const checked = [];
  for (let i = 0; i < _batchTerms.length; i++) {
    const cb = document.getElementById('mc' + i);
    if (cb && cb.checked) checked.push(i);
  }
  if (!checked.length) { toast('체크된 항목이 없습니다', 'ter'); return; }

  const apiType = document.getElementById('ai-draft-api')?.value || '';
  const model   = document.getElementById('ai-draft-model')?.value || '';
  const prog    = document.getElementById('ai-draft-prog');
  const runBtn  = document.getElementById('ai-draft-run-btn');
  if (runBtn) runBtn.disabled = true;
  prog.style.display = 'block';
  prog.style.background = ''; prog.style.border = ''; prog.style.color = '';

  const total = checked.length;
  let done = 0, ok = 0, fail = 0;

  for (const i of checked) {
    const t = _batchTerms[i];
    prog.textContent = `🤖 AI 초안 입력 중… ${done}/${total} (성공 ${ok} / 실패 ${fail})`;
    // 진행 중 상태: 배지 업데이트
    const stEl = document.getElementById('ai-status-' + i);
    if (stEl) { stEl.textContent = 'AI 입력 중...'; stEl.style.color='var(--ac)'; stEl.style.background='rgba(0,180,255,0.12)'; stEl.style.borderColor='rgba(0,180,255,0.4)'; }
    try {
      await fillAiDraft(i, t.word, apiType, model, t.sources);
      ok++;
    } catch(e) {
      fail++;
      if (stEl) { stEl.textContent = 'AI 입력 실패'; stEl.style.color='var(--re)'; stEl.style.background='rgba(255,80,80,0.12)'; stEl.style.borderColor='rgba(255,80,80,0.4)'; }
      console.warn('[ai_draft] 실패:', t.word, e);
    }
    done++;
    await new Promise(r => setTimeout(r, 150));
  }

  // 체크 안 된 항목은 '보류' 유지 (이미 기본값)
  prog.textContent = `✅ AI 초안 완료 — ${ok}개 성공 / ${fail}개 실패 (체크 ${total}개 / 전체 ${_batchTerms.length}개)`;
  prog.style.background = ok > 0 ? 'rgba(70,200,100,0.10)' : 'rgba(255,80,80,0.10)';
  prog.style.border     = ok > 0 ? '1px solid var(--gr)' : '1px solid var(--re)';
  prog.style.color      = ok > 0 ? 'var(--gr)' : 'var(--re)';
  if (runBtn) runBtn.disabled = false;
  toast(`AI 초안 완료 — ${ok}/${total}`, ok > 0 ? 'tok' : 'ter');
}

async function fillAiDraft(i, word, apiType, model, sources) {
  const payload = { word };
  if (apiType) payload.api_type = apiType;
  if (model)   payload.model    = model;
  if (sources) payload.sources  = sources;

  const res  = await fetch('/api/batch/ai_draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || 'AI 초안 실패');

  // 관련/합성어(base form)와 간단명세 업데이트
  const baseEl = document.getElementById(`edit-rel-${i}`);
  if (baseEl && data.base_form) baseEl.value = data.base_form;
  
  const shortDescEl = document.getElementById(`ai-short-desc-${i}`);
  if (shortDescEl && data.short_description) {
    shortDescEl.innerHTML = `<span style="color:var(--tx3)">간단 설명:</span> ${escapeHtml(data.short_description)}`;
    shortDescEl.style.display = 'block';
  }

  // EN/KO/JA/ZH 명칭 필드 채우기
  const enEl = document.getElementById(`edit-name-en-${i}`);
  const koEl = document.getElementById(`edit-name-ko-${i}`);
  const jaEl = document.getElementById(`edit-name-ja-${i}`);
  const zhEl = document.getElementById(`edit-name-zh-${i}`);
  if (enEl && data.en) enEl.value = data.en;
  if (koEl && data.ko) koEl.value = data.ko;
  if (jaEl && data.ja) jaEl.value = data.ja;
  if (zhEl && data.zh) zhEl.value = data.zh;

  // 설명(KO/EN) 무조건 덮어쓰기
  const descKoEl = document.getElementById(`edit-desc-ko-${i}`);
  const descEnEl = document.getElementById(`edit-desc-en-${i}`);
  const koDesc = data.description_ko || data.ko_desc || data.description || '';
  const enDesc = data.description_en || data.en_desc || koDesc;
  if (descKoEl && koDesc) descKoEl.value = koDesc;
  if (descEnEl && enDesc) descEnEl.value = enDesc;

  // 발음 정보를 상세 패널에 표시 (이미 열려 있는 경우에만)
  if (data.pronunciation) {
    const det = document.getElementById(`det${i}`);
    if (det) {
      let pronRow = det.querySelector('.ai-pron-row');
      if (!pronRow) {
        pronRow = document.createElement('div');
        pronRow.className = 'ai-pron-row';
        pronRow.style.cssText = 'font-size:10px;color:var(--pu);margin-bottom:6px;padding:4px 8px;background:rgba(130,80,255,0.08);border-radius:3px;line-height:1.8';
        det.insertBefore(pronRow, det.firstChild);
      }
      const pr = data.pronunciation;
      const parts = [];
      if (pr.en) parts.push(`<b>EN</b> ${escapeHtml(pr.en)}`);
      if (pr.ko) parts.push(`<b>KO</b> ${escapeHtml(pr.ko)}`);
      if (pr.ja) parts.push(`<b>JA</b> ${escapeHtml(pr.ja)}`);
      if (pr.zh) parts.push(`<b>ZH</b> ${escapeHtml(pr.zh)}`);
      pronRow.innerHTML = '🔊 발음: ' + parts.join(' &nbsp;|&nbsp; ');
    }
  }

  // _batchTerms 에도 lang 반영 (다음 doMergeProcessed에서 사용)
  const t = _batchTerms[i];
  if (!t.lang) t.lang = {};
  if (data.en) t.lang.en = data.en;
  if (data.ko) t.lang.ko = data.ko;
  if (data.ja) t.lang.ja = data.ja;
  if (data.zh) t.lang.zh_hans = data.zh;
  // _batchTerms 설명(KO/EN) 업데이트
  if (koDesc || enDesc) {
    t.enriched = t.enriched || {};
    t.enriched.description_i18n = t.enriched.description_i18n || {};
    if (koDesc) t.enriched.description_i18n.ko = koDesc;
    if (enDesc) t.enriched.description_i18n.en = enDesc;
  }

  // ai-status 배지: 성공 표시
  const aiStEl = document.getElementById('ai-status-' + i);
  if (aiStEl) {
    aiStEl.textContent = 'AI 입력 성공';
    aiStEl.style.color = 'var(--gr)';
    aiStEl.style.background = 'rgba(70,200,100,0.12)';
    aiStEl.style.borderColor = 'rgba(70,200,100,0.4)';
  }

  // 시각 피드백: 행 배경에 보라색 하이라이트
  const mcEl = document.getElementById(`mc${i}`);
  if (mcEl) {
    const row = mcEl.closest('.merge-item');
    if (row) {
      row.style.borderLeft = '3px solid var(--pu)';
      setTimeout(() => { row.style.borderLeft = ''; }, 2500);
    }
  }
}

function closeDetailsScroll(index) {
  const panel = document.getElementById('det' + index);
  if (!panel) return;
  const rowHeader = panel.closest('.merge-item');
  panel.style.display = 'none';
  const container = document.getElementById('merge-preview');
  if (!rowHeader || !container) return;
  
  const nextItem = rowHeader.nextElementSibling || rowHeader;
  
  const containerRect = container.getBoundingClientRect();
  const targetTop = nextItem.getBoundingClientRect().top;
  const containerTop = containerRect.top;
  const targetRelativeOffset = containerRect.height * 0.5; // 화면 정중앙(1/2)에 위치하도록 조정
  
  const diff = targetTop - containerTop - targetRelativeOffset;
  container.scrollBy({ top: diff, behavior: 'smooth' });
}

// ── 사용자 편집 적용 (관련 단어/합성어 / 참고 URL) ──
function applyUserEdit(i) {
  const t = _batchTerms[i];
  if (!t) return;
  const relInput = (document.getElementById(`edit-rel-${i}`)?.value || '').trim();
  const refUrl   = (document.getElementById(`edit-url-${i}`)?.value || '').trim();
  const refDomain = getMultiInputValue(`edit-domain-${i}`);
  const isCompound = relInput.includes(' ');
  // 명칭 (lang) 수집
  const nameEn = (document.getElementById(`edit-name-en-${i}`)?.value || '').trim();
  const nameKo = (document.getElementById(`edit-name-ko-${i}`)?.value || '').trim();
  const nameJa = (document.getElementById(`edit-name-ja-${i}`)?.value || '').trim();
  const nameZh = (document.getElementById(`edit-name-zh-${i}`)?.value || '').trim();
  // 설명 수집 + 단방향 auto-copy 규칙
  let descKo = (document.getElementById(`edit-desc-ko-${i}`)?.value || '').trim();
  let descEn = (document.getElementById(`edit-desc-en-${i}`)?.value || '').trim();
  if (descKo && !descEn) { descEn = descKo; }   // KO만 있으면 EN에 복사 (번역 대체)
  if (descEn && !descKo) { descKo = descEn; }   // EN만 있으면 KO에 복사

  const langCustom = {};
  if (nameEn) langCustom.en = nameEn;
  if (nameKo) langCustom.ko = nameKo;
  if (nameJa) langCustom.ja = nameJa;
  if (nameZh) langCustom.zh_hans = nameZh;

  const descCustom = {};
  if (descKo) descCustom.ko = descKo;
  if (descEn) descCustom.en = descEn;

  t.user_edit = {
    related_input: relInput, ref_url: refUrl, domain: refDomain.length ? refDomain : null, is_compound: isCompound,
    lang_custom: Object.keys(langCustom).length ? langCustom : null,
    desc_custom: Object.keys(descCustom).length ? descCustom : null,
  };

  // 시각 피드백: 적용 버튼 ✓
  const det = document.getElementById(`det${i}`);
  const applyBtn = document.getElementById(`btn-apply-${i}`);
  if(applyBtn) { applyBtn.textContent='✓ 적용됨'; applyBtn.style.background='var(--gr)';
    setTimeout(()=>{applyBtn.textContent='적용';applyBtn.style.background='var(--ac)';},1800); }

  // 시각 피드백: "상세" 버튼 보라색으로 강조
  if(det && det.previousElementSibling) {
    const detailBtn = Array.from(det.previousElementSibling.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('상세'));
    if(detailBtn) {
      detailBtn.style.background = 'rgba(130, 80, 255, 0.15)';
      detailBtn.style.color = 'var(--pu)';
      detailBtn.style.border = '1px solid rgba(130, 80, 255, 0.6)';
    }
  }

  // 상세 패널 상단에 미리보기 행 표시
  if(det && relInput) {
    let relRow = det.querySelector('.user-rel-row');
    if(!relRow) {
      relRow = document.createElement('div');
      relRow.className = 'user-rel-row';
      relRow.style.cssText = 'color:var(--pu);margin-top:4px;margin-bottom:4px;padding:4px 6px;background:rgba(130,80,255,0.1);border-radius:3px';
      det.insertBefore(relRow, det.firstChild);
    }
    const typeTag = isCompound
      ? `<span style="font-size:9px;background:var(--ac);color:#000;padding:1px 5px;border-radius:3px;margin-left:4px">합성어</span>`
      : `<span style="font-size:9px;background:var(--pu);color:#fff;padding:1px 5px;border-radius:3px;margin-left:4px">단어</span>`;
    relRow.innerHTML = `<span style="color:var(--pu)">관련 (사용자):</span> <b>${escapeHtml(relInput)}</b>${typeTag}`;
  }
}

async function doMergeProcessed(){
  const sts=document.getElementById('merge-status');
  sts.textContent='처리 중…';
  
  let appW = [], appC = [], rej = [];
  let _compoundRequests = [];
  
  _batchTerms.forEach((t, i) => {
    const cb = document.getElementById(`mc${i}`);
    const isChecked = cb && cb.checked;
    
    if (!isChecked) {
       rej.push(t);
       return;
    }
    
    let wordBody = {
      id: t.word,
      lang: {en: t.word, ko: t.word},
      canonical_pos: "noun",
      domain: "general",
      status: t.reason === "사전 확인" ? "auto_registered" : "active"
    };
    if (t.enriched) {
       if (t.enriched.canonical_pos) wordBody.canonical_pos = t.enriched.canonical_pos;
       if (t.enriched.description_i18n) wordBody.description_i18n = t.enriched.description_i18n;
       if (t.enriched.variants && t.enriched.variants.length > 0) wordBody.variants = t.enriched.variants;
       // source_urls: enriched 기본 + 사용자 참고 URL 병합
       let srcUrls = t.enriched.source_urls ? [...t.enriched.source_urls] : [];
       if (t.user_edit && t.user_edit.ref_url) srcUrls.unshift(t.user_edit.ref_url);
       if (srcUrls.length) wordBody.source_urls = srcUrls;
       // from: enriched.from 또는 사용자 관련 단어
       if (t.enriched.from) wordBody.from = t.enriched.from;
    }
    // 사용자 편집 반영
    if (t.user_edit) {
       const ui = t.user_edit;
       if (!ui.is_compound) {
         // 단어 → from 필드로 사용
         if (ui.related_input) wordBody.from = ui.related_input;
       }
       // ref_url: source_urls 맨 앞 삽입
       if (ui.ref_url) {
         wordBody.source_urls = wordBody.source_urls || [];
         if (!wordBody.source_urls.includes(ui.ref_url))
           wordBody.source_urls.unshift(ui.ref_url);
       }
    }
    // lang: enriched lang이 있으면 우선 적용 (user_edit이 최우선)
    if (t.lang && (t.lang.ko || t.lang.ja)) {
       wordBody.lang = { en: t.word, ...t.lang };
    }
    // user_edit.lang_custom 최우선 덮어쓰기
    if (t.user_edit && t.user_edit.lang_custom) {
       wordBody.lang = { ...wordBody.lang, ...t.user_edit.lang_custom };
    }
    // user_edit.desc_custom: 설명 덮어쓰기
    if (t.user_edit && t.user_edit.desc_custom && Object.keys(t.user_edit.desc_custom).length) {
       wordBody.description_i18n = { ...(wordBody.description_i18n || {}), ...t.user_edit.desc_custom };
    }
    // 도메인 반영
    if (t.user_edit && t.user_edit.domain) {
       wordBody.domain = t.user_edit.domain;
    }
    
    // [NEW] ID Swap: 사용자가 지정한 영어 명칭(lang_custom.en 또는 enrichment)이 원래 파싱된 토큰(t.word)과 다를 경우 
    // 영어 명칭을 ID로 사용하고, 원래 토큰을 variants에 병합 (약어 또는 variant)
    if (wordBody.lang && wordBody.lang.en && !t.user_edit?.is_compound) {
       const userEn = wordBody.lang.en.trim().toLowerCase();
       const originalId = t.word.trim().toLowerCase();
       if (userEn && userEn !== originalId) {
          wordBody.id = userEn;
          wordBody.variants = wordBody.variants || [];
          
          // 길이가 짧으면 abbreviation으로 우선 판단
          const isAbbr = originalId.length < userEn.length;
          const varType = isAbbr ? "abbreviation" : "variant";
          
          const existingVar = wordBody.variants.find(v => (v.value||"").toLowerCase() === originalId || (v.short||"").toLowerCase() === originalId);
          if (!existingVar) {
             if (isAbbr) {
                 wordBody.variants.push({ type: "abbreviation", short: t.word.toUpperCase(), long: wordBody.lang.en });
             } else {
                 wordBody.variants.push({ type: varType, value: t.word });
             }
          }
       }
    }

    appW.push(wordBody);
    
    // 합성어인 경우: register_compound API 별도 호출 목록에 추가
    if (t.user_edit && t.user_edit.is_compound) {
      _compoundRequests.push({
        abbrev:       t.word,
        phrase:       t.user_edit.related_input,
        ref_url:      t.user_edit.ref_url || '',
        lang_custom:  t.user_edit.lang_custom  || null,
        desc_custom:  t.user_edit.desc_custom  || null,
        domain:       t.user_edit.domain || null,
      });
    }
  });

  if (!appW.length && !appC.length && !rej.length) {
    toast('처리할 대상 없음','ter'); return;
  }
  
  const res = await fetch('/api/batch/merge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file: _batchSelFile,
      approved_words: appW,
      approved_compounds: appC,
      rejected: rej
    })
  });
  
  const d = await res.json();
  if(!d.ok){ toast(d.error||'실패', 'ter'); sts.textContent=''; return; }

  // ── 합성어 등록 처리 ──
  let compSummary = '';
  if(_compoundRequests.length > 0) {
    let totalFound=0, totalAsVar=0, totalNewWord=0, totalComp=0;
    for(const req of _compoundRequests) {
      try {
        const cr = await fetch('/api/batch/register_compound', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify(req)
        });
        const cd = await cr.json();
        if(cd.ok) {
          totalFound   += (cd.words_found      || []).length;
          totalAsVar   += (cd.words_as_variant  || []).length;
          totalNewWord += (cd.words_new         || []).length;
          totalComp    += cd.compound_added ? 1 : 0;
        } else {
          const rolled = cd.rolled_back ? ' (rollback 완료)' : '';
          toast(`합성어 등록 실패 (${req.abbrev}): ${cd.error||''}${rolled}`, 'ter');
        }
      } catch(e) { toast(`합성어 API 오류: ${e.message}`, 'ter'); }
    }
    compSummary = ` | 합성어 ${totalComp}개 등록, 단어 ${totalFound}개 확인, 신규 ${totalNewWord}개 words 등록, 형태소 ${totalAsVar}개 이미 포함`;
    if(totalNewWord > 0) toast(`합성어 처리 완료 — ${totalNewWord}개 단어가 words.json에 자동 등록되었습니다.`, 'tin', 5000);
    await reloadCompounds();
  }

  sts.textContent=`성공: ${d.added}개 승인, ${rej.length}개 보류${compSummary}`;
  toast('병합 및 보류 이동 처리 완료', 'tok');
  await reloadWords(); 
  await reloadCompounds();
  await loadDrafts();
}

// ── UTILS ──
function x(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
const escapeHtml = x;
function confirmDel(cb,nm){document.getElementById('del-nm').textContent=nm;document.getElementById('del-ok').onclick=cb;openOv('del-ov');}
function openOv(id){document.getElementById(id).classList.add('open');}
function closeOv(id){document.getElementById(id).classList.remove('open');}
document.querySelectorAll('.ov').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)o.classList.remove('open');}));
function toast(msg,cls='tin',ms=3200){const c=document.getElementById('toasts'),d=document.createElement('div');d.className=`toast ${cls}`;d.textContent=msg;c.appendChild(d);setTimeout(()=>d.remove(),ms);}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){['word-ov','compound-ov','banned-ov','checkid-ov','git-ov','settings-ov','run-ov','log-ov','batch-ov','del-ov'].forEach(closeOv);}if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();const cur=document.querySelector('.view.active .search-inp');if(cur)cur.focus();}});

// ── LANG & SETTINGS ──
function changeLang(lang) {
  window.LANG = lang;
  updateI18n();
  localStorage.setItem('glossary_lang', lang);
  document.getElementById('lang-sel').value = lang;
  renderWords();
}
function openSettings() {
  document.getElementById('pref-lang').value = window.LANG || 'ko';
  document.getElementById('pref-tz').value   = document.getElementById('tz-sel').value || 'KST';
  openOv('settings-ov');
}
function saveSettings() {
  const lang = document.getElementById('pref-lang').value;
  const tz   = document.getElementById('pref-tz').value;
  document.getElementById('tz-sel').value = tz;
  localStorage.setItem('glossary_tz', tz);
  changeLang(lang);
  updateAllTimestamps();
  closeOv('settings-ov');
  toast('설정 저장됨', 'tok', 2000);
}

function loadDraftsToMerge() {
  if (!DRAFTS || !DRAFTS.length) {
    toast('보류 항목이 없습니다.', 'tin');
    return;
  }
  
  openBatchModal();
  switchBtab('merge');
  selectBatchFile('drafts.json', [...DRAFTS]);
}

boot();
async function fillWordAiDraft() {
  const word = document.getElementById('wf-id').value.trim();
  if (!word) { alert('단어(id)를 먼저 입력해주세요.'); return; }
  
  const btn = event.currentTarget || event.target;
  const originalText = btn.textContent;
  btn.textContent = '가져오는 중...';
  btn.disabled = true;
  
  try {
    const payload = { word: word };
    const res = await fetch('/api/batch/ai_draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'AI 초안 실패');
    
    // 기본 도메인
    if (data.domain) {
      document.getElementById('wf-domain').innerHTML = ''; // 초기화
      initMultiInput('wf-domain', [data.domain], 'domain-list');
    }
    
    // 번역 및 설명
    if (data.ko) document.getElementById('wf-ko').value = data.ko;
    if (data.en) document.getElementById('wf-en').value = data.en;
    if (data.ja) document.getElementById('wf-ja').value = data.ja;
    if (data.zh) document.getElementById('wf-zh').value = data.zh;
    if (data.description_ko) document.getElementById('wf-desc').value = data.description_ko;
    if (data.description_en) document.getElementById('wf-desc-en').value = data.description_en;
    
    // 형태소/관계어 (있으면 채우기)
    if (data.abbr) document.getElementById('wf-abbr').value = data.abbr;
    if (data.from) document.getElementById('wf-from').value = data.from;
    
    if (data.variants && data.variants.length > 0) {
      document.getElementById('wf-variants').value = data.variants.map(v => `${v.type}:${v.value}`).join('\n');
    }
    if (data.synonyms && data.synonyms.length > 0) {
      document.getElementById('wf-synonyms').value = data.synonyms.join(', ');
    }
    if (data.antonyms && data.antonyms.length > 0) {
      document.getElementById('wf-antonyms').value = data.antonyms.join(', ');
    }
    if (data.source_urls && data.source_urls.length > 0) {
      document.getElementById('wf-urls').value = data.source_urls.join('\n');
    }
    if (data.not_terms && data.not_terms.length > 0) {
      document.getElementById('wf-not').value = data.not_terms.join(', ');
    } else if (data.not && data.not.length > 0) {
      document.getElementById('wf-not').value = data.not.join(', ');
    }
    
  } catch(err) {
    alert(err.message);
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}


