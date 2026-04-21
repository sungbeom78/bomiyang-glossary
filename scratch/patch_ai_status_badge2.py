"""
patch_ai_status_badge2.py
발견:n회 뒤, miniDesc 스팬 앞에 ai-status 배지 삽입
들여쓰기: 13 스페이스 (실제 파일 기준)
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

# 실제 파일에서 발견 부분 바로 다음에 오는 miniDesc 스팬 패턴 (13 spaces)
OLD = (
    '</span>\n'
    '              <span style="margin-left:16px;font-size:11px;color:var(--ye);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${miniDesc}</span>'
)
# 13 spaces로 교정
OLD13 = (
    '</span>\n'
    '             <span style="margin-left:16px;font-size:11px;color:var(--ye);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${miniDesc}</span>'
)

BADGE = (
    '<span id="ai-status-${i}" style="margin-left:8px;font-family:var(--mono);font-size:9px;'
    'padding:1px 7px;border-radius:10px;background:rgba(255,255,255,0.07);color:var(--tx3);'
    'white-space:nowrap;border:1px solid rgba(255,255,255,0.1)">보류</span>'
)

NEW13 = (
    '</span>\n'
    '             ' + BADGE + '\n'
    '             <span style="margin-left:8px;font-size:11px;color:var(--ye);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${miniDesc}</span>'
)

# 13-space 버전만 시도
if OLD13 in content:
    result = content.replace(OLD13, NEW13, 1)
    TARGET.write_text(result, encoding="utf-8")
    print("OK (13-space): ai-status 배지 삽입 완료")
else:
    # 발견횟수 스팬 다음 내용을 정밀 출력
    idx = content.find("</span>\n             <span style")
    sub = content[idx:idx+200]
    print("NOT FOUND. 실제 영역:")
    print(repr(sub))
