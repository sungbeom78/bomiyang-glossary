# Glossary Change Log

## 2026-04-19 15:35:00
### Modified - Refactored README files for generic usage
- Removed specific project references (e.g. BomTS) to make the Glossary submodule a generic naming enforcement tool.
- Restructured all README files (`README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md`) to have a unified architecture and concepts.
- Added latest features (GlossaryWriter, wikt_sense.py pipeline, Variants instead of isolated words).
- Replaced legacy `.env` scan configuration instructions with `.scan_list` and `.scan_ignore`.
- Radically simplified the Korean README (`README.ko.md`) to match the structural flow of other languages.
- File: `README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md`

## 2026-04-19 15:30:00
### Added / Modified / Fixed - 작업 통합 검토 및 dictionary migration

**Task 1 — 최근 3개 대화 작업 반영 검토**
- ✅ PROJECTION_VARIANT_TYPES 확장 (굴절형/파생형 포함)
- ✅ abbreviation top-level 필드 + _extract_word_variants §4.6
- ✅ GlossaryWriter 단일 저장 진입점
- ✅ server.py write APIs → GlossaryWriter 사용
- ✅ apply_pending_words.py → GlossaryWriter 사용

**Task 2/3 — migration/new word 경로 불일치 및 중복 수정**
- ❌→✅ `bin/batch_items.py`:
  - `_apply_to_words_json()` 함수를 GlossaryWriter 기반으로 전환
  - 직접 `words_path.write_text()` 제거 → `gw.add_word(skip_duplicate=True)` 사용
  - backup 자동 생성 보장
  - 반환값으로 실제 추가된 단어 수 표시로 개선
- 유지 레거시 (점진적 전환 대상): bin/fix_*.py, bin/migrate_*.py, bin/clean_*.py

**Task 4 — dictionary migration**
- schema V-011: `canonical_pos='prep'` 비표준 → `adv`로 수정
  - 대상: `with`, `without` (2개)
- `lang.ko` 미등록 단어 기본값 채우기 (21개)
  - abstract/average/bomiyang/cascading/chinese/comma/content/delivery/encryption/
    interface/network/program/separated/share/sheets/standard/style/syntax/tree/true/yuan
- 총 23건 수정 (GlossaryWriter, backup 자동 생성)

### Verification
- `python generate_glossary.py validate` → FATAL 0건 OK
- `python generate_glossary.py generate` → terms.json 2888개 OK
- dict_audit.py:
  - POS: noun/adj/verb/adv/prefix (prep 0개)
  - lang.ko 없음: 0개
  - auto_registered status: 0개

---

### Added / Modified - words.json top-level abbreviation 필드 구현

**사유**: 단어 단위 약어(auto, KR 등)를 words.json에서 관리할 수 없어
  check-id에서 약어 resolve가 불가했던 문제 해결.

### Added
- `schema/word.schema.json`: `abbreviation` top-level 필드 추가 (optional)
  - fields: short(필수), long, case_sensitive, confidence, ambiguity
  - `note` 필드 추가 (auto-registered 등 메타 주석)
- `generate_glossary.py`:
  - `_extract_word_variants()` §4.6 확장: top-level abbreviation.short를 variant_map에 포함
  - V-450 검증: abbreviation.long 미등록 단어 참조 시 WARN
  - V-451 검증: abbreviation.short 독립 word 존재 시 canonical_pos 일관성 확인
- `core/writer.py`:
  - `add_word_abbreviation(word_id, short, long, case_sensitive, confidence, ambiguity)` 추가

### Modified
- `dictionary/words.json`:
  - `automatic`: canonical_pos noun→adj, lang 보완(ko/ja/zh_hans),
    variants(adv_form/noun_form/verb_derived/agent) 추가,
    abbreviation: {short:"auto", long:"automatic", confidence:"high", ambiguity:"low"} 추가
  - `auto`: canonical_pos noun→prefix, from:"automatic" 추가,
    description_i18n 접두사 역할 반영
- `core/__init__.py`: 절대 import → 상대 import 수정

### Verification
- `python generate_glossary.py validate` → FATAL 0건 OK
- `python generate_glossary.py generate` → terms.json 2888개 생성 OK
- `python generate_glossary.py check-id auto` → [WARN] abbreviation (root: automatic) OK
- `python generate_glossary.py check-id auto_trade` → automatic + trade resolve OK

---

### Added - glossary 서브모듈 자체 완결형 지침 분리 구축

**사유**: glossary가 Git submodule로 관리되므로 main 프로젝트에 종속된 지침을
  glossary 내부로 완전히 분리. 어떤 main 프로젝트에 연결해도 독립적으로 동작 가능.

### Added
- AGENTS.md 전면 재작성 — glossary 자체 완결형 지침 (서브모듈 독립 원칙 명시)
- GEMINI.md 전면 재작성 — glossary 전용 AI 규칙 (G-1~G-7)
- .agents/workflows/change-code-procedure.md 신설
  - §DATA (GlossaryWriter 사용 의무)
  - §VALIDATE (validate/generate 검증)
  - §IDENTIFIER (check-id 절차)
  - §DOCS (문서 업데이트 의무)
  - §FAILURE (실패 처리)
- .agents/workflows/new-identifier-procedure.md 신설
  - Wiktionary + AI 파이프라인 사용법 포함 (wikt_sense.fetch_and_process)
- .agents/workflows/safe-command-policy.md 신설
  - Grade A (자동 허용): validate, generate, check-id
  - Grade B (조건부): GlossaryWriter 경유 스크립트
  - Grade C (금지): 직접 write

### Modified
- doc/README_AI_GUIDELINE.md 전면 확장
  - 데이터 아키텍처 개요 (디렉토리 구조)
  - validate V-코드 표 (V-104/V-202/V-301/V-303/V-352)
  - GlossaryWriter API 전체 목록
  - PROJECTION_VARIANT_TYPES 확장 내역 문서화
  - 환경 설정 (.env 필수 항목)
  - Wiktionary + AI 파이프라인 사용법
- doc/module_index.md — core/writer.py GlossaryWriter 및 generate_glossary.py(Projection) 항목 추가

