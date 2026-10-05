# 용어 영역(areas) 규칙

> 기존 규칙(`glossary_rule.md`)에 **추가**되는 규칙이다. 영역을 선언하지 않은 사용처(예: BOM_TS)는
> 이 규칙이 생기기 전과 **완전히 같은 결과**를 얻는다 (인덱스·감사 결과 바이트 단위 동일).

## 1. 원칙

| # | 규칙 | 예 |
|---|---|---|
| R1 | 영문 하나 : 한글명 N 개 (영역마다, 한 영역 안에서도 여럿 가능) | `no`: general=금지, data=번호 |
| R2 | 한글명 하나 → 영문 하나 (**사전 전체 기준**) | '정보'는 `info` 만. `information` 추가 금지. 업종이 달라도 같은 한글은 같은 영문 (학교 '교육'=`education` 이면 HRD 는 '훈련'=`training`) |
| R3 | 한 영역 안에서 영문 단어 항목은 하나 (한글명은 여럿 가능) | data 영역의 `no` 는 하나 |
| R4 | 같은 영문이 여러 영역에 속할 수 있다 | `credit`: general, trading |
| R5 | 새 단어는 general 뜻(사전적 일반 의미)을 가진다. **처음 등록한 프로젝트의 업무 뜻이 general 이 되지 않는다** | `value` general=값, market=거래대금 |

코드·컬럼·테이블 이름에는 영문 하나만 쓰이므로 R1 의 한글명 여럿은 이름 충돌을 만들지 않는다.

## 2. 영역(area)

- 영역은 **업무 영역** 기준이다 (조직도 기준이 아님 -- 부서 개편과 무관하게 용어 뜻은 유지된다).
- 영역은 평평한 목록 `dictionary/areas.json` 으로 관리하고, 깊이 제한이 없다.
  ```json
  {"id": "general", "name_ko": "일반", "tags": ["root"]}
  {"id": "trading", "name_ko": "매매", "tags": ["domain", "legacy"]}
  {"id": "data",    "name_ko": "데이터 명명", "tags": ["naming"]}
  ```
- 태그: `root`(general), `domain`(업무 도메인으로 쓰이는 영역), `area`(세부 업무 영역), `naming`(명명 규칙 영역,
  예: DB 분류어), `category`(기술 분류), `legacy`(이 규칙 이전부터 쓰던 `domain` 값).
- 단어의 기존 `domain` 필드 = **소속 영역 목록**. 기존 값은 바꾸지 않는다.

## 3. 뜻(senses)과 약어

```json
{"id": "no", "domain": ["system", "data"], "lang": {"en": "no", "ko": "금지"},
 "senses": {"general": ["금지"], "data": ["번호"]},
 "area_abbreviations": {}}
```
- `senses`: 영역 → 한글명 목록. 한 영역에 이름이 여럿이면 목록에 여러 개.
- 출력: 영역 사이는 `, `, 한 영역 안의 여러 이름은 `/` -- 예 `금지, 번호`, `주제/과목/주체`.
- `senses` 가 없는 기존 단어는 "`lang.ko` = 첫 번째 `domain` 영역의 뜻"으로 **읽을 때만** 해석한다 (파일은 그대로).
- `area_abbreviations`: 영역 → 약어. 영역 안에서만 유효하므로 전역 약어와 철자가 겹쳐도 된다
  (data 영역 `timestamp`→`at` 과 trading 의 `active_trade`→`at` 공존).
- `lang.ko` 는 대표 뜻으로 유지한다 (기존 도구 호환).

## 4. 찾는 순서

사용처(프로젝트)는 자기 영역 순서를 선언한다 (앞 = 일반, 뒤 = 구체).
```yaml
glossary:
  areas: [general, school, nursing, nursing_mgmt]
```
뜻과 약어는 **뒤에서부터** 찾는다: `nursing_mgmt → nursing → school → general`. 선언하지 않으면 영역을 쓰지 않는다(기존과 동일).

## 5. 등록 순서 (최대 3회 검토, 찾으면 즉시 종료)

1. 우리 영역(선언 순서의 뒤에서부터, general 제외)에 같은 뜻이 있는가 → 재사용
2. general 에 같은 뜻이 있는가 → 재사용 (**가능하면 general 단어를 우선한다**)
3. 한글명 전체 색인에 같은 한글명이 다른 영문으로 있는가 → 있으면 그 영문을 써야 한다 (R2)

모두 없으면 등록한다. 일반적인 뜻이면 general 에, 그 영역에서만 다른 뜻이면 해당 영역 뜻으로 추가한다.
처음 등록되는 영문이면 general 뜻도 함께 등록한다 (R5).

## 6. 보완 필요 표시 (`need_modify`)

이 규칙에 어긋나는 **기존** 항목은 값을 고치지 않고 표시만 한다.
```json
"need_modify": {"status": "open", "issues": [{"code": "R2_DUP_KO", "detail": "'중단' = abort, stop"}]}
```
- 코드: `R2_DUP_KO`(같은 한글명이 여러 영문), `NO_GENERAL_SENSE`(general 뜻 없음), `UNKNOWN_AREA`(목록에 없는 영역).
- `python generate_glossary.py diagnose` 는 목록만 출력, `--write` 는 `need_modify` 필드를 기록한다.
- validate 는 이 문제를 **경고(WARN)** 로만 낸다 -- 기존 시스템을 막지 않는다. 정리는 별도로 판단한다.

## 7. 도구

| 명령 / API | 용도 |
|---|---|
| `generate_glossary.py areas` | 영역 목록 |
| `generate_glossary.py meaning <id> [--areas a,b]` | 영역 순서에 따른 뜻 |
| `generate_glossary.py diagnose [--write]` | 원칙 위반 진단 / need_modify 기록 |
| `GlossaryWriter.add_area / add_sense / set_area_abbreviation / set_need_modify` | 등록 |
| `GlossaryAuditor(areas=[...])` | 영역 약어를 반영한 감사, `meaning()` · `resolve()` 조회 |
| `build/index/ko_index.json`, `area_map.json`, `senses.json` | 새 인덱스 (기존 인덱스 파일은 변하지 않음) |
