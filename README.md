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
