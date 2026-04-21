"""
patch_server_ai_desc.py
server.py의 batch_ai_draft 프롬프트 수정
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "server.py"
content = TARGET.read_text(encoding="utf-8")

OLD_DOC = '            "description": "먼저 들어온 데이터나 자산이 먼저 처리되거나 나가는 방식으로 …"'
NEW_DOC = '            "description_ko": "먼저 들어온 데이터가...",\n            "description_en": "A method where the first..."'

OLD_PROMPT = """        f'6. One-sentence description in Korean (한 줄 설명, 실용적이고 쉽게)\\n\\n'
        f'Respond ONLY with a valid JSON object (no markdown, no explanation):\\n'
        f'{{\\n'
        f'  "en": "...",\\n'
        f'  "ko": "...",\\n'
        f'  "ja": "...",\\n'
        f'  "zh": "...",\\n'
        f'  "pronunciation": {{"en": "...", "ko": "...", "ja": "...", "zh": "..."}},\\n'
        f'  "description": "..."\\n'
        f'}}'"""

NEW_PROMPT = """        f'6. One-sentence description in BOTH Korean and English (한국어 한 줄, 영어 한 줄 설명)\\n\\n'
        f'Respond ONLY with a valid JSON object (no markdown, no explanation):\\n'
        f'{{\\n'
        f'  "en": "...",\\n'
        f'  "ko": "...",\\n'
        f'  "ja": "...",\\n'
        f'  "zh": "...",\\n'
        f'  "pronunciation": {{"en": "...", "ko": "...", "ja": "...", "zh": "..."}},\\n'
        f'  "description_ko": "...",\\n'
        f'  "description_en": "..."\\n'
        f'}}'"""

c1 = content.find(OLD_DOC) >= 0
c2 = content.find(OLD_PROMPT) >= 0

if c1 and c2:
    content = content.replace(OLD_DOC, NEW_DOC)
    content = content.replace(OLD_PROMPT, NEW_PROMPT)
    TARGET.write_text(content, encoding="utf-8")
    print("server.py 패치 완료")
else:
    print(f"NOT FOUND, c1={c1}, c2={c2}")
    if not c2:
        idx = content.find("6. One-sentence")
        print("프롬프트 부근:", repr(content[idx:idx+300]))
