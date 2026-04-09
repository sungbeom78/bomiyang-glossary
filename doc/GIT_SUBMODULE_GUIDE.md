# Git & Git Submodule 사용 가이드
## — glossary 레포를 여러 프로젝트에서 공유하는 방법

> Git을 처음 사용하시는 분을 위한 단계별 완전 가이드입니다.
https://github.com/[내계정]/glossary.git

---

## 1단계: Git 기본 개념 (딱 3가지만)

```
커밋(Commit)  : 파일 변경 내용을 저장하는 행위. "저장"과 같음.
레포(Repo)    : 커밋들이 쌓이는 저장소. "프로젝트 폴더 + 변경 이력" 전체.
서브모듈      : 다른 레포를 내 레포 안에 "폴더처럼" 포함시키는 기능.
```

**우리 목표:**
```
[antigravity]    ← 자동매매 프로젝트
  └── glossary/  ← glossary 레포가 submodule로 연결됨

[future-project] ← 다음 프로젝트
  └── glossary/  ← 같은 glossary 레포가 여기도 연결됨
```

두 프로젝트가 같은 glossary를 공유. 한 곳에서 수정하면 양쪽에서 받아쓸 수 있음.

---

## 2단계: 준비 — Git 설치 및 초기 설정

```bash
# Git 설치 확인
git --version
# 출력: git version 2.x.x  → 이미 설치됨
# 없으면: https://git-scm.com 에서 설치

# 최초 1회만: 이름과 이메일 설정 (커밋 기록에 표시됨)
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## 3단계: glossary 레포 만들기

### 3-1. GitHub에서 새 레포 생성
1. https://github.com 접속 → 로그인
2. 우상단 `+` → `New repository`
3. Repository name: `glossary`
4. `Private` 선택 (본인만 사용)
5. `Add a README file` 체크
6. `Create repository` 클릭

### 3-2. 로컬에 클론(다운로드)
```bash
# 원하는 위치로 이동 (예: ~/projects/)
cd ~/projects

# GitHub에서 클론
git clone https://github.com/sungbeom78/bomiyang-glossary
cd glossary
```

### 3-3. 파일 추가 및 첫 커밋
```bash
# glossary 폴더 안에 파일 복사
# (terms.json, GLOSSARY.md, generate_glossary.py, validate.py 를 이 폴더로 복사)

# 파일 구조 확인
ls -la
# 출력:
# terms.json
# GLOSSARY.md
# generate_glossary.py
# validate.py

# Git에 파일 등록 (staging)
git add .

# 커밋 — "이 시점의 스냅샷을 저장"
git commit -m "초기 용어 사전 구성 (225개 용어)"

# GitHub에 업로드
git push origin main
```

---

## 4단계: 기존 프로젝트(antigravity)에 submodule 연결

```bash
# antigravity 프로젝트 루트로 이동
cd ~/projects/antigravity

# submodule 추가
# 형식: git submodule add [레포URL] [폴더명]
git submodule add https://github.com/sungbeom78/bomiyang-glossary glossary

# 이제 폴더 구조:
# antigravity/
#   ├── glossary/        ← submodule (glossary 레포의 내용)
#   │   ├── terms.json
#   │   ├── GLOSSARY.md
#   │   └── ...
#   ├── .gitmodules      ← submodule 정보 파일 (자동 생성)
#   └── ... (기존 파일들)

# .gitmodules 내용 확인
cat .gitmodules
# 출력:
# [submodule "glossary"]
#     path = glossary
#     url = https://github.com/[내계정]/glossary.git

# antigravity 레포에 submodule 연결 정보 커밋
git add .gitmodules glossary
git commit -m "glossary submodule 연결"
git push
```

---

## 5단계: 용어 수정하는 방법

용어 수정은 항상 **glossary 레포에서** 합니다.

```bash
# glossary 폴더로 이동
cd ~/projects/antigravity/glossary
# 또는
cd ~/projects/glossary

# terms.json 수정 (편집기로 열어서 내용 변경)
# 예: 새 용어 추가, 약어 수정 등

