# Glossary v2.5.1 Rollout & Rollback Plan

> Plan §8 Step 9–10 / §1.3 Trading Freeze 기반  
> 작성일: 2026-04-16

---

## Step 9. Rollout — 배포 절차

### 9.1 사전 조건 (배포 전 체크리스트)

```
[ ] generate FATAL 0건 확인
    # glossary/ 루트에서 실행
    python generate_glossary.py validate

[ ] regression test 전 통과
    python bin/test_regression.py

[ ] DB compatibility test 전 통과
    python bin/test_db_compat.py

[ ] terms.json checksum 정상
    → validate 출력에서 V-010 없음 확인

[ ] git status clean (uncommitted 변경 없음)
    git status

[ ] 현재 시간이 Trading Freeze 범위 밖인지 확인 (§1.3)
```

### 9.2 Trading Freeze 기준 (§1.3)

**배포 금지 시간대:**

| 구분 | 금지 시간 (KST) |
|------|----------------|
| 한국 주식 (KIS) | 09:00 – 15:30 |
| 해외 FX (MT5) | 런던/뉴욕 오버랩: 21:00 – 02:00 |
| 코인 (Upbit) | active position 보유 시 상시 금지 |

**배포 허용 시간대 (권장):**
- 한국 주식 시장 마감 후: **15:35 – 08:55**
- 주말 전체 (토, 일)
- active position 없는 상태 확인 후

### 9.3 Maintenance Window 절차

```powershell
# 실행 위치: glossary/ 루트 (generate_glossary.py 위치)
# PowerShell 기준

# 1. 서비스 상태 확인 (active position 체크)
#    → 트레이딩 엔진 대시보드 또는 로그 확인

# 2. generate_glossary.py 최종 검증
python generate_glossary.py validate
python generate_glossary.py generate

# 3. glossary 저장소 코바 (서브모듈로 운영하는 경우)
git add dictionary/words.json dictionary/compounds.json dictionary/terms.json GLOSSARY.md
git commit -m 'release: v2.5.1 variants array 전환 완료'
git push

# 4. 상위 프로젝트 서브모듈 포인터 업데이트 (서브모듈 구조인 경우)
#    프로젝트 루트에서 실행
Push-Location ..
git add glossary
git commit -m 'chore: update glossary submodule to v2.5.1'
git push
Pop-Location

# 5. 웹 UI 서버 재시작 (운영 중인 경우)
#    Ctrl+C → python web/server.py

# 6. 배포 후 검증
python generate_glossary.py validate   # FATAL 0건 재확인
python bin/test_regression.py         # regression 재실행
```

### 9.4 배포 후 모니터링

배포 직후 **30분간** 다음 항목 모니터링:

```
[ ] glossary.log — ERROR / CRITICAL 없음
    # glossary/ 루트 기준: log/ 디렉토리
[ ] web UI 정상 접속 (http://localhost:5000)
[ ] generate 버튼 정상 동작
[ ] validate 버튼 FATAL 0건
[ ] check-id 정상 동작
```

---

## Step 10. Rollback — 즉시 복구 플랜

### 10.1 Rollback 기준

다음 중 하나 이상 발생 시 즉시 rollback:

- validate FATAL 신규 발생
- terms.json checksum 불일치 (V-010 CRITICAL)
- web UI 접속 불가 또는 generate 오류
- regression test 실패
- 트레이딩 엔진에서 glossary 로드 오류

### 10.2 Git 기반 Rollback (권장)

```powershell
# 실행 위치: glossary/ 루트 (generate_glossary.py 위치)
# PowerShell 기준

# 1. 현재 커밋 확인
git log --oneline -5

# 2. 이전 안정 커밋으로 복구
git checkout <이전_커밋_해시>
#   예: git checkout a1b2c3d

# 3. 복구 후 검증
python generate_glossary.py validate
python generate_glossary.py generate

# 4. rollback 커밋
$rollback_branch = "rollback/v2.5.1-$(Get-Date -Format 'yyyyMMdd')"
git checkout -b $rollback_branch
git add dictionary/
git commit -m 'rollback: v2.5.1 배포 취소 → 이전 상태 복원'
git push

# 상위 프로젝트 서브모듈 포인터 복구 (서브모듈인 경우)
Push-Location ..
git add glossary
git commit -m 'chore: rollback glossary submodule'
git push
Pop-Location
```

