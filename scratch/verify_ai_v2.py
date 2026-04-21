"""verify_ai_v2.py — AI 초안 v2 패치 전체 검증"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

content = (Path(__file__).parent.parent / "web" / "index.html").read_text(encoding="utf-8")

checks = {
    "1. RUN 버튼 (btn-ac, runAiDraftForChecked)":
        ('id="ai-draft-run-btn" class="btn btn-ac"' in content
         and 'onclick="runAiDraftForChecked()"' in content),
    "2. ai-status 배지 HTML 삽입":
        ('id="ai-status-${i}"' in content and '>보류</span>' in content),
    "3. renderChunk: 자동실행 제거":
        ('setTimeout(function(){ runAiDraftForAll(); }, 200)' not in content),
    "4. renderChunk: mc체크박스 일괄설정":
        ('aiChk2' in content and 'cb.checked = true' in content),
    "5. DOMContentLoaded: mc일괄토글":
        ('cb.checked = chk.checked' in content),
    "6. runAiDraftForChecked 함수":
        ('async function runAiDraftForChecked()' in content),
    "7. runAiDraftForAll 완전 제거":
        ('async function runAiDraftForAll()' not in content),
    "8. fillAiDraft: 성공 배지":
        ("aiStEl.textContent = '성공'" in content),
    "9. runAiDraftForChecked: 실패 배지":
        ("stEl.textContent = '실패'" in content),
}

all_ok = True
for name, ok in checks.items():
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}]  {name}")
    if not ok:
        all_ok = False

print()
print("최종:", "ALL PASS" if all_ok else "SOME FAILED")
