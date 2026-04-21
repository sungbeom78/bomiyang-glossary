"""
patch_ai_v2.py  —  AI 초안 UX 개선
1. 마스터 체크박스 → 모든 mc{i} 체크박스 전체 선택/해제
2. RUN 버튼 항상 표시, 클릭 시 체크된 항목만 처리
3. 항목 행에 AI 상태(성공/실패/보류) 배지 표시
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")
NL = "\r\n" if "\r\n" in content else "\n"

def S(s):
    return s.replace("\n", NL)

changes = []

# ─────────────────────────────────────────────
# 1. HTML: RUN 버튼 - display:none 제거, class btn-ac, onclick 변경
# ─────────────────────────────────────────────
OLD1 = '<button id="ai-draft-run-btn" class="btn btn-gh" style="padding:3px 9px;font-size:9px;display:none" onclick="runAiDraftForAll()">▷ AI 초안 실행</button>'
NEW1 = '<button id="ai-draft-run-btn" class="btn btn-ac" style="padding:3px 9px;font-size:9px;font-weight:700" onclick="runAiDraftForChecked()">▷ RUN</button>'
if OLD1 in content:
    content = content.replace(OLD1, NEW1, 1)
    changes.append("1. RUN 버튼 HTML 수정 OK")
else:
    changes.append("1. RUN 버튼 HTML: NOT FOUND")

# ─────────────────────────────────────────────
# 2. 항목 행 HTML 템플릿: 발견:n회 뒤에 ai-status 배지 삽입
# ─────────────────────────────────────────────
OLD2 = (
    '<span style="font-family:var(--mono);font-size:10px;color:var(--tx3);margin-left:12px;white-space:nowrap;">발견: ${t.count}회</span>\n'
    '              <span style="margin-left:16px;font-size:11px;color:var(--ye);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${miniDesc}</span>\n'
    '              ${detailsHtml ? `<button class="btn btn-gh" style="margin-left:8px;padding:3px 7px;font-size:9px"'
)
NEW2 = (
    '<span style="font-family:var(--mono);font-size:10px;color:var(--tx3);margin-left:12px;white-space:nowrap;">발견: ${t.count}회</span>\n'
    '              <span id="ai-status-${i}" style="margin-left:8px;font-family:var(--mono);font-size:9px;padding:1px 7px;border-radius:10px;background:rgba(255,255,255,0.07);color:var(--tx3);white-space:nowrap;border:1px solid rgba(255,255,255,0.1)">보류</span>\n'
    '              <span style="margin-left:8px;font-size:11px;color:var(--ye);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${miniDesc}</span>\n'
    '              ${detailsHtml ? `<button class="btn btn-gh" style="margin-left:8px;padding:3px 7px;font-size:9px"'
)
# CRLF 대응
OLD2_cr = OLD2.replace("\n", NL)
NEW2_cr = NEW2.replace("\n", NL)
if OLD2_cr in content:
    content = content.replace(OLD2_cr, NEW2_cr, 1)
    changes.append("2. ai-status 배지 삽입 OK")
else:
    changes.append("2. ai-status 배지: NOT FOUND (CRLF 시도)")

# ─────────────────────────────────────────────
# 3. renderChunk else 블록: 자동실행 제거, 마스터 체크 적용
# ─────────────────────────────────────────────
OLD3 = S(
    "       // AI 초안 체크박스 상태 확인 -> 자동 실행 or 버튼 표시\n"
    "       const aiChk = document.getElementById('ai-draft-chk');\n"
    "       const aiRunBtn = document.getElementById('ai-draft-run-btn');\n"
    "       if (aiChk && aiChk.checked) {\n"
    "         setTimeout(function(){ runAiDraftForAll(); }, 200);\n"
    "       } else {\n"
    "         if (aiRunBtn) aiRunBtn.style.display = '';\n"
    "       }\n"
    "    }"
)
NEW3 = S(
    "       // 마스터 체크박스가 ON이면 모든 mc{i} 체크박스도 ON\n"
    "       const aiChk2 = document.getElementById('ai-draft-chk');\n"
    "       if (aiChk2 && aiChk2.checked) {\n"
    "         for (let j = 0; j < _batchTerms.length; j++) {\n"
    "           const cb = document.getElementById('mc' + j); if (cb) cb.checked = true;\n"
    "         }\n"
    "       }\n"
    "    }"
)
if OLD3 in content:
    content = content.replace(OLD3, NEW3, 1)
    changes.append("3. renderChunk else 블록 수정 OK")
else:
    changes.append("3. renderChunk else 블록: NOT FOUND")

# ─────────────────────────────────────────────
# 4. DOMContentLoaded: 체크박스 핸들러 → mc{i} 전체 토글
# ─────────────────────────────────────────────
OLD4 = S(
    "// ai-draft-chk 토글 시 run 버튼 표시/숨김\n"
    "document.addEventListener('DOMContentLoaded', () => {\n"
    "  const chk = document.getElementById('ai-draft-chk');\n"
    "  const btn = document.getElementById('ai-draft-run-btn');\n"
    "  if (chk && btn) {\n"
    "    chk.addEventListener('change', () => {\n"
    "      // 파일이 이미 로드된 상태에서만 버튼 제어\n"
    "      if (_batchTerms.length > 0) {\n"
    "        btn.style.display = chk.checked ? 'none' : '';\n"
    "        if (chk.checked) runAiDraftForAll();\n"
    "      }\n"
    "    });\n"
    "  }\n"
    "});"
)
NEW4 = S(
    "// ai-draft-chk 마스터 체크박스: 모든 mc{i} 일괄 선택/해제\n"
    "document.addEventListener('DOMContentLoaded', () => {\n"
    "  const chk = document.getElementById('ai-draft-chk');\n"
    "  if (chk) {\n"
    "    chk.addEventListener('change', () => {\n"
    "      for (let j = 0; j < _batchTerms.length; j++) {\n"
    "        const cb = document.getElementById('mc' + j); if (cb) cb.checked = chk.checked;\n"
    "      }\n"
    "    });\n"
    "  }\n"
    "});"
)
if OLD4 in content:
    content = content.replace(OLD4, NEW4, 1)
    changes.append("4. DOMContentLoaded 핸들러 수정 OK")
else:
    changes.append("4. DOMContentLoaded 핸들러: NOT FOUND")

# ─────────────────────────────────────────────
# 5. runAiDraftForAll → runAiDraftForChecked (체크된 항목만)
# ─────────────────────────────────────────────
OLD5 = S(
    "// ── AI 초안 자동 입력 (병합 탭) ──\n"
    "async function runAiDraftForAll() {\n"
    "  if (!_batchTerms.length) { toast('먼저 파일을 로드하세요', 'ter'); return; }\n"
    "  const apiType = document.getElementById('ai-draft-api')?.value || '';\n"
    "  const model   = document.getElementById('ai-draft-model')?.value || '';\n"
    "  const prog    = document.getElementById('ai-draft-prog');\n"
    "  const runBtn  = document.getElementById('ai-draft-run-btn');\n"
    "  if (runBtn) runBtn.disabled = true;\n"
    "  prog.style.display = 'block';\n"
    "  \n"
    "  const total = _batchTerms.length;\n"
    "  let done = 0, ok = 0, fail = 0;\n"
    "\n"
    "  for (let i = 0; i < total; i++) {\n"
    "    const t = _batchTerms[i];\n"
    "    prog.textContent = `🤖 AI 초안 입력 중… ${done}/${total} (성공 ${ok} / 실패 ${fail})`;\n"
    "    try {\n"
    "      await fillAiDraft(i, t.word, apiType, model);\n"
    "      ok++;\n"
    "    } catch(e) {\n"
    "      fail++;\n"
    "      console.warn('[ai_draft] 실패:', t.word, e);\n"
    "    }\n"
    "    done++;\n"
    "    // 과도한 연속 API 호출 방지: 150ms 간격\n"
    "    await new Promise(r => setTimeout(r, 150));\n"
    "  }\n"
    "  \n"
    "  prog.textContent = `✅ AI 초안 완료 — ${ok}개 성공 / ${fail}개 실패 (총 ${total}개)`;\n"
    "  prog.style.background = ok > 0 ? 'var(--gr-bg)' : 'var(--re-bg)';\n"
    "  prog.style.border = ok > 0 ? '1px solid var(--gr)' : '1px solid var(--re)';\n"
    "  prog.style.color  = ok > 0 ? 'var(--gr)' : 'var(--re)';\n"
    "  if (runBtn) runBtn.disabled = false;\n"
    "  toast(`AI 초안 완료 — ${ok}/${total}`, ok > 0 ? 'tok' : 'ter');\n"
    "}"
)
NEW5 = S(
    "// ── AI 초안 입력 (체크된 항목만) ──\n"
    "async function runAiDraftForChecked() {\n"
    "  if (!_batchTerms.length) { toast('먼저 파일을 로드하세요', 'ter'); return; }\n"
    "  // 체크된 mc{i} 인덱스 수집\n"
    "  const checked = [];\n"
    "  for (let i = 0; i < _batchTerms.length; i++) {\n"
    "    const cb = document.getElementById('mc' + i);\n"
    "    if (cb && cb.checked) checked.push(i);\n"
    "  }\n"
    "  if (!checked.length) { toast('체크된 항목이 없습니다', 'ter'); return; }\n"
    "\n"
    "  const apiType = document.getElementById('ai-draft-api')?.value || '';\n"
    "  const model   = document.getElementById('ai-draft-model')?.value || '';\n"
    "  const prog    = document.getElementById('ai-draft-prog');\n"
    "  const runBtn  = document.getElementById('ai-draft-run-btn');\n"
    "  if (runBtn) runBtn.disabled = true;\n"
    "  prog.style.display = 'block';\n"
    "  prog.style.background = ''; prog.style.border = ''; prog.style.color = '';\n"
    "\n"
    "  const total = checked.length;\n"
    "  let done = 0, ok = 0, fail = 0;\n"
    "\n"
    "  for (const i of checked) {\n"
    "    const t = _batchTerms[i];\n"
    "    prog.textContent = `🤖 AI 초안 입력 중… ${done}/${total} (성공 ${ok} / 실패 ${fail})`;\n"
    "    // 진행 중 상태: 배지 업데이트\n"
    "    const stEl = document.getElementById('ai-status-' + i);\n"
    "    if (stEl) { stEl.textContent = '…'; stEl.style.color='var(--ac)'; stEl.style.background='rgba(0,180,255,0.12)'; stEl.style.borderColor='rgba(0,180,255,0.4)'; }\n"
    "    try {\n"
    "      await fillAiDraft(i, t.word, apiType, model);\n"
    "      ok++;\n"
    "    } catch(e) {\n"
    "      fail++;\n"
    "      if (stEl) { stEl.textContent = '실패'; stEl.style.color='var(--re)'; stEl.style.background='rgba(255,80,80,0.12)'; stEl.style.borderColor='rgba(255,80,80,0.4)'; }\n"
    "      console.warn('[ai_draft] 실패:', t.word, e);\n"
    "    }\n"
    "    done++;\n"
    "    await new Promise(r => setTimeout(r, 150));\n"
    "  }\n"
    "\n"
    "  // 체크 안 된 항목은 '보류' 유지 (이미 기본값)\n"
    "  prog.textContent = `✅ AI 초안 완료 — ${ok}개 성공 / ${fail}개 실패 (체크 ${total}개 / 전체 ${_batchTerms.length}개)`;\n"
    "  prog.style.background = ok > 0 ? 'rgba(70,200,100,0.10)' : 'rgba(255,80,80,0.10)';\n"
    "  prog.style.border     = ok > 0 ? '1px solid var(--gr)' : '1px solid var(--re)';\n"
    "  prog.style.color      = ok > 0 ? 'var(--gr)' : 'var(--re)';\n"
    "  if (runBtn) runBtn.disabled = false;\n"
    "  toast(`AI 초안 완료 — ${ok}/${total}`, ok > 0 ? 'tok' : 'ter');\n"
    "}"
)
if OLD5 in content:
    content = content.replace(OLD5, NEW5, 1)
    changes.append("5. runAiDraftForAll → runAiDraftForChecked OK")
else:
    changes.append("5. runAiDraftForAll 함수: NOT FOUND")

# ─────────────────────────────────────────────
# 6. fillAiDraft: 성공 시 ai-status 배지 업데이트
# ─────────────────────────────────────────────
OLD6 = S(
    "  // 시각 피드백: 행 배경에 보라색 하이라이트\n"
    "  const mcEl = document.getElementById(`mc${i}`);"
)
NEW6 = S(
    "  // ai-status 배지: 성공 표시\n"
    "  const aiStEl = document.getElementById('ai-status-' + i);\n"
    "  if (aiStEl) {\n"
    "    aiStEl.textContent = '성공';\n"
    "    aiStEl.style.color = 'var(--gr)';\n"
    "    aiStEl.style.background = 'rgba(70,200,100,0.12)';\n"
    "    aiStEl.style.borderColor = 'rgba(70,200,100,0.4)';\n"
    "  }\n"
    "\n"
    "  // 시각 피드백: 행 배경에 보라색 하이라이트\n"
    "  const mcEl = document.getElementById(`mc${i}`);"
)
if OLD6 in content:
    content = content.replace(OLD6, NEW6, 1)
    changes.append("6. fillAiDraft 성공 배지 OK")
else:
    changes.append("6. fillAiDraft 성공 배지: NOT FOUND")

# ─────────────────────────────────────────────
# 저장
# ─────────────────────────────────────────────
TARGET.write_text(content, encoding="utf-8")

print("=== 패치 결과 ===")
for c in changes:
    print(" ", c)