### 연관 변경 (main 프로젝트)
- .agents/workflows/change-code-procedure.md §GLOSSARY 절 → §SUBMODULE 참조 주석으로 대체
- doc/module_index.md glossary 전용 항목 제거 (glossary/doc/module_index.md로 이동)
> **Archive**: ?댁쟾 湲곕줉? `doc/change_log_archive/202604_change_log.md` ??蹂닿?.

---

## [2026-04-19 11:17:00]
### Added ??諛곗튂 蹂묓빀 ?몄쭛 ?뱀뀡???ㅺ뎅??紐낆묶/?ㅻ챸 ?낅젰 湲곕뒫 異붽?

#### ?묒뾽 ?댁슜

**諛곌꼍**: 諛곗튂 蹂묓빀 ???⑥뼱瑜??깅줉?섍린 ?꾩뿉 ?쒓?쨌?곸뼱쨌?쇰낯?는룹쨷援?뼱 紐낆묶怨??쒓?/?곷Ц ?ㅻ챸??吏곸젒 ?낅젰?????덉뼱????
`atr ??Average True Range` 媛숈씠 ?⑥뼱???⑹꽦?댁쓽 ?ㅺ뎅??紐낆묶???щ엺??紐낆떆?섍퀬???????ъ슜.

**1. ?몄쭛 ?뱀뀡 UI 異붽?** (`web/index.html`)

`???깅줉 ???섏젙` ?뱀뀡????媛쒖쓽 sub-?뱀뀡 異붽?:

