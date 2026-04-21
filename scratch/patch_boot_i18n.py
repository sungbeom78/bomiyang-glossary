"""
patch_boot_i18n.py
boot() 험수 내에서 updateI18n() 호출 추가.
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

OLD = """  const savedTz   = localStorage.getItem('glossary_tz')   || 'KST';
  window.LANG = savedLang;
  const langSel = document.getElementById('lang-sel');
  if (langSel) langSel.value = savedLang;
  const tzSel = document.getElementById('tz-sel');"""

NEW = """  const savedTz   = localStorage.getItem('glossary_tz')   || 'KST';
  window.LANG = savedLang;
  updateI18n(); // 초기 다국어 적용
  const langSel = document.getElementById('lang-sel');
  if (langSel) langSel.value = savedLang;
  const tzSel = document.getElementById('tz-sel');"""

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    TARGET.write_text(content, encoding="utf-8")
    print("boot 패치 완료")
else:
    print("NOT FOUND")