### 10.3 Symlink 기반 Rollback (선택)

운영 환경에 symlink를 사용하는 경우:

```powershell
# 배포 전 백업 생성 (배포 시 항상 수행) - glossary/ 루트 기준
$ts = Get-Date -Format 'yyyyMMdd_HHmm'
Copy-Item -Path dictionary -Destination "dictionary.bak.$ts" -Recurse

# 롤백 시 이전 백업로 교체 (심링크 미사용 환경)
# 이전 백업 디렉토리를 직접 dictionary로 이름 변경:
Rename-Item -Path dictionary -NewName dictionary.broken
Rename-Item -Path "dictionary.bak.20260416_1535" -NewName dictionary

# (선택) 심링크 기반 구성을 지원하는 운영 환경에서는
# mklink /D dictionary_active dictionary.bak.20260416_1535 (관리자 CMD 필요)
```

### 10.4 긴급 복구 절차 (Hotfix)

FATAL이 발생했으나 rollback이 어려운 경우:

```powershell
# 실행 위치: glossary/ 루트 (generate_glossary.py 위치)

# 1. 운영 산출물로 원인 파악
Get-Content build\report\dependency_missing.json
Get-Content build\report\projection_skipped.json

# 2. 해당 항목 수동 수정
#    → words.json 또는 compounds.json 직접 편집

# 3. 즉시 재생성
python generate_glossary.py generate

# 4. validate 확인
python generate_glossary.py validate

# 5. hotfix 커밋
git add dictionary/
git commit -m 'hotfix: [오류 내용] 긴급 수정'
git push
```

### 10.5 Rollback 판단 기준표

| 증상 | 조치 |
|------|------|
| FATAL 1–2건, 원인 명확 | hotfix 후 재배포 |
| FATAL 다수 또는 원인 불명 | 즉시 git rollback |
| checksum CRITICAL | git rollback → 원인 분석 |
| web UI 완전 불능 | git rollback → 서버 재시작 |
| 트레이딩 엔진 glossary 오류 | git rollback → 엔진 재시작 |

---

## 부록: Trading Freeze 자동화 코드 스니펫 (§1.3 참고용)

```python
# trading_freeze.py — 장중 배포 방지 체크
# 실제 구현 시 web/server.py commit 엔드포인트에 삽입

from datetime import datetime, time
import pytz

KST = pytz.timezone("Asia/Seoul")

def is_trading_freeze() -> tuple[bool, str]:
    """
    Returns (is_frozen: bool, reason: str)
    """
    now_kst = datetime.now(KST)
    weekday = now_kst.weekday()  # 0=월, 5=토, 6=일

    # 주말은 허용
    if weekday >= 5:
        return False, ""

    t = now_kst.time()

    # 한국 주식 시장 (09:00–15:30 KST)
    if time(9, 0) <= t <= time(15, 30):
        return True, f"한국 주식 시장 운영 중 ({t.strftime('%H:%M')} KST)"

    # 해외 FX 오버랩 (21:00–02:00 KST)
    if t >= time(21, 0) or t <= time(2, 0):
        return True, f"해외 FX 거래 시간 ({t.strftime('%H:%M')} KST)"

    return False, ""


# web/server.py commit 엔드포인트에 추가:
# frozen, reason = is_trading_freeze()
# if frozen:
#     return jsonify({"ok": False, "error": f"Trading Freeze: {reason}"}), 403
```

---

## 문서 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-16 | Plan v2.5.1 §8 Step 9–10 기반 초안 작성 |
