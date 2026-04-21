"""
patch_fill_ai_draft.py
index.html 의 fillAiDraft 함수 내 조건부 로직을 무조건 덮어쓰기로 변경하고,
data.description_ko / data.description_en 필드를 모두 반영.
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

OLD_BLOCK = """  // 설명 채우기 (비어 있는 경우만)
  const descKoEl = document.getElementById(`edit-desc-ko-${i}`);
  const descEnEl = document.getElementById(`edit-desc-en-${i}`);
  if (descKoEl && !descKoEl.value.trim() && data.description) descKoEl.value = data.description;
  if (descEnEl && !descEnEl.value.trim() && data.description)  descEnEl.value = data.description;"""

NEW_BLOCK = """  // 설명(KO/EN) 무조건 덮어쓰기
  const descKoEl = document.getElementById(`edit-desc-ko-${i}`);
  const descEnEl = document.getElementById(`edit-desc-en-${i}`);
  const koDesc = data.description_ko || data.ko_desc || data.description || '';
  const enDesc = data.description_en || data.en_desc || koDesc;
  if (descKoEl && koDesc) descKoEl.value = koDesc;
  if (descEnEl && enDesc) descEnEl.value = enDesc;"""

OLD_BLOCK2 = """  if (data.description && !t.enriched?.description_i18n?.ko) {
    t.enriched = t.enriched || {};
    t.enriched.description_i18n = t.enriched.description_i18n || {};
    if (!t.enriched.description_i18n.ko) t.enriched.description_i18n.ko = data.description;
    if (!t.enriched.description_i18n.en) t.enriched.description_i18n.en = data.description;
  }"""

NEW_BLOCK2 = """  // _batchTerms 설명(KO/EN) 업데이트
  if (koDesc || enDesc) {
    t.enriched = t.enriched || {};
    t.enriched.description_i18n = t.enriched.description_i18n || {};
    if (koDesc) t.enriched.description_i18n.ko = koDesc;
    if (enDesc) t.enriched.description_i18n.en = enDesc;
  }"""

c1 = OLD_BLOCK in content
c2 = OLD_BLOCK2 in content

if c1 and c2:
    content = content.replace(OLD_BLOCK, NEW_BLOCK)
    content = content.replace(OLD_BLOCK2, NEW_BLOCK2)
    TARGET.write_text(content, encoding="utf-8")
    print("index.html fillAiDraft 패치 완료")
else:
    print(f"NOT FOUND, c1={c1}, c2={c2}")
    if not c1:
        idx = content.find("const descKoEl")
        print("c1:", repr(content[idx-50:idx+200]))
    if not c2:
        idx = content.find("if (data.description &&")
        print("c2:", repr(content[idx-50:idx+200]))
