"""
patch_i18n.py
UI 전체 영문화/한국어 스위칭을 위한 i18n 시스템 구축
"""
from pathlib import Path
import re

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

I18N_JS = """
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
    btn_close: "닫기"
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
    btn_close: "Close"
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

"""

# 1. 스크립트 상단에 I18N_JS 주입
if "I18N_DICT" not in content:
    content = content.replace("<script>", "<script>\n" + I18N_JS, 1)

# 2. HTML 요소들에 data-i18n 추가
replacements = {
    'onclick="switchTab(\'words\')">단어<span': 'data-i18n="tab_words" onclick="switchTab(\'words\')">단어<span',
    'onclick="switchTab(\'compounds\')">복합어<span': 'data-i18n="tab_compounds" onclick="switchTab(\'compounds\')">복합어<span',
    'onclick="switchTab(\'banned\')">금지표현<span': 'data-i18n="tab_banned" onclick="switchTab(\'banned\')">금지표현<span',
    'onclick="switchTab(\'drafts\')">보류(Drafts)<span': 'data-i18n="tab_drafts" onclick="switchTab(\'drafts\')">보류(Drafts)<span',
    '>⚙ 설정</button>': ' data-i18n="btn_settings">⚙ 설정</button>',
    '+ 단어 추가</button>': '+ 단어 추가</button>'.replace('+ 단어 추가', '<span data-i18n="btn_add_word">+ 단어 추가</span>'),
    'placeholder="검색 — id, 영문, 한글, 약어…"': 'placeholder="검색 — id, 영문, 한글, 약어…" data-i18n="search_placeholder"',
    '<option value="">전체 domain</option>': '<option value="" data-i18n="all_domain">전체 domain</option>',
    '<option value="">전체 품사</option>': '<option value="" data-i18n="all_pos">전체 품사</option>',
    '>ID<span': ' data-i18n="th_id">ID<span',
    '>ENGLISH<span': ' data-i18n="th_en">ENGLISH<span',
    '>한글<span': ' data-i18n="th_ko">한글<span',
    '>ABBR<span': ' data-i18n="th_abbr">ABBR<span',
    '>POS<span': ' data-i18n="th_pos">POS<span',
    '>DOMAIN<span': ' data-i18n="th_domain">DOMAIN<span',
    '>설명<span': ' data-i18n="th_desc">설명<span',
    '<div class="mt">환경 설정</div>': '<div class="mt" data-i18n="setting_title">환경 설정</div>',
}

for old, new in replacements.items():
    content = content.replace(old, new)
    
# button + 단어 추가 fix (it has an icon sometimes but let's just make it simpler)
content = content.replace('<button class="btn btn-ac" onclick="openEditModal()">+ 단어 추가</button>', '<button class="btn btn-ac" onclick="openEditModal()" data-i18n="btn_add_word">+ 단어 추가</button>')

# 3. changeLang 함수 안에서 updateI18n() 호출 추가
if 'function changeLang(lang) {' in content and 'updateI18n();' not in content:
    content = content.replace(
        "function changeLang(lang) {\n  window.LANG = lang;",
        "function changeLang(lang) {\n  window.LANG = lang;\n  updateI18n();"
    )

# 4. renderStats() 에서 문자열 하드코딩 교체
old_stats = "`단어 ${window._data.words.length} · 복합어 ${window._data.compounds.length} · 금지 ${window._data.banned.length} · 보류 ${window._data.drafts.length}`"
new_stats = "t('stats_format', {words: window._data.words.length, compounds: window._data.compounds.length, banned: window._data.banned.length, drafts: window._data.drafts.length})"
content = content.replace(old_stats, new_stats)

TARGET.write_text(content, encoding="utf-8")
print("patch_i18n.py 적용 완료")