# 수정 후 GLOSSARY.md 재생성
python3 generate_glossary.py

# 유효성 검사
python3 validate.py

# 커밋
git add terms.json GLOSSARY.md
git commit -m "용어 추가: backtest 관련 3개 항목"
git push
```

---

## 6단계: 다른 프로젝트에서 glossary 가져오기

### 신규 프로젝트에 연결
```bash
cd ~/projects/new-project
git submodule add https://github.com/[내계정]/glossary.git glossary
```

### 기존 프로젝트에서 최신 glossary 받기
```bash
# 방법 1: glossary 폴더 안에서
cd ~/projects/antigravity/glossary
git pull origin main

# 방법 2: 프로젝트 루트에서
cd ~/projects/antigravity
git submodule update --remote glossary

# 이후 antigravity 레포에도 업데이트 기록 커밋
git add glossary
git commit -m "glossary 최신화"
git push
```

---

## 7단계: 프로젝트를 새 PC에서 클론할 때

```bash
# 일반 클론은 submodule 내용을 가져오지 않음!
git clone https://github.com/[내계정]/antigravity.git
cd antigravity

# submodule 초기화 및 다운로드 (이 명령어 1회 실행)
git submodule update --init --recursive

# 이제 glossary/ 폴더에 내용이 채워짐
```

---

## 전체 워크플로우 요약

```
일상적인 흐름:

1. 용어 추가/수정 필요
   │
   ▼
2. cd ~/projects/glossary (또는 antigravity/glossary)
   terms.json 편집
   python3 generate_glossary.py
   python3 validate.py
   git add . && git commit -m "용어 수정: ..." && git push
   │
   ▼
3. 다른 프로젝트에서 최신화 필요할 때
   cd [프로젝트]
   git submodule update --remote glossary
   git add glossary && git commit -m "glossary 최신화" && git push
```

---

## 자주 쓰는 Git 명령어 치트시트

```bash
# 현재 상태 확인 (변경된 파일 목록)
git status

# 변경 내용 확인 (줄 단위 diff)
git diff

# 모든 파일 staging
git add .

# 특정 파일만 staging
git add terms.json GLOSSARY.md

# 커밋
git commit -m "커밋 메시지"

# GitHub에 올리기
git push

# GitHub에서 받기
git pull

# 커밋 이력 보기
git log --oneline

# 특정 시점으로 파일 되돌리기 (위험! 신중히)
git checkout [커밋해시] -- terms.json
```

---

## 커밋 메시지 규칙 (권장)

```
feat: 새 용어 추가 (backtest 카테고리 5개)
fix:  abbr_short 충돌 수정 (TS → TRK_ST)
docs: GLOSSARY.md 재생성
chore: validate.py 검사 조건 추가
```

---

## 주의사항

```
⚠️  submodule의 파일을 직접 편집 후 antigravity 레포에만 커밋하면
    glossary 레포에는 반영이 안 됩니다.
    항상 glossary 레포에서 먼저 커밋·푸시하세요.

⚠️  terms.json은 항상 valid한 JSON이어야 합니다.
    편집 후 반드시 python3 validate.py 실행하세요.
```


## 참고 - 잘못 추가한 sub module 삭제하기
git rm -f [폴더명] ## 서브모듈 정보 제거 및 파일 삭제
rm -rf .git/modules/[폴더명] ## Git 내부 설정 디렉토리 삭제 // Git은 서브모듈의 기록을 .git/modules 폴더 안에 보관합니다. 이 부분까지 지워야 나중에 같은 이름으로 서브모듈을 추가할 때 충돌이 발생하지 않습니다.
git commit -m "Remove unwanted submodule: [폴더명]"
#### 경로 끝에 슬래시(/)를 붙이지 마세요. 예를 들어 git rm -f folder/가 아니라 git rm -f folder와 같이 입력해야 정확히 인식됩니다.
#### 복구 불가: git rm으로 삭제한 후 커밋하면 해당 서브모듈의 이력이 현재 브랜치에서 제거됩니다. 필요한 데이터가 있다면 미리 백업해 두세요.