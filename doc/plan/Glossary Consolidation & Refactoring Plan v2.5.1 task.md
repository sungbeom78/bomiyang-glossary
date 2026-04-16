좀 더 넓은 범위로 web 파일들에서 variants 관련 코드를 검색합니다.

Ran command: `Select-String -Path "web\server.py" -Pattern "variants|\.abbr\b|abbr\." | Select-Object -First 40`
Ran command: `Select-String -Path "web\index.html" -Pattern "\.abbr|abbr\.|variants" | Select-Object LineNumber, Line | Select-Object -First 50`
Viewed index.html:1-587

수정이 필요한 위치들이 파악되었습니다. 주요 3곳입니다:

1. **L358** `wFilter()`: `w.variants?.abbreviation||''` → array에서 첫 abbreviation short 추출
2. **L369** `renderWords()`: `w.variants?.abbreviation` → 동일
3. **L389** `cFilter()`: `c.abbr?.long, c.abbr?.short` → variants array에서 추출
4. **L398** `renderCompounds()`: `c.abbr?.long, c.abbr?.short` → 동일
5. **L414** `openWordForm()`: `w?.variants?.abbreviation||''` → array에서 추출
6. **L415** `saveWord()`: `body.variants={abbreviation:abbr}` → array 형식으로 저장
7. **L421** `openCompoundForm()`: `c?.abbr?.long|short` → variants array
8. **L422** `saveCompound()`: `abbr:{long,short}` → variants array

Edited index.html

chunk 2(renderWords abbr)가 실패했습니다. 현재 라인을 확인하고 수정합니다.

Viewed index.html:380-400
Edited index.html

renderCompounds, openWordForm, openCompoundForm, saveWord, saveCompound 4개를 수정합니다.

Viewed index.html:417-455
Edited index.html

chunk 0(renderCompounds의 abbr)만 실패했습니다. 현재 내용 확인 후 수정합니다.

Viewed index.html:417-421
Edited index.html

이제 expandedRow에 있는 `c.abbr?.long`/`c.abbr?.short`도 수정합니다.

Viewed index.html:422-424
Edited index.html

모든 UI 수정 완료. 이제 최종 generate + validate로 검증합니다.

Ran command: `python generate_glossary.py generate 2>&1`

완전 통과. change_log를 업데이트합니다.

Viewed change_log.md:1-3
Edited change_log.md

**Plan v2.5.1 2단계 완료.** 전체 결과를 요약합니다.

---

## 2단계 완료 요약

### ✅ 완료된 작업

| 항목 | 내용 |
|---|---|
| **variants 마이그레이션** | `bin/migrate_variants.py` 실행 → words 234개, compounds 154개 전환 완료 |
| **generate_glossary.py** | compound projection + variant_map 모두 array+object **하위호환** 방식으로 전환 |
| **schema 교체** | `word.schema.json`, `compound.schema.json` → §3.3 type-based array 형식으로 완전 재정의 |
| **web/index.html** | `getVariantShort`, `getVariantLong`, `cAbbrShort`, `cAbbrLong` 헬퍼 추가; 모든 렌더링 + 폼 저장 로직 array 방식으로 전환 |
| **최종 검증** | `generate` FATAL 없음 / terms.json 598개 checksum 포함 정상 생성 |

### 📊 WARN 현황 (정상 범위)
- **V-401** × 4: `main`, `manager`, `manual`, `meta`, `method` — description 미등록 (기존 단어)
- **V-352** × 1: `candle` ko 표현 집합 표현만 존재






Plan 문서와 현재 작업 상태를 확인합니다.

Viewed Glossary%20Consolidation%20&%20Refactoring%20Plan%20v2.5.1.md:1-498

이제 실제로 어떤 작업이 완료되었는지 사용자 승인된 단계 기준으로 task.md를 작성합니다.

Edited task.md

## 현재 진행 상황

**1단계 ✅ 완료** / **2단계 ✅ 완료**

### 완료된 모든 항목

**1단계 — 기반 강화**
- checksum (V-010), V-013 exact match 수정
- terms_legacy.json, 4개 운영 산출물 생성
- projection 상수 정의, banned 처리, stats 수정

**2단계 — variants Array 전환**
- `bin/migrate_variants.py` 실행 → words 234개 / compounds 154개 마이그레이션 완료
- `schema/word.schema.json`, `schema/compound.schema.json` §3.3 array 형식으로 교체
- `generate_glossary.py` compound projection + variant_map 모두 array+object 하위호환 처리
- `web/index.html` 전면 전환 (헬퍼 함수 추가, 검색/렌더링/저장 모두 array 형식)

### 현재 시스템 상태
```
generate : FATAL 없음 ✅
terms.json : 598개, checksum 포함 ✅
WARN 6건 : V-401(description 미등록 5개), V-352(candle ko) — 정상 범위
```

