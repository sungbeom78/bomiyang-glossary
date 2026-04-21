"""
patch_ai_trigger.py
renderChunk else 블록에 AI 초안 자동 트리거를 삽입한다.
LF / CRLF 양쪽 대응.
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

# 실제 파일의 줄바꿈 감지
NL = "\r\n" if "\r\n" in content else "\n"

def S(s):
    """'\n' 를 실제 줄바꿈으로 치환"""
    return s.replace("\n", NL)

OLD = S(
    "    } else {\n"
    "       progEl.style.display = 'none';\n"
    "       document.getElementById('merge-actions').style.display='flex';\n"
    "       document.getElementById('merge-status').textContent=`총 ${_batchTerms.length}개`;\n"
    "    }"
)

NEW = S(
    "    } else {\n"
    "       progEl.style.display = 'none';\n"
    "       document.getElementById('merge-actions').style.display='flex';\n"
    "       document.getElementById('merge-status').textContent=`총 ${_batchTerms.length}개`;\n"
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

if OLD in content:
    result = content.replace(OLD, NEW, 1)
    TARGET.write_text(result, encoding="utf-8")
    print("OK: AI 초안 트리거 삽입 완료 (줄바꿈:", repr(NL), ")")
else:
    # 진단
    idx = content.find("progEl.style.display = 'none';")
    if idx >= 0:
        region = content[idx - 80 : idx + 250]
        print("FOUND at", idx)
        print(repr(region))
    else:
        print("NOT FOUND")