**?뙋 紐낆묶 (?좏깮)** ??2??洹몃━???덉씠?꾩썐:
- **EN** ?낅젰: enriched data `lang.en` ?먮룞 梨꾩? (?놁쑝硫?鍮?移?
- **KO** ?낅젰: enriched data `lang.ko` ?먮룞 梨꾩?
- **JA** ?낅젰: enriched data `lang.ja` ?먮룞 梨꾩?
- **ZH** ?낅젰: enriched data `lang.zh_hans` ?먮룞 梨꾩?

**?뱷 ?ㅻ챸 (?좏깮)** ??2??textarea:
- **KO** textarea: enriched `description_i18n.ko` ?먮룞 梨꾩?
- **EN** textarea: enriched `description_i18n.en` ?먮룞 梨꾩?
- ?ㅻ챸? ?덈궡: "?쒓?留??낅젰 ???곷Ц?쇰줈 蹂듭궗, 諛섎????숈씪"
  - KO留??낅젰 ??EN???먮룞 蹂듭궗 (踰덉뿭 ?泥?/ ?ъ슜?먭? 吏곸젒 ?섏젙 媛??
  - EN留??낅젰 ??KO???먮룞 蹂듭궗

**2. `applyUserEdit(i)` ?섏젙** (`web/index.html`)
- 4媛??몄뼱 ?꾨뱶 ??`lang_custom: {en, ko, ja, zh_hans}` ?????- 2媛??ㅻ챸 ?꾨뱶 ??`desc_custom: {ko, en}` ?????(auto-copy 洹쒖튃 ?곸슜)
- `t.user_edit = { ..., lang_custom, desc_custom }`

**3. `doMergeProcessed()` ?섏젙** (`web/index.html`)
- `user_edit.lang_custom` ??`wordBody.lang` 理쒖슦????뼱?곌린
- `user_edit.desc_custom` ??`wordBody.description_i18n` ??뼱?곌린
- compound ?붿껌??`lang_custom`, `desc_custom` ?ы븿?섏뿬 ?쒕쾭 ?꾨떖

**4. ?쒕쾭 `batch_register_compound` ?섏젙** (`web/server.py`)
- body?먯꽌 `lang_custom`, `desc_custom` ?섏떊
- ?쎌뼱 ?⑥뼱 ?먯껜(abbrev_id)媛 `words_new`???대떦?섎㈃ `lang_custom`/`desc_custom` ?곸슜
- compound ?뷀듃由? `comp_lang = default_lang + lang_custom`, `comp_desc = desc_custom || default_desc`

**?덉떆 (`atr`)**:
```
愿???⑥뼱/?⑹꽦?? average true range
EN: Average True Range
KO: ?됯퇏 ?ㅼ쭏 蹂????JA: 亮녑쓦?잆겗影꾢쎊
ZH: 亮녑쓦?잌츩力℡퉭
KO ?ㅻ챸: ?뱀씪??怨좉?쨌?媛, 洹몃━怨??꾩씪 醫낃????媛?Gap)源뚯? ?ы븿?섏뿬 ?쒖옣??吏꾩쭨 蹂????쓣 怨꾩궛
??compounds.json: average_true_range (abbrev: ATR, lang 4媛??몄뼱, desc KO+EN)
??words.json: average, true, range 媛곴컖 auto-?깅줉
```

#### Verification
- UI: EN/KO/JA/ZH 紐낆묶 ?꾨뱶 + KO/EN ?ㅻ챸 textarea ?뺤긽 ?뚮뜑留???- Auto-fill: enriched ?곗씠???먮룞 梨꾩? ??- `py_compile web/server.py` ??OK ??- 釉뚮씪?곗?: `atr` ??ぉ?먯꽌 ?꾩껜 ?낅젰 ???숈옉 ?뺤씤 ??
#### Affected Files
- `web/index.html` (MODIFY: 紐낆묶/?ㅻ챸 ?뱀뀡 UI, applyUserEdit, doMergeProcessed)
- `web/server.py` (MODIFY: batch_register_compound ??lang_custom/desc_custom 諛섏쁺)

---

## [2026-04-19 10:51:00]
### Fixed ??register_compound ?몃옖??뀡 湲곕컲 ?ъ옉??(words ?곗꽑 ?깅줉 + rollback)

#### 臾몄젣
湲곗〈 `batch_register_compound`??誘몃벑濡??⑥뼱瑜?`pending_words.json`??異붽??섎뒗 諛⑹떇?댁뿀?쇰굹,
??寃쎌슦 `compounds.json`???깅줉??compound媛 李몄“?섎뒗 ?⑥뼱媛 `words.json`???녿뒗 ?곹깭媛 諛쒖깮?????덉쓬.
?먰븳 words? compounds媛 蹂꾧컻 ?묒뾽?쇰줈 ?ㅽ뻾?섏뼱 ?ㅽ뙣 ??partial state媛 ?⑤뒗 臾몄젣 議댁옱.

#### ?섏젙 ?댁슜 (`web/server.py` ??`batch_register_compound`)

**?깅줉 ?쒖꽌 蹂寃?(words ??compound)**:
1. 援щЦ ?⑥뼱蹂꾨줈 `words.json` 議댁옱 ?щ? ?먮퀎:
   - **id濡??대? ?덉쓬** ??`words_found` (?ㅽ궢)
   - **variants.value濡??대? ?ы븿** ??`words_as_variant` (?ㅽ궢, ?뺥깭?뚯뿉 ?대? ?덉쓬)
   - **?꾩쟾 誘몃벑濡?* ??`words_new` ??**Step 1?먯꽌 words.json??諛붾줈 ?깅줉**
2. Step 1: `words_new` ?⑥뼱?ㅼ쓣 `words.json`??癒쇱? ?깅줉
3. Step 2: `compounds.json`??compound ?뷀듃由??깅줉

**?몃옖??뀡 泥섎━**:
- ?쒖옉 ??`copy.deepcopy`濡?`wd_snapshot`, `cd_snapshot` ?앹꽦
- ?덉쇅 諛쒖깮 ?? `save_words(wd_snapshot)`, `save_compounds(cd_snapshot)` ?몄텧濡??먮났
- ?묐떟??`rolled_back: true` ?ы븿

**?묐떟 援ъ“ 蹂寃?*:
- `words_found`: id濡??대? ?덈뒗 ?⑥뼱
- `words_as_variant`: variants???대? ?ы븿???⑥뼱 (?좉퇋 ?깅줉 遺덊븘??
- `words_new`: ?덈줈 `words.json`???깅줉???⑥뼱 紐⑸줉
- `total_words_registered`: ?좉퇋 ?깅줉 ??
**?대씪?댁뼵??toast ?낅뜲?댄듃** (`web/index.html`):
- `?⑹꽦??N媛??깅줉, ?⑥뼱 N媛??뺤씤, ?좉퇋 N媛?words ?깅줉, ?뺥깭??N媛??대? ?ы븿` ?뺤떇
- ?ㅽ뙣 ??`rollback ?꾨즺` ?쒖떆

#### Verification
- `py_compile web/server.py` ??OK ??- `pending_words.json` ?섏〈 ?쒓굅 ??- Rollback 濡쒖쭅: deepcopy + save 蹂듭썝 ??
#### Affected Files
- `web/server.py` (MODIFY: batch_register_compound ?꾩쟾 ?ъ옉??
- `web/index.html` (MODIFY: ?⑹꽦??泥섎━ ??toast 硫붿떆吏 ?낅뜲?댄듃)

---

## [2026-04-19 10:43:00]
### Added ??諛곗튂 蹂묓빀 ?⑹꽦??compound) ?깅줉 湲곕뒫

#### ?묒뾽 ?댁슜

**諛곌꼍**: 諛곗튂 蹂묓빀?먯꽌 "愿???⑥뼱" ?낅젰???⑥씪 ?⑥뼱留?泥섎━?섏뿬, `adx ??automatic data exchange` 媛숈? ?⑹꽦???쎌뼱瑜?compounds.json???깅줉?섎뒗 湲곕뒫???놁뿀??

**1. ?몄쭛 UI ?섏젙** (`web/index.html`)
- "愿???⑥뼱:" ??"愿???⑥뼱/?⑹꽦??" ?쇰꺼 蹂寃?- placeholder: `?⑥뼱(?? annotation) ?먮뒗 ?⑹꽦???? automatic data exchange)`
- 怨듬갚 ?ы븿 ???먮룞?쇰줈 `?⑹꽦?? ?뚮? 諛곗? ?쒖떆, ?⑥씪 ?⑥뼱 ??`?⑥뼱` 蹂대씪 諛곗?

**2. `applyUserEdit(i)` ?섏젙** (`web/index.html`)
- `is_compound = relInput.includes(' ')` ?먮룞 媛먯?
- `t.user_edit = { related_input, ref_url, is_compound }` 援ъ“濡????
**3. `doMergeProcessed()` ?섏젙** (`web/index.html`)
- ?⑥뼱(`is_compound=false`): 湲곗〈 `from` ?꾨뱶 濡쒖쭅 ?좎?
- ?⑹꽦??`is_compound=true`): `_compoundRequests` 紐⑸줉??異붽? ??蹂꾨룄 API ?몄텧
- ?뱀씤 ?꾨즺 ??寃곌낵??`?⑹꽦??N媛??깅줉, ?⑥뼱 N媛??뺤씤, pending N媛? ?쒖떆

**4. `POST /api/batch/register_compound` ?좉퇋 ?붾뱶?ъ씤??* (`web/server.py`)
- Input: `{ abbrev, phrase, ref_url }`
- 泥섎━:
  1. 援щЦ???⑥뼱濡?遺꾨━ ??`compound_id = word1_word2_word3`
  2. `words.json` 議댁옱 ?щ? ?뺤씤
  3. 誘몃벑濡??⑥뼱 ??`pending_words.json` ?먮룞 異붽? (note: Auto-pending from compound)
  4. `compounds.json`??compound ?뷀듃由?異붽?:
     - `words[]`: 援ъ꽦 ?⑥뼱 ID 由ъ뒪??     - `variants`: `[{type:"abbreviation", short:"ADX", long:"adx"}]`
     - `source_urls`: ref_url ?덉쑝硫??ы븿
- ?묐떟: `{ compound_id, compound_added, words_found, words_pending, newly_pending, pending_count }`

**5. ?ы띁 異붽?** (`web/server.py`)
- `PENDING_PATH = DICT_DIR / "pending_words.json"`
- `load_pending_words()`, `save_pending_words()` (罹먯떆 吏??

**?숈옉 ?먮쫫 ?덉떆 (`adx`)**:
1. ?곸꽭????愿???⑥뼱/?⑹꽦?? `automatic data exchange` ?낅젰
2. ?먮룞?쇰줈 `?⑹꽦?? 諛곗? ?쒖떆
3. ?곸슜 ?대┃ ??`t.user_edit.is_compound = true` ???4. ?좏깮 ?뱀씤 ?대┃ ??`/api/batch/register_compound` ?몄텧
5. 寃곌낵:
   - `compounds.json`??`automatic_data_exchange` 異붽? (variants.short=ADX)
   - `automatic`, `data`, `exchange` 以?words.json 誘몃벑濡??⑥뼱 ??pending_words
   - ?곹깭 ?쒖떆: `?⑹꽦??1媛??깅줉, ?⑥뼱 N媛??뺤씤, pending N媛?

#### Verification
- UI ?몄쭛 ?뱀뀡 蹂寃? ??label/placeholder/badge ?쒖떆
- `applyUserEdit` is_compound 媛먯?: ??怨듬갚 ???⑹꽦??諛곗?
- `/api/batch/register_compound` syntax: ??py_compile OK
- 釉뚮씪?곗? ?숈옉: ??automatic data exchange + URL ?낅젰 ?뺤긽

#### Affected Files
- `web/server.py` (ADD: PENDING_PATH, load/save_pending_words, batch_register_compound endpoint)
- `web/index.html` (MODIFY: applyUserEdit, doMergeProcessed, ?몄쭛 ?뱀뀡 UI)

---

## [2026-04-19 09:38:00]
### Added ??諛곗튂 蹂묓빀 ?몃씪???몄쭛 湲곕뒫 (愿???⑥뼱 / 李멸퀬 URL)

#### ?묒뾽 ?댁슜

**諛곌꼍**: 諛곗튂 蹂묓빀 ??AI媛 ?섎せ 遺꾨쪟?섍굅??遺議깊븳 ?뺣낫媛 ?덈뒗 ?⑥뼱(?? `ann` ??`annotation`)瑜??깅줉 ?꾩뿉 ?щ엺??吏곸젒 蹂댁셿?????덉뼱????

**1. UI 異붽?** (`web/index.html`)

?곸꽭 ?⑤꼸(?곸꽭?? ?섎떒??`???깅줉 ???섏젙` ?뱀뀡 異붽?:
- **愿???⑥뼱** ?낅젰 ?꾨뱶: ???⑥뼱媛 ?뚯깮??/ ?섎??섎뒗 ?⑥뼱 (?? `annotation`)
  - `from` ?꾨뱶濡???????숈씪 ?섎? ?먯튃???곕씪 words.json??`from: "annotation"` ???- **李멸퀬 URL** ?낅젰 ?꾨뱶: ?좏깮??李멸퀬 臾몄꽌 URL
- **?곸슜** 踰꾪듉: ?대┃ ??`_batchTerms[i].user_edit`????? `???곸슜?? ?쇰뱶諛??쒖떆
- ?곸슜 吏곹썑 ?곸꽭 ?⑤꼸 ?곷떒??`愿???⑥뼱 (?ъ슜??: xxx` ???ㅼ떆媛?異붽?

**2. `applyUserEdit(i)` ?⑥닔 異붽?** (`web/index.html`)
- ?낅젰媛믪쓣 `t.user_edit = { related_word, ref_url }` ?뺥깭濡?蹂댁〈
- ?낅젰媛믪? 紐⑤떖???レ븯?ㅺ? ?ъ뿴?대룄 ?좎?

**3. `doMergeProcessed()` ?섏젙** (`web/index.html`)
- `user_edit.related_word` ??`wordBody.from` ?쇰줈 諛섏쁺
- `user_edit.ref_url` ??`wordBody.source_urls` 留??욎뿉 ?쎌엯 (湲곗〈 URL 蹂댁〈)
- `t.lang` (enriched ?ㅺ뎅?대챸) ?덉쑝硫?wordBody.lang?먮룄 諛섏쁺

**?숈옉 ?먮쫫 ?덉떆 (`ann` ?⑥뼱)**:
1. ?곸꽭???대┃ ???몄쭛 ?뱀뀡 ?쒖떆
2. 愿???⑥뼱: `annotation` ?낅젰
3. 李멸퀬 URL: `https://pylint.pycqa.org/.../AnnAssign.html` ?낅젰
4. ?곸슜 ??`_batchTerms[i].user_edit` ???5. ?좏깮 ?뱀씤 ?대┃ ??words.json??`{id:"ann", ..., from:"annotation", source_urls:["https://..."]}` ???
#### Verification
- ?몄쭛 ?뱀뀡 UI ?뚮뜑留? ??- annotation + URL ?낅젰 ???곸슜: ??(`愿???⑥뼱 (?ъ슜??: annotation` ?쒖떆)
- 紐⑤떖 ?ъ삤?????낅젰媛??좎?: ??- `doMergeProcessed`: user_edit.from + source_urls 諛섏쁺 濡쒖쭅 異붽? ??
#### Affected Files
- `web/index.html` (MODIFY: applyUserEdit ?⑥닔 異붽?, ?곸꽭 ?⑤꼸 ?몄쭛 ?뱀뀡, doMergeProcessed 蹂묓빀 濡쒖쭅 媛쒖꽑)

---

## [2026-04-19 08:53:00]
### Fixed ??諛곗튂 蹂묓빀 ?곸꽭 ?⑤꼸 ?뺣낫 ?꾨씫 ?섏젙

#### ?묒뾽 ?댁슜

**臾몄젣**: 諛곗튂 蹂묓빀(3. 蹂묓빀) ?붾㈃??"?곸꽭?? ?⑤꼸??JSON???쇰? ?뺣낫留??쒖떆?섍퀬 ?섎㉧吏 ?꾨뱶(variants, from, lang, sources)媛 ?꾨씫??

**?섏젙 ?댁슜** (`web/index.html`):

1. **?쒖떆 議곌굔 ?뺤옣**
   - 湲곗〈: `enr.description_i18n || source_urls` ?덉쓣 ?뚮쭔 ?곸꽭 踰꾪듉 ?쒖떆
   - 蹂寃? `lang`, `reason`, `sources` ???대뼡 ?꾨뱶?쇰룄 ?덉쑝硫?踰꾪듉 ??긽 ?쒖떆

2. **?곸꽭 ?⑤꼸 ?쒖떆 ?꾨뱶 異붽?**
   - **?몄뼱 (lang)**: KO / JA / ZH ?ㅺ뎅???대쫫
   - **KO ?ㅻ챸 / EN ?ㅻ챸**: `description_i18n` (湲곗〈 ?좎?)
   - **from**: ?댁썝 ?⑥뼱 (?좉퇋)
   - **variants**: ?뺥깭??紐⑸줉 ??`value(type)` ?뺤떇?쇰줈 ?섏뿴 (?좉퇋)
   - **URL**: 異쒖쿂 URL ???щ윭 媛쒖씤 寃쎌슦 紐⑤몢 ?쒖떆 (湲곗〈 1媛쒕쭔 ???꾩껜)
   - **?먯젙**: AI ?먯젙 `reason` ?꾨뱶 (?좉퇋)
   - **諛쒓껄 ?꾩튂**: `sources` 以묐났 ?쒓굅 ????紐⑸줉 ?쒖떆 (?좉퇋)

3. **?먮룞 ?ㅽ겕濡?*
   - ?곸꽭???대┃ ??`merge-preview` 而⑦뀒?대꼫 湲곗? ?대떦 ?⑤꼸濡?遺?쒕읇寃??ㅽ겕濡?
#### Verification
- `alert` (enriched ?덉쓬): ?몄뼱/?ㅻ챸/variants/URL/?먯젙/諛쒓껄 ?꾩튂 ?꾩껜 ?쒖떆 ??- `adx` (enriched ?놁쓬): ?먯젙 + 諛쒓껄 ?꾩튂 ?뺤긽 ?쒖떆 ??- ?먮룞 ?ㅽ겕濡? merge-preview 而⑦뀒?대꼫 ??smooth scroll ?숈옉 ?뺤씤 ??
#### Affected Files
- `web/index.html` (MODIFY: 蹂묓빀 ?곸꽭 ?⑤꼸 ?뚮뜑 濡쒖쭅 媛쒖꽑)

---

## [2026-04-19 00:34:00]
### Added ??pending_words 15媛?words.json ?곸슜 + Migration

#### ?묒뾽 ?댁슜

**1. `bin/apply_pending_words.py` ?ㅽ뻾 (?좉퇋 ?ㅽ겕由쏀듃)**

pending_words.json ?붿뿬 15媛쒕? ?꾩쟾???ㅽ궎留?lang, description_i18n, variants ?ы븿)濡?words.json??異붽?.

| word | domain | 鍮꾧퀬 |
|------|--------|------|
| adapt | system | ?숈궗, adapter.variants?먯꽌 adapt ?쒓굅 |
| authenticate | infra | ?숈궗, auth.variants?먯꽌 authenticate ?쒓굅 |
| low | market | adj, lower.variants?먯꽌 low ?쒓굅 |
| manage | system | ?숈궗 |
| notify | system | ?숈궗 |
| orchestrate | system | ?숈궗 |
| real | market | adj |
| scan | system | ?숈궗 |
| schedule | system | ?숈궗 |
| select | system | ?숈궗 |
| slip | trading | 紐낆궗/?숈궗 (slippage) |
| snap | system | ?숈궗 (snapshot) |
| store | infra | ?숈궗 |
| volatile | trading | adj, volatility.variants?먯꽌 volatile ?쒓굅 |
| watch | system | ?숈궗 |

**2. 異⑸룎 ?닿껐**

- `adapter.variants`: adapt ?쒓굅 (1媛?
- `auth.variants`: authenticate ?쒓굅 (1媛?
- `lower.variants`: low ?쒓굅 (3媛? lower媛 low??variant???寃?
- `volatility.variants`: volatile ?쒓굅 (1媛?
- `market_scanner.variants`: SCAN abbreviation ?쒓굅 (V-202 FATAL ?닿껐)

**3. Migration 寃곌낵**

- validate: FATAL 0嫄???- terms.json ?ъ깮?? **718 ??733媛?* (+15)
- words: 233 ??248媛?- pending_words: 15 ??0媛?(?꾩쟾 ?뚯쭊)

#### Affected Files
- `bin/apply_pending_words.py` (NEW)
- `dictionary/words.json` (MODIFY: +15媛??⑥뼱, 4媛?variant ?뺣━)
- `dictionary/compounds.json` (MODIFY: market_scanner SCAN abbreviation ?쒓굅)
- `dictionary/pending_words.json` (MODIFY: 15 ??0媛?
- `dictionary/terms.json` (REGENERATED: 733媛?
- `build/index/*` (REGENERATED)
- `GLOSSARY.md` (REGENERATED)

---

## [2026-04-19 00:28:00]
### Added / Modified ??.scan_list/.scan_ignore ?꾩엯 + dictionary ?뺤젣 + Migration

#### ?묒뾽 ?댁슜

**1. ?ㅼ틪 ????쒖쇅 ?ㅼ젙 ?뚯씪 ?꾩엯**

- `glossary/.scan_list` (NEW): ?ㅼ틪 ????대뜑/?뚯씪 ?⑦꽩 紐낆떆??愿由?  - `dir:config`, `dir:script`, `dir:src`
  - `root:.env*`, `root:run*.py`
- `glossary/.scan_ignore` (NEW): ?ㅼ틪 ?쒖쇅 ?대뜑/?뚯씪 ?⑦꽩 愿由?  - `dir:__pycache__`, `ext:.md`, `pattern:.git*`
- ?쒖쇅 洹쒖튃????긽 ?ㅼ틪 ??곷낫???곗꽑 ?곸슜

**2. `bin/scan_items.py` 由ы뙥?곕쭅**

- `load_scan_config()` ?좉퇋 ?⑥닔: .scan_list / .scan_ignore ?뚯떛
- `_matches_ignore_pattern()` ?좉퇋 ?⑥닔: fnmatch 湲곕컲 ?⑦꽩 留ㅼ묶
- `ItemScanner.__init__()`: `scan_config` ?뚮씪誘명꽣 異붽?
- `scan()`: scan_list ?덉쑝硫?`_scan_with_config()`, ?놁쑝硫?`_scan_legacy()` ?대갚
- `_scan_with_config()`: root_patterns(glob) + scan_dirs(?ш?) 湲곕컲 ?ㅼ틪
- `_scan_file()`: ?뺤옣?먮퀎 遺꾧린 怨듯넻 硫붿꽌??異붿텧
- `_scan_legacy()`: 湲곗〈 exclude_dirs 湲곕컲 ?ㅼ틪 ?좎? (?섏쐞?명솚)
- 寃利? `--count` 湲곗? 684媛??꾨낫 異붿텧 ?뺤씤

**3. `dictionary/pending_words.json` ?뺤젣**

- `bin/clean_pending_words.py` (NEW): pending_words ?뺤젣 ?ㅽ겕由쏀듃
- ?쒓굅 21嫄?
  - words.json ?대? ?깅줉: disable, rank, relax
  - ?꾨찓??臾닿?(?몄뼱??: latin, french, italian, ancient_greek, middle_english
  - ?묐몢??遺덉슜?? tele, re, un, intra
  - ?쇰컲?? old, new, off, back, bottom, middle, heart, dash, earlier
- ?붿뿬 15媛?(怨꾩냽 寃?????: adapt, authenticate, low, manage, notify, orchestrate, real, scan, schedule, select, slip, snap, store, volatile, watch

**4. Migration ?ㅽ뻾**

- validate: FATAL 0嫄???- terms.json ?ъ깮?? 718媛?(checksum ?ы븿)
- GLOSSARY.md 媛깆떊

#### Affected Files
- `glossary/.scan_list` (NEW)
- `glossary/.scan_ignore` (NEW)
- `bin/scan_items.py` (MODIFY: scan_config 援ъ“ 異붽?)
- `bin/clean_pending_words.py` (NEW)
- `dictionary/pending_words.json` (MODIFY: 21媛??쒓굅)
- `dictionary/terms.json` (REGENERATED)
- `build/index/*` (REGENERATED)
- `GLOSSARY.md` (REGENERATED)

---

## [2026-04-19 00:08:00]
### Fixed / Modified ??words.json ?뺥빀??+ banned.json ???쒖떆 ?섏젙 + Migration

#### ?묒뾽 ?댁슜

**1. V-301 variant-id 異⑸룎 ?닿껐 (bin/fix_v301_conflicts.py ?좉퇋)**
?ъ슜?먭? ?낅┰ ?⑥뼱濡?異붽?????ぉ怨?遺紐?word.variants 媛?異⑸룎 6嫄??닿껐:
- `rank.variants`?먯꽌 `ranking` (present_participle, noun_form) ?쒓굅
- `realize.variants`?먯꽌 `realized` (past) ?쒓굅
- `extend.variants`?먯꽌 `extended` (past) ?쒓굅
- `track.variants`?먯꽌 `tracking` (present_participle) ?쒓굅
- `use.variants`?먯꽌 `used` (past) ?쒓굅
- `run.variants`?먯꽌 `runner` (agent) ?쒓굅

?ㅺ퀎 ?먯튃: ?낅┰ word濡?紐낆떆?곸쑝濡??깅줉????ぉ? 遺紐⑥쓽 ?뺥깭???뚯깮??紐⑸줉?먯꽌 ?쒓굅.

**2. Migration ?ㅽ뻾 (generate)**
- validate: FATAL 0嫄?(WARN 1嫄???candle.ko='罹붾뱾', ?덉슜)
- terms.json ?ъ깮?? 718媛? checksum ?ы븿

**3. banned.json ???쒖떆 踰꾧렇 ?섏젙 (web/index.html)**
- ?먯씤: `correct:{type,value}` 媛앹껜瑜?`b.correct` ?⑥닚 李몄“ ??`[object Object]` ?쒖떆
- `reason_i18n:{ko,en}` 援ъ“瑜?`b.reason` ?⑥닚 李몄“ ??鍮?媛??쒖떆
- ?섏젙:
  - `renderBanned()`: `correct.value`, `reason_i18n.ko` ?щ컮瑜닿쾶 異붿텧
  - `bFilter()`: 寃?됰룄 ?숈씪 寃쎈줈濡??섏젙
  - `openBannedForm()`: correct.value, reason_i18n.ko瑜????꾨뱶??諛붿씤??  - `saveBanned()`: `correct:{type:'id', value}`, `reason_i18n:{ko,en}` 援ъ“濡????
**4. ?ㅼ틪 ?쒖쇅 ?대뜑 ?뺤씤**
?꾩옱 EXCLUDE_DIRS ?ㅼ젙:
- ?쒖쇅?? backup, data, tmp, glossary, .git, __pycache__, node_modules, .venv, venv, lib_test, tests
- ?ㅼ틪?? cache, config, doc, log, script, src, test, tool

**5. banned.json ?댁슜 寃??*
- 8媛?紐⑤몢 ?좏슚???댁슜
- correct.value 以?words.json???녿뒗 寃? fx_fut, fxfutures ??compounds?먯꽌???놁쓬. ?⑥닚 李몄“ id (蹂꾨룄 ?깅줉 ?꾩슂 ?놁쓬)
- KIS ??kr_stock: words.json???뺤긽 議댁옱

#### Affected Files
- `bin/fix_v301_conflicts.py` (NEW)
- `dictionary/words.json` (MODIFY: 6媛?variant ?쒓굅)
- `dictionary/terms.json` (REGENERATED)
- `build/index/*` (REGENERATED)
- `GLOSSARY.md` (REGENERATED)
- `web/index.html` (MODIFY: banned ?뚮뜑留??ㅽ궎留??섏젙)

---

## [2026-04-18 23:53:00]
### Fixed / Modified / Added ??諛곗튂 ?뚯씠?꾨씪???뺥빀??媛쒖꽑 v1.1 + Migration

#### 紐⑹쟻
諛곗튂 ?ㅼ틪 寃곌낵(`items.json`)???뺥깭???뚯깮?뺤씠 諛섎났 ?깆옣?섎뒗 洹쇰낯 ?먯씤???쒓굅?섍퀬,
`words__derived_terms.json` synonym ?덉쭏???뺤젣????`terms.json`???ъ깮?깊븳??

---

#### Step 1 ??`bin/scan_items.py` exclusion 踰꾧렇 ?섏젙

**File: bin/scan_items.py (MODIFY)**

`load_existing_words_and_tokens()` ?⑥닔??variants ?쎄린 濡쒖쭅??`list[dict]` 援ъ“瑜?`dict`濡??섎せ 媛꾩＜?섏뿬 variants surface媛 exclusion token???꾪? ?ы븿?섏? ?딆븯?? 寃곌낵?곸쑝濡?`accounts`, `buying`, `checks` ???뺥깭???뚯깮?뺤씠 留ㅻ쾲 諛곗튂 ?꾨낫(`items.json`)???щ벑?ν븯??臾몄젣媛 諛쒖깮?덈떎.

##### 蹂寃??댁슜:
- `variants`??`list[{type, value|short}]` 援ъ“濡??щ컮瑜닿쾶 諛섎났 泥섎━
- `auto_plural` 濡쒖쭅: variants??`type=="plural"`???녿뒗 noun?먮쭔 ?곸슜
- compounds.id??token?쇰줈 異붽?
- `words__derived_terms.json`??surface(underscore/怨듬갚 ?녿뒗 寃???exclusion??異붽?
  ???뚯깮??synonym???대? 愿怨??뚯븙??寃쎌슦 ?꾨낫?먯꽌 ?쒖쇅
- `_add()` 硫붿꽌?? naive `t[:-1] in existing` ??텛濡??쒓굅 (?ㅽ깘 媛??
  ??`t in self.existing` ?꾩쟾 留ㅼ묶留??ъ슜

##### ?④낵:
- ?댁쟾 exclusion ?좏겙: ~228媛?(id留?
- ?섏젙 ??exclusion ?좏겙: ~900+媛?(id + variants + derived_terms)

---

#### Step 2 ??`dictionary/words__derived_terms.json` ?덉쭏 ?뺤젣

**File: dictionary/words__derived_terms.json (MODIFY)**
**File: bin/clean_derived_terms.py (NEW)**

- ?먮낯 739媛????뺤젣 ??662媛?(77嫄??쒓굅)
- ?쒓굅 湲곗?:
  - `synonym` 以?`words.id`? 異⑸룎?섎뒗 寃?(account?뭕alance, order?뭖ommand ??
  - `synonym` 以?`words.variants`???대? 議댁옱?섎뒗 寃?(enter, tops, err ??
  - `synonym` 以?underscore/怨듬갚 ?ы븿 ?쒗쁽 (?먯뿰???꾨떂): 43嫄?  - ?꾨찓??臾닿? ?숈쓽??(臾쇰━쨌踰붿즲 ?⑹뼱 ??: 13嫄?
---

#### Step 3 ??`generate_glossary.py generate` Migration ?ㅽ뻾

##### ?ъ쟾 泥섎━: V-104 FATAL ?닿껐
**File: dictionary/words.json (MODIFY)**
**File: bin/fix_missing_words.py (NEW)**

compounds媛 李몄“?섏?留?words.json???녿뜕 5媛??⑥뼱 異붽?:
- `ranking` (sector_ranking, symbol_ranking, db_sector_rankings 李몄“)
- `realized` (realized_pnl 李몄“)
- `tracking` (tracking_start 李몄“)
- `extended` (extended_market_start, extended_market_end 李몄“)
- `used` (margin_used 李몄“)

words.json: 228媛???233媛?
##### generate 寃곌낵:
- `validate` FATAL: 8嫄???0嫄???- `terms.json` ?ъ깮?? 718媛?(checksum ?ы븿)
- `terms_legacy.json`: 0媛?deprecated
- `dependency_missing.json`: 0嫄?- `GLOSSARY.md` 媛깆떊

---

#### module_index.md ?낅뜲?댄듃 ?댁슜:
- `bin/scan_items.py`: variants ?쎄린 諛⑹떇 諛?exclusion 踰붿쐞 蹂寃?(v1.1)
- `bin/clean_derived_terms.py`: ?좉퇋 異붽? (synonym ?덉쭏 ?뺤젣)
- `bin/fix_missing_words.py`: ?좉퇋 異붽? (V-104 ?꾩떆 ?섏젙??

---

## [2026-04-18 21:00:00]
### Modified ??????쒕낫??湲곕뒫 ?뺤옣 (v3.4)

#### 紐⑹쟻
1. JSON???덈뒗 紐⑤뱺 ?꾨뱶瑜?UI?먯꽌 議고쉶쨌?섏젙 媛?ν븯?꾨줉 ?뺤옣
2. ?몄뼱 ?꾪솚 踰꾪듉(??EN/JA/ZH) 異붽?
3. ?섍꼍?ㅼ젙 紐⑤떖?먯꽌 湲곕낯 ?몄뼱쨌?쒓컙?瑜?localStorage?????
#### 蹂寃??뚯씪

**web/index.html (MODIFY)**
- `topbar`: `lang-sel` ?쒕∼?ㅼ슫 異붽? (?쒓뎅??English/?ζ쑍沃?訝?뻼), `???ㅼ젙` 踰꾪듉 異붽?
- ?⑥뼱 ?섏젙 紐⑤떖(`word-ov`) ?꾨㈃ 媛쒗렪
  - **湲곕낯 ?뺣낫**: id, pos, status, domain
  - **?ㅺ뎅??踰덉뿭**: en, ko, ja, zh_hans
  - **?ㅻ챸**: ko (?꾩닔), en (?좏깮)
  - **?뺥깭??愿怨꾩뼱**: abbr, from, variants (type:value 以꾨컮轅?, synonyms, antonyms, source_urls, not
  - 以묐났 `wf-status` ?쒓굅 (湲곗〈 踰꾧렇 ?섏젙)
  - 蹂듯빀??紐⑤떖(`compound-ov`)??以묐났 `wf-status` ?쒓굅
- ?섍꼍?ㅼ젙 紐⑤떖(`settings-ov`) ?좉퇋 異붽?
  - 湲곕낯 ?쒖떆 ?몄뼱, 湲곕낯 ?쒓컙? ?좏깮 ??localStorage ???- `renderWords()`:
  - `window.LANG` 媛믪뿉 ?곕씪 踰덉뿭 ???쒓뎅???곸뼱/?쇰낯??以묎뎅?? ?숈쟻 ?꾪솚
  - ?ㅻ챸(description) ?대룄 ?좏깮 ?몄뼱濡??먮룞 ?꾪솚
  - ?뺤옣 ??xrow) ?꾩껜 ?꾨뱶 ?쒖떆: lang.ja, lang.zh_hans, description(en), from, variants 移? synonyms, antonyms, source_urls 留곹겕
- `openWordForm()`: ?좉퇋 ?꾨뱶 9媛?異붽? 梨꾩?
- `saveWord()`: ?좉퇋 ?꾨뱶瑜?JSON body???ы븿 (ja, zh_hans, descEn, from, variants, synonyms, antonyms, source_urls)
- `variantsToText()` / `textToVariants()` ?ы띁 ?⑥닔 異붽?
- `changeLang(lang)`, `openSettings()`, `saveSettings()` ?⑥닔 異붽?
- `boot()`: localStorage?먯꽌 ??λ맂 ?몄뼱쨌?쒓컙? 蹂듭썝
- Escape ?몃뱾?ъ뿉 `settings-ov` 異붽?

#### 寃利?- 釉뚮씪?곗? ?뚮뜑留??뺤씤: account ?뺤옣 ?됱뿉??lang.ja(?㏂궖?╉꺍??, lang.zh_hans(躍먩댎), description(en), variants 移? source_url 留곹겕 ?뺤긽 ?쒖떆
- ?섏젙 紐⑤떖: 9媛??좉퇋 ?꾨뱶 紐⑤몢 ?뺤긽 ?쒖떆 諛?湲곗〈 ?곗씠??梨꾩? ?뺤씤
- ?ㅼ젙 紐⑤떖: ??????몄뼱 利됱떆 ?꾪솚, localStorage 諛섏쁺 ?뺤씤
- 228媛??꾩껜 ?뚮뜑留??좎?

---

## [2026-04-18 20:09:00]
### Modified ??????쒕낫???뚮뜑留??깅뒫 理쒖쟻??(v3.3)

#### 紐⑹쟻
228媛??꾩껜 ?⑥뼱 ??ぉ???꾩쟾??異쒕젰 蹂댁옣 諛?1珥????섏씠吏 濡쒕뵫 ?ъ꽦

#### 蹂寃??댁슜

**web/server.py (MODIFY)**
- `_load_json()`: mtime 湲곕컲 ?몃찓紐⑤━ 罹먯떆 異붽?
  - ?뚯씪 蹂寃??놁쓣 ???뚯씪 I/O ?꾩쟾 ?쒓굅 (留?GET 留덈떎 208KB JSON ?ы뙆??諛⑹?)
  - `_cache: dict` ?꾩뿭 罹먯떆 ?뺤뀛?덈━ ?꾩엯
  - `_invalidate_cache(path)` ??save ??罹먯떆 臾댄슚??- `/api/words` GET: ETag + If-None-Match 吏??  - md5 湲곕컲 ETag ?앹꽦 ??304 Not Modified ?묐떟?쇰줈 ?대씪?댁뼵??以묐났 ?꾩넚 諛⑹?

**web/index.html (MODIFY)**
- `boot()` ?ш뎄議고솕: words瑜?癒쇱? 濡쒕뱶??泥??섏씤?몃? ?욌떦源 (吏꾪뻾???뚮뜑)
  - ?섎㉧吏 compounds/banned/drafts??蹂묐젹 fetch
- `renderWords()` ?꾨㈃ 理쒖쟻??
  - `DocumentFragment` ?ъ슜?쇰줈 DOM ?쎌엯 1?뚮줈 吏묒빟
  - `for` 猷⑦봽濡?援먯껜 (`forEach` ??誘몄꽭 ?ㅻ쾭?ㅻ뱶 ?쒓굅)
  - HTML 臾몄옄?댁쓣 吏㏃? ?멸렇癒쇳듃 ?곌껐濡?遺꾪븷 (媛?낆꽦 + ?붿쭊 理쒖쟻??
  - ?대깽???꾩엫(event delegation): 媛쒕퀎 `addEventListener` 228媛??쒓굅,
    tbody ?⑥쐞 click/dblclick ?몃뱾??1媛쒕줈 ?泥?  - ??젣 踰꾪듉: `onclick` ?몃씪????`data-del-word`, `data-del-ko` ?띿꽦?쇰줈 遺꾨━
  - ?섏젙 留곹겕: `onclick` ?몃씪????`data-edit-word` ?띿꽦?쇰줈 遺꾨━
- `reloadWords()`: ETag 罹먯떆 ?ㅻ뜑 吏??(304 ?묐떟 ??遺덊븘?뷀븳 JSON ?뚯떛 ?ㅽ궢)
- `_wordsETag` ?꾩뿭 蹂??異붽?

#### 寃利?寃곌낵
- ?⑥뼱 228媛??꾩껜 ?뺤긽 ?뚮뜑留??뺤씤
- ?섏씠吏 濡쒕뵫 1珥??대궡
- ?쒕쾭 臾몃쾿 寃?? `py_compile` PASS

### Notes
- 湲곗〈 change_log.md 515以???500以?珥덇낵濡?`doc/change_log_archive/202604_change_log.md` ?꾩뭅?대튃 ?섑뻾

