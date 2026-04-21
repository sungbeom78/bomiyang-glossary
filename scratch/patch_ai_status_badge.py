"""
patch_ai_status_badge.py — ai-status 배지 삽입
발견:n회 스팬 바로 뒤에 삽입 (단순 문자열 기준)
"""
from pathlib import Path

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

# 발견:n회 스팬 종료 태그 바로 뒤, miniDesc 스팬 이전
ANCHOR = '</span>\n              <span style="margin-left:16px;font-size:11px;color:var(--ye);flex:1;'
BADGE  = '<span id="ai-status-${i}" style="margin-left:8px;font-family:var(--mono);font-size:9px;padding:1px 7px;border-radius:10px;background:rgba(255,255,255,0.07);color:var(--tx3);white-space:nowrap;border:1px solid rgba(255,255,255,0.1)">보류</span>\n              '

# 발견:n회가 있는 줄 다음의 첫 번째 </span>\n<span miniDesc> 패턴을 찾는다
idx_count = content.find("발견: ${t.count}회")
if idx_count < 0:
    print("NOT FOUND: 발견횟수 스팬")
else:
    # 그 이후에서 ANCHOR를 찾는다
    idx_anchor = content.find(ANCHOR, idx_count)
    if idx_anchor < 0:
        # 실제 내용 확인
        region = content[idx_count:idx_count+300]
        print("ANCHOR NOT FOUND, region:")
        print(repr(region))
    else:
        # ANCHOR 앞에 BADGE 삽입
        ins_pos = idx_anchor + len("</span>\n")  # </span>\n 다음에 삽입
        # ANCHOR에서 </span>\n '까지가 경계
        insert_at = idx_anchor + len("</span>") + 1  # \n 다음
        new_content = content[:insert_at] + "              " + BADGE.strip() + "\n" + content[insert_at:]
        TARGET.write_text(new_content, encoding="utf-8")
        print("OK: ai-status 배지 삽입 완료")
        # 검증
        check = "ai-status-${i}" in new_content
        print("검증:", "OK" if check else "MISSING")
