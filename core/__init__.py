# glossary/core/__init__.py
"""
glossary.core — Glossary 핵심 유틸리티 패키지.

주요 모듈:
  writer.GlossaryWriter — words.json / compounds.json 단일 저장 진입점
"""
from .writer import GlossaryWriter

__all__ = ["GlossaryWriter"]
