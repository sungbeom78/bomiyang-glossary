# bomiyang-glossary
A structured glossary for managing and standardizing technical terms across projects.

용어를 일관된 기준으로 정리하고 관리하기 위한 개인 Glossary 저장소입니다.

이 저장소는 용어 원본 데이터, 검증 스크립트, 문서 생성기, 로컬 웹 편집 UI로 구성됩니다.

## 목적

- 프로젝트에서 사용하는 용어를 한 곳에서 관리
- 한글명, 영문명, 약어, 카테고리, 설명을 표준화
- 문서와 코드에서 같은 용어를 일관되게 사용
- 용어 데이터를 기반으로 Markdown 문서를 자동 생성

## 구성

```text
glossary/
├── terms.json
├── GLOSSARY.md
├── bin/
│   ├── run.py
│   ├── validate.py
│   └── generate_glossary.py
└── web/
    ├── server.py
    └── index.html

## 실행 옵션 (run.py)

`run.py`는 용어 검증, 문서 생성, 변경 감지(watch) 기능을 제공하는 실행 진입점입니다.

### 기본 실행

```bash
python run.py
```

기본 동작:

* `terms.json` 검증 수행
* `GLOSSARY.md` 생성

즉, **validate → generate** 순서로 실행됩니다.

---

### 검증만 수행

```bash
python run.py --check
```

* `terms.json` 검증만 수행
* `GLOSSARY.md` 생성하지 않음

---

### 강제 생성

```bash
python run.py --force
```

* 검증 수행
* 검증 오류가 있어도 `GLOSSARY.md` 생성 강행

---

### 변경 감지 모드 (watch)

```bash
python run.py --watch
```

* `terms.json` 변경 감지
* 저장 시 자동 실행:

  * 검증
  * 문서 생성

---

### 변경 감지 + 검증만

```bash
python run.py --watch --check
```

* `terms.json` 변경 감지
* 저장 시 검증만 수행
* 문서 생성은 하지 않음

---

### 추천 사용 방법

```bash
python run.py --watch
```

* 터미널에 watch 모드를 띄워두고
* `terms.json`을 수정하면 저장 시 자동으로 `GLOSSARY.md`가 갱신됨
* 에디터 Markdown Preview를 열어두면 실시간 결과 확인 가능

---

## 웹 UI

로컬 웹 서버를 통해 용어를 조회 및 수정할 수 있습니다.

### 실행

```bash
python web/server.py
```

브라우저에서 UI를 통해 용어를 관리할 수 있습니다.

---

### 주요 기능

* 한글 / 영문 / 약어 기준 검색
* 카테고리 필터링
* 테이블 기반 용어 편집
* 용어 검증
* `GLOSSARY.md` 생성
* GitHub commit & push (웹에서 직접 수행)

---

### 상단 버튼 기능

* `check`

  * 용어 검증만 수행

* `generate`

  * `GLOSSARY.md` 생성

* `commit & push`

  * 변경 파일 확인
  * 커밋 메시지 입력
  * 아래 순서로 자동 실행:

    * validate
    * add
    * commit
    * push

* `추가`

  * 신규 용어 추가 모달 열기

---

<img width="1055" height="850" alt="image" src="https://github.com/user-attachments/assets/0f80b4a9-8a3f-4a9c-9130-dd887263876c" />

## 인라인 편집 UX

테이블에서 직접 용어를 수정할 수 있습니다.

### 편집 동작

* 셀 클릭

  * 즉시 입력 모드로 전환

* Enter

  * 저장 후 편집 종료

* Tab / Shift+Tab

  * 저장 후 다음 / 이전 셀 이동

* Esc

  * 수정 취소 (원래 값 복원)

* 다른 행 클릭

  * 현재 셀 자동 저장 후 이동

* categories 클릭

  * 체크박스 형태로 선택 가능

* `...` 버튼

  * note / NOT 관련 필드 편집 또는 삭제

---

### 단축키

* Ctrl + K

  * 검색창 포커스

* Ctrl + N

  * 용어 추가 모달 열기

* Esc

  * 편집 취소 또는 모달 닫기

---

## GitHub 연동

웹 UI에서 직접 GitHub로 변경사항을 반영할 수 있습니다.

### commit & push 동작 흐름

버튼 클릭 시 다음 순서로 실행됩니다:

1. 용어 검증
2. 변경 파일 확인
3. 커밋 메시지 입력
4. Git 작업 수행

   * add
   * commit
   * push

---

## 기본 작업 흐름

일반적인 사용 흐름은 다음과 같습니다:

1. `terms.json` 또는 웹 UI에서 용어 수정
2. `check`로 검증
3. `generate`로 문서 생성
4. `GLOSSARY.md` 결과 확인
5. `commit & push`로 GitHub 반영

---

## 참고

* `terms.json`은 용어의 기준 데이터입니다.
* `GLOSSARY.md`는 생성 결과물이므로 직접 수정하지 않습니다.
* watch 모드를 활용하면 반복 작업을 자동화할 수 있습니다.