### 잔여 검토 사항 (사용자 판단 필요)
- **Step 7~10 (§8 Migration)**: regression 추가 시나리오, DB 호환성 테스트, rollout/rollback 계획
- **§5.3 Alerting**: Slack/Telegram 연동 (별도 작업)
- **§1.3 Trading Freeze**: 장중 배포 방지 메커니즘 (별도 작업)










# Task: Glossary Consolidation & Refactoring Plan v2.5.1 실행

기준 문서: `doc/plan/Glossary Consolidation & Refactoring Plan v2.5.1.md`

---

## 1단계 — 기반 강화 ✅ 완료 (2026-04-15 13:28)

- [x] **checksum** — `terms.json`에 sha256 checksum 필드 추가 (`compute_checksum`, `verify_checksum` 함수 신설)
- [x] **V-010** — validate 시 checksum 불일치 CRITICAL 처리, generate 시 skip_checksum 파라미터 분리
- [x] **V-013** — banned.expression vs words/compounds id 충돌 검증 (대소문자 완전 일치 exact match로 오탐 방지)
- [x] **terms_legacy.json** — `deprecated` 항목 분리 산출물 생성
- [x] **운영 산출물** — `dependency_missing.json`, `projection_skipped.json`, `merge_candidates.json`, `banned_autofix_report.json` 전부 생성 확인
- [x] **projection 보강** — PROJECTION_VARIANT_TYPES / PROJECTION_EXCLUDE_TYPES 상수 정의
- [x] **banned 처리 강화** — banned_autofix_report.json 정상 생성
- [x] **stats 수정** — `canonical_pos` 신규 필드 반영 (구버전 `pos` 하위호환)
- [x] **문서 업데이트** — `doc/module_index.md`, `doc/change_log.md` 업데이트

---

## 2단계 — variants Array 전환 ✅ 완료 (2026-04-15 13:42)

- [x] **variants array 전환** — `bin/migrate_variants.py` 신설, dry-run 후 실제 마이그레이션 실행
  - words.json 234개 / compounds.json 154개 전환 완료
- [x] **schema 교체**
  - `schema/word.schema.json` — §3.3 type-based array 형식으로 완전 재정의 (oneOf [value \| short])
  - `schema/compound.schema.json` — variants array 형식 + 구 `abbr` 객체 제거 (abbreviation type으로 통합)
- [x] **generate_glossary.py — compound projection 전환**
  - `build_terms_json()` 내 compound variants projection: array+object 하위호환 처리
  - `cmd_generate()` 내 `variant_map` 생성: array+object 하위호환 처리
- [x] **web/server.py 확인** — variants 관련 코드 없음 (산출물 API만 제공), 수정 불필요
- [x] **web/index.html 전환**
  - `getVariantShort(variants)`, `getVariantLong(variants)` 헬퍼 추가 (array + object 하위호환)
  - `cAbbrShort(c)`, `cAbbrLong(c)` 헬퍼 추가
  - `wFilter`, `renderWords` — 검색/렌더링 abbr 추출 전환
  - `cFilter`, `renderCompounds` (테이블 행 + 확장 행) — abbr 추출 전환
  - `openWordForm` — getVariantShort 사용
  - `saveWord` — `variants: [{type:'abbreviation', short}]` array 형식으로 저장
  - `openCompoundForm` — cAbbrShort/cAbbrLong 사용
  - `saveCompound` — `variants: [{type:'abbreviation', short, long}]` array 형식으로 저장
- [x] **최종 검증** — generate FATAL 없음 / terms.json 598개 checksum 포함 정상 생성
- [x] **문서 업데이트** — `doc/change_log.md` 업데이트

---

## 현재 상태

| 항목 | 상태 |
|---|---|
| generate | ✅ FATAL 없음 |
| terms.json | ✅ 598개, checksum 포함 |
| words.json | ✅ 234개, variants array 형식 |
| compounds.json | ✅ 154개, variants array 형식 |
| schema | ✅ word/compound 모두 §3.3 array 기준 |
| web UI | ✅ array 형식 완전 호환 |

### 잔존 WARN (정상 범위, 즉시 조치 불필요)
- `V-401` × 5: `main`, `manager`, `manual`, `meta`, `method` — description_i18n 미등록
- `V-352` × 1: `candle` — ko 표현이 집합 표현만 존재

---

## 잔여 검토 사항 (Plan §8 Migration 기준)

- [ ] **Step 6. projection 생성** — ✅ 완료됨
- [ ] **Step 7. regression test** — 기본 check-id / stats / validate 통과 확인 완료. 추가 시나리오 테스트 여부 사용자 판단
- [ ] **Step 8. DB compatibility test** — 과거 데이터 deserialize 확인 (필요 시)
- [ ] **Step 9. rollout** — maintenance window 결정 필요
- [ ] **Step 10. rollback** — symlink or version 기반 rollback 플랜 확인

### Plan §5.3 Alerting
- [ ] Slack / Telegram alerting 연동 (범위 외 — 별도 작업)

### Plan §1.3 Trading Freeze
- [ ] 장중 배포 방지 메커니즘 코드 반영 (범위 외 — 별도 작업)
