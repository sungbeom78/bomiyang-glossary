"""
patch_i18n_modals.py
Index.html 모달 타이틀과 그 외 누락된 다국어 지원 요소들을 패치
"""
from pathlib import Path
import re

TARGET = Path(__file__).parent.parent / "web" / "index.html"
content = TARGET.read_text(encoding="utf-8")

# 1. Update I18N_DICT values by inserting new keys
NEW_KO = """btn_close: "닫기",
    modal_settings: "⚙ 환경설정",
    modal_checkid: "⊙ check-id / suggest",
    modal_log: "📋 서버 로그",
    modal_git: "⎇ commit & push",
    modal_run: "실행",
    modal_batch: "⚙ 배치 병합",
    tab_scan: "1. 스캔",
    tab_result: "2. 결과 파일",
    tab_merge: "3. 병합" """

NEW_EN = """btn_close: "Close",
    modal_settings: "⚙ Settings",
    modal_checkid: "⊙ check-id / suggest",
    modal_log: "📋 Server Logs",
    modal_git: "⎇ commit & push",
    modal_run: "Run",
    modal_batch: "⚙ Batch Merge",
    tab_scan: "1. Scan",
    tab_result: "2. Results",
    tab_merge: "3. Merge" """

content = re.sub(r'btn_close: "닫기"', NEW_KO, content)
content = re.sub(r'btn_close: "Close"', NEW_EN, content)

# 2. Add data-i18n to Modal Titles
replacements = {
    '<div class="mt">⚙ 환경설정</div>': '<div class="mt" data-i18n="modal_settings">⚙ 환경설정</div>',
    '<div class="mt">⊙ check-id / suggest</div>': '<div class="mt" data-i18n="modal_checkid">⊙ check-id / suggest</div>',
    '<div class="mt">📋 서버 로그</div>': '<div class="mt" data-i18n="modal_log">📋 서버 로그</div>',
    '<div class="mt">⎇ commit &amp; push</div>': '<div class="mt" data-i18n="modal_git">⎇ commit &amp; push</div>',
    '<div class="mt" id="run-title">실행</div>': '<div class="mt" id="run-title" data-i18n="modal_run">실행</div>',
    '<div class="mt">⚙ 배치 병합 (batch)</div>': '<div class="mt" data-i18n="modal_batch">⚙ 배치 병합 (batch)</div>',
    '>1. 스캔</button>': ' data-i18n="tab_scan">1. 스캔</button>',
    '>2. 결과 파일</button>': ' data-i18n="tab_result">2. 결과 파일</button>',
    '>3. 병합</button>': ' data-i18n="tab_merge">3. 병합</button>',
    '<button class="btn btn-gh" onclick="closeOv(\'settings-ov\')">닫기</button>': '<button class="btn btn-gh" onclick="closeOv(\'settings-ov\')" data-i18n="btn_close">닫기</button>',
    '<button class="btn btn-gh" onclick="closeOv(\'checkid-ov\')">닫기</button>': '<button class="btn btn-gh" onclick="closeOv(\'checkid-ov\')" data-i18n="btn_close">닫기</button>',
    '<button class="btn btn-gh" onclick="closeOv(\'git-ov\')">닫기</button>': '<button class="btn btn-gh" onclick="closeOv(\'git-ov\')" data-i18n="btn_close">닫기</button>',
    '<button class="btn btn-gh" onclick="closeOv(\'run-ov\')">닫기</button>': '<button class="btn btn-gh" onclick="closeOv(\'run-ov\')" data-i18n="btn_close">닫기</button>',
    '<button class="btn btn-gh" onclick="closeOv(\'log-ov\')">닫기</button>': '<button class="btn btn-gh" onclick="closeOv(\'log-ov\')" data-i18n="btn_close">닫기</button>'
}

for old, new in replacements.items():
    content = content.replace(old, new)

TARGET.write_text(content, encoding="utf-8")
print("patch_i18n_modals 적용 완료")
