"""4대 카테고리 통합 수집기 (업무·생산성, 생활금융·세테크, 모바일·디지털, 1인부업·크리에이터)."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

MULTI_CATEGORY_SEEDS = [
    # -------------------------------------------------------------
    # 1. 업무·생산성
    # -------------------------------------------------------------
    {
        "title": "ChatGPT로 엑셀 VLOOKUP·INDEX-MATCH 복합 함수 1분 만에 자동 작성하기",
        "url": "https://chatgpt.com",
        "source_name": "엑셀 업무 자동화",
        "main_category": "업무·생산성",
        "sub_category": "엑셀/데이터",
        "description": "실무에서 가장 많이 쓰는 VLOOKUP, XLOOKUP, INDEX MATCH 수식을 오류 없이 자연어로 요청하고, 조건부 서식과 매크로 VBA 코드까지 즉시 뽑아내는 실전 프롬프트 가이드입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "텍스트 개요만 넣으면 3분 만에 발표자료 슬라이드를 뽑아주는 Gamma AI",
        "url": "https://gamma.app",
        "source_name": "AI 문서·발표",
        "main_category": "업무·생산성",
        "sub_category": "문서/PPT",
        "description": "파워포인트 디자인과 레이아웃 고민 없이, 텍스트 목차나 보고서 내용만 붙여넣으면 고품질 디자인과 시각 다이어그램이 적용된 PPT 슬라이드를 자동 생성하는 무료 도구입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "1시간 분량 회의 녹음 파일을 30초 만에 텍스트 요약본으로 바꾸는 Whisper/Vrew",
        "url": "https://vrew.voyagerx.com",
        "source_name": "회의록 자동화",
        "main_category": "업무·생산성",
        "sub_category": "회의록/AI",
        "description": "클로바노트 무료 시간이 부족할 때 로컬이나 무료로 음성 파일을 텍스트로 받아쓰고, 참석자별 발언 분리와 안건별 핵심 요약 회의록을 즉시 뽑아내는 방법입니다.",
        "published_at": "2026-11-14",
    },

    # -------------------------------------------------------------
    # 2. 생활금융·세테크
    # -------------------------------------------------------------
    {
        "title": "해외주식 수익 250만원 넘었을 때 양도소득세 0원 만드는 합법 절세법",
        "url": "https://www.hometax.go.kr",
        "source_name": "국세청 홈택스 실전 절세",
        "main_category": "생활금융·세테크",
        "sub_category": "절세/세금",
        "description": "해외주식 250만원 기본공제를 초과하여 수익이 발생했을 때, 배우자 증여(10년 6억원 비과세)를 통해 취득가액을 높여 양도세를 한 푼도 내지 않고 현금화하는 실전 절세 공식입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "ISA 계좌 만기 해지 후 연금저축으로 옮겨 세액공제 300만원 더 받는 법",
        "url": "https://www.fss.or.kr",
        "source_name": "금융감독원 금융 팁",
        "main_category": "생활금융·세테크",
        "sub_category": "연금/절세",
        "description": "3년 만기된 중개형 ISA 잔액을 연금저축펀드나 IRP 계좌로 전환 입금하면 납입금액의 10%(최대 300만원 한도)를 추가 세액공제받아 연말정산 환급금을 극대화하는 세테크 방법입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "하루만 맡겨도 연 3~3.5% 이자 받는 파킹통장 금리 비교 및 복리 세팅법",
        "url": "https://bank-salads.com",
        "source_name": "스마트 파킹통장",
        "main_category": "생활금융·세테크",
        "sub_category": "예적금/파킹통장",
        "description": "수시입출금 통장에 방치된 비상금을 케이뱅크, 토스뱅크, 저축은행 등 매일 이자를 주는 파킹통장으로 이동시켜 1일 단위 복리 효과를 얻는 스마트 금융 세팅입니다.",
        "published_at": "2026-11-14",
    },

    # -------------------------------------------------------------
    # 3. 모바일·디지털생활
    # -------------------------------------------------------------
    {
        "title": "카카오톡 단톡방 티 안 나게 조용히 나가기 및 텍스트 자동 요약 설정법",
        "url": "https://www.kakaocorp.com",
        "source_name": "카카오톡 필수 설정",
        "main_category": "모바일·디지털생활",
        "sub_category": "카카오톡 꿀팁",
        "description": "알림만 쌓이는 수많은 단톡방에서 'OO님이 나갔습니다' 메시지 없이 조용히 나가는 방법과, 쌓인 수백 개 대화를 AI로 3줄 요약해 확인하는 최신 기능 사용법입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "갤럭시 통화녹음 텍스트 자동 변환 및 핵심 요약 무료로 켜는 법",
        "url": "https://www.samsung.com/sec/apps/galaxy-ai",
        "source_name": "삼성 Galaxy AI",
        "main_category": "모바일·디지털생활",
        "sub_category": "스마트폰 설정",
        "description": "별도 유료 앱 설치 없이 삼성 기본 전화 앱의 통화녹음 파일을 텍스트 스크립트로 자동 변환하고, 주요 할 일과 통화 요약본을 즉시 추출해 업무 메모로 남기는 방법입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "아이폰 사진에서 배경(누끼) 1초 만에 따고 스티커·합성 사진 만드는 법",
        "url": "https://support.apple.com/ko-kr/HT213454",
        "source_name": "Apple iOS 팁",
        "main_category": "모바일·디지털생활",
        "sub_category": "아이폰 사진",
        "description": "포토샵 없이 아이폰 기본 사진 앱에서 피사체를 손가락으로 꾹 누르기만 하면 배경이 깔끔하게 지워진 누끼 이미지를 복사하고, 카카오톡 스티커나 인스타 스토리에 합성하는 방법입니다.",
        "published_at": "2026-11-14",
    },

    # -------------------------------------------------------------
    # 4. 1인비즈니스·부업
    # -------------------------------------------------------------
    {
        "title": "Canva + AI로 인스타그램 카드뉴스 10분 만에 5장 찍어내는 템플릿",
        "url": "https://www.canva.com",
        "source_name": "콘텐츠 제작 자동화",
        "main_category": "1인비즈니스·부업",
        "sub_category": "카드뉴스/SNS",
        "description": "디자인 감각이 없어도 ChatGPT로 뽑은 대본을 캔바(Canva) 일괄 생성(Bulk Create) 기능에 연결하여 표지부터 결론까지 카드뉴스 슬라이드 5장을 10분 만에 완성하는 워크플로우입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "Vrew(브루) AI로 대본만 넣고 유튜브 숏폼 자막·영상 15분 만에 완성하기",
        "url": "https://vrew.voyagerx.com",
        "source_name": "숏폼 영상 부업",
        "main_category": "1인비즈니스·부업",
        "sub_category": "유튜브 숏폼",
        "description": "촬영이나 마이크 없이 텍스트 대본만 입력하면 AI 음성 성우, 자동 싱크 자막, 어울리는 무료 영상 소스를 알아서 붙여 쇼츠/릴스용 60초 영상을 초고속으로 만드는 실전 가이드입니다.",
        "published_at": "2026-11-14",
    },
    {
        "title": "스마트스토어 구매전환율 올리는 상품 상세페이지 문구 ChatGPT 작성 공식",
        "url": "https://chatgpt.com",
        "source_name": "이커머스 마케팅",
        "main_category": "1인비즈니스·부업",
        "sub_category": "스마트스토어/상세페이지",
        "description": "상품의 장점만 나열하지 않고 '고객의 불편함 자극 → 해결책 제시 → 신뢰도 증명'의 3단계 설득 공식(PAS)을 적용해 지갑을 열게 만드는 상세페이지 카피라이팅 프롬프트입니다.",
        "published_at": "2026-11-14",
    },
]


class MultiCategoryCollector:
    """4대 카테고리 통합 수집기."""

    def __init__(self) -> None:
        pass

    def collect_all(self) -> list[dict[str, Any]]:
        """4대 카테고리 전체 아이템 반환."""
        return list(MULTI_CATEGORY_SEEDS)

    def collect_by_category(self, main_cat: str) -> list[dict[str, Any]]:
        """특정 카테고리만 필터링하여 반환."""
        return [it for it in MULTI_CATEGORY_SEEDS if it["main_category"] == main_cat]
