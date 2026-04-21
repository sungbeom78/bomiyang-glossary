"""verify_patch.py — AI trigger 삽입 결과 확인"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

needle = "runAiDraftForAll"
occurrences = []
start = 0
while True:
    idx = content.find(needle, start)
    if idx == -1:
        break
    occurrences.append(idx)
    start = idx + 1

print(f"총 {len(occurrences)}곳에서 'runAiDraftForAll' 발견:")
for idx in occurrences:
    snippet = content[max(0, idx - 50):idx + 100].replace("\n", " ").replace("\r", "")
    print(f"  [{idx}] ...{snippet}...")

# renderChunk else 블록 확인
ai_trigger_check = "setTimeout(function(){ runAiDraftForAll(); }, 200);" in content
print(f"\nAI 자동 트리거 삽입 여부: {'OK' if ai_trigger_check else 'MISSING'}")

# AI 초안 체크박스 HTML 확인
chk_html = "ai-draft-chk" in content
print(f"ai-draft-chk 체크박스: {'OK' if chk_html else 'MISSING'}")

# API 엔드포인트 확인
server_path = Path(__file__).parent.parent / "web" / "server.py"
server = server_path.read_text(encoding="utf-8")
draft_api = "/api/batch/ai_draft" in server
call_api  = "_call_ai_api" in server
print(f"\nserver.py /api/batch/ai_draft: {'OK' if draft_api else 'MISSING'}")
print(f"server.py _call_ai_api:         {'OK' if call_api  else 'MISSING'}")
