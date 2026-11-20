"""직장인 실무 생산성 도구 및 꿀팁 큐레이션 수집기."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

# 실무 직장인들이 검색량이 높고 반응이 뜨거운 엄선된 생산성 테마 풀
CURATED_SEEDS = [
    {
        "title": "ChatGPT로 엑셀 VLOOKUP·INDEX-MATCH 복합 함수 1분 만에 자동 작성하기",
        "url": "https://chatgpt.com",
        "source_name": "엑셀 업무 자동화",
        "category": "엑셀/데이터",
        "description": "실무에서 가장 많이 쓰는 VLOOKUP, XLOOKUP, INDEX MATCH 수식을 오류 없이 자연어로 요청하고, 조건부 서식과 매크로 VBA 코드까지 즉시 뽑아내는 실전 프롬프트 가이드입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "텍스트 개요만 넣으면 3분 만에 발표자료 슬라이드를 뽑아주는 Gamma AI",
        "url": "https://gamma.app",
        "source_name": "AI 문서·발표",
        "category": "문서/PPT",
        "description": "파워포인트 디자인과 레이아웃 고민 없이, 텍스트 목차나 보고서 내용만 붙여넣으면 고품질 디자인과 시각 다이어그램이 적용된 PPT 슬라이드를 자동 생성하는 무료 도구입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "1시간 분량 회의 녹음 파일을 30초 만에 텍스트 요약본으로 바꾸는 Whisper/Vrew",
        "url": "https://vrew.voyagerx.com",
        "source_name": "회의록 자동화",
        "category": "AI실무",
        "description": "클로바노트 무료 시간이 부족할 때 로컬이나 무료로 음성 파일을 텍스트로 받아쓰고, 참석자별 발언 분리와 안건별 핵심 요약 회의록을 즉시 뽑아내는 방법입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "서식 깨짐 없이 100페이지 영문 PDF 계약서·보고서를 번역하는 무료 툴",
        "url": "https://www.deepl.com/translator/files",
        "source_name": "문서 번역",
        "category": "문서/PPT",
        "description": "표와 그래프 레이아웃이 어그러지는 구글 번역 대신, 원본 서식을 100% 유지하면서 자연스러운 한국어로 번역하는 DeepL 문서 번역 실무 팁입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "노션(Notion)에 반복 업무 체크리스트와 주간 업무 보고서 자동화 구축하기",
        "url": "https://www.notion.so",
        "source_name": "노션 업무 세팅",
        "category": "노션/정리",
        "description": "매주 반복되는 프로젝트 일정, 마감일 디데이 자동 계산, 주간 업무 보고서 템플릿을 한 번 세팅하여 칼퇴를 돕는 노션 데이터베이스 실무 세팅법입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "Stirling-PDF: 개인정보 유출 걱정 없이 로컬에서 무제한 PDF 편집·변환",
        "url": "https://github.com/Stirling-Tools/Stirling-PDF",
        "source_name": "오픈소스 생산성",
        "category": "업무자동화",
        "description": "회사 보안 정책 때문에 유료 사이트에 PDF를 업로드할 수 없을 때, 내 PC에서 안전하게 PDF 합치기, 분할, 암호 해제, OCR 텍스트 추출을 수행하는 오픈소스 무료 도구입니다.",
        "published_at": "2026-11-14",
    },
]


class CuratedCollector:
    """직장인 실무 생산성 큐레이션 아이템 수집."""

    def __init__(self) -> None:
        pass

    def collect(self) -> list[dict[str, Any]]:
        """엄선된 실무 생산성 아이템 목록 반환."""
        return list(CURATED_SEEDS)
